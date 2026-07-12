from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, Job, ScrapeRun
from app.schemas import StatsResponse

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    total_jobs = db.execute(select(func.count(Job.id))).scalar_one()
    jobs_today = db.execute(select(func.count(Job.id)).where(Job.first_seen_at >= today_start)).scalar_one()
    jobs_week = db.execute(select(func.count(Job.id)).where(Job.first_seen_at >= week_start)).scalar_one()
    companies_tracked = db.execute(select(func.count(Company.id)).where(Company.active.is_(True))).scalar_one()

    by_company_rows = db.execute(
        select(Company.name, func.count(Job.id)).join(Job, Job.company_id == Company.id).group_by(Company.name)
    ).all()
    by_role_rows = db.execute(select(Job.normalized_role, func.count(Job.id)).group_by(Job.normalized_role)).all()
    by_location_rows = db.execute(select(Job.location, func.count(Job.id)).group_by(Job.location)).all()

    last_run = db.execute(select(ScrapeRun).order_by(ScrapeRun.started_at.desc()).limit(1)).scalar_one_or_none()

    return StatsResponse(
        total_jobs=total_jobs,
        jobs_today=jobs_today,
        jobs_this_week=jobs_week,
        companies_tracked=companies_tracked,
        companies_with_jobs=len(by_company_rows),
        by_company=dict(by_company_rows),
        by_role=dict(by_role_rows),
        by_location=dict(by_location_rows),
        last_scrape_at=last_run.finished_at if last_run else None,
        last_scrape_new_jobs=last_run.new_jobs if last_run else 0,
    )
