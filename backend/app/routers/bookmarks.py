from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Bookmark
from app.schemas import BookmarkCreate, BookmarkOut

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


@router.get("", response_model=list[BookmarkOut])
def list_bookmarks(db: Session = Depends(get_db)):
    query = select(Bookmark).options(joinedload(Bookmark.job)).order_by(Bookmark.created_at.desc())
    return db.execute(query).scalars().unique().all()


@router.post("", response_model=BookmarkOut, status_code=201)
def create_bookmark(payload: BookmarkCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(Bookmark).where(Bookmark.job_id == payload.job_id)).scalar_one_or_none()
    if existing:
        return existing
    bookmark = Bookmark(job_id=payload.job_id, note=payload.note)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


@router.delete("/{bookmark_id}", status_code=204)
def delete_bookmark(bookmark_id: str, db: Session = Depends(get_db)):
    bookmark = db.get(Bookmark, bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    db.delete(bookmark)
    db.commit()
