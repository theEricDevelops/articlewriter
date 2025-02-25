import pytest
import json
from datetime import datetime, timezone, timedelta
import time
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc, func

from app.models.source import Source
from app.models.article import Article
from app.models.topic import Topic
from app.models.outline import Outline
from app.models.article_sources import ArticleSource

def test_create_source(db_session):
    """Test creating a simple source."""
    source = Source(
        url="https://example.com/test-source",
        title="Test Source",
        publication="Test Publication",
        publication_date=datetime.now(timezone.utc),
        summary="This is a test summary."
    )
    db_session.add(source)
    db_session.commit()
    
    # Verify source is created
    fetched_source = db_session.query(Source).filter(Source.id == source.id).first()
    assert fetched_source is not None
    assert fetched_source.url == "https://example.com/test-source"
    assert fetched_source.title == "Test Source"
    assert fetched_source.publication == "Test Publication"
    assert fetched_source.publication_date is not None
    assert fetched_source.summary == "This is a test summary."
    assert fetched_source.created_at is not None
    assert fetched_source.updated_at is not None

def test_source_unique_url_constraint(db_session):
    """Test that source URLs must be unique."""
    # Create first source
    source1 = Source(
        url="https://example.com/unique-test",
        title="Unique Test Source 1",
        publication="Test Publication",
        publication_date=datetime.now(timezone.utc),
        summary="First source with this URL."
    )
    db_session.add(source1)
    db_session.commit()
    
    # Create second source with same URL
    source2 = Source(
        url="https://example.com/unique-test",  # Same URL
        title="Unique Test Source 2",
        publication="Another Publication",
        publication_date=datetime.now(timezone.utc),
        summary="Second source with same URL."
    )
    db_session.add(source2)
    
    # Should raise IntegrityError for unique constraint violation
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()

def test_source_timestamps(db_session):
    """Test source timestamp behavior."""
    # Create a source
    source = Source(
        url="https://example.com/timestamp-test",
        title="Timestamp Test Source",
        publication="Test Publication",
        publication_date=datetime.now(timezone.utc),
        summary="Testing timestamps."
    )
    db_session.add(source)
    db_session.commit()
    
    # Check timestamps are created
    assert source.created_at is not None
    assert source.updated_at is not None
    
    # Store original timestamps
    original_created = source.created_at
    original_updated = source.updated_at
    
    # Wait a moment to ensure timestamp difference
    time.sleep(1)
    
    # Update the source
    source.title = "Updated Timestamp Test Source"
    db_session.commit()
    
    # Verify timestamps
    assert source.created_at == original_created  # created_at shouldn't change
    assert source.updated_at > original_updated  # updated_at should be newer

