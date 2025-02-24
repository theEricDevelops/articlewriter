from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..models import Base

# SQLAlchemy model for the database
class Topic(Base):
    """Represents a topic in the database."""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.now(datetime.timezone.utc))

    # Relationships
    articles = relationship("Article", back_populates="topic")
    outlines = relationship("Outline", back_populates="topic")