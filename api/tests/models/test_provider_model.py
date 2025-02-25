import pytest
import json
from datetime import datetime, timezone, timedelta
import time
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc, func

from app.models.provider import Provider
from app.models.prompt import Prompt
from app.models.prompt_provider import PromptProvider
from app.models.job import Job

def test_create_provider(db_session):
    """Test creating a simple provider."""
    provider = Provider(
        name="Test Provider",
        api_key="test_key_12345",
        endpoint="https://api.test-provider.com",
        model_name=json.dumps(["test-model-1", "test-model-2"]),
        default_model="test-model-1"
    )
    db_session.add(provider)
    db_session.commit()
    
    # Verify provider is created
    fetched_provider = db_session.query(Provider).filter(Provider.id == provider.id).first()
    assert fetched_provider is not None
    assert fetched_provider.name == "Test Provider"
    assert fetched_provider.api_key == "test_key_12345"
    assert fetched_provider.endpoint == "https://api.test-provider.com"
    assert json.loads(fetched_provider.model_name) == ["test-model-1", "test-model-2"]
    assert fetched_provider.default_model == "test-model-1"
    assert fetched_provider.created_at is not None
    assert fetched_provider.updated_at is not None

def test_provider_unique_name_constraint(db_session):
    """Test that provider names must be unique."""
    # Create first provider
    provider1 = Provider(
        name="Unique Test Provider",
        api_key="key_1",
        endpoint="https://api.unique1.com",
        model_name=json.dumps(["model-1"]),
        default_model="model-1"
    )
    db_session.add(provider1)
    db_session.commit()
    
    # Create second provider with same name
    provider2 = Provider(
        name="Unique Test Provider",  # Same name
        api_key="key_2",
        endpoint="https://api.unique2.com",
        model_name=json.dumps(["model-2"]),
        default_model="model-2"
    )
    db_session.add(provider2)
    
    # Should raise IntegrityError for unique constraint violation
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()

def test_provider_timestamps(db_session):
    """Test provider timestamp behavior."""
    # Create a provider
    provider = Provider(
        name="Timestamp Test Provider",
        api_key="timestamp_key",
        endpoint="https://api.timestamp.com",
        model_name=json.dumps(["timestamp-model"]),
        default_model="timestamp-model"
    )
    db_session.add(provider)
    db_session.commit()
    
    # Check timestamps are created
    assert provider.created_at is not None
    assert provider.updated_at is not None
    
    # Store original timestamps
    original_created = provider.created_at
    original_updated = provider.updated_at
    
    # Wait a moment to ensure timestamp difference
    time.sleep(1)
    
    # Update the provider
    provider.endpoint = "https://api.timestamp-updated.com"
    db_session.commit()
    
    # Verify timestamps
    assert provider.created_at == original_created  # created_at shouldn't change
    assert provider.updated_at > original_updated  # updated_at should be newer

def test_provider_with_prompt_relationship(db_session):
    """Test creating a provider and associating it with a prompt."""
    # Create a provider
    provider = Provider(
        name="Prompt Relationship Test Provider",
        api_key="prompt_key",
        endpoint="https://api.prompt.com",
        model_name=json.dumps(["prompt-model"]),
        default_model="prompt-model"
    )
    db_session.add(provider)
    db_session.commit()
    
    # Create a prompt
    prompt = Prompt(
        name="Provider Relationship Test Prompt",
        template_text="Testing provider relationships.",
        description="A prompt for testing provider relationships."
    )
    db_session.add(prompt)
    db_session.commit()
    
    # Associate the prompt with the provider
    prompt_provider = PromptProvider(
        prompt_id=prompt.id,
        provider_id=provider.id,
        configuration=json.dumps({"temperature": 0.7, "max_tokens": 100})
    )
    db_session.add(prompt_provider)
    db_session.commit()
    
    # Verify the provider-prompt relationship
    fetched_provider = db_session.query(Provider).filter(Provider.id == provider.id).first()
    assert len(fetched_provider.prompts) == 1
    assert fetched_provider.prompts[0].prompt_id == prompt.id
    assert fetched_provider.prompts[0].prompt.name == "Provider Relationship Test Prompt"
    assert json.loads(fetched_provider.prompts[0].configuration)["temperature"] == 0.7
    
    # Verify the relationship from prompt side
    fetched_prompt = db_session.query(Prompt).filter(Prompt.id == prompt.id).first()
    assert len(fetched_prompt.providers) == 1
    assert fetched_prompt.providers[0].provider_id == provider.id
    assert fetched_prompt.providers[0].provider.name == "Prompt Relationship Test Provider"

