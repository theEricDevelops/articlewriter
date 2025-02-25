import pytest
from datetime import datetime
from pydantic import ValidationError

# Import schema classes (adjust paths as needed)
from app.routes.topics import TopicCreate, TopicUpdate, TopicResponse
from app.routes.articles import ArticleCreate, ArticleUpdate, ArticleResponse
from app.routes.sources import SourceCreate, SourceUpdate, SourceResponse

def test_topic_schemas():
    """Test topic-related schemas."""
    # Test the creation schema
    topic_data = {
        "title": "Test Topic",
        "description": "This is a test topic"
    }
    topic_create = TopicCreate(**topic_data)
    assert topic_create.title == "Test Topic"
    assert topic_create.description == "This is a test topic"
    
    # Test the update schema
    update_data = {"title": "Updated Topic"}
    topic_update = TopicUpdate(**update_data)
    assert topic_update.title == "Updated Topic"
    assert topic_update.description is None
    
    # Test the response schema
    created_at = datetime.now()
    updated_at = datetime.now()
    topic_response_data = {
        **topic_data,
        "id": 1,
        "created_at": created_at,
        "updated_at": updated_at,
        "article_ids": [1, 2],
        "outline_ids": [1]
    }
    topic_response = TopicResponse(**topic_response_data)
    assert topic_response.id == 1
    assert topic_response.title == "Test Topic"
    assert topic_response.created_at == created_at
    assert topic_response.updated_at == updated_at
    assert len(topic_response.article_ids) == 2
    assert len(topic_response.outline_ids) == 1
    
    # Test validation - required fields
    with pytest.raises(ValidationError):
        TopicCreate()  # Missing required 'title' field

def test_article_schemas():
    """Test article-related schemas."""
    # Test the creation schema
    article_data = {
        "title": "Test Article",
        "status": "draft",
        "article_metadata": {"tone": "formal"},
        "topic_id": 1,
        "outline_id": 1,
        "source_ids": [1, 2]
    }
    article_create = ArticleCreate(**article_data)
    assert article_create.title == "Test Article"
    assert article_create.status == "draft"
    assert article_create.article_metadata["tone"] == "formal"
    assert article_create.topic_id == 1
    assert article_create.outline_id == 1
    assert len(article_create.source_ids) == 2
    
    # Test update schema
    update_data = {
        "title": "Updated Article",
        "status": "published"
    }
    article_update = ArticleUpdate(**update_data)
    assert article_update.title == "Updated Article"
    assert article_update.status == "published"
    assert article_update.topic_id is None
    
    # Test validation - status enum
    with pytest.raises(ValidationError):
        ArticleCreate(title="Test", status="invalid_status", topic_id=1, outline_id=1)

def test_source_create_schema():
    """Test source-related schemas."""
    # Test the creation schema
    current_time = datetime.now()
    source_data = {
        "url": "https://example.com",
        "title": "Test Source",
        "publication": "Test Publication",
        "publication_date": current_time,
        "summary": "This is a test summary"
    }
    source_create = SourceCreate(**source_data)
    assert source_create.url == "https://example.com"
    assert source_create.title == "Test Source"
    assert source_create.publication == "Test Publication"
    assert source_create.publication_date == current_time
    assert source_create.summary == "This is a test summary"
    
    # Test update schema
    update_data = {"title": "Updated Source"}
    source_update = SourceUpdate(**update_data)
    assert source_update.title == "Updated Source"
    assert source_update.url is None
    
    # Test validation - URL format
    with pytest.raises(ValidationError):
        SourceCreate(
            url="not-a-valid-url",
            title="Invalid URL",
            publication="Test",
            publication_date=datetime.now(),
            summary="Test"
        )