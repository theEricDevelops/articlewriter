from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_db
from ..models.outline import Outline
from ..schemas.outlines import OutlineCreate, OutlineUpdate, OutlineResponse
import json

router = APIRouter()

@router.post("/", response_model=OutlineResponse)
async def create_outline(outline: OutlineCreate, db: Session = Depends(get_db)):
    db_outline = Outline(
        structure=json.dumps(outline.structure),
        outline_metadata=json.dumps(outline.instructions.dict()) if outline.instructions else None,
        topic_id=outline.topic_id
    )
    db.add(db_outline)
    db.commit()
    db.refresh(db_outline)
    return db_outline

@router.get("/", response_model=List[OutlineResponse])
async def read_outlines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    outlines = db.query(Outline).offset(skip).limit(limit).all()
    return outlines

@router.get("/{outline_id}", response_model=OutlineResponse)
async def read_outline(outline_id: int, db: Session = Depends(get_db)):
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if outline is None:
        raise HTTPException(status_code=404, detail="Outline not found")
    return outline

@router.put("/{outline_id}", response_model=OutlineResponse)
async def update_outline(outline_id: int, outline_update: OutlineUpdate, db: Session = Depends(get_db)):
    db_outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if db_outline is None:
        raise HTTPException(status_code=404, detail="Outline not found")
    update_data = outline_update.dict(exclude_unset=True)
    if "structure" in update_data:
        update_data["structure"] = json.dumps(update_data["structure"])
    if "instructions" in update_data:
        update_data["outline_metadata"] = json.dumps(update_data["instructions"].dict()) if update_data["instructions"] else None
        del update_data["instructions"]
    for key, value in update_data.items():
        setattr(db_outline, key, value)
    db.commit()
    db.refresh(db_outline)
    return db_outline

@router.delete("/{outline_id}", response_model=OutlineResponse)
async def delete_outline(outline_id: int, db: Session = Depends(get_db)):
    db_outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if db_outline is None:
        raise HTTPException(status_code=404, detail="Outline not found")
    db.delete(db_outline)
    db.commit()
    return db_outline