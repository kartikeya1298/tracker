"""Local helper that inspects the career sites this project can't reach automatically.

Run this on YOUR machine (not inside the dev sandbox) — it needs real outbound network
access to career sites, which the sandboxed session this project was built in does not
have. It does two things:

1. Qualcomm's dc subdomain is ambiguous (wd12 vs wd5) — this hits Workday's real CxS
   JSON API directly for both candidates and reports which one actually returns jobs.
   No browser needed, no guessing. (Already resolved as of this tool's last run —
   kept here in case a future company needs the same treatment.)

2. For every other unverified/`custom`-platform company in the registry, it loads the
   career site in a real (headed, to reduce bot-detection false negatives) Chromium and:
   a. Tries to dismiss a cookie-consent banner (OneTrust and similar are extremely
      common and can visually cover/block the results grid even though the DOM behind
      it is fine — but some sites also gate rendering on consent).
   b. Runs the DOM detection heuristic once immediately (covers sites where the search
      query in the URL already works).
   c. If that finds nothing, looks for a search input on the page, types "data
      scientist" into it, submits, waits for the page to settle, and re-runs detection.
      This is the main upgrade over the first pass of this tool — a lot of "no
      candidates found" results turned out to be sites that never actually executed
      the URL-encoded search query without a real keystroke+submit interaction.

   Detection itself groups DOM nodes by tag+class, first by job/career/listing-related
   class-name keywords, then (if that finds nothing — common on sites using hashed
   CSS-in-JS classnames) by "repeated element containing a title-length anchor link."
   For each candidate it captures the selector, how many matched, and an HTML snippet
   of the first two — that snippet is what actually tells us the real
   title/location/link selectors to put in registry.py.

Output: one JSON file per company in ./site_inspections/<slug>.json (now includes a
`stage` field: "initial" or "after_search", so you know which path found it), a
screenshot per company, and a summary.json across all of them.

Usage:
    pip install playwright httpx
    playwright install chromium
    python inspect_career_sites.py                 # all remaining companies
    python inspect_career_sites.py --only zoho,ibm  # just these
    python inspect_career_sites.py --headless       # default is headed
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).parent / "site_inspections"
SEARCH_TEXT = "data scientist"

# The 28 rows still `verified=False` in backend/app/scrapers/registry.py as of this
# tool's last update (2026-07-12, after the first inspection pass resolved 12 more
# companies). If you've since edited registry.py, update this list to match.
CUSTOM_SITES: list[tuple[str, str]] = [
    ("nokia", "https://jobs.nokia.com/en/sites/CX_1/jobs"),
    ("bosch", "https://jobs.bosch.com/en/"),
    ("ericsson", "https://career2.successfactors.eu/careers?company=Ericsson"),
    ("oracle", "https://careers.oracle.com/en/sites/jobsearch/jobs"),
    ("google", "https://www.google.com/about/careers/applications/jobs/results?q=data%20scientist"),
    ("cisco", "https://jobs.cisco.com/jobs/SearchJobs/data%2520scientist"),
    ("ibm", "https://www.ibm.com/careers/search?field_keyword_18[0]=Data%20and%20AI"),
    ("intel", "https://jobs.intel.com/en/search-jobs?k=data%20scientist"),
    ("apple", "https://jobs.apple.com/en-us/search?search=data%20scientist"),
    ("uber", "https://www.uber.com/us/en/careers/list/?query=data%20scientist"),
    ("linkedin", "https://careers.linkedin.com/jobs/search?keywords=data%20scientist"),
    ("servicenow", "https://careers.servicenow.com/jobs/?search=data+scientist"),
    ("snowflake", "https://careers.snowflake.com/us/en/search-results?keywords=data%20scientist"),
    ("jpmorgan-chase", "https://careers.jpmorgan.com/us/en/search-results?keywords=data%20scientist"),
    ("capgemini", "https://www.capgemini.com/careers/join-capgemini/?search=data+scientist"),
    ("cognizant", "https://careers.cognizant.com/global/en/search-results?keywords=data%20scientist"),
    ("tcs", "https://ibegin.tcs.com/iBegin/jobs/search?searchText=data+scientist"),
    ("hcltech", "https://www.hcltech.com/careers/job-search?keywords=data+scientist"),
    ("wipro", "https://careers.wipro.com/careers-home/jobs?keywords=data+scientist"),
    ("tech-mahindra", "https://careers.techmahindra.com/find-a-job?keywords=data+scientist"),
    ("kpmg", "https://kpmg.com/us/en/careers/search-openings.html?q=data+scientist"),
    ("genpact", "https://genpact.taleo.net/careersection/genpact_ext/jobsearch.ftl?searchText=data+scientist"),
    ("dxc-technology", "https://jobs.dxc.com/global/en/search-results?keywords=data%20scientist"),
    ("mphasis", "https://careers.mphasis.com/search?searchText=data+scientist"),
    ("zoho", "https://www.zoho.com/careers/openpositions.html"),
    ("freshworks", "https://www.freshworks.com/company/careers/"),
    ("gocomet", "https://gocomet.com/careers/"),
    ("samsung-rd", "https://www.samsung.com/in/careers/job-search/"),
]

QUALCOMM_CANDIDATES = [
    ("qualcomm", "wd12", "External"),
    ("qualcomm", "wd5", "External"),
]

COOKIE_BANNER_SELECTORS = [
    "#onetrust-accept-btn-handler",  # OneTrust - extremely common
    "button#onetrust-accept-btn-handler",
    "#truste-consent-button",
    "button[aria-label='Accept all cookies']",
    "button[aria-label='Accept All Cookies']",
    "button[aria-label='Accept Cookies']",
    "button[title='Accept all cookies']",
    "[id*='accept' i][id*='cookie' i]",
    "[class*='accept' i][class*='cookie' i]",
    "button:has-text('Accept All')",
    "button:has-text('Accept all')",
    "button:has-text('Accept Cookies')",
    "button:has-text('I Accept')",
    "button:has-text('I Agree')",
    "button:has-text('Allow all')",
    "button:has-text('Allow All')",
    "button:has-text('Got it')",
]

SEARCH_INPUT_SELECTORS = [
    "input[type='search']",
    "input[placeholder*='search' i]",
    "input[placeholder*='keyword' i]",
    "input[placeholder*='job title' i]",
    "input[aria-label*='search' i]",
    "input[aria-label*='keyword' i]",
    "input[name*='keyword' i]",
    "input[name='q']",
    "input#keyword",
    "input.search-input",
    "input[data-testid*='search' i]",
]

SEARCH_SUBMIT_SELECTORS = [
    "button[type='submit']",
    "button[aria-label*='search' i]",
    "button.search-button",
    "button:has-text('Search')",
    "button:has-text('Find Jobs')",
]

DETECT_JS = r"""
() => {
  function selectorFor(el) {
    const cls = (el.className && typeof el.className === 'string') ? el.className.trim() : '';
    const classPart = cls ? '.' + cls.split(/\s+/).filter(Boolean).join('.') : '';
    return el.tagName.toLowerCase() + classPart;
  }

  const KEYWORDS = ['job','career','posting','listing','result','card','tile','vacancy','position','req'];
  const all = Array.from(document.querySelectorAll('body *'));

  // Pass 1: class name hints at "job listing"
  const byKeyword = {};
  for (const el of all) {
    if (!el.className || typeof el.className !== 'string' || !el.className.trim()) continue;
    const lower = el.className.toLowerCase();
    if (!KEYWORDS.some(k => lower.includes(k))) continue;
    const key = selectorFor(el);
    (byKeyword[key] = byKeyword[key] || []).push(el);
  }

  // Pass 2 (fallback for hashed/CSS-in-JS classnames): repeated element containing a
  // title-length anchor link.
  const byAnchor = {};
  for (const el of all) {
    if (!el.className || typeof el.className !== 'string' || !el.className.trim()) continue;
    const anchor = el.tagName.toLowerCase() === 'a' ? el : el.querySelector('a');
    if (!anchor) continue;
    const text = (anchor.innerText || '').trim();
    if (text.length < 10 || text.length > 120) continue;
    const key = selectorFor(el);
    (byAnchor[key] = byAnchor[key] || []).push(el);
  }

  function topCandidates(groups) {
    return Object.entries(groups)
      .filter(([, els]) => els.length >= 3 && els.length <= 500)
      .sort((a, b) => b[1].length - a[1].length)
      .slice(0, 6)
      .map(([selector, els]) => ({
        selector,
        count: els.length,
        sample_html: els.slice(0, 2).map(el => el.outerHTML.slice(0, 1500)),
        sample_text: els.slice(0, 2).map(el => (el.innerText || '').slice(0, 200)),
      }));
  }

  const keywordCandidates = topCandidates(byKeyword);
  const seen = new Set(keywordCandidates.map(c => c.selector));
  const anchorCandidates = topCandidates(byAnchor).filter(c => !seen.has(c.selector));

  return {
    keyword_candidates: keywordCandidates,
    structural_candidates: anchorCandidates,
    page_title: document.title,
  };
}
"""


def verify_qualcomm() -> dict:
    print("== Qualcomm (direct Workday API check, no browser) ==")
    result = {}
    for tenant, dc, site in QUALCOMM_CANDIDATES:
        url = f"https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
        try:
            resp = httpx.post(
                url, json={"appliedFacets": {}, "limit": 5, "offset": 0, "searchText": SEARCH_TEXT},
                timeout=20,
            )
            ok = resp.status_code == 200 and "jobPostings" in resp.text
            count = resp.json().get("total") if ok else None
            print(f"  dc={dc}: HTTP {resp.status_code}, jobPostings present={ok}, total={count}")
            result[dc] = {"status_code": resp.status_code, "ok": ok, "total": count}
        except Exception as exc:  # noqa: BLE001
            print(f"  dc={dc}: request failed ({exc})")
            result[dc] = {"error": str(exc)}
    return result


def dismiss_cookie_banner(page: Page) -> bool:
    for sel in COOKIE_BANNER_SELECTORS:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click(timeout=2000)
                page.wait_for_timeout(500)
                return True
        except PlaywrightError:
            continue
    return False


def try_search_interaction(page: Page) -> bool:
    """Find a search box, type the target query, submit, and wait for the page to
    settle. Returns True if an input was found and interacted with (not whether it
    produced results — caller re-runs detection to check that)."""
    search_input = None
    for sel in SEARCH_INPUT_SELECTORS:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                search_input = el
                break
        except PlaywrightError:
            continue

    if search_input is None:
        return False

    try:
        search_input.click(timeout=2000)
        search_input.fill("")
        search_input.type(SEARCH_TEXT, delay=30)
    except PlaywrightError:
        return False

    submitted = False
    for sel in SEARCH_SUBMIT_SELECTORS:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click(timeout=2000)
                submitted = True
                break
        except PlaywrightError:
            continue
    if not submitted:
        try:
            search_input.press("Enter")
        except PlaywrightError:
            pass

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightError:
        pass
    page.wait_for_timeout(2500)
    return True


def inspect_site(browser, slug: str, url: str, timeout_ms: int) -> dict:
    print(f"== {slug} -> {url}")
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    record: dict = {"slug": slug, "url": url}
    try:
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightError:
            pass
        page.wait_for_timeout(2000)

        dismissed = dismiss_cookie_banner(page)
        if dismissed:
            print("   -> dismissed a cookie banner")

        analysis = page.evaluate(DETECT_JS)
        n_candidates = len(analysis.get("keyword_candidates", [])) + len(analysis.get("structural_candidates", []))
        stage = "initial"

        if n_candidates == 0:
            print("   -> no candidates on initial load, trying search interaction...")
            interacted = try_search_interaction(page)
            if interacted:
                analysis = page.evaluate(DETECT_JS)
                n_candidates = len(analysis.get("keyword_candidates", [])) + len(analysis.get("structural_candidates", []))
                stage = "after_search"
                print(f"   -> after search: {n_candidates} candidates" if n_candidates else "   -> still nothing after search")
            else:
                print("   -> no search box found on page")

        record.update(analysis)
        record["stage"] = stage
        record["cookie_banner_dismissed"] = dismissed
        record["status"] = "ok" if n_candidates > 0 else "no_candidates_found"

        screenshot_path = OUTPUT_DIR / f"{slug}.png"
        page.screenshot(path=str(screenshot_path), full_page=False)
        record["screenshot"] = screenshot_path.name

        print(f"   -> {n_candidates} candidate patterns found (stage={stage})")
        if n_candidates == 0:
            print("   -> WARNING: nothing matched even after search interaction. May need login, may be canvas/iframe-rendered, or uses a non-standard search UI.")
    except PlaywrightError as exc:
        record["status"] = "blocked_or_error"
        record["error"] = str(exc)
        print(f"   -> FAILED: {exc}")
    finally:
        page.close()
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="Comma-separated slugs to run instead of all companies")
    parser.add_argument("--headless", action="store_true", help="Run headless (default: headed, less likely to be bot-blocked)")
    parser.add_argument("--timeout", type=int, default=45000, help="Per-site navigation timeout in ms (default 45000)")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds to wait between sites (politeness)")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    sites = CUSTOM_SITES
    if args.only:
        wanted = set(args.only.split(","))
        sites = [(s, u) for s, u in CUSTOM_SITES if s in wanted]
        if not sites and "qualcomm" not in wanted:
            print(f"No matching slugs for --only={args.only}")
            sys.exit(1)

    summary = {}

    if args.only and "qualcomm" in args.only.split(","):
        summary["qualcomm"] = verify_qualcomm()
        (OUTPUT_DIR / "qualcomm.json").write_text(json.dumps(summary["qualcomm"], indent=2))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        try:
            for i, (slug, url) in enumerate(sites):
                record = inspect_site(browser, slug, url, args.timeout)
                (OUTPUT_DIR / f"{slug}.json").write_text(json.dumps(record, indent=2))
                summary[slug] = record.get("status")
                if i < len(sites) - 1:
                    time.sleep(args.delay)
        finally:
            browser.close()

    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nDone. Results in {OUTPUT_DIR}/ — send that folder back (or paste individual .json files).")
    ok = sum(1 for v in summary.values() if v == "ok")
    print(f"{ok} sites yielded candidate patterns; {len(summary) - ok} need a closer look (see status field).")


if __name__ == "__main__":
    main()