def test_provider_with_multiple_prompts(db_session):
    """Test associating a provider with multiple prompts."""
    # Create a provider
    provider = Provider(
        name="Multiple Prompts Test Provider",
        api_key="multi_prompt_key",
        endpoint="https://api.multi-prompt.com",
        model_name=json.dumps(["multi-prompt-model"]),
        default_model="multi-prompt-model"
    )
    db_session.add(provider)
    db_session.commit()
    
    # Create multiple prompts
    prompts = [
        Prompt(
            name=f"Test Prompt {i}",
            template_text=f"Template for prompt {i}",
            description=f"Description for prompt {i}"
        )
        for i in range(3)
    ]
    db_session.add_all(prompts)
    db_session.commit()
    
    # Associate the prompts with the provider
    for prompt in prompts:
        prompt_provider = PromptProvider(
            prompt_id=prompt.id,
            provider_id=provider.id,
            configuration=json.dumps({"temperature": 0.7, "max_tokens": 100})
        )
        db_session.add(prompt_provider)
    db_session.commit()
    
    # Verify the relationships
    fetched_provider = db_session.query(Provider).filter(Provider.id == provider.id).first()
    assert len(fetched_provider.prompts) == 3
    
    # Check that all prompts are associated with the provider
    prompt_ids = [prompt.id for prompt in prompts]
    for prompt_provider in fetched_provider.prompts:
        assert prompt_provider.prompt_id in prompt_ids

def test_provider_with_job_relationship(db_session):
    """Test creating a provider and associating it with a job."""
    # Create a provider
    provider = Provider(
        name="Job Relationship Test Provider",
        api_key="job_key",
        endpoint="https://api.job.com",
        model_name=json.dumps(["job-model"]),
        default_model="job-model"
    )
    db_session.add(provider)
    db_session.commit()
    
    # Create a job associated with the provider
    job = Job(
        status="pending",
        provider_id=provider.id
    )
    db_session.add(job)
    db_session.commit()
    
    # Verify the provider-job relationship
    fetched_job = db_session.query(Job).filter(Job.id == job.id).first()
    assert fetched_job.provider_id == provider.id
    assert fetched_job.provider.name == "Job Relationship Test Provider"
    
    # Verify the relationship from provider side
    fetched_provider = db_session.query(Provider).filter(Provider.id == provider.id).first()
    assert len(fetched_provider.jobs) == 1
    assert fetched_provider.jobs[0].id == job.id

def test_provider_deletion_with_prompt(db_session):
    """Test that a provider with an associated prompt cannot be deleted."""
    # Create a provider
    provider = Provider(
        name="Deletion Test Provider",
        api_key="deletion_test_key",
        endpoint="https://api.deletion-test.com",
        model_name=json.dumps(["deletion-model"]),
        default_model="deletion-model"
    )
    db_session.add(provider)
    db_session.commit()
    
    # Create a prompt
    prompt = Prompt(
        name="Deletion Test Prompt",
        template_text="Testing deletion.",
        description="A prompt for testing deletion."
    )
    db_session.add(prompt)
    db_session.commit()
    
    # Associate the prompt with the provider
    prompt_provider = PromptProvider(
        prompt_id=prompt.id,
        provider_id=provider.id,
        configuration=json.dumps({"temperature": 0.7, "max_tokens": 100})
    )
    db_session.add(prompt_provider)
    db_session.commit()
    
    provider_id = provider.id
    
    # Try to delete the provider
    db_session.delete(provider)
    
    # Should raise IntegrityError since the provider has an associated prompt
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()
    
    # Verify both provider and prompt still exist
    assert db_session.query(Provider).filter(Provider.id == provider_id).first() is not None
    assert db_session.query(Prompt).filter(Prompt.id == prompt.id).first() is not None
    
    # Now delete the prompt_provider association first
    db_session.delete(prompt_provider)
    db_session.commit()
    
    # Now we should be able to delete the provider
    db_session.delete(provider)
    db_session.commit()
    
    # Verify both provider and prompt_provider are gone
    assert db_session.query(Provider).filter(Provider.id == provider_id).first() is None
    assert db_session.query(PromptProvider).filter(PromptProvider.provider_id == provider_id).first() is None
    
    # Verify the prompt still exists
    assert db_session.query(Prompt).filter(Prompt.id == prompt.id).first() is not None

def test_provider_deletion_with_job(db_session):
    """Test that a provider with an associated job cannot be deleted."""
    # Create a provider
    provider = Provider(
        name="Job Deletion Test Provider",
        api_key="job_deletion_key",
        endpoint="https://api.job-deletion.com",
        model_name=json.dumps(["job-deletion-model"]),
        default_model="job-deletion-model"
    )
    db_session.add(provider)
    db_session.commit()
    
    # Create a job associated with the provider
    job = Job(
        status="pending",
        provider_id=provider.id
    )
    db_session.add(job)
    db_session.commit()
    
    provider_id = provider.id
    
    # Try to delete the provider
    db_session.delete(provider)
    
    # Should raise IntegrityError since the provider has an associated job
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()
    
    # Verify both provider and job still exist
    assert db_session.query(Provider).filter(Provider.id == provider_id).first() is not None
    assert db_session.query(Job).filter(Job.id == job.id).first() is not None
    
    # Now delete the job first
    db_session.delete(job)
    db_session.commit()
    
    # Now we should be able to delete the provider
    db_session.delete(provider)
    db_session.commit()
    
    # Verify both provider and job are gone
    assert db_session.query(Provider).filter(Provider.id == provider_id).first() is None
    assert db_session.query(Job).filter(Job.id == job.id).first() is None

