from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_db
from ..models.provider import Provider
from ..schemas.providers import ProviderCreate, ProviderUpdate, ProviderResponse
import json

router = APIRouter()

@router.post("/", response_model=ProviderResponse)
async def create_provider(provider: ProviderCreate, db: Session = Depends(get_db)):
    db_provider = Provider(
        name=provider.name,
        api_key=provider.api_key,
        endpoint=provider.endpoint,
        model_name=json.dumps(provider.model_name) if provider.model_name else None,
        default_model=provider.default_model
    )
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider

@router.get("/", response_model=List[ProviderResponse])
async def read_providers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    providers = db.query(Provider).offset(skip).limit(limit).all()
    return providers

@router.get("/{provider_id}", response_model=ProviderResponse)
async def read_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider

@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: int, provider_update: ProviderUpdate, db: Session = Depends(get_db)):
    db_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if db_provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    update_data = provider_update.dict(exclude_unset=True)
    if "model_name" in update_data:
        update_data["model_name"] = json.dumps(update_data["model_name"]) if update_data["model_name"] else None
    for key, value in update_data.items():
        setattr(db_provider, key, value)
    db.commit()
    db.refresh(db_provider)
    return db_provider

@router.delete("/{provider_id}", response_model=ProviderResponse)
async def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    db_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if db_provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.delete(db_provider)
    db.commit()
    return db_provider