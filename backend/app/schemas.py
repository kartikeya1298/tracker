from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import ApplicationStatus, ATSPlatform


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    platform: ATSPlatform
    careers_url: str
    logo_url: str
    active: bool


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    title: str
    normalized_role: str
    location: str
    is_india: bool
    is_remote: bool
    is_internship: bool
    experience_required: str
    min_experience_years: float | None
    max_experience_years: float | None
    salary: str
    description: str
    skills: str
    apply_url: str
    posted_date: datetime | None
    ai_summary: str
    ai_skills: str
    resume_match_score: float | None
    resume_match_notes: str
    learning_recommendations: str
    rank_score: float | None
    first_seen_at: datetime
    company: CompanyOut | None = None


class JobListResponse(BaseModel):
    total: int
    items: list[JobOut]


class StatsResponse(BaseModel):
    total_jobs: int
    jobs_today: int
    jobs_this_week: int
    companies_tracked: int
    companies_with_jobs: int
    by_company: dict[str, int]
    by_role: dict[str, int]
    by_location: dict[str, int]
    last_scrape_at: datetime | None
    last_scrape_new_jobs: int


class BookmarkCreate(BaseModel):
    job_id: str
    note: str = ""


class BookmarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    note: str
    created_at: datetime
    job: JobOut | None = None


class ApplicationCreate(BaseModel):
    job_id: str
    status: ApplicationStatus = ApplicationStatus.SAVED
    notes: str = ""


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    status: ApplicationStatus
    notes: str
    applied_at: datetime | None
    created_at: datetime
    updated_at: datetime
    job: JobOut | None = None
