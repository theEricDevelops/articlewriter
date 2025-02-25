import pytest
import json
from datetime import datetime, timezone, timedelta
import time
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc, func

from app.models.outline import Outline
from app.models.topic import Topic
from app.models.article import Article

def test_create_outline(db_session):
    """Test creating a simple outline."""
    # Create prerequisite topic
    topic = Topic(title="Test Topic", description="Test Topic Description")
    db_session.add(topic)
    db_session.commit()
    
    # Create outline
    outline_structure = {
        "sections": [
            {"title": "Introduction", "content": "Introduce the topic"},
            {"title": "Main Body", "content": "Discuss the details"},
            {"title": "Conclusion", "content": "Summarize findings"}
        ]
    }
    
    outline = Outline(
        structure=json.dumps(outline_structure),
        outline_metadata=json.dumps({"style": "detailed"}),
        topic_id=topic.id
    )
    db_session.add(outline)
    db_session.commit()
    
    # Verify outline is created
    fetched_outline = db_session.query(Outline).filter(Outline.id == outline.id).first()
    assert fetched_outline is not None
    assert json.loads(fetched_outline.structure) == outline_structure
    assert json.loads(fetched_outline.outline_metadata)["style"] == "detailed"
    assert fetched_outline.topic_id == topic.id
    assert fetched_outline.created_at is not None
    assert fetched_outline.updated_at is not None

def test_outline_null_constraints(db_session):
    """Test NOT NULL constraints on the Outline model."""
    # Create a topic
    topic = Topic(title="Constraint Test Topic", description="Testing constraints")
    db_session.add(topic)
    db_session.commit()
    
    # Test missing structure (should fail)
    outline_missing_structure = Outline(
        topic_id=topic.id
        # structure is missing
    )
    db_session.add(outline_missing_structure)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    
    # Test missing topic_id (should fail)
    outline_missing_topic = Outline(
        structure=json.dumps({"sections": ["Test"]})
        # topic_id is missing
    )
    db_session.add(outline_missing_topic)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    
    # Test valid outline (should pass)
    valid_outline = Outline(
        structure=json.dumps({"sections": ["Test"]}),
        topic_id=topic.id
    )
    db_session.add(valid_outline)
    db_session.commit()  # This should succeed
    
    # Verify outline was created
    assert valid_outline.id is not None

def test_outline_timestamps(db_session):
    """Test outline timestamp behavior."""
    # Create prerequisite topic
    topic = Topic(title="Timestamp Test Topic", description="Testing timestamps")
    db_session.add(topic)
    db_session.commit()
    
    # Create outline
    outline = Outline(
        structure=json.dumps({"sections": ["Test"]}),
        topic_id=topic.id
    )
    db_session.add(outline)
    db_session.commit()
    
    # Check timestamps are created
    assert outline.created_at is not None
    assert outline.updated_at is not None
    
    # Store original timestamps
    original_created = outline.created_at
    original_updated = outline.updated_at
    
    # Wait a moment to ensure timestamp difference
    time.sleep(1)
    
    # Update the outline
    outline_structure = json.loads(outline.structure)
    outline_structure["sections"].append("New Section")
    outline.structure = json.dumps(outline_structure)
    db_session.commit()
    
    # Verify timestamps
    assert outline.created_at == original_created  # created_at shouldn't change
    assert outline.updated_at > original_updated  # updated_at should be newer

def test_outline_topic_relationship(db_session):
    """Test the relationship between Outline and Topic."""
    # Create prerequisite topic
    topic = Topic(title="Relationship Test Topic", description="Testing relationships")
    db_session.add(topic)
    db_session.commit()
    
    # Create outline
    outline = Outline(
        structure=json.dumps({"sections": ["Test"]}),
        topic_id=topic.id
    )
    db_session.add(outline)
    db_session.commit()
    
    # Verify relationship from outline to topic
    fetched_outline = db_session.query(Outline).filter(Outline.id == outline.id).first()
    assert fetched_outline.topic is not None
    assert fetched_outline.topic.id == topic.id
    assert fetched_outline.topic.title == "Relationship Test Topic"
    
    # Verify relationship from topic to outlines
    fetched_topic = db_session.query(Topic).filter(Topic.id == topic.id).first()
    assert len(fetched_topic.outlines) > 0
    assert outline.id in [o.id for o in fetched_topic.outlines]

