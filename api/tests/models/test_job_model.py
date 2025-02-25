import pytest
import json
from datetime import datetime, timezone, timedelta
import time
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc, func

from app.models.job import Job
from app.models.article import Article
from app.models.provider import Provider
from app.models.topic import Topic
from app.models.outline import Outline

def test_create_job(db_session):
    """Test creating a simple job."""
    job = Job(
        status="pending"
    )
    db_session.add(job)
    db_session.commit()
    
    # Verify job is created
    fetched_job = db_session.query(Job).filter(Job.id == job.id).first()
    assert fetched_job is not None
    assert fetched_job.status == "pending"
    assert fetched_job.created_at is not None
    assert fetched_job.updated_at is not None
    assert fetched_job.article_id is None
    assert fetched_job.provider_id is None

def test_job_with_article(db_session):
    """Test creating a job with an associated article."""
    # Create prerequisite objects
    topic = Topic(title="Job Test Topic", description="Test Description")
    outline = Outline(
        topic=topic,
        structure=json.dumps({"sections": ["Intro", "Body", "Conclusion"]})
    )
    db_session.add_all([topic, outline])
    db_session.commit()
    
    # Create an article
    article = Article(
        title="Job Test Article",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Create a job associated with the article
    job = Job(
        status="pending",
        article_id=article.id
    )
    db_session.add(job)
    db_session.commit()
    
    # Verify the job-article relationship
    fetched_job = db_session.query(Job).filter(Job.id == job.id).first()
    assert fetched_job.article_id == article.id
    assert fetched_job.article.title == "Job Test Article"
    
    # Verify the relationship from article side
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    assert len(fetched_article.jobs) == 1
    assert fetched_article.jobs[0].id == job.id

def test_job_with_provider(db_session):
    """Test creating a job with an associated provider."""
    # Create a provider
    provider = Provider(
        name="Test Provider",
        api_key="test_key_12345",
        endpoint="https://api.test-provider.com",
        model_name="test-model"
    )
    db_session.add(provider)
    db_session.commit()
    
    # Create a job with provider
    job = Job(
        status="pending",
        provider_id=provider.id
    )
    db_session.add(job)
    db_session.commit()
    
    # Verify the job-provider relationship
    fetched_job = db_session.query(Job).filter(Job.id == job.id).first()
    assert fetched_job.provider_id == provider.id
    assert fetched_job.provider.name == "Test Provider"
    
    # Verify the relationship from provider side
    fetched_provider = db_session.query(Provider).filter(Provider.id == provider.id).first()
    assert len(fetched_provider.jobs) == 1
    assert fetched_provider.jobs[0].id == job.id

def test_job_with_article_and_provider(db_session):
    """Test creating a job with both article and provider."""
    # Create prerequisite objects for article
    topic = Topic(title="Complete Job Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    article = Article(
        title="Complete Job Test Article",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    
    # Create provider
    provider = Provider(
        name="Complete Test Provider",
        api_key="complete_test_key",
        endpoint="https://api.complete-test.com",
        model_name="complete-model"
    )
    
    db_session.add_all([article, provider])
    db_session.commit()
    
    # Create job with both article and provider
    job = Job(
        status="pending",
        article_id=article.id,
        provider_id=provider.id
    )
    db_session.add(job)
    db_session.commit()
    
    # Verify relationships
    fetched_job = db_session.query(Job).filter(Job.id == job.id).first()
    assert fetched_job.article.title == "Complete Job Test Article"
    assert fetched_job.provider.name == "Complete Test Provider"

def test_job_timestamps(db_session):
    """Test job timestamp behavior."""
    # Create a job
    job = Job(status="pending")
    db_session.add(job)
    db_session.commit()
    
    # Check timestamps are created
    assert job.created_at is not None
    assert job.updated_at is not None
    
    # Store original timestamps
    original_created = job.created_at
    original_updated = job.updated_at
    
    # Wait a moment to ensure timestamp difference
    time.sleep(1)
    
    # Update the job
    job.status = "in_progress"
    db_session.commit()
    
    # Verify timestamps
    assert job.created_at == original_created  # created_at shouldn't change
    assert job.updated_at > original_updated  # updated_at should be newer

def test_job_status_transitions(db_session):
    """Test different job status transitions."""
    # Create a job
    job = Job(status="pending")
    db_session.add(job)
    db_session.commit()
    
    # Test status transitions
    job.status = "in_progress"
    db_session.commit()
    assert job.status == "in_progress"
    
    job.status = "completed"
    db_session.commit()
    assert job.status == "completed"
    
    job.status = "failed"
    db_session.commit()
    assert job.status == "failed"

def test_job_deletion(db_session):
    """Test deleting a job."""
    # Create prerequisite objects
    provider = Provider(
        name="Deletion Test Provider",
        api_key="deletion_test_key",
        endpoint="https://api.deletion-test.com",
        model_name="deletion-model"
    )
    topic = Topic(title="Deletion Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([provider, topic, outline])
    db_session.commit()
    
    article = Article(
        title="Deletion Test Article",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Create a job with relationships
    job = Job(
        status="pending",
        article_id=article.id,
        provider_id=provider.id
    )
    db_session.add(job)
    db_session.commit()
    
    job_id = job.id
    
    # Delete the job
    db_session.delete(job)
    db_session.commit()
    
    # Verify job is deleted
    deleted_job = db_session.query(Job).filter(Job.id == job_id).first()
    assert deleted_job is None
    
    # Verify related objects still exist
    fetched_article = db_session.query(Article).filter(Article.id == article.id).first()
    assert fetched_article is not None
    
    fetched_provider = db_session.query(Provider).filter(Provider.id == provider.id).first()
    assert fetched_provider is not None

def test_job_cascade_article_deletion(db_session):
    """Test what happens to jobs when an article is deleted."""
    # Create prerequisite objects
    topic = Topic(title="Cascade Test Topic", description="Test")
    outline = Outline(topic=topic, structure=json.dumps({"sections": ["Test"]}))
    db_session.add_all([topic, outline])
    db_session.commit()
    
    article = Article(
        title="Cascade Test Article",
        status="draft",
        topic_id=topic.id,
        outline_id=outline.id
    )
    db_session.add(article)
    db_session.commit()
    
    # Create multiple jobs for the article
    jobs = [
        Job(status="pending", article_id=article.id),
        Job(status="in_progress", article_id=article.id)
    ]
    db_session.add_all(jobs)
    db_session.commit()
    
    job_ids = [job.id for job in jobs]
    
    # Delete the article
    db_session.delete(article)
    db_session.commit()
    
    # Check what happened to the jobs
    # SQLite will set NULL for article_id by default
    for job_id in job_ids:
        job = db_session.query(Job).filter(Job.id == job_id).first()
        # Jobs should still exist with article_id set to NULL
        assert job is not None
        assert job.article_id is None

def test_job_query_methods(db_session):
    """Test common query patterns for jobs."""
    # Create jobs with different statuses
    jobs = [
        Job(status="pending"),
        Job(status="pending"),
        Job(status="in_progress"),
        Job(status="completed"),
        Job(status="failed")
    ]
    db_session.add_all(jobs)
    db_session.commit()
    
    # Test filtering by status
    pending_jobs = db_session.query(Job).filter(Job.status == "pending").all()
    assert len(pending_jobs) == 2
    
    in_progress_jobs = db_session.query(Job).filter(Job.status == "in_progress").all()
    assert len(in_progress_jobs) == 1
    
    completed_jobs = db_session.query(Job).filter(Job.status == "completed").all()
    assert len(completed_jobs) == 1
    
    failed_jobs = db_session.query(Job).filter(Job.status == "failed").all()
    assert len(failed_jobs) == 1
    
    # Test compound conditions
    pending_or_failed = db_session.query(Job).filter(
        or_(Job.status == "pending", Job.status == "failed")
    ).all()
    assert len(pending_or_failed) == 3
    
    # Test ordering by created_at
    ordered_jobs = db_session.query(Job).order_by(desc(Job.created_at)).all()
    for i in range(len(ordered_jobs) - 1):
        assert ordered_jobs[i].created_at >= ordered_jobs[i+1].created_at

def test_job_batch_operations(db_session):
    """Test batch operations on jobs."""
    # Batch create jobs
    batch_jobs = [
        Job(status="pending") for _ in range(5)
    ]
    db_session.add_all(batch_jobs)
    db_session.commit()
    
    # Get all job IDs
    job_ids = [job.id for job in batch_jobs]
    
    # Batch update jobs
    db_session.query(Job).filter(
        Job.id.in_(job_ids)
    ).update({"status": "in_progress"}, synchronize_session=False)
    db_session.commit()
    
    # Verify all were updated
    updated_count = db_session.query(Job).filter(
        and_(Job.id.in_(job_ids), Job.status == "in_progress")
    ).count()
    assert updated_count == 5
    
    # Batch delete
    db_session.query(Job).filter(Job.id.in_(job_ids)).delete(synchronize_session=False)
    db_session.commit()
    
    # Verify all were deleted
    remaining = db_session.query(Job).filter(Job.id.in_(job_ids)).count()
    assert remaining == 0

def test_job_sorting_and_pagination(db_session):
    """Test sorting and pagination of jobs."""
    # Create jobs with different timestamps
    base_time = datetime.now()
    jobs = []
    
    for i in range(10):
        job = Job(status="pending")
        # Manually adjust created_at for testing sort order
        # Note: This is for testing only and might require adaptation based on your ORM setup
        if hasattr(job, '_created_at'):
            job._created_at = base_time - timedelta(hours=i)
        jobs.append(job)
    
    db_session.add_all(jobs)
    db_session.commit()
    
    # Sort by created_at descending (newest first)
    sorted_desc = db_session.query(Job).order_by(desc(Job.created_at)).all()
    
    # Check if sorted correctly
    for i in range(len(sorted_desc) - 1):
        assert sorted_desc[i].created_at >= sorted_desc[i+1].created_at
    
    # Test pagination - page 1 (first 3 jobs)
    page_size = 3
    page1 = db_session.query(Job).order_by(Job.created_at).limit(page_size).all()
    
    assert len(page1) == page_size
    
    # Test pagination - page 2 (next 3 jobs)
    page2 = db_session.query(Job).order_by(Job.created_at).offset(page_size).limit(page_size).all()
    
    assert len(page2) == page_size
    # Ensure page2 contains different jobs than page1
    assert set([j.id for j in page1]).isdisjoint(set([j.id for j in page2]))

def test_job_aggregations(db_session):
    """Test aggregation queries on jobs."""
    # Create jobs with different statuses
    statuses = ["pending", "in_progress", "completed", "failed"]
    jobs = []
    
    # Create multiple jobs with different statuses
    for status in statuses:
        for _ in range(3):  # 3 jobs of each status
            jobs.append(Job(status=status))
    
    db_session.add_all(jobs)
    db_session.commit()
    
    # Count jobs by status
    status_counts = db_session.query(
        Job.status, func.count(Job.id)
    ).group_by(Job.status).all()
    
    status_count_dict = dict(status_counts)
    for status in statuses:
        assert status_count_dict[status] == 3
    
    # Count jobs created today
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_count = db_session.query(Job).filter(
        and_(
            Job.created_at >= today_start,
            Job.created_at <= today_end
        )
    ).count()
    
    assert today_count == len(jobs)  # All jobs were created today

def test_job_constraints(db_session):
    """Test constraints on the Job model."""
    # Test default status
    job = Job()  # No status provided
    db_session.add(job)
    db_session.commit()
    
    assert job.status == "pending"  # Should use the default
    
    # Since status is nullable=False but SQLite doesn't enforce it at commit time,
    # we'll just test that the default value is applied correctly
    
    # Test a status change to None (which may or may not be allowed depending on your DB)
    job.status = None
    
    # Some databases will allow this at the ORM level but fail on commit
    # Others will reject it immediately
    try:
        db_session.commit()
        # If we get here, the NULL was accepted (which shouldn't be the case with SQLite,
        # but explicit constraints aren't always enforced)
        db_session.refresh(job)
        assert job.status is not None  # Check if DB applied default
    except IntegrityError:
        # This is the expected behavior with proper NOT NULL constraints
        db_session.rollback()

def test_foreign_key_constraints(db_session):
    """Test foreign key constraints on the Job model."""
    # In SQLite, foreign key constraints may not be enforced by default
    # Let's check if the relationships work as expected
    
    # Create a job with a fake article_id
    job_with_fake_article = Job(
        status="pending",
        article_id=999999  # Assuming this ID doesn't exist
    )
    db_session.add(job_with_fake_article)
    
    try:
        db_session.commit()
        # If we get here, SQLite didn't enforce the foreign key (which is the default behavior)
        # Let's check that the relationship returns None for non-existent articles
        assert job_with_fake_article.article is None
    except IntegrityError:
        # This would happen if SQLite has foreign key constraints enabled
        db_session.rollback()
    
    # Create a job with a fake provider_id
    db_session.rollback()  # Make sure we start clean
    
    job_with_fake_provider = Job(
        status="pending",
        provider_id=999999  # Assuming this ID doesn't exist
    )
    db_session.add(job_with_fake_provider)
    
    try:
        db_session.commit()
        # If we get here, SQLite didn't enforce the foreign key
        # Let's check that the relationship returns None for non-existent providers
        assert job_with_fake_provider.provider is None
    except IntegrityError:
        # This would happen if SQLite has foreign key constraints enabled
        db_session.rollback()