from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_db
from ..models.topic import Topic
from ..schemas.topics import TopicCreate, TopicUpdate, TopicResponse

router = APIRouter()

@router.post("/", response_model=TopicResponse)
async def create_topic(topic: TopicCreate, db: Session = Depends(get_db)):
    db_topic = Topic(**topic.dict())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@router.get("/", response_model=List[TopicResponse])
async def read_topics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    topics = db.query(Topic).offset(skip).limit(limit).all()
    return topics

@router.get("/{topic_id}", response_model=TopicResponse)
async def read_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(topic_id: int, topic_update: TopicUpdate, db: Session = Depends(get_db)):
    db_topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if db_topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    update_data = topic_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_topic, key, value)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@router.delete("/{topic_id}", response_model=TopicResponse)
async def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    db_topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if db_topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(db_topic)
    db.commit()
    return db_topic