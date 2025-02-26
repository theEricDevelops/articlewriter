from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils.db_utils import db_manager
from app.models.source import Source
from app.schemas.sources import SourceCreate, SourceUpdate, SourceResponse

router = APIRouter()

@router.post("/", response_model=SourceResponse)
async def create_source(source: SourceCreate, db: Session = Depends(db_manager.get_db)):
    db_source = Source(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.get("/", response_model=List[SourceResponse])
async def read_sources(skip: int = 0, limit: int = 100, db: Session = Depends(db_manager.get_db)):
    sources = db.query(Source).offset(skip).limit(limit).all()
    return sources

@router.get("/{source_id}", response_model=SourceResponse)
async def read_source(source_id: int, db: Session = Depends(db_manager.get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source

@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(source_id: int, source_update: SourceUpdate, db: Session = Depends(db_manager.get_db)):
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    update_data = source_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_source, key, value)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.delete("/{source_id}", response_model=SourceResponse)
async def delete_source(source_id: int, db: Session = Depends(db_manager.get_db)):
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(db_source)
    db.commit()
    return db_source