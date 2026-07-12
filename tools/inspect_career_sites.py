"""Local helper that inspects the career sites this project can't reach automatically.

Run this on YOUR machine (not inside the dev sandbox) — it needs real outbound network
access to career sites, which the sandboxed session this project was built in does not
have. It does two things:

1. Qualcomm's dc subdomain is ambiguous (wd12 vs wd5) — this hits Workday's real CxS
   JSON API directly for both candidates and reports which one actually returns jobs.
   No browser needed, no guessing.

2. For every other unverified/`custom`-platform company in the registry, it loads the
   career site in a real (headed, to reduce bot-detection false negatives) Chromium,
   and runs a heuristic in-page scan for repeated "job card" elements — grouping DOM
   nodes by tag+class, first by job/career/listing-related class-name keywords, then
   (if that finds nothing — common on sites using hashed CSS-in-JS classnames) by
   "repeated element containing a title-length anchor link." For each candidate it
   captures the selector, how many matched, and an HTML snippet of the first two — that
   snippet is what actually tells us the real title/location/link selectors to put in
   registry.py, which a full-page HTML dump would bury in noise.

Output: one JSON file per company in ./site_inspections/<slug>.json, a screenshot per
company for visual cross-check, and a summary.json across all of them. Send the
site_inspections/ folder (or just paste individual JSON files) back and the registry
config gets written directly from the candidates you point at.

Usage:
    pip install playwright httpx
    playwright install chromium
    python inspect_career_sites.py                 # all companies
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
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).parent / "site_inspections"

# Kept in sync with the `verified=False` / platform=CUSTOM|SUCCESSFACTORS|ORACLE_CAREERS|
# SAP_CAREERS rows in backend/app/scrapers/registry.py as of this tool's authoring.
# If you've since edited registry.py, update this list to match — it's intentionally
# standalone (no dependency on the backend's Python environment) so it runs with just
# playwright+httpx installed.
CUSTOM_SITES: list[tuple[str, str]] = [
    ("nokia", "https://jobs.nokia.com/en/sites/CX_1/jobs"),
    ("sap", "https://jobs.sap.com/search/"),
    ("siemens", "https://jobs.siemens.com/en_US/externaljobs/SearchJobs"),
    ("bosch", "https://jobs.bosch.com/en/"),
    ("ericsson", "https://career2.successfactors.eu/careers?company=Ericsson"),
    ("oracle", "https://careers.oracle.com/en/sites/jobsearch/jobs"),
    ("amazon", "https://www.amazon.jobs/en/search?base_query=data+scientist"),
    ("microsoft", "https://jobs.careers.microsoft.com/global/en/search?q=data%20scientist"),
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
    ("goldman-sachs", "https://higher.gs.com/roles?query=data%20scientist"),
    ("deloitte", "https://apply.deloitte.com/careers/SearchJobs/data-scientist"),
    ("accenture", "https://www.accenture.com/in-en/careers/jobsearch?jk=data%20scientist"),
    ("capgemini", "https://www.capgemini.com/careers/join-capgemini/?search=data+scientist"),
    ("cognizant", "https://careers.cognizant.com/global/en/search-results?keywords=data%20scientist"),
    ("infosys", "https://career.infosys.com/jobs?searchText=data%20scientist"),
    ("tcs", "https://ibegin.tcs.com/iBegin/jobs/search?searchText=data+scientist"),
    ("hcltech", "https://www.hcltech.com/careers/job-search?keywords=data+scientist"),
    ("wipro", "https://careers.wipro.com/careers-home/jobs?keywords=data+scientist"),
    ("tech-mahindra", "https://careers.techmahindra.com/find-a-job?keywords=data+scientist"),
    ("ltimindtree", "https://careers.ltimindtree.com/search?searchText=data+scientist"),
    ("ey", "https://careers.ey.com/ey/search/?q=data+scientist"),
    ("pwc", "https://jobs.us.pwc.com/search-jobs/data%20scientist"),
    ("kpmg", "https://kpmg.com/us/en/careers/search-openings.html?q=data+scientist"),
    ("genpact", "https://genpact.taleo.net/careersection/genpact_ext/jobsearch.ftl?searchText=data+scientist"),
    ("dxc-technology", "https://jobs.dxc.com/global/en/search-results?keywords=data%20scientist"),
    ("mphasis", "https://careers.mphasis.com/search?searchText=data+scientist"),
    ("zoho", "https://www.zoho.com/careers/openpositions.html"),
    ("freshworks", "https://www.freshworks.com/company/careers/"),
    ("gocomet", "https://gocomet.com/careers/"),
    ("samsung-rd", "https://www.samsung.com/in/careers/job-search/"),
]

# Workday's real public CxS API. Qualcomm's dc segment was ambiguous from search results
# (wd12 vs wd5) — hit both directly and see which actually returns postings.
QUALCOMM_CANDIDATES = [
    ("qualcomm", "wd12", "External"),
    ("qualcomm", "wd5", "External"),
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
                url, json={"appliedFacets": {}, "limit": 5, "offset": 0, "searchText": "data scientist"},
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


def inspect_site(browser, slug: str, url: str, timeout_ms: int) -> dict:
    print(f"== {slug} -> {url}")
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    record: dict = {"slug": slug, "url": url}
    try:
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightError:
            pass  # some sites never go idle (polling widgets); proceed anyway
        page.wait_for_timeout(2000)  # let client-side rendering settle

        analysis = page.evaluate(DETECT_JS)
        record.update(analysis)
        record["status"] = "ok"

        screenshot_path = OUTPUT_DIR / f"{slug}.png"
        page.screenshot(path=str(screenshot_path), full_page=False)
        record["screenshot"] = screenshot_path.name

        n_candidates = len(analysis.get("keyword_candidates", [])) + len(analysis.get("structural_candidates", []))
        print(f"   -> {n_candidates} candidate patterns found")
        if n_candidates == 0:
            record["status"] = "no_candidates_found"
            print("   -> WARNING: nothing matched. Site may need login, may be entirely canvas/iframe-rendered, or search box needs interaction.")
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

    if not args.only or "qualcomm" in (args.only or "").split(","):
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
