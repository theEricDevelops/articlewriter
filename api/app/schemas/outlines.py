from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List

class OutlineBase(BaseModel):
    """Base model for shared outline fields."""
    structure: List[str]  # e.g., ["Intro", "Section 1", "Conclusion"]
    outline_metadata: Optional[Dict] = None  # Optional metadata as a dictionary

class OutlineCreate(OutlineBase):
    """Model for creating a new outline."""
    topic_id: int

class OutlineUpdate(BaseModel):
    """Model for updating an existing outline."""
    structure: Optional[List[str]] = None
    outline_metadata: Optional[Dict] = None
    topic_id: Optional[int] = None

class OutlineResponse(OutlineBase):
    """Model for returning outline data in API responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    topic_id: int
    article_ids: List[int]  # List of associated article IDs

    class Config:
        from_attributes = True  # Allows mapping from SQLAlchemy objects