from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawJob:
    """Normalized job record produced by every scraper adapter, prior to filtering/AI enrichment."""

    title: str
    location: str
    apply_url: str
    external_id: str = ""
    description: str = ""
    salary: str = ""
    experience_text: str = ""
    posted_date: datetime | None = None
    raw: dict = field(default_factory=dict)


class BaseScraper(ABC):
    """Every ATS adapter implements `fetch_jobs`, returning normalized RawJob records
    for a single company. Adapters should be resilient: catch and log per-item parsing
    errors rather than failing the whole run, and respect request timeouts."""

    platform_name: str = "base"

    def __init__(self, identifier: str, timeout: int = 30):
        self.identifier = identifier
        self.timeout = timeout

    @abstractmethod
    async def fetch_jobs(self) -> list[RawJob]:
        ...
