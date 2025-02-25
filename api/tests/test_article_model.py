import pytest
import json
from datetime import datetime, timezone
from app.models.article import Article
from app.models.topic import Topic
from app.models.outline import Outline
from app.models.source import Source
from app.models.job import Job
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc, func

def test_create_article(db_session):
    """Test creating a new article with relationships."""
    # Create prerequisite objects
    topic = Topic(title="Test Topic", description="Test Description")
    outline = Outline(
        topic=topic,
        structure=json.dumps({"sections": ["Intro", "Body", "Conclusion"]})
    )
    source1 = Source(
        url="https://example.com/source1",
        title="Source 1",
        publication="Test Publication",
        publication_date=datetime.strptime("2023-01-01", "%Y-%m-%d"),
        summary="Test summary"
    )
    source2 = Source(
        url="https://example.com/source2",
        title="Source 2",
        publication="Test Publication",
        publication_date=datetime.strptime("2023-01-02", "%Y-%m-%d"),
        summary="Test summary 2"
    )
    
    db_session.add_all([topic, outline, source1, source2])
    db_session.commit()
    
    # Create the article
    article = Article(
        title="Test Article",
        status="draft",
        article_metadata=json.dumps({"tone": "formal"}),
        topic_id=topic.id,
        outline_id=outline.id
    )
    article.sources.extend([source1, source2])
    
    db_session.add(article)
    db_session.commit()
    
    # Fetch and verify
    fetched_article = db_session.query(Article).filter(Article.title == "Test Article").first()
    assert fetched_article is not None
    assert fetched_article.title == "Test Article"
    assert fetched_article.status == "draft"
    assert json.loads(fetched_article.article_metadata)["tone"] == "formal"
    assert fetched_article.topic_id == topic.id
    assert fetched_article.outline_id == outline.id
    assert len(fetched_article.sources) == 2
    assert fetched_article.sources[0].title in ["Source 1", "Source 2"]
    assert fetched_article.topic.title == "Test Topic"
    assert fetched_article.outline.structure == json.dumps({"sections": ["Intro", "Body", "Conclusion"]})

