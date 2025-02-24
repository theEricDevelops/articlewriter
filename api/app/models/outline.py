from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..models import Base

class Outline(Base):
    """Represents an outline in the database."""
    __tablename__ = "outlines"
    
    id = Column(Integer, primary_key=True, index=True)
    structure = Column(Text, nullable=False)  # JSON string
    outline_metadata = Column(Text)  # JSON string for instructions, e.g., {"style": "detailed"}
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc), 
                       onupdate=lambda: datetime.now(datetime.timezone.utc))
    
    # Foreign key
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    
    # Relationships
    topic = relationship("Topic", back_populates="outlines")
    articles = relationship("Article", back_populates="outline")