from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict

class ArticleBase(BaseModel):
    """Base model for shared article fields."""
    title: str
    status: str = "draft"
    article_metadata: Optional[Dict] = None

class ArticleCreate(ArticleBase):
    """Model for creating a new article."""
    topic_id: int
    outline_id: int
    source_ids: Optional[list[int]] = None

class ArticleUpdate(BaseModel):
    """Model for updating an existing article."""
    title: Optional[str] = None
    status: Optional[str] = None
    article_metadata: Optional[Dict] = None
    topic_id: Optional[int] = None
    outline_id: Optional[int] = None
    source_ids: Optional[list[int]] = None

class ArticleResponse(ArticleBase):
    """Model for returning article data in API responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    topic_id: int
    outline_id: int
    source_ids: list[int]
    article_metadata: Optional[Dict] = None

    model_config = ConfigDict(from_attributes=True)