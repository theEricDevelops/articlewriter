from sqlalchemy import Column, Integer, String
from . import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy import DateTime

# SQLAlchemy model for the database
class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.now(datetime.timezone.utc))

# Pydantic model for request/response validation
class TopicModel(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows mapping from SQLAlchemy objects