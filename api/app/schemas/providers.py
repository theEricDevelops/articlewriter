from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ProviderBase(BaseModel):
    name: str
    api_key: str
    endpoint: str
    model_name: Optional[List[str]] = None
    default_model: Optional[str] = "auto"

class ProviderCreate(ProviderBase):
    pass

class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    model_name: Optional[List[str]] = None
    default_model: Optional[str] = None

class ProviderResponse(ProviderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True