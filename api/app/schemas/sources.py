from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class SourceBase(BaseModel):
    """Base model for shared source fields."""
    url: str
    title: str
    publication: str
    publication_date: datetime
    summary: str

class SourceCreate(SourceBase):
    """Model for creating a new source."""
    pass  # Inherits all fields from SourceBase; no additional fields needed

class SourceUpdate(BaseModel):
    """Model for updating an existing source."""
    url: Optional[str] = None
    title: Optional[str] = None
    publication: Optional[str] = None
    publication_date: Optional[datetime] = None
    summary: Optional[str] = None

class SourceResponse(SourceBase):
    """Model for returning source data in API responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    article_ids: list[int]  # List of associated article IDs

    model_config = ConfigDict(from_attributes=True) # Allows mapping from SQLAlchemy objects