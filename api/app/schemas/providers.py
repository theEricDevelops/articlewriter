from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ProviderBase(BaseModel):
    """Base model for shared provider fields."""
    name: str
    api_key: str  # Required
    endpoint: str  # Required
    model_name: Optional[List[str]] = None  # List of supported models
    default_model: Optional[str] = "auto"  # "auto" or specific model

class ProviderCreate(ProviderBase):
    """Model for creating a new provider."""
    pass  # Inherits all fields from ProviderBase

class ProviderUpdate(BaseModel):
    """Model for updating an existing provider."""
    name: Optional[str] = None
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    model_name: Optional[List[str]] = None  # Update the model list
    default_model: Optional[str] = None  # Update default model selection

class ProviderResponse(ProviderBase):
    """Model for returning provider data in API responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    prompt_ids: List[int]  # List of associated prompt IDs

    class Config:
        from_attributes = True  # Allows mapping from SQLAlchemy objects