def test_outline_article_relationship(db_session):
    """Test the relationship between Outline and Article."""
    # Create prerequisite topic
    topic = Topic(title="Article Rel Topic", description="Testing article relationship")
    db_session.add(topic)
    db_session.commit()
    
    # Create outline
    outline = Outline(
        structure=json.dumps({"sections": ["Intro", "Body", "Conclusion"]}),
        topic_id=topic.id
    )
    db_session.add(outline)
    db_session.commit()
    
    # Create articles using this outline
    articles = [
        Article(
            title=f"Test Article {i}",
            status="draft",
            topic_id=topic.id,
            outline_id=outline.id
        )
        for i in range(3)
    ]
    db_session.add_all(articles)
    db_session.commit()
    
    # Verify relationship from outline to articles
    fetched_outline = db_session.query(Outline).filter(Outline.id == outline.id).first()
    assert len(fetched_outline.articles) == 3
    article_titles = [a.title for a in fetched_outline.articles]
    for i in range(3):
        assert f"Test Article {i}" in article_titles
    
    # Verify relationship from article to outline
    for article in articles:
        fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
        assert fetched_article.outline is not None
        assert fetched_article.outline.id == outline.id
        assert json.loads(fetched_article.outline.structure)["sections"] == ["Intro", "Body", "Conclusion"]

