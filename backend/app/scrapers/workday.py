import logging
from datetime import datetime

import httpx

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


class WorkdayScraper(BaseScraper):
    """Uses the Workday CxS JSON API that backs myworkdayjobs.com career sites.

    `identifier` format: "tenant|dc|site", e.g. "amazon|amazon|amazon_jobs" for a career
    site hosted at https://amazon.wd1.myworkdayjobs.com/amazon_jobs (dc = the workday
    data-center subdomain segment, commonly wd1/wd3/wd5 — verify per company).
    """

    platform_name = "workday"
    PAGE_SIZE = 20
    MAX_PAGES = 25  # safety cap: up to 500 postings per company per run

    def __init__(self, identifier: str, timeout: int = 30):
        super().__init__(identifier, timeout)
        parts = identifier.split("|")
        if len(parts) != 3:
            raise ValueError(f"Workday identifier must be 'tenant|dc|site', got: {identifier!r}")
        self.tenant, self.dc, self.site = parts

    @property
    def base_url(self) -> str:
        return f"https://{self.tenant}.{self.dc}.myworkdayjobs.com"

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/wday/cxs/{self.tenant}/{self.site}/jobs"

    async def fetch_jobs(self) -> list[RawJob]:
        jobs: list[RawJob] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            offset = 0
            for _ in range(self.MAX_PAGES):
                payload = {"appliedFacets": {}, "limit": self.PAGE_SIZE, "offset": offset, "searchText": ""}
                resp = await client.post(self.api_url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                postings = data.get("jobPostings", [])
                if not postings:
                    break
                for item in postings:
                    try:
                        jobs.append(self._parse_posting(item))
                    except Exception:
                        logger.exception("Failed to parse Workday job item for %s", self.identifier)
                total = data.get("total", 0)
                offset += self.PAGE_SIZE
                if offset >= total:
                    break
        return jobs

    def _parse_posting(self, item: dict) -> RawJob:
        path = item.get("externalPath", "")
        apply_url = f"{self.base_url}/{self.site}{path}" if path else self.base_url
        posted_date = _parse_relative_date(item.get("postedOn", ""))
        return RawJob(
            title=item.get("title", ""),
            location=item.get("locationsText", "") or item.get("locationText", ""),
            apply_url=apply_url,
            external_id=item.get("bulletFields", [None])[0] or path,
            description="",  # requires a follow-up detail request; enriched lazily if needed
            posted_date=posted_date,
            raw=item,
        )


def _parse_relative_date(text: str) -> datetime | None:
    """Workday returns fuzzy strings like 'Posted Today' / 'Posted 3 Days Ago'; we don't
    guess an exact timestamp from these, so leave None and rely on first_seen_at instead."""
    return None
