from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from . import Base

class Job(Base):
    """Represents an asynchronous task for AI generation in the database."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False, default="pending")  # e.g., "pending", "completed", "failed"
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    article = relationship("Article", back_populates="jobs")
    provider = relationship("Provider", back_populates="jobs")