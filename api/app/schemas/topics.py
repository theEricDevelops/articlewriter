from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class TopicBase(BaseModel):
    """Base model for shared topic fields."""
    title: str
    description: Optional[str] = None  # Optional since description can be null in the database

class TopicCreate(TopicBase):
    """Model for creating a new topic."""
    pass  # Inherits all fields from TopicBase; no additional fields needed

class TopicUpdate(BaseModel):
    """Model for updating an existing topic."""
    title: Optional[str] = None
    description: Optional[str] = None

class TopicResponse(TopicBase):
    """Model for returning topic data in API responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    article_ids: List[int]  # List of associated article IDs
    outline_ids: List[int]  # List of associated outline IDs

    model_config = ConfigDict(from_attributes = True)  # Allows mapping from SQLAlchemy objects