import pytest
import json
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
import time
from app.models.topic import Topic
from app.models.outline import Outline
from app.models.article import Article
from app.models.source import Source
from app.models.article_sources import ArticleSource

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

def test_topic_deletion_with_outline(db_session):
    """Test that a topic with an outline cannot be deleted."""
    # Create topic and outline
    topic = Topic(title="Deletion Test Topic", description="Testing deletion")
    db_session.add(topic)
    db_session.commit()
    
    outline = Outline(
        structure=json.dumps({"sections": ["Test"]}),
        topic_id=topic.id
    )
    db_session.add(outline)
    db_session.commit()
    
    outline_id = outline.id
    topic_id = topic.id
    
    # Try to delete the topic
    db_session.delete(topic)
    
    # Should raise IntegrityError since the topic has an associated outline
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()
    
    # Verify both topic and outline still exist
    assert db_session.query(Topic).filter(Topic.id == topic_id).first() is not None
    assert db_session.query(Outline).filter(Outline.id == outline_id).first() is not None
    
    # Now delete the outline first
    db_session.delete(outline)
    db_session.commit()
    
    # Now we should be able to delete the topic
    db_session.delete(topic)
    db_session.commit()
    
    # Verify both are gone
    assert db_session.query(Topic).filter(Topic.id == topic_id).first() is None
    assert db_session.query(Outline).filter(Outline.id == outline_id).first() is None

def test_topic_deletion_with_article(db_session):
    """Test that a topic with an article cannot be deleted."""
    # Create topic
    topic = Topic(title="Article Topic Deletion Test", description="Testing deletion constraints")
    db_session.add(topic)
    db_session.commit()
    
    # Create outline
    outline = Outline(
        structure=json.dumps({"sections": ["Test"]}),
        topic_id=topic.id
    )
    db_session.add(outline)
    db_session.commit()
    
    # Create article
    article = Article(
        title="Topic Deletion Test Article",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Try to delete the topic
    db_session.delete(topic)
    
    # Should raise IntegrityError since the topic has an associated article
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()
    
    # Try to delete the outline
    db_session.delete(outline)
    
    # Should raise IntegrityError since the outline has an associated article
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()
    
    # Delete in the correct order - article first, then outline, then topic
    db_session.delete(article)
    db_session.commit()
    
    db_session.delete(outline)
    db_session.commit()
    
    db_session.delete(topic)
    db_session.commit()
    
    # Verify all are gone
    assert db_session.query(Article).filter(Article.id == article.id).first() is None
    assert db_session.query(Outline).filter(Outline.id == outline.id).first() is None
    assert db_session.query(Topic).filter(Topic.id == topic.id).first() is None

def test_topic_deletion_with_source(db_session):
    """Test that a topic with a source cannot be deleted."""
    # Create topic
    topic = Topic(title="Source Topic Deletion Test", description="Testing deletion constraints")
    db_session.add(topic)
    db_session.commit()
    
    # Create outline
    outline = Outline(
        structure=json.dumps({"sections": ["Test"]}),
        topic_id=topic.id
    )
    db_session.add(outline)
    db_session.commit()
    
    # Create article
    article = Article(
        title="Source Topic Deletion Test Article",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Create source
    source = Source(
        url="https://example.com/source-topic-deletion-test",
        title="Source Topic Deletion Test Source",
        publication="Test Publication",
        publication_date=datetime.now(timezone.utc),
        summary="Testing source deletion constraints."
    )
    db_session.add(source)
    db_session.commit()
    
    # Associate source with article
    article.sources.append(source)
    db_session.commit()
    
    # Try to delete the topic
    db_session.delete(topic)
    
    # Should raise IntegrityError since the topic has an article with an associated source
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()
    
    # Delete in the correct order
    # First remove the source-article association
    article.sources.remove(source)
    db_session.commit()
    
    # Now delete the source
    db_session.delete(source)
    db_session.commit()
    
    # Delete the article
    db_session.delete(article)
    db_session.commit()
    
    # Delete the outline
    db_session.delete(outline)
    db_session.commit()
    
    # Now we should be able to delete the topic
    db_session.delete(topic)
    db_session.commit()
    
    # Verify all are gone
    assert db_session.query(Source).filter(Source.id == source.id).first() is None
    assert db_session.query(Article).filter(Article.id == article.id).first() is None
    assert db_session.query(Outline).filter(Outline.id == outline.id).first() is None
    assert db_session.query(Topic).filter(Topic.id == topic.id).first() is None