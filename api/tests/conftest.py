import os
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.models.topic import Topic
from app.models.outline import Outline
from app.models.article import Article
from app.models.source import Source
from app.models.prompt import Prompt
from app.models.provider import Provider
from app.models.prompt_provider import PromptProvider
from app.models.job import Job

# Use in-memory SQLite database for testing
@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Clean up
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_data(db_session):
    """Create a set of related sample data for testing."""
    # Create a topic
    topic = Topic(title="Sample Topic", description="Sample description")
    db_session.add(topic)
    db_session.flush()  # Get ID without committing
    
    # Create an outline
    outline = Outline(
        topic_id=topic.id,
        structure='{"sections": ["Introduction", "Body", "Conclusion"]}',
        outline_metadata='{"style": "formal"}'
    )
    db_session.add(outline)
    db_session.flush()
    
    # Create sources
    source1 = Source(
        url="https://example.com/1",
        title="Source 1",
        publication="Publication 1",
        publication_date=datetime.now(),
        summary="Summary 1"
    )
    source2 = Source(
        url="https://example.com/2",
        title="Source 2",
        publication="Publication 2",
        publication_date=datetime.now(),
        summary="Summary 2"
    )
    db_session.add_all([source1, source2])
    db_session.flush()
    
    # Create an article
    article = Article(
        title="Sample Article",
        status="draft",
        article_metadata='{"tone": "informative"}',
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.flush()
    
    # Associate sources with article
    article.sources = [source1, source2]
    
    # Create a provider
    provider = Provider(
        name="OpenAI",
        api_key="test_key",
        endpoint="https://api.openai.com/v1",
        model_name='["gpt-3.5-turbo", "gpt-4"]',
        default_model="auto"
    )
    db_session.add(provider)
    db_session.flush()
    
    # Create a prompt
    prompt = Prompt(
        name="Article Generation",
        template_text="Generate an article about {{topic}}",
        description="Basic article generation prompt"
    )
    db_session.add(prompt)
    db_session.flush()
    
    # Create prompt-provider association
    prompt_provider = PromptProvider(
        prompt_id=prompt.id,
        provider_id=provider.id,
        prompt_metadata='{"max_tokens": 2000}'
    )
    db_session.add(prompt_provider)
    
    # Create a job
    job = Job(
        status="pending",
        article_id=article.id,
        provider_id=provider.id
    )
    db_session.add(job)
    
    db_session.commit()
    
    # Return created objects for use in tests
    return {
        "topic": topic,
        "outline": outline,
        "sources": [source1, source2],
        "article": article,
        "provider": provider,
        "prompt": prompt,
        "prompt_provider": prompt_provider,
        "job": job
    }