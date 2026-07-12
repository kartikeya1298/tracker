from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Company, Job
from app.pipeline import run_pipeline
from app.schemas import JobListResponse, JobOut

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
def list_jobs(
    db: Session = Depends(get_db),
    search: str | None = None,
    company: list[str] | None = Query(None),
    role: list[str] | None = Query(None),
    location: str | None = None,
    india_only: bool = False,
    include_remote: bool = True,
    include_internships: bool = False,
    sort_by: str = Query("rank_score", pattern="^(rank_score|posted_date|first_seen_at|title)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Job).options(joinedload(Job.company)).join(Company)

    if search:
        like = f"%{search}%"
        query = query.where(
            or_(Job.title.ilike(like), Job.description.ilike(like), Company.name.ilike(like), Job.skills.ilike(like))
        )
    if company:
        query = query.where(Company.slug.in_(company))
    if role:
        query = query.where(Job.normalized_role.in_(role))
    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
    if india_only:
        query = query.where(Job.is_india.is_(True))
    if not include_remote:
        query = query.where(Job.is_remote.is_(False) | Job.is_india.is_(True))
    if not include_internships:
        query = query.where(Job.is_internship.is_(False))

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    sort_col = getattr(Job, sort_by)
    sort_col = sort_col.desc() if order == "desc" else sort_col.asc()
    query = query.order_by(sort_col).offset(offset).limit(limit)

    items = db.execute(query).scalars().unique().all()
    return JobListResponse(total=total, items=items)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id, options=[joinedload(Job.company)])
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/scrape-now")
async def trigger_scrape_now():
    """Manually trigger a scrape cycle outside the 15-minute schedule (useful for testing)."""
    run = await run_pipeline()
    return {
        "companies_scraped": run.companies_scraped,
        "jobs_found": run.jobs_found,
        "new_jobs": run.new_jobs,
        "errors": run.errors,
    }
