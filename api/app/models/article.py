from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..models import Base

class Article(Base):
    """Represents an article in the database."""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="draft")  # e.g., "draft", "edited", "published"
    article_metadata = Column(Text)  # JSON string for instructions, e.g., {"tone": "formal"}
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc), 
                       onupdate=lambda: datetime.now(datetime.timezone.utc))
    
    # Foreign keys
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    #outline_id = Column(Integer, ForeignKey("outlines.id"), nullable=False)
    
    # Relationships
    topic = relationship("Topic", back_populates="articles")
    #outline = relationship("Outline", back_populates="articles")
    sources = relationship("Source", secondary="article_sources", back_populates="articles")

# TO DO: in models/outline.py: articles = relationship("Article", back_populates="outline")