def test_source_with_article_relationship(db_session):
    """Test creating a source and associating it with an article."""
    # Create prerequisite objects for article
    topic = Topic(title="Source Test Topic", description="Test Description")
    outline = Outline(
        topic=topic,
        structure=json.dumps({"sections": ["Intro", "Body", "Conclusion"]})
    )
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create an article
    article = Article(
        title="Source Test Article",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Create a source
    source = Source(
        url="https://example.com/article-relationship-test",
        title="Article Relationship Test Source",
        publication="Test Publication",
        publication_date=datetime.now(timezone.utc),
        summary="Testing article relationships."
    )
    db_session.add(source)
    db_session.commit()
    
    # Associate the source with the article
    article.sources.append(source)
    db_session.commit()
    
    # Verify the article-source relationship
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    assert len(fetched_article.sources) == 1
    assert fetched_article.sources[0].id == source.id
    assert fetched_article.sources[0].title == "Article Relationship Test Source"
    
    # Verify the relationship from source side
    fetched_source = db_session.query(Source).filter(Source.id == source.id).first()
    assert len(fetched_source.articles) == 1
    assert fetched_source.articles[0].id == article.id
    assert fetched_source.articles[0].title == "Source Test Article"

def test_source_with_multiple_articles(db_session):
    """Test associating a source with multiple articles."""
    # Create prerequisite objects for articles
    topic = Topic(title="Multiple Articles Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create multiple articles
    articles = [
        Article(title="Article 1", status="draft", topic_id=topic.id, outline_id=outline.id),
        Article(title="Article 2", status="draft", topic_id=topic.id, outline_id=outline.id),
        Article(title="Article 3", status="draft", topic_id=topic.id, outline_id=outline.id)
    ]
    db_session.add_all(articles)
    db_session.commit()
    
    # Create a source
    source = Source(
        url="https://example.com/multiple-articles-test",
        title="Multiple Articles Test Source",
        publication="Test Publication",
        publication_date=datetime.now(timezone.utc),
        summary="Testing with multiple articles."
    )
    db_session.add(source)
    db_session.commit()
    
    # Associate the source with all articles
    for article in articles:
        article.sources.append(source)
    db_session.commit()
    
    # Verify the relationships
    fetched_source = db_session.query(Source).filter(Source.id == source.id).first()
    assert len(fetched_source.articles) == 3
    
    # Check that all articles are associated with the source
    article_ids = [article.id for article in articles]
    for article in fetched_source.articles:
        assert article.id in article_ids

def test_source_deletion_with_articles(db_session):
    """Test deleting a source that has article relationships."""
    # Create prerequisite objects for article
    topic = Topic(title="Deletion Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create an article
    article = Article(
        title="Deletion Test Article",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Create a source
    source = Source(
        url="https://example.com/deletion-test",
        title="Deletion Test Source",
        publication="Test Publication",
        publication_date=datetime.now(timezone.utc),
        summary="Testing deletion."
    )
    db_session.add(source)
    db_session.commit()
    
    # Associate the source with the article
    article.sources.append(source)
    db_session.commit()
    
    source_id = source.id
    
    # Delete the source
    db_session.delete(source)
    db_session.commit()
    
    # Verify source is deleted
    deleted_source = db_session.query(Source).filter(Source.id == source_id).first()
    assert deleted_source is None
    
    # Verify article still exists
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    assert fetched_article is not None
    
    # Verify association is gone
    assert len(fetched_article.sources) == 0
    
    # Verify junction table entry is gone
    article_source_entry = db_session.query(ArticleSource).filter(
        ArticleSource.source_id == source_id,
        ArticleSource.article_id == article.id
    ).first()
    assert article_source_entry is None

def test_article_deletion_with_sources(db_session):
    """Test deleting an article that has source relationships."""
    # Create prerequisite objects for article
    topic = Topic(title="Article Deletion Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create an article
    article = Article(
        title="Article Deletion Test",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Create sources
    sources = [
        Source(
            url=f"https://example.com/article-deletion-test-{i}",
            title=f"Article Deletion Test Source {i}",
            publication="Test Publication",
            publication_date=datetime.now(timezone.utc),
            summary=f"Testing article deletion {i}."
        )
        for i in range(1, 4)
    ]
    db_session.add_all(sources)
    db_session.commit()
    
    # Associate the sources with the article
    article.sources.extend(sources)
    db_session.commit()
    
    article_id = article.id
    source_ids = [source.id for source in sources]
    
    # Delete the article
    db_session.delete(article)
    db_session.commit()
    
    # Verify article is deleted
    deleted_article = db_session.query(Article).filter(Article.id == article_id).first()
    assert deleted_article is None
    
    # Verify sources still exist
    for source_id in source_ids:
        source = db_session.query(Source).filter(Source.id == source_id).first()
        assert source is not None
    
    # Verify associations are gone
    for source_id in source_ids:
        article_source_entry = db_session.query(ArticleSource).filter(
            ArticleSource.source_id == source_id,
            ArticleSource.article_id == article_id
        ).first()
        assert article_source_entry is None

def test_source_update(db_session):
    """Test updating source attributes."""
    # Create a source
    source = Source(
        url="https://example.com/update-test",
        title="Update Test Source",
        publication="Original Publication",
        publication_date=datetime.now(timezone.utc),
        summary="Original summary."
    )
    db_session.add(source)
    db_session.commit()
    
    # Update source attributes
    source.title = "Updated Test Source"
    source.publication = "Updated Publication"
    source.summary = "Updated summary."
    new_date = datetime.now(timezone.utc) - timedelta(days=7)
    source.publication_date = new_date
    db_session.commit()
    
    # Verify updates
    fetched_source = db_session.query(Source).filter(Source.id == source.id).first()
    assert fetched_source.title == "Updated Test Source"
    assert fetched_source.publication == "Updated Publication"
    assert fetched_source.summary == "Updated summary."
    assert fetched_source.publication_date.date() == new_date.date()

def test_source_query_methods(db_session):
    """Test common query patterns for sources."""
    # Create sources with different attributes
    publications = ["Publication A", "Publication B", "Publication C"]
    
    # Create clearly differentiated dates - use datetime.date to avoid timezone issues
    base_date = datetime.now().date()
    dates = [
        datetime.combine(base_date - timedelta(days=1), datetime.min.time()),
        datetime.combine(base_date - timedelta(days=7), datetime.min.time()),
        datetime.combine(base_date - timedelta(days=30), datetime.min.time())
    ]
    
    sources = []
    for i, (pub, date) in enumerate(zip(publications, dates)):
        source = Source(
            url=f"https://example.com/query-test-{i}",
            title=f"Query Test Source {i}",
            publication=pub,
            publication_date=date,
            summary=f"Testing queries {i}."
        )
        sources.append(source)
    
    db_session.add_all(sources)
    db_session.commit()
    
    # Test filtering by publication
    pub_a_sources = db_session.query(Source).filter(Source.publication == "Publication A").all()
    assert len(pub_a_sources) == 1
    assert pub_a_sources[0].title == "Query Test Source 0"
    
    # Test filtering by date range - use date() to compare just the date part
    one_week_ago = (datetime.now().date() - timedelta(days=7))
    
    # Query for sources from the last 7 days
    recent_sources = db_session.query(Source).filter(
        Source.publication_date >= datetime.combine(one_week_ago, datetime.min.time())
    ).all()
    
    assert len(recent_sources) == 2  # Should include the 1-day and 7-day old sources
    
    # Alternative approach - query for all sources and filter in Python
    all_sources = db_session.query(Source).all()
    python_filtered_sources = [
        s for s in all_sources 
        if s.publication_date.date() >= one_week_ago
    ]
    assert len(python_filtered_sources) == 2
    
    # Test sorting by date
    sorted_sources = db_session.query(Source).order_by(desc(Source.publication_date)).all()
    # Sources should be ordered newest to oldest
    for i in range(len(sorted_sources) - 1):
        assert sorted_sources[i].publication_date >= sorted_sources[i+1].publication_date


def test_source_batch_operations(db_session):
    """Test batch operations on sources."""
    # Batch create sources
    batch_sources = [
        Source(
            url=f"https://example.com/batch-test-{i}",
            title=f"Batch Test Source {i}",
            publication="Test Publication",
            publication_date=datetime.now(timezone.utc),
            summary=f"Testing batch operations {i}."
        )
        for i in range(5)
    ]
    db_session.add_all(batch_sources)
    db_session.commit()
    
    # Get all source IDs
    source_ids = [source.id for source in batch_sources]
    
    # Batch update sources
    db_session.query(Source).filter(
        Source.id.in_(source_ids)
    ).update({"publication": "Updated Publication"}, synchronize_session=False)
    db_session.commit()
    
    # Verify all were updated
    updated_count = db_session.query(Source).filter(
        and_(Source.id.in_(source_ids), Source.publication == "Updated Publication")
    ).count()
    assert updated_count == 5
    
    # Batch delete
    db_session.query(Source).filter(Source.id.in_(source_ids)).delete(synchronize_session=False)
    db_session.commit()
    
    # Verify all were deleted
    remaining = db_session.query(Source).filter(Source.id.in_(source_ids)).count()
    assert remaining == 0

def test_source_pagination(db_session):
    """Test pagination of sources."""
    # Create a batch of sources
    batch_sources = [
        Source(
            url=f"https://example.com/pagination-test-{i}",
            title=f"Pagination Test Source {i}",
            publication="Test Publication",
            publication_date=datetime.now(timezone.utc),
            summary=f"Testing pagination {i}."
        )
        for i in range(20)  # Create 20 sources
    ]
    db_session.add_all(batch_sources)
    db_session.commit()
    
    # Test pagination - page 1 (first 5 sources)
    page_size = 5
    page1 = db_session.query(Source).filter(
        Source.url.like("https://example.com/pagination-test-%")
    ).order_by(Source.id).limit(page_size).all()
    
    assert len(page1) == page_size
    
    # Test pagination - page 2 (next 5 sources)
    page2 = db_session.query(Source).filter(
        Source.url.like("https://example.com/pagination-test-%")
    ).order_by(Source.id).offset(page_size).limit(page_size).all()
    
    assert len(page2) == page_size
    # Ensure page2 contains different sources than page1
    assert set([s.id for s in page1]).isdisjoint(set([s.id for s in page2]))
    
    # Test pagination - last page
    last_page = db_session.query(Source).filter(
        Source.url.like("https://example.com/pagination-test-%")
    ).order_by(Source.id).offset(15).limit(page_size).all()
    
    assert len(last_page) == 5  # Should have exactly 5 results

def test_source_aggregations(db_session):
    """Test aggregation queries on sources."""
    # Create sources with different publications
    publications = ["Publication A", "Publication A", "Publication B", "Publication B", "Publication C"]
    
    sources = []
    for i, pub in enumerate(publications):
        source = Source(
            url=f"https://example.com/aggregation-test-{i}",
            title=f"Aggregation Test Source {i}",
            publication=pub,
            publication_date=datetime.now(timezone.utc) - timedelta(days=i),
            summary=f"Testing aggregations {i}."
        )
        sources.append(source)
    
    db_session.add_all(sources)
    db_session.commit()
    
    # Count sources by publication
    pub_counts = db_session.query(
        Source.publication, func.count(Source.id)
    ).group_by(Source.publication).all()
    
    pub_count_dict = dict(pub_counts)
    assert pub_count_dict["Publication A"] == 2
    assert pub_count_dict["Publication B"] == 2
    assert pub_count_dict["Publication C"] == 1
    
    # Count sources by date (this month)
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_count = db_session.query(Source).filter(
        Source.publication_date >= month_start
    ).count()
    
    assert this_month_count == 5  # All our test sources are from this month

def test_source_with_null_fields(db_session):
    """Test creating a source with nullable fields set to None."""
    # Create a source with some nullable fields as None
    source = Source(
        url="https://example.com/null-fields-test",
        title="Null Fields Test Source",
        # publication is left as None
        publication_date=datetime.now(timezone.utc),
        # summary is left as None
    )
    db_session.add(source)
    db_session.commit()
    
    # Verify source is created with NULL fields
    fetched_source = db_session.query(Source).filter(Source.id == source.id).first()
    assert fetched_source is not None
    assert fetched_source.url == "https://example.com/null-fields-test"
    assert fetched_source.title == "Null Fields Test Source"
    assert fetched_source.publication is None
    assert fetched_source.summary is None