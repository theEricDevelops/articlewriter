from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

__all__ = ["JobBase", "JobCreate", "JobUpdate", "JobResponse"]

class JobBase(BaseModel):
    """Base model for shared job fields."""
    status: str = "pending"  # e.g., "pending", "completed", "failed"

class JobCreate(JobBase):
    """Model for creating a new job."""
    article_id: Optional[int] = None  # Optional link to an article
    provider_id: Optional[int] = None  # Optional link to a provider

class JobUpdate(BaseModel):
    """Model for updating an existing job."""
    status: Optional[str] = None  # Update status (e.g., "completed")
    article_id: Optional[int] = None  # Update article association
    provider_id: Optional[int] = None  # Update provider association

class JobResponse(JobBase):
    """Model for returning job data in API responses."""
    id: int
    article_id: Optional[int]
    provider_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) # Allows mapping from SQLAlchemy objects