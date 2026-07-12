from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()


def _normalize_database_url(url: str) -> str:
    # Managed Postgres providers (Render, Heroku, Railway, ...) hand back a plain
    # postgres:// or postgresql:// URL; SQLAlchemy needs the +psycopg driver suffix
    # to use psycopg3 instead of defaulting to the (uninstalled) psycopg2.
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


engine = create_engine(_normalize_database_url(settings.database_url), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401  ensures models are registered

    Base.metadata.create_all(bind=engine)
