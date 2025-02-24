from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class PromptBase(BaseModel):
    """Base model for shared prompt fields."""
    name: str
    template_text: str
    description: Optional[str] = None

class PromptCreate(PromptBase):
    """Model for creating a new prompt."""
    provider_ids: Optional[List[int]] = None  # Optional list of provider IDs to associate
    prompt_metadata: Optional[Dict] = None  # Optional metadata for prompt-provider combos

class PromptUpdate(BaseModel):
    """Model for updating an existing prompt."""
    name: Optional[str] = None
    template_text: Optional[str] = None
    description: Optional[str] = None
    provider_ids: Optional[List[int]] = None  # Optional update to provider associations
    prompt_metadata: Optional[Dict] = None  # Optional update to metadata

class PromptResponse(PromptBase):
    """Model for returning prompt data in API responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    provider_ids: List[int]  # List of associated provider IDs
    prompt_metadata: Optional[Dict] = None  # Metadata from Prompt_Providers (if single provider context)

    class Config:
        from_attributes = True  # Allows mapping from SQLAlchemy objects