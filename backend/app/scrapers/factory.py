from app.models import ATSPlatform
from app.scrapers.base import BaseScraper
from app.scrapers.generic import GenericPlaywrightScraper
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.scrapers.workday import WorkdayScraper

_ADAPTERS: dict[ATSPlatform, type[BaseScraper]] = {
    ATSPlatform.GREENHOUSE: GreenhouseScraper,
    ATSPlatform.LEVER: LeverScraper,
    ATSPlatform.WORKDAY: WorkdayScraper,
    ATSPlatform.TALEO: GenericPlaywrightScraper,
    ATSPlatform.SUCCESSFACTORS: GenericPlaywrightScraper,
    ATSPlatform.ORACLE_CAREERS: GenericPlaywrightScraper,
    ATSPlatform.SAP_CAREERS: GenericPlaywrightScraper,
    ATSPlatform.CUSTOM: GenericPlaywrightScraper,
}


def get_scraper(platform: ATSPlatform, identifier: str, timeout: int = 30) -> BaseScraper:
    adapter_cls = _ADAPTERS.get(platform)
    if adapter_cls is None:
        raise ValueError(f"No scraper adapter registered for platform: {platform}")
    return adapter_cls(identifier, timeout=timeout)
