from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from . import Base

class PromptProvider(Base):
    """Links prompts to providers with specific metadata."""
    __tablename__ = "prompt_providers"
    
    prompt_id = Column(Integer, ForeignKey("prompts.id"), primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), primary_key=True)
    prompt_metadata = Column(Text)  # e.g., {"target_audience": "technical", "tone": "formal"}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    prompt = relationship("Prompt", back_populates="providers")
    provider = relationship("Provider", back_populates="prompts")