def test_provider_update(db_session):
    """Test updating provider attributes."""
    # Create a provider
    provider = Provider(
        name="Update Test Provider",
        api_key="original_key",
        endpoint="https://api.original.com",
        model_name=json.dumps(["original-model"]),
        default_model="original-model"
    )
    db_session.add(provider)
    db_session.commit()
    
    # Verify initial values
    assert provider.name == "Update Test Provider"
    assert provider.api_key == "original_key"
    assert provider.endpoint == "https://api.original.com"
    assert json.loads(provider.model_name) == ["original-model"]
    assert provider.default_model == "original-model"
    
    # Store original timestamps
    original_created = provider.created_at
    original_updated = provider.updated_at
    
    # Update provider attributes
    provider.name = "Updated Test Provider"
    provider.api_key = "updated_key"
    provider.endpoint = "https://api.updated.com"
    provider.model_name = json.dumps(["updated-model-1", "updated-model-2"])
    provider.default_model = "updated-model-1"
    db_session.commit()
    
    # Verify updates
    fetched_provider = db_session.query(Provider).filter(Provider.id == provider.id).first()
    assert fetched_provider.name == "Updated Test Provider"
    assert fetched_provider.api_key == "updated_key"
    assert fetched_provider.endpoint == "https://api.updated.com"
    assert json.loads(fetched_provider.model_name) == ["updated-model-1", "updated-model-2"]
    assert fetched_provider.default_model == "updated-model-1"
    
    # Verify timestamps
    assert fetched_provider.created_at == original_created  # created_at shouldn't change
    assert fetched_provider.updated_at > original_updated  # updated_at should be newer

def test_provider_query_methods(db_session):
    """Test common query patterns for providers."""
    # Create providers with different attributes
    provider_names = ["Provider A", "Provider B", "Provider C"]
    endpoints = ["https://api.a.com", "https://api.b.com", "https://api.c.com"]
    
    # Create clearly differentiated creation times - use datetime to avoid timezone issues
    base_time = datetime.now(timezone.utc)
    providers = []
    for i, (name, endpoint) in enumerate(zip(provider_names, endpoints)):
        provider = Provider(
            name=name,
            api_key=f"key_{i}",
            endpoint=endpoint,
            model_name=json.dumps([f"model-{i}-1", f"model-{i}-2"]),
            default_model=f"model-{i}-1"
        )
        # We can't directly set created_at due to default value function
        providers.append(provider)
    
    db_session.add_all(providers)
    db_session.commit()
    
    # Add slight delay between creation times
    for i, provider in enumerate(providers):
        # Update to modify timestamps
        provider.endpoint += f"-updated"
        db_session.commit()
        time.sleep(0.1)  # Small delay to ensure different timestamps
    
    # Test sorting by created_at
    sorted_providers = db_session.query(Provider).order_by(desc(Provider.created_at)).all()
    
    # Verify sort order
    for i in range(len(sorted_providers) - 1):
        assert sorted_providers[i].created_at >= sorted_providers[i+1].created_at
    
    # Test filtering by name
    provider_b = db_session.query(Provider).filter(Provider.name == "Provider B").first()
    assert provider_b is not None
    assert provider_b.endpoint == "https://api.b.com-updated"
    
    # Test filtering with LIKE on endpoint
    providers_with_api = db_session.query(Provider).filter(
        Provider.endpoint.like('%api%')
    ).all()
    assert len(providers_with_api) == 3

def test_provider_batch_operations(db_session):
    """Test batch operations on providers."""
    # Batch create providers
    batch_providers = [
        Provider(
            name=f"Batch Provider {i}",
            api_key=f"key_{i}",
            endpoint=f"https://api.batch{i}.com",
            model_name=json.dumps([f"batch-model-{i}"]),
            default_model=f"batch-model-{i}"
        )
        for i in range(5)
    ]
    db_session.add_all(batch_providers)
    db_session.commit()
    
    # Get all provider IDs
    provider_ids = [provider.id for provider in batch_providers]
    
    # Batch update providers - update endpoint
    db_session.query(Provider).filter(
        Provider.id.in_(provider_ids)
    ).update({"endpoint": "https://api.batch-updated.com"}, synchronize_session=False)
    db_session.commit()
    
    # Verify all were updated
    updated_count = db_session.query(Provider).filter(
        and_(Provider.id.in_(provider_ids), Provider.endpoint == "https://api.batch-updated.com")
    ).count()
    assert updated_count == 5
    
    # Batch delete
    db_session.query(Provider).filter(Provider.id.in_(provider_ids)).delete(synchronize_session=False)
    db_session.commit()
    
    # Verify all were deleted
    remaining = db_session.query(Provider).filter(Provider.id.in_(provider_ids)).count()
    assert remaining == 0
