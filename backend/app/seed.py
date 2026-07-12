import logging

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Company
from app.scrapers.registry import COMPANIES

logger = logging.getLogger(__name__)


def seed_companies():
    db = SessionLocal()
    try:
        existing_slugs = {c.slug for c in db.execute(select(Company)).scalars().all()}
        added = 0
        for entry in COMPANIES:
            if entry["slug"] in existing_slugs:
                continue
            db.add(
                Company(
                    name=entry["name"],
                    slug=entry["slug"],
                    platform=entry["platform"],
                    identifier=entry["identifier"],
                    careers_url=entry["careers_url"],
                    active=True,
                )
            )
            added += 1
        db.commit()
        logger.info("Seeded %s new companies (total tracked: %s)", added, len(COMPANIES))
    finally:
        db.close()
