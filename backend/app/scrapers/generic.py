import json
import logging
from urllib.parse import urljoin

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

# A realistic desktop UA + masking navigator.webdriver clears basic bot-detection
# checks (navigator.webdriver === true is a very common, cheap signal) that a few
# of the registry's configured sites are known to trip on a bare Playwright profile.
REALISTIC_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
MASK_WEBDRIVER_JS = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"


class GenericPlaywrightScraper(BaseScraper):
    """Config-driven scraper for career sites that don't expose a public JSON API
    (SuccessFactors, Oracle Taleo/Oracle Careers, SAP Careers, and one-off custom sites).

    `identifier` is a JSON blob describing how to scrape the listing page, e.g.:

        {
          "url": "https://careers.example.com/search?q=data+scientist",
          "wait_selector": ".job-list-item",
          "item_selector": ".job-list-item",
          "title_selector": ".job-title",
          "location_selector": ".job-location",
          "link_selector": "a",
          "link_attr": "href",
          "next_page_selector": ".pagination-next",  // optional
          "search_input_selector": "input[type=search]",   // optional
          "search_submit_selector": "button.search-btn",   // optional; falls back to Enter
          "search_text": "data scientist"                  // optional; defaults below
        }

    `search_input_selector` exists because several sites (Apple, Snowflake, IBM as of
    this comment) don't actually run a search from the URL's query string alone on
    initial page load — the query param is present but the client-side search only
    fires from a real keystroke+submit against the search box. When configured, this
    fills that box and submits before scanning for listings. Known limitation: only
    one search term runs per scrape cycle, so a site gated this way will only surface
    postings matching that literal phrase, not the full 20-role catalog the way an
    API-backed adapter (which returns everything and lets our own role matcher filter)
    would — "data scientist" is chosen as the broadest single term with the best hit
    rate across the target roles, but it will still under-count roles that don't share
    that phrase (e.g. "Business Analyst").

    This intentionally scrapes only the listing page for title/location/link — full
    descriptions are fetched lazily via `fetch_description` when a job first matches
    our role/location filters, to avoid loading every detail page on every 15-min run.
    """

    platform_name = "generic"
    MAX_PAGES = 5
    DEFAULT_SEARCH_TEXT = "data scientist"

    def __init__(self, identifier: str, timeout: int = 30):
        super().__init__(identifier, timeout)
        self.config = json.loads(identifier)

    async def _run_search_interaction(self, page, cfg: dict) -> None:
        input_sel = cfg.get("search_input_selector")
        if not input_sel:
            return
        try:
            await page.fill(input_sel, cfg.get("search_text", self.DEFAULT_SEARCH_TEXT), timeout=5000)
            submit_sel = cfg.get("search_submit_selector")
            if submit_sel:
                await page.click(submit_sel, timeout=5000)
            else:
                await page.press(input_sel, "Enter")
            await page.wait_for_load_state("networkidle", timeout=15000)
            await page.wait_for_timeout(1500)
        except PlaywrightError:
            logger.warning("Search interaction failed for %s (selector %s)", cfg.get("url"), input_sel)

    async def fetch_jobs(self) -> list[RawJob]:
        jobs: list[RawJob] = []
        cfg = self.config
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=REALISTIC_UA)
            await page.add_init_script(MASK_WEBDRIVER_JS)
            try:
                url = cfg["url"]
                search_done = False
                for _ in range(self.MAX_PAGES):
                    await page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                    if not search_done:
                        await self._run_search_interaction(page, cfg)
                        search_done = True
                    wait_selector = cfg.get("wait_selector", cfg["item_selector"])
                    try:
                        await page.wait_for_selector(wait_selector, timeout=self.timeout * 1000)
                    except Exception:
                        logger.warning("No results matched %s at %s", wait_selector, url)
                        break

                    items = await page.query_selector_all(cfg["item_selector"])
                    if not items:
                        break

                    for item in items:
                        try:
                            title_el = await item.query_selector(cfg["title_selector"])
                            location_el = await item.query_selector(cfg.get("location_selector", ""))
                            link_el = await item.query_selector(cfg.get("link_selector", "a"))

                            title = (await title_el.inner_text()).strip() if title_el else ""
                            location = (await location_el.inner_text()).strip() if location_el else ""
                            href = ""
                            if link_el:
                                href = await link_el.get_attribute(cfg.get("link_attr", "href")) or ""
                            apply_url = urljoin(url, href) if href else url

                            if title:
                                jobs.append(
                                    RawJob(
                                        title=title,
                                        location=location,
                                        apply_url=apply_url,
                                        external_id=apply_url,
                                    )
                                )
                        except Exception:
                            logger.exception("Failed to parse listing item at %s", url)

                    next_selector = cfg.get("next_page_selector")
                    if not next_selector:
                        break
                    next_btn = await page.query_selector(next_selector)
                    if not next_btn:
                        break
                    await next_btn.click()
                    await page.wait_for_timeout(1500)
                    url = page.url
            finally:
                await browser.close()
        return jobs

    async def fetch_description(self, apply_url: str) -> str:
        cfg = self.config
        desc_selector = cfg.get("description_selector", "body")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=REALISTIC_UA)
            await page.add_init_script(MASK_WEBDRIVER_JS)
            try:
                await page.goto(apply_url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                el = await page.query_selector(desc_selector)
                return (await el.inner_text()).strip() if el else ""
            except Exception:
                logger.exception("Failed to fetch description at %s", apply_url)
                return ""
            finally:
                await browser.close()
