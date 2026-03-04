from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.link_repository import LinkRepo
from app.schemas.link import ShortenRequest, ShortenResponse, StatsResponse


def _get_or_404(db: Session, short_id: str):
    link = LinkRepo.get_by_short_id(db, short_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return link


def shorten(db: Session, payload: ShortenRequest) -> ShortenResponse:
    original_url = str(payload.url)
    link = LinkRepo.create(db, original_url)
    return ShortenResponse(
        short_id=link.short_id,
        short_url=f"{settings.base_domain}/{link.short_id}",
        original_url=original_url,
    )


def resolve(db: Session, short_id: str) -> str:
    link = _get_or_404(db, short_id)
    LinkRepo.increment_clicks(db, link.id)
    return link.original_url


def stats(db: Session, short_id: str) -> StatsResponse:
    link = _get_or_404(db, short_id)
    return StatsResponse(
        short_id=link.short_id,
        original_url=link.original_url,
        clicks=link.clicks,
        created_at=link.created_at,
    )
