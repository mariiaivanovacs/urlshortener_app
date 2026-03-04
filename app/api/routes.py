from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.link import ShortenRequest, ShortenResponse, StatsResponse
import app.services.link_service as svc

router = APIRouter()


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
def shorten_url(payload: ShortenRequest, db: Session = Depends(get_db)):
    return svc.shorten(db, payload)


# /stats/{short_id} must be registered before /{short_id} to avoid route conflict
@router.get("/stats/{short_id}", response_model=StatsResponse)
def get_stats(short_id: str, db: Session = Depends(get_db)):
    return svc.stats(db, short_id)


@router.get("/{short_id}", response_class=RedirectResponse)
def redirect(short_id: str, db: Session = Depends(get_db)):
    original_url = svc.resolve(db, short_id)
    return RedirectResponse(url=original_url, status_code=302)
