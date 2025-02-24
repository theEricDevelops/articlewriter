from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class Prompt(Base):
    """Represents a reusable AI prompt template in the database."""
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    template_text = Column(Text, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc), 
                       onupdate=lambda: datetime.now(datetime.timezone.utc))
    
    providers = relationship("PromptProvider", back_populates="prompt")