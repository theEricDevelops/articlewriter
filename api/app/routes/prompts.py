from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_db
from ..models.prompt import Prompt
from ..schemas.prompts import PromptCreate, PromptUpdate, PromptResponse

router = APIRouter()

@router.post("/", response_model=PromptResponse)
async def create_prompt(prompt: PromptCreate, db: Session = Depends(get_db)):
    db_prompt = Prompt(**prompt.dict(exclude={"provider_ids", "prompt_metadata"}))
    if prompt.provider_ids:
        for provider_id in prompt.provider_ids:
            db_prompt.providers.append(PromptProvider(
                provider_id=provider_id,
                prompt_metadata=json.dumps(prompt.prompt_metadata) if prompt.prompt_metadata else None
            ))
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

@router.get("/", response_model=List[PromptResponse])
async def read_prompts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    prompts = db.query(Prompt).offset(skip).limit(limit).all()
    return prompts

@router.get("/{prompt_id}", response_model=PromptResponse)
async def read_prompt(prompt_id: int, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt

@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(prompt_id: int, prompt_update: PromptUpdate, db: Session = Depends(get_db)):
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if db_prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    update_data = prompt_update.dict(exclude_unset=True)
    if "provider_ids" in update_data or "prompt_metadata" in update_data:
        db.query(PromptProvider).filter(PromptProvider.prompt_id == prompt_id).delete()
        if prompt_update.provider_ids:
            for provider_id in prompt_update.provider_ids:
                db_prompt.providers.append(PromptProvider(
                    provider_id=provider_id,
                    prompt_metadata=json.dumps(prompt_update.prompt_metadata) if prompt_update.prompt_metadata else None
                ))
        del update_data["provider_ids"]
        if "prompt_metadata" in update_data:
            del update_data["prompt_metadata"]
    for key, value in update_data.items():
        setattr(db_prompt, key, value)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

@router.delete("/{prompt_id}", response_model=PromptResponse)
async def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if db_prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    db.delete(db_prompt)
    db.commit()
    return db_prompt