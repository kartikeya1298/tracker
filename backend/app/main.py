import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import applications, bookmarks, companies, export, jobs, stats
from app.scheduler import start_scheduler, stop_scheduler
from app.seed import seed_companies

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_companies()
    start_scheduler()
    logger.info("DataScience Career Tracker AI backend started")
    yield
    stop_scheduler()


app = FastAPI(title="DataScience Career Tracker AI", version="1.0.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(companies.router)
app.include_router(stats.router)
app.include_router(bookmarks.router)
app.include_router(applications.router)
app.include_router(export.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