def test_outline_deletion_with_articles(db_session):
    """Test that an outline with articles cannot be deleted."""
    # Create prerequisite objects
    topic = Topic(title="Outline Deletion Topic", description="Testing outline deletion")
    db_session.add(topic)
    db_session.commit()
    
    outline = Outline(
        structure=json.dumps({"sections": ["Test"]}),
        topic_id=topic.id
    )
    db_session.add(outline)
    db_session.commit()
    
    # Create article with this outline
    article = Article(
        title="Outline Deletion Test Article",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Try to delete the outline
    db_session.delete(outline)
    
    # Should raise IntegrityError since the outline has an associated article
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()
    
    # Delete the article first
    db_session.delete(article)
    db_session.commit()
    
    # Now we should be able to delete the outline
    db_session.delete(outline)
    db_session.commit()
    
    # Verify outline is gone
    assert db_session.query(Outline).filter(Outline.id == outline.id).first() is None

def test_outline_structure_json(db_session):
    """Test working with the JSON structure field of the Outline model."""
    # Create prerequisite topic
    topic = Topic(title="JSON Test Topic", description="Testing JSON handling")
    db_session.add(topic)
    db_session.commit()
    
    # Create outline with complex structure
    complex_structure = {
        "title": "Complex Outline",
        "description": "Testing complex JSON structures",
        "sections": [
            {
                "title": "Introduction",
                "subsections": [
                    {"title": "Background", "content_length": 500},
                    {"title": "Purpose", "content_length": 300}
                ]
            },
            {
                "title": "Main Body",
                "subsections": [
                    {"title": "Methodology", "content_length": 800},
                    {"title": "Results", "content_length": 1200},
                    {"title": "Discussion", "content_length": 1500}
                ]
            },
            {
                "title": "Conclusion",
                "subsections": [
                    {"title": "Summary", "content_length": 400},
                    {"title": "Future Work", "content_length": 300}
                ]
            }
        ],
        "total_sections": 3,
        "estimated_words": 5000
    }
    
    outline = Outline(
        structure=json.dumps(complex_structure),
        topic_id=topic.id
    )
    db_session.add(outline)
    db_session.commit()
    
    # Retrieve and verify JSON structure
    fetched_outline = db_session.query(Outline).filter(Outline.id == outline.id).first()
    restored_structure = json.loads(fetched_outline.structure)
    
    assert restored_structure["title"] == "Complex Outline"
    assert len(restored_structure["sections"]) == 3
    assert restored_structure["sections"][0]["title"] == "Introduction"
    assert len(restored_structure["sections"][1]["subsections"]) == 3
    assert restored_structure["estimated_words"] == 5000
    
    # Update a value in the JSON structure
    restored_structure["estimated_words"] = 6000
    restored_structure["sections"][0]["subsections"].append({"title": "New Subsection", "content_length": 200})
    
    fetched_outline.structure = json.dumps(restored_structure)
    db_session.commit()
    
    # Verify update
    updated_outline = db_session.query(Outline).filter(Outline.id == outline.id).first()
    updated_structure = json.loads(updated_outline.structure)
    
    assert updated_structure["estimated_words"] == 6000
    assert len(updated_structure["sections"][0]["subsections"]) == 3
    assert updated_structure["sections"][0]["subsections"][2]["title"] == "New Subsection"

def test_outline_metadata_json(db_session):
    """Test working with the outline_metadata JSON field."""
    # Create prerequisite topic
    topic = Topic(title="Metadata Test Topic", description="Testing metadata JSON")
    db_session.add(topic)
    db_session.commit()
    
    # Create outline with metadata
    metadata = {
        "style": "detailed",
        "target_audience": "technical",
        "complexity_level": "advanced",
        "include_images": True,
        "suggested_sources": [
            "https://example.com/source1",
            "https://example.com/source2"
        ],
        "keywords": ["AI", "machine learning", "data science"]
    }
    
    outline = Outline(
        structure=json.dumps({"sections": ["Test"]}),
        outline_metadata=json.dumps(metadata),
        topic_id=topic.id
    )
    db_session.add(outline)
    db_session.commit()
    
    # Retrieve and verify metadata
    fetched_outline = db_session.query(Outline).filter(Outline.id == outline.id).first()
    restored_metadata = json.loads(fetched_outline.outline_metadata)
    
    assert restored_metadata["style"] == "detailed"
    assert restored_metadata["complexity_level"] == "advanced"
    assert restored_metadata["include_images"] is True
    assert len(restored_metadata["suggested_sources"]) == 2
    assert len(restored_metadata["keywords"]) == 3
    assert "machine learning" in restored_metadata["keywords"]
    
    # Update metadata
    restored_metadata["complexity_level"] = "intermediate"
    restored_metadata["keywords"].append("natural language processing")
    
    fetched_outline.outline_metadata = json.dumps(restored_metadata)
    db_session.commit()
    
    # Verify update
    updated_outline = db_session.query(Outline).filter(Outline.id == outline.id).first()
    updated_metadata = json.loads(updated_outline.outline_metadata)
    
    assert updated_metadata["complexity_level"] == "intermediate"
    assert len(updated_metadata["keywords"]) == 4
    assert "natural language processing" in updated_metadata["keywords"]

def test_outline_query_methods(db_session):
    """Test common query patterns for outlines."""
    # Create prerequisite topic
    topic = Topic(title="Query Test Topic", description="Testing queries")
    db_session.add(topic)
    db_session.commit()
    
    # Create multiple outlines with different creation times
    outlines = []
    for i in range(5):
        outline = Outline(
            structure=json.dumps({"sections": [f"Section {i+1}"]}),
            topic_id=topic.id
        )
        # We can't directly set created_at due to default value function
        outlines.append(outline)
    
    db_session.add_all(outlines)
    db_session.commit()
    
    # Add slight delay between creation times
    for i, outline in enumerate(outlines):
        # Update to modify timestamps
        structure = json.loads(outline.structure)
        structure["sections"].append(f"Extra section {i}")
        outline.structure = json.dumps(structure)
        db_session.commit()
        time.sleep(0.1)  # Small delay to ensure different timestamps
    
    # Test sorting by created_at
    sorted_outlines = db_session.query(Outline).order_by(desc(Outline.created_at)).all()
    
    # Verify sort order
    for i in range(len(sorted_outlines) - 1):
        assert sorted_outlines[i].created_at >= sorted_outlines[i+1].created_at
    
    # Test filtering with LIKE on JSON content (requires JSON stored as text)
    # This is a basic text search in the JSON string
    section3_outlines = db_session.query(Outline).filter(
        Outline.structure.like('%Section 3%')
    ).all()
    
    # At least one outline should have "Section 3"
    assert len(section3_outlines) >= 1

def test_outline_batch_operations(db_session):
    """Test batch operations on outlines."""
    # Create prerequisite topic
    topic = Topic(title="Batch Test Topic", description="Testing batch operations")
    db_session.add(topic)
    db_session.commit()
    
    # Batch create outlines
    batch_outlines = [
        Outline(
            structure=json.dumps({"sections": [f"Section for batch outline {i}"]}),
            topic_id=topic.id
        )
        for i in range(5)
    ]
    db_session.add_all(batch_outlines)
    db_session.commit()
    
    # Get all outline IDs
    outline_ids = [outline.id for outline in batch_outlines]
    
    # Test batch update - this is tricky with JSON fields since we need to operate on the text
    # Let's add a simple metadata field to all outlines
    for outline in batch_outlines:
        outline.outline_metadata = json.dumps({"batch_updated": True})
    db_session.commit()
    
    # Verify all were updated
    updated_outlines = db_session.query(Outline).filter(Outline.id.in_(outline_ids)).all()
    for outline in updated_outlines:
        metadata = json.loads(outline.outline_metadata) if outline.outline_metadata else {}
        assert metadata.get("batch_updated") is True
    
    # Batch delete
    db_session.query(Outline).filter(Outline.id.in_(outline_ids)).delete(synchronize_session=False)
    db_session.commit()
    
    # Verify all were deleted
    remaining = db_session.query(Outline).filter(Outline.id.in_(outline_ids)).count()
    assert remaining == 0

def test_outline_multiple_per_topic(db_session):
    """Test creating multiple outlines for a single topic."""
    # Create a topic
    topic = Topic(title="Multiple Outlines Topic", description="Testing multiple outlines")
    db_session.add(topic)
    db_session.commit()
    
    # Create multiple outlines for the same topic
    outline_structures = [
        {"type": "brief", "sections": ["Quick Intro", "Key Points", "Summary"]},
        {"type": "standard", "sections": ["Introduction", "Main Body", "Conclusion"]},
        {"type": "detailed", "sections": [
            "Executive Summary", 
            "Detailed Introduction", 
            "Background", 
            "Analysis", 
            "Findings", 
            "Recommendations", 
            "Conclusion"
        ]}
    ]
    
    outlines = []
    for structure in outline_structures:
        outline = Outline(
            structure=json.dumps(structure),
            outline_metadata=json.dumps({"type": structure["type"]}),
            topic_id=topic.id
        )
        outlines.append(outline)
    
    db_session.add_all(outlines)
    db_session.commit()
    
    # Verify all outlines are associated with the topic
    topic_outlines = db_session.query(Outline).filter(Outline.topic_id == topic.id).all()
    assert len(topic_outlines) == 3
    
    # Verify each outline has the correct structure
    for outline in topic_outlines:
        structure = json.loads(outline.structure)
        metadata = json.loads(outline.outline_metadata) if outline.outline_metadata else {}
        
        if metadata.get("type") == "brief":
            assert len(structure["sections"]) == 3
            assert "Quick Intro" in structure["sections"]
        elif metadata.get("type") == "standard":
            assert len(structure["sections"]) == 3
            assert "Main Body" in structure["sections"]
        elif metadata.get("type") == "detailed":
            assert len(structure["sections"]) == 7
            assert "Executive Summary" in structure["sections"]
