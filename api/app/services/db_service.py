from sqlalchemy.orm import Session
from ..models import *

async def get_all_topics(db: Session):
    """Fetch all topics from the database."""
    return db.query(Topic).all()

async def get_topic_by_id(db: Session, topic_id: int):
    """Fetch a topic by its ID."""
    return db.query(Topic).filter(Topic.id == topic_id).first()