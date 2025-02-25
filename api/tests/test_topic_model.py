import pytest
from datetime import datetime, timezone
import time
from app.models.topic import Topic

def test_create_topic(db_session):
    """Test creating a new topic."""
    # Record the current time for comparison
    before_create = datetime.now(timezone.utc)
    
    new_topic = Topic(
        title="Test Topic",
        description="This is a test topic"
    )
    db_session.add(new_topic)
    db_session.commit()
    
    # Fetch the topic and verify properties
    fetched_topic = db_session.query(Topic).filter(Topic.title == "Test Topic").first()
    assert fetched_topic is not None
    assert fetched_topic.title == "Test Topic"
    assert fetched_topic.description == "This is a test topic"
    
    # Verify timestamps
    assert fetched_topic.created_at is not None
    assert fetched_topic.updated_at is not None
    
    # Ensure the timestamps are timezone-aware for comparison
    if fetched_topic.created_at.tzinfo is None:
        created_at_aware = fetched_topic.created_at.replace(tzinfo=timezone.utc)
    else:
        created_at_aware = fetched_topic.created_at
        
    if fetched_topic.updated_at.tzinfo is None:
        updated_at_aware = fetched_topic.updated_at.replace(tzinfo=timezone.utc)
    else:
        updated_at_aware = fetched_topic.updated_at
    
    assert created_at_aware >= before_create
    assert updated_at_aware >= before_create
    
    # Verify relationships
    assert len(fetched_topic.articles) == 0
    assert len(fetched_topic.outlines) == 0


def test_update_topic(db_session):
    """Test updating a topic updates the updated_at timestamp."""
    # Create a topic
    topic = Topic(title="Original Title", description="Original description")
    db_session.add(topic)
    db_session.commit()
    
    # Record the original timestamp
    original_updated_at = topic.updated_at
    
    # Wait a short time to ensure timestamp difference
    time.sleep(0.001)
    
    # Update the topic
    topic.title = "Updated Title"
    db_session.commit()
    
    # Fetch the updated topic
    updated_topic = db_session.query(Topic).filter(Topic.id == topic.id).first()
    
    # Verify the update
    assert updated_topic.title == "Updated Title"
    assert updated_topic.updated_at > original_updated_at
    assert updated_topic.created_at == topic.created_at  # Created timestamp shouldn't change

def test_delete_topic(db_session):
    """Test deleting a topic."""
    # Create a topic
    topic = Topic(title="Topic to Delete", description="This topic will be deleted")
    db_session.add(topic)
    db_session.commit()
    
    # Get the topic id for later verification
    topic_id = topic.id
    
    # Verify the topic exists
    assert db_session.query(Topic).filter(Topic.id == topic_id).first() is not None
    
    # Delete the topic
    db_session.delete(topic)
    db_session.commit()
    
    # Verify the topic no longer exists
    assert db_session.query(Topic).filter(Topic.id == topic_id).first() is None