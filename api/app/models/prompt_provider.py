from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class PromptProvider(Base):
    """Links prompts to providers with specific metadata."""
    __tablename__ = "prompt_providers"
    
    prompt_id = Column(Integer, ForeignKey("prompts.id"), primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), primary_key=True)
    prompt_metadata = Column(Text)  # e.g., {"target_audience": "technical", "tone": "formal"}
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc), 
                       onupdate=lambda: datetime.now(datetime.timezone.utc))
    
    prompt = relationship("Prompt", back_populates="providers")
    provider = relationship("Provider", back_populates="prompts")