from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base

# SQLAlchemy model for the "links" table
class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    short_id = Column(String(12), unique=True, index=True, nullable=False)
    original_url = Column(Text, nullable=False)
    clicks = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Link(id={self.id}, short_id={self.short_id!r})>"
