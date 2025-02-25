import pytest
import json
from datetime import datetime
from app.models.topic import Topic
from app.models.outline import Outline
from app.models.article import Article
from app.models.source import Source
from app.models.article_sources import ArticleSource
from app.models.prompt import Prompt
from app.models.provider import Provider
from app.models.prompt_provider import PromptProvider
from app.models.job import Job

def test_full_database_workflow(db_session):
    """Test a complete workflow involving all models."""
    # Create a topic
    topic = Topic(title="AI Ethics", description="Discussion of ethical considerations in AI")
    db_session.add(topic)
    db_session.commit()
    
    # Create an outline for the topic
    outline = Outline(
        topic_id=topic.id,
        structure=json.dumps({
            "sections": [
                {"title": "Introduction", "content_points": ["Define AI ethics", "Why it matters"]},
                {"title": "Key Challenges", "content_points": ["Privacy", "Bias", "Transparency"]},
                {"title": "Conclusion", "content_points": ["Future directions", "Call to action"]}
            ]
        })
    )
    db_session.add(outline)
    
    # Create sources
    source1 = Source(
        url="https://example.com/ai-ethics-1",
        title="Understanding AI Ethics",
        publication="AI Journal",
        publication_date=datetime.now(),
        summary="A comprehensive overview of AI ethics principles"
    )
    source2 = Source(
        url="https://example.com/ai-ethics-2",
        title="Bias in Machine Learning",
        publication="Tech Ethics Today",
        publication_date=datetime.now(),
        summary="Discussion of bias issues in machine learning models"
    )
    db_session.add_all([source1, source2])
    db_session.commit()
    
    # Create an article
    article = Article(
        title="The State of AI Ethics Today",
        status="draft",
        article_metadata=json.dumps({"tone": "academic", "word_count": 1500}),
        topic_id=topic.id,
        outline_id=outline.id
    )
    article.sources.extend([source1, source2])
    db_session.add(article)
    db_session.commit()
    
    # Create a provider
    provider = Provider(
        name="OpenAI",
        api_key="sk-test-key",
        endpoint="https://api.openai.com/v1",
        model_name=json.dumps(["gpt-3.5-turbo", "gpt-4"]),
        default_model="gpt-4"
    )
    db_session.add(provider)
    db_session.commit()
    
    # Create a prompt
    prompt = Prompt(
        name="Article Generation",
        template_text="Write an article about {topic} with tone {tone}.",
        description="Generic article generation prompt"
    )
    db_session.add(prompt)
    db_session.commit()
    
    # Create prompt-provider relationship
    pp = PromptProvider(
        prompt_id=prompt.id,
        provider_id=provider.id,
        prompt_metadata=json.dumps({"max_tokens": 1000, "temperature": 0.7})
    )
    db_session.add(pp)
    db_session.commit()
    
    # Create a job
    job = Job(
        status="pending",
        article_id=article.id,
        provider_id=provider.id
    )
    db_session.add(job)
    db_session.commit()
    
    # Verify everything was created and relationships work
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    assert fetched_article.title == "The State of AI Ethics Today"
    assert fetched_article.topic.title == "AI Ethics"
    assert len(fetched_article.sources) == 2
    assert len(fetched_article.jobs) == 1
    
    fetched_job = db_session.query(Job).filter(Job.id == job.id).first()
    assert fetched_job.article.title == "The State of AI Ethics Today"
    assert fetched_job.provider.name == "OpenAI"
    
    fetched_prompt = db_session.query(Prompt).filter(Prompt.id == prompt.id).first()
    assert len(fetched_prompt.providers) == 1
    assert fetched_prompt.providers[0].provider.name == "OpenAI"
    
    # Test cascade deletes by removing a topic
    db_session.delete(topic)
    db_session.commit()
    
    # Verify that related objects are also deleted (if cascade is set)
    remaining_articles = db_session.query(Article).filter(Article.topic_id == topic.id).all()
    assert len(remaining_articles) == 0