def test_article_timestamps(db_session):
    """Test the automatic timestamp fields."""
    # Create prerequisite objects
    topic = Topic(title="Timestamp Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create article
    article = Article(
        title="Timestamp Test",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Check timestamps are created
    assert article.created_at is not None
    assert article.updated_at is not None
    
    # Store original timestamps
    original_created = article.created_at
    original_updated = article.updated_at
    
    # Wait a moment to ensure timestamp difference
    import time
    time.sleep(1)
    
    # Update the article
    article.title = "Updated Title"
    db_session.commit()
    
    # Verify timestamps
    assert article.created_at == original_created  # created_at shouldn't change
    assert article.updated_at > original_updated  # updated_at should be newer

def test_article_status_transitions(db_session):
    """Test changing article status."""
    # Create prerequisite objects
    topic = Topic(title="Status Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create article
    article = Article(
        title="Status Test",
        status="draft",  # Initial status
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Test status transitions
    article.status = "edited"
    db_session.commit()
    assert article.status == "edited"
    
    article.status = "published"
    db_session.commit()
    assert article.status == "published"

def test_article_relationships(db_session):
    """Test the relationships between Article and other models."""
    # Create prerequisite objects
    topic = Topic(title="Relationship Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    source = Source(
        url="https://example.com/relationship-test",
        title="Relationship Test Source",
        publication="Test Publication",
        publication_date=datetime.now(timezone.utc),
        summary="Test"
    )
    db_session.add_all([topic, outline, source])
    db_session.commit()
    
    # Create article
    article = Article(
        title="Relationship Test",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    article.sources.append(source)
    db_session.add(article)
    db_session.commit()
    
    # Test relationships
    fetched_article = db_session.query(Article).filter(Article.title == "Relationship Test").first()
    
    # Test many-to-one relationships
    assert fetched_article.topic.title == "Relationship Test Topic"
    assert fetched_article.outline.structure == json.dumps({"sections": ["Test"]})
    
    # Test many-to-many relationship
    assert len(fetched_article.sources) == 1
    assert fetched_article.sources[0].title == "Relationship Test Source"
    
    # Test relationship from the other side
    assert source.articles[0].id == article.id
    
    # Check if the job can reference the article
    # This assumes your Job model has an article_id field
    if hasattr(Job, 'article_id'):
        # Create a job associated with the article
        job = Job(
            status="pending",
            article_id=article.id
        )
        db_session.add(job)
        db_session.commit()
        
        # Check the relationship from job to article
        fetched_job = db_session.query(Job).filter(Job.article_id == article.id).first()
        assert fetched_job is not None
        assert fetched_job.article_id == article.id

def test_article_content_update(db_session):
    """Test updating article content incrementally."""
    # Create prerequisite objects
    topic = Topic(title="Content Update Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({
        "sections": ["Introduction", "Main Body", "Conclusion"]
    }))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create article
    article = Article(
        title="Content Update Test",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id,
        article_metadata=json.dumps({"tone": "formal"})
    )
    db_session.add(article)
    db_session.commit()
    
    # Update article with content for introduction
    article_content = {"Introduction": "This is the introduction text."}
    article.article_content = json.dumps(article_content)
    db_session.commit()
    
    # Verify content was saved
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    saved_content = json.loads(fetched_article.article_content)
    assert "Introduction" in saved_content
    assert saved_content["Introduction"] == "This is the introduction text."
    
    # Add content for a new section
    article_content["Main Body"] = "This is the main body text."
    article.article_content = json.dumps(article_content)
    db_session.commit()
    
    # Verify updated content
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    saved_content = json.loads(fetched_article.article_content)
    assert "Main Body" in saved_content
    assert len(saved_content) == 2

def test_article_metadata_update(db_session):
    """Test updating article metadata."""
    # Create prerequisite objects
    topic = Topic(title="Metadata Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create article with initial metadata
    initial_metadata = {
        "tone": "formal",
        "word_count": 1000,
        "target_audience": "professionals"
    }
    article = Article(
        title="Metadata Test",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id,
        article_metadata=json.dumps(initial_metadata)
    )
    db_session.add(article)
    db_session.commit()
    
    # Update metadata
    updated_metadata = json.loads(article.article_metadata)
    updated_metadata["tone"] = "casual"
    updated_metadata["seo_keywords"] = ["test", "article", "metadata"]
    article.article_metadata = json.dumps(updated_metadata)
    db_session.commit()
    
    # Verify metadata was updated
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    saved_metadata = json.loads(fetched_article.article_metadata)
    assert saved_metadata["tone"] == "casual"
    assert "seo_keywords" in saved_metadata
    assert len(saved_metadata["seo_keywords"]) == 3

def test_article_deletion(db_session):
    """Test deleting an article and its cascading effects."""
    # Create prerequisite objects
    topic = Topic(title="Deletion Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    source = Source(
        url="https://example.com/deletion-test",
        title="Deletion Test Source",
        publication="Test Publication",
        publication_date=datetime.now(timezone.utc),
        summary="Test"
    )
    db_session.add_all([topic, outline, source])
    db_session.commit()
    
    # Create article
    article = Article(
        title="Deletion Test",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    article.sources.append(source)
    db_session.add(article)
    db_session.commit()
    
    article_id = article.id
    
    # Delete the article
    db_session.delete(article)
    db_session.commit()
    
    # Verify article is deleted
    deleted_article = db_session.query(Article).filter(Article.id == article_id).first()
    assert deleted_article is None
    
    # Verify source still exists (since it's a many-to-many)
    source_check = db_session.query(Source).filter(Source.id == source.id).first()
    assert source_check is not None
    
    # Verify the association in article_sources is gone
    from app.models.article_sources import ArticleSource
    association = db_session.query(ArticleSource).filter(
        ArticleSource.article_id == article_id,
        ArticleSource.source_id == source.id
    ).first()
    assert association is None

def test_article_constraints(db_session):
    """Test constraints on the Article model."""
    # Test NOT NULL constraints
    article = Article(
        # Missing title
        status="draft",
        # missing topic_id
        # missing outline_id
    )
    db_session.add(article)
    
    # Should raise IntegrityError for missing required fields
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    # Roll back the failed transaction
    db_session.rollback()
    
    # Create prerequisite objects
    topic = Topic(title="Constraint Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Test default values
    article = Article(
        title="Constraint Test",
        # status has default "draft"
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Verify default values
    assert article.status == "draft"
    assert article.created_at is not None
    assert article.updated_at is not None

def test_article_query_methods(db_session):
    """Test common query patterns for articles."""
    # Create prerequisite objects
    topic = Topic(title="Query Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create multiple articles with different statuses
    articles = [
        Article(title="Draft Article 1", status="draft", topic_id=topic.id, outline_id=outline.id),
        Article(title="Draft Article 2", status="draft", topic_id=topic.id, outline_id=outline.id),
        Article(title="Edited Article", status="edited", topic_id=topic.id, outline_id=outline.id),
        Article(title="Published Article", status="published", topic_id=topic.id, outline_id=outline.id)
    ]
    db_session.add_all(articles)
    db_session.commit()
    
    # Test filtering by status
    draft_articles = db_session.query(Article).filter(Article.status == "draft").all()
    assert len(draft_articles) == 2
    
    edited_articles = db_session.query(Article).filter(Article.status == "edited").all()
    assert len(edited_articles) == 1
    
    published_articles = db_session.query(Article).filter(Article.status == "published").all()
    assert len(published_articles) == 1
    
    # Test filtering by title
    article_by_title = db_session.query(Article).filter(
        Article.title == "Edited Article"
    ).first()
    assert article_by_title is not None
    assert article_by_title.status == "edited"
    
    # Test filtering with LIKE
    articles_with_draft = db_session.query(Article).filter(
        Article.title.like("%Draft%")
    ).all()
    assert len(articles_with_draft) == 2

def test_article_batch_operations(db_session):
    """Test batch operations on articles."""
    # Create prerequisite objects
    topic = Topic(title="Batch Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Batch create articles
    batch_articles = [
        Article(title=f"Batch Article {i}", status="draft", topic_id=topic.id, outline_id=outline.id)
        for i in range(1, 6)  # Create 5 articles
    ]
    db_session.add_all(batch_articles)
    db_session.commit()
    
    # Verify all were created
    count = db_session.query(Article).filter(Article.title.like("Batch Article%")).count()
    assert count == 5
    
    # Batch update articles
    db_session.query(Article).filter(
        Article.title.like("Batch Article%")
    ).update({"status": "edited"}, synchronize_session=False)
    db_session.commit()
    
    # Verify all were updated
    updated_count = db_session.query(Article).filter(
        and_(Article.title.like("Batch Article%"), Article.status == "edited")
    ).count()
    assert updated_count == 5
    
    # Batch delete
    db_session.query(Article).filter(Article.title.like("Batch Article%")).delete(synchronize_session=False)
    db_session.commit()
    
    # Verify all were deleted
    remaining = db_session.query(Article).filter(Article.title.like("Batch Article%")).count()
    assert remaining == 0

def test_article_sorting_and_pagination(db_session):
    """Test sorting and pagination of articles."""
    # Create prerequisite objects
    topic = Topic(title="Sorting Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create articles with different timestamps
    base_time = datetime.now()
    articles = []
    
    for i in range(10):
        # Create articles with staggered creation times
        article = Article(
            title=f"Sorting Article {i}",
            status="draft",
            topic_id=topic.id,
            outline_id=outline.id,
        )
        # Simulate articles created at different times
        if hasattr(article, '_created_at'):
            article._created_at = base_time - timedelta(days=i)
        articles.append(article)
    
    db_session.add_all(articles)
    db_session.commit()
    
    # Sort by created_at descending (newest first)
    sorted_desc = db_session.query(Article).filter(
        Article.title.like("Sorting Article%")
    ).order_by(desc(Article.created_at)).all()
    
    # Check if sorted correctly
    for i in range(len(sorted_desc) - 1):
        assert sorted_desc[i].created_at >= sorted_desc[i+1].created_at
    
    # Test pagination - page 1 (first 3 articles)
    page_size = 3
    page1 = db_session.query(Article).filter(
        Article.title.like("Sorting Article%")
    ).order_by(Article.created_at).limit(page_size).all()
    
    assert len(page1) == page_size
    
    # Test pagination - page 2 (next 3 articles)
    page2 = db_session.query(Article).filter(
        Article.title.like("Sorting Article%")
    ).order_by(Article.created_at).offset(page_size).limit(page_size).all()
    
    assert len(page2) == page_size
    # Ensure page2 contains different articles than page1
    assert set([a.id for a in page1]).isdisjoint(set([a.id for a in page2]))

def test_article_aggregations(db_session):
    """Test aggregation queries on articles."""
    # Create prerequisite objects
    topic1 = Topic(title="Aggregation Topic 1", description="Test")
    topic2 = Topic(title="Aggregation Topic 2", description="Test")
    outline = Outline(topic=topic1, structure=json.dumps({"sections": ["Test"]}))
    outline2 = Outline(topic=topic2, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic1, topic2, outline, outline2])
    db_session.commit()
    
    # Create articles with different statuses and topics
    articles = [
        # Topic 1 articles
        Article(title="Topic1 Draft1", status="draft", topic_id=topic1.id, outline_id=outline.id),
        Article(title="Topic1 Draft2", status="draft", topic_id=topic1.id, outline_id=outline.id),
        Article(title="Topic1 Edited", status="edited", topic_id=topic1.id, outline_id=outline.id),
        Article(title="Topic1 Published", status="published", topic_id=topic1.id, outline_id=outline.id),
        # Topic 2 articles
        Article(title="Topic2 Draft", status="draft", topic_id=topic2.id, outline_id=outline2.id),
        Article(title="Topic2 Edited", status="edited", topic_id=topic2.id, outline_id=outline2.id),
        Article(title="Topic2 Published1", status="published", topic_id=topic2.id, outline_id=outline2.id),
        Article(title="Topic2 Published2", status="published", topic_id=topic2.id, outline_id=outline2.id),
    ]
    db_session.add_all(articles)
    db_session.commit()
    
    # Count articles by status
    status_counts = db_session.query(
        Article.status, func.count(Article.id)
    ).group_by(Article.status).all()
    
    status_count_dict = dict(status_counts)
    assert status_count_dict["draft"] == 3
    assert status_count_dict["edited"] == 2
    assert status_count_dict["published"] == 3
    
    # Count articles by topic
    topic_counts = db_session.query(
        Article.topic_id, func.count(Article.id)
    ).group_by(Article.topic_id).all()
    
    topic_count_dict = dict(topic_counts)
    assert topic_count_dict[topic1.id] == 4
    assert topic_count_dict[topic2.id] == 4
    
    # Complex query: Count published articles by topic
    published_by_topic = db_session.query(
        Article.topic_id, func.count(Article.id)
    ).filter(
        Article.status == "published"
    ).group_by(Article.topic_id).all()
    
    published_topic_dict = dict(published_by_topic)
    assert published_topic_dict[topic1.id] == 1
    assert published_topic_dict[topic2.id] == 2

def test_article_unique_constraints(db_session):
    """Test any unique constraints on the Article model."""
    # This is an example - adjust based on your actual constraints
    # Create prerequisite objects
    topic = Topic(title="Unique Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create an article
    article1 = Article(
        title="Unique Article",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article1)
    db_session.commit()
    
    # If you have unique constraints, test them here
    # For example, if title must be unique per topic:
    article2 = Article(
        title="Unique Article",  # Same title
        status="draft",
        topic_id=topic.id,  # Same topic
        outline_id=outline.id
    )
    db_session.add(article2)
    
    # If you expect a unique constraint error, uncomment this:
    # with pytest.raises(IntegrityError):
    #     db_session.commit()
    # db_session.rollback()
    
    # If you don't have this constraint, this should pass:
    db_session.commit()
    # Check that both articles exist
    count = db_session.query(Article).filter(Article.title == "Unique Article").count()
    assert count == 2

def test_article_source_management(db_session):
    """Test adding and removing sources from an article."""
    # Create prerequisite objects
    topic = Topic(title="Source Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    sources = [
        Source(
            url=f"https://example.com/source{i}",
            title=f"Source {i}",
            publication="Test Publication",
            publication_date=datetime.now(timezone.utc),
            summary=f"Test summary {i}"
        )
        for i in range(1, 6)  # Create 5 sources
    ]
    
    db_session.add_all([topic, outline] + sources)
    db_session.commit()
    
    # Create article with no sources initially
    article = Article(
        title="Source Management Test",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Add sources one by one
    for i in range(3):  # Add first 3 sources
        article.sources.append(sources[i])
    db_session.commit()
    
    # Verify sources were added
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    assert len(fetched_article.sources) == 3
    
    # Remove a source
    article.sources.remove(sources[0])
    db_session.commit()
    
    # Verify source was removed
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    assert len(fetched_article.sources) == 2
    source_ids = [s.id for s in fetched_article.sources]
    assert sources[0].id not in source_ids
    
    # Clear all sources
    article.sources = []
    db_session.commit()
    
    # Verify all sources were removed
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    assert len(fetched_article.sources) == 0
    
    # Add multiple sources at once
    article.sources = sources  # Add all 5 sources
    db_session.commit()
    
    # Verify all sources were added
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    assert len(fetched_article.sources) == 5