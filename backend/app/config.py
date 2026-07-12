from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://tracker:tracker@localhost:5432/career_tracker"
    redis_url: str = "redis://localhost:6379/0"

    # Scheduler
    scrape_interval_minutes: int = 15
    scraper_concurrency: int = 5
    scraper_request_timeout_seconds: int = 30

    # Filters (defaults, overridable per-request)
    include_remote: bool = True
    include_global: bool = False
    include_internships: bool = False
    target_locations: List[str] = ["india"]
    max_experience_years: float = 2.0

    # AI (Anthropic Claude)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    ai_features_enabled: bool = True

    # Email notifications
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    notification_from_email: str = "career-tracker@example.com"
    notification_to_emails: List[str] = []

    # App
    secret_key: str = "change-me-in-production"
    cors_origins: List[str] = ["http://localhost:3000"]
    resume_text_path: str = "./data/resume.txt"

    playwright_headless: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
