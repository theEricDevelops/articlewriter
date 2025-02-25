from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from . import Base

class Provider(Base):
    """Represents an AI provider in the database."""
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, unique=True, nullable=False)  # e.g., "OpenAI", "xAI"
    api_key = Column(Text, nullable=False)  # Shared across all models
    endpoint = Column(Text, nullable=False)  # Shared across all models
    model_name = Column(Text)  # JSON array, e.g., '["gpt-3.5-turbo", "gpt-4"]'
    default_model = Column(Text, default="auto")  # "auto" or specific model like "gpt-4"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship via junction table
    prompts = relationship("PromptProvider", back_populates="provider")
    jobs = relationship("Job", back_populates="provider")