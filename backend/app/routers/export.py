import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Job

router = APIRouter(prefix="/api/export", tags=["export"])

COLUMNS = [
    "Company", "Role", "Location", "Experience", "Salary", "Skills",
    "Resume Match %", "Posted Date", "Apply Link",
]


def _rows(db: Session):
    jobs = db.execute(select(Job).options(joinedload(Job.company)).order_by(Job.first_seen_at.desc())).scalars().unique().all()
    for job in jobs:
        yield [
            job.company.name if job.company else "",
            job.title,
            job.location,
            job.experience_required,
            job.salary,
            job.skills or job.ai_skills,
            job.resume_match_score if job.resume_match_score is not None else "",
            job.posted_date.isoformat() if job.posted_date else "",
            job.apply_url,
        ]


@router.get("/csv")
def export_csv(db: Session = Depends(get_db)):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(COLUMNS)
    for row in _rows(db):
        writer.writerow(row)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ds_jobs.csv"},
    )


@router.get("/xlsx")
def export_xlsx(db: Session = Depends(get_db)):
    wb = Workbook()
    ws = wb.active
    ws.title = "DS Jobs"
    ws.append(COLUMNS)
    for row in _rows(db):
        ws.append(row)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=ds_jobs.xlsx"},
    )
