import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.enrichment import enrich_job
from app.ai.resume import load_resume_text
from app.config import get_settings
from app.core.dedup import compute_dedup_hash
from app.core.filters import (
    is_entry_level,
    is_internship,
    is_remote_location,
    location_passes_filter,
    parse_experience,
)
from app.core.ranking import compute_rank_score
from app.core.roles import match_role
from app.database import SessionLocal
from app.models import Company, Job, NotificationLog, ScrapeRun
from app.notifications.email import send_job_notification
from app.scrapers.base import RawJob
from app.scrapers.factory import get_scraper

logger = logging.getLogger(__name__)


async def scrape_company(company: Company) -> tuple[Company, list[RawJob], str | None]:
    settings = get_settings()
    try:
        scraper = get_scraper(company.platform, company.identifier, timeout=settings.scraper_request_timeout_seconds)
        jobs = await scraper.fetch_jobs()
        return company, jobs, None
    except Exception as exc:  # noqa: BLE001 - isolate per-company failures
        logger.exception("Scrape failed for %s", company.name)
        return company, [], str(exc)


async def run_pipeline() -> ScrapeRun:
    """Full monitoring cycle: scrape all active companies concurrently, filter to
    target roles/experience/location, dedup against existing jobs, enrich new matches
    with AI, persist, and send notifications. Designed to be called by the scheduler
    every `scrape_interval_minutes`, and safe to call manually/on-demand."""
    settings = get_settings()
    db: Session = SessionLocal()
    run = ScrapeRun()
    db.add(run)
    db.commit()
    db.refresh(run)

    errors: list[str] = []
    total_jobs_found = 0
    new_jobs_count = 0
    companies: list[Company] = []

    try:
        companies = db.execute(select(Company).where(Company.active.is_(True))).scalars().all()
        resume_text = load_resume_text()

        semaphore = asyncio.Semaphore(settings.scraper_concurrency)

        async def bounded_scrape(c: Company):
            async with semaphore:
                return await scrape_company(c)

        results = await asyncio.gather(*(bounded_scrape(c) for c in companies))

        for company, raw_jobs, error in results:
            if error:
                errors.append(f"{company.name}: {error}")
                continue
            total_jobs_found += len(raw_jobs)

            for raw in raw_jobs:
                role = match_role(raw.title)
                if role is None:
                    continue

                internship = is_internship(raw.title, raw.description)
                if internship and not settings.include_internships:
                    continue

                if not location_passes_filter(raw.location, settings.include_remote, settings.include_global):
                    continue

                exp_range = parse_experience(f"{raw.experience_text} {raw.description}")
                if not is_entry_level(raw.title, raw.description, exp_range, settings.max_experience_years):
                    continue

                dedup_hash = compute_dedup_hash(company.slug, raw.external_id, raw.title, raw.location)
                existing = db.execute(select(Job).where(Job.dedup_hash == dedup_hash)).scalar_one_or_none()
                if existing:
                    continue  # already tracked, never re-notify

                job = Job(
                    company_id=company.id,
                    title=raw.title,
                    normalized_role=role,
                    location=raw.location,
                    is_india=location_passes_filter(raw.location, False, False),
                    is_remote=is_remote_location(raw.location),
                    is_internship=internship,
                    experience_required=exp_range.raw_text,
                    min_experience_years=exp_range.min_years,
                    max_experience_years=exp_range.max_years,
                    description=raw.description,
                    apply_url=raw.apply_url,
                    external_id=raw.external_id,
                    posted_date=raw.posted_date or datetime.now(timezone.utc),
                    dedup_hash=dedup_hash,
                )

                if settings.ai_features_enabled:
                    enrichment = await enrich_job(raw.title, company.name, raw.location, raw.description, resume_text)
                    job.ai_summary = enrichment.summary
                    job.ai_skills = ", ".join(enrichment.skills)
                    job.skills = job.ai_skills
                    job.resume_match_score = enrichment.resume_match_score
                    job.resume_match_notes = enrichment.resume_match_notes
                    job.learning_recommendations = enrichment.learning_recommendations

                job.rank_score = compute_rank_score(raw.title, company.slug, job.resume_match_score)

                db.add(job)
                db.commit()
                db.refresh(job)
                new_jobs_count += 1

                sent = send_job_notification(job, company)
                job.notified = sent
                db.add(NotificationLog(job_id=job.id, channel="email", success=sent))
                db.commit()

    finally:
        run.finished_at = datetime.now(timezone.utc)
        run.companies_scraped = len(companies)
        run.jobs_found = total_jobs_found
        run.new_jobs = new_jobs_count
        run.errors = "\n".join(errors)
        db.add(run)
        db.commit()
        db.close()

    return run
