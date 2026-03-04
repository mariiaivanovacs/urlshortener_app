from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.link import Link
from app.utils.base62 import encode_base62


class LinkRepo:
    @staticmethod
    def create(db: Session, original_url: str) -> Link:
        link = Link(original_url=original_url, short_id="")
        db.add(link)
        db.flush()  # populates link.id without committing
        link.short_id = encode_base62(link.id)
        db.commit()
        db.refresh(link)
        return link

    @staticmethod
    def get_by_short_id(db: Session, short_id: str) -> Link | None:
        return db.query(Link).filter(Link.short_id == short_id).first()

    @staticmethod
    def increment_clicks(db: Session, link_id: int) -> None:
        db.execute(
            update(Link).where(Link.id == link_id).values(clicks=Link.clicks + 1)
        )
        db.commit()
