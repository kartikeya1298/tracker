import json
import logging
from urllib.parse import urljoin

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


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
          "next_page_selector": ".pagination-next"   // optional
        }

    This intentionally scrapes only the listing page for title/location/link — full
    descriptions are fetched lazily via `fetch_description` when a job first matches
    our role/location filters, to avoid loading every detail page on every 15-min run.
    """

    platform_name = "generic"
    MAX_PAGES = 5

    def __init__(self, identifier: str, timeout: int = 30):
        super().__init__(identifier, timeout)
        self.config = json.loads(identifier)

    async def fetch_jobs(self) -> list[RawJob]:
        jobs: list[RawJob] = []
        cfg = self.config
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                url = cfg["url"]
                for _ in range(self.MAX_PAGES):
                    await page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
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
            page = await browser.new_page()
            try:
                await page.goto(apply_url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                el = await page.query_selector(desc_selector)
                return (await el.inner_text()).strip() if el else ""
            except Exception:
                logger.exception("Failed to fetch description at %s", apply_url)
                return ""
            finally:
                await browser.close()
