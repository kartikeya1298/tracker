import logging
from datetime import datetime, timezone

import httpx

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


class LeverScraper(BaseScraper):
    """Uses Lever's public postings JSON API — no auth required.
    `identifier` is the Lever site/company slug, e.g. for https://jobs.lever.co/netflix it's "netflix".
    """

    platform_name = "lever"
    API_URL = "https://api.lever.co/v0/postings/{site}?mode=json"

    async def fetch_jobs(self) -> list[RawJob]:
        url = self.API_URL.format(site=self.identifier)
        jobs: list[RawJob] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        for item in data:
            try:
                categories = item.get("categories", {}) or {}
                location = categories.get("location", "") or ""
                description = "\n".join(
                    filter(
                        None,
                        [
                            item.get("descriptionPlain", ""),
                            "\n".join(
                                (lst.get("text", "") or "") + "\n" + "\n".join(lst.get("content", []) or [])
                                for lst in item.get("lists", [])
                            ),
                        ],
                    )
                )
                posted_ms = item.get("createdAt")
                posted_date = (
                    datetime.fromtimestamp(posted_ms / 1000, tz=timezone.utc) if posted_ms else None
                )
                jobs.append(
                    RawJob(
                        title=item.get("text", ""),
                        location=location,
                        apply_url=item.get("hostedUrl", ""),
                        external_id=item.get("id", ""),
                        description=description,
                        posted_date=posted_date,
                        raw=item,
                    )
                )
            except Exception:
                logger.exception("Failed to parse Lever job item for %s", self.identifier)
        return jobs
