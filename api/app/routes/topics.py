from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..services import get_all_topics, get_topic_by_id
from ..services import generate_topics_ai
from ..models import TopicModel
from typing import List

router = APIRouter()

# Generate topics using AI (async)
@router.post("/generate", response_model=List[TopicModel])
async def generate_topics(prompt: str):
    """Generate topics based on a prompt using an AI service."""
    return await generate_topics_ai(prompt)

# List all topics (async)
@router.get("/", response_model=List[TopicModel])
async def list_topics(db: Session = Depends(get_db)):
    """Retrieve all topics from the database."""
    return await get_all_topics(db)

# Get a specific topic by ID (async)
@router.get("/{topic_id}", response_model=TopicModel)
async def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Retrieve a topic by its ID."""
    topic = await get_topic_by_id(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic