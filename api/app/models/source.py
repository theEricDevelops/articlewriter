from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from . import Base

class Source(Base):
    """Represents a source in the database."""
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True)  # Fixed 'unique=true' to 'unique=True'
    title = Column(String, index=True)
    publication = Column(String)
    publication_date = Column(DateTime)
    summary = Column(String)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship with Article via the junction table
    articles = relationship("Article", secondary="article_sources", back_populates="sources")