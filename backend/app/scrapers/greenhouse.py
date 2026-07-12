import logging

import httpx

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


class GreenhouseScraper(BaseScraper):
    """Uses Greenhouse's public job board JSON API — no auth required.
    `identifier` is the board token, e.g. for https://boards.greenhouse.io/airbnb it's "airbnb".
    """

    platform_name = "greenhouse"
    API_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"

    async def fetch_jobs(self) -> list[RawJob]:
        url = self.API_URL.format(token=self.identifier)
        jobs: list[RawJob] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        for item in data.get("jobs", []):
            try:
                location = (item.get("location") or {}).get("name", "")
                jobs.append(
                    RawJob(
                        title=item.get("title", ""),
                        location=location,
                        apply_url=item.get("absolute_url", ""),
                        external_id=str(item.get("id", "")),
                        description=item.get("content", "") or "",
                        posted_date=_parse_date(item.get("updated_at")),
                        raw=item,
                    )
                )
            except Exception:
                logger.exception("Failed to parse Greenhouse job item for %s", self.identifier)
        return jobs


def _parse_date(value: str | None):
    if not value:
        return None
    from datetime import datetime

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
