import pytest
import json
from datetime import datetime, timezone, timedelta
import time
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc, func

from app.models.prompt import Prompt
from app.models.provider import Provider
from app.models.prompt_provider import PromptProvider

def test_create_prompt(db_session):
    """Test creating a simple prompt."""
    prompt = Prompt(
        name="Test Prompt",
        template_text="This is a test prompt template.",
        description="A prompt for testing purposes."
    )
    db_session.add(prompt)
    db_session.commit()
    
    # Verify prompt is created
    fetched_prompt = db_session.query(Prompt).filter(Prompt.id == prompt.id).first()
    assert fetched_prompt is not None
    assert fetched_prompt.name == "Test Prompt"
    assert fetched_prompt.template_text == "This is a test prompt template."
    assert fetched_prompt.description == "A prompt for testing purposes."
    assert fetched_prompt.created_at is not None
    assert fetched_prompt.updated_at is not None

def test_prompt_update(db_session):
    """Test updating prompt attributes."""
    # Create a prompt
    prompt = Prompt(
        name="Update Test Prompt",
        template_text="This is the original template text.",
        description="This is the original description."
    )
    db_session.add(prompt)
    db_session.commit()
    
    # Verify initial values
    assert prompt.name == "Update Test Prompt"
    assert prompt.template_text == "This is the original template text."
    assert prompt.description == "This is the original description."
    
    # Store original timestamps
    original_created = prompt.created_at
    original_updated = prompt.updated_at
    
    # Update prompt attributes
    prompt.name = "Updated Test Prompt"
    prompt.template_text = "This is the updated template text."
    prompt.description = "This is the updated description."
    db_session.commit()
    
    # Verify updates
    fetched_prompt = db_session.query(Prompt).filter(Prompt.id == prompt.id).first()
    assert fetched_prompt.name == "Updated Test Prompt"
    assert fetched_prompt.template_text == "This is the updated template text."
    assert fetched_prompt.description == "This is the updated description"
    
    # Verify timestamps
    assert fetched_prompt.created_at == original_created  # created_at shouldn't change
    assert fetched_prompt.updated_at > original_updated  # updated_at should be newer

def test_prompt_unique_name_constraint(db_session):
    """Test that prompt names must be unique."""
    # Create first prompt
    prompt1 = Prompt(
        name="Unique Test Prompt",
        template_text="First prompt with this name.",
        description="First prompt for unique test."
    )
    db_session.add(prompt1)
    db_session.commit()
    
    # Create second prompt with same name
    prompt2 = Prompt(
        name="Unique Test Prompt",  # Same name
        template_text="Second prompt with same name.",
        description="Second prompt for unique test."
    )
    db_session.add(prompt2)
    
    # Should raise IntegrityError for unique constraint violation
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()

def test_prompt_timestamps(db_session):
    """Test prompt timestamp behavior."""
    # Create a prompt
    prompt = Prompt(
        name="Timestamp Test Prompt",
        template_text="Testing timestamps.",
        description="A prompt for testing timestamp behavior."
    )
    db_session.add(prompt)
    db_session.commit()
    
    # Check timestamps are created
    assert prompt.created_at is not None
    assert prompt.updated_at is not None
    
    # Store original timestamps
    original_created = prompt.created_at
    original_updated = prompt.updated_at
    
    # Wait a moment to ensure timestamp difference
    time.sleep(1)
    
    # Update the prompt
    prompt.description = "Updated description for timestamp test."
    db_session.commit()
    
    # Verify timestamps
    assert prompt.created_at == original_created  # created_at shouldn't change
    assert prompt.updated_at > original_updated  # updated_at should be newer

def test_prompt_with_null_fields(db_session):
    """Test creating a prompt with nullable fields set to None."""
    # Create a prompt with some nullable fields as None
    prompt = Prompt(
        name="Null Fields Test Prompt",
        template_text="This prompt tests nullable fields.",
        # description is left as None
    )
    db_session.add(prompt)
    db_session.commit()
    
    # Verify prompt is created with NULL fields
    fetched_prompt = db_session.query(Prompt).filter(Prompt.id == prompt.id).first()
    assert fetched_prompt is not None
    assert fetched_prompt.name == "Null Fields Test Prompt"
    assert fetched_prompt.template_text == "This prompt tests nullable fields."
    assert fetched_prompt.description is None

def test_prompt_with_provider_relationship(db_session):
    """Test creating a prompt and associating it with a provider."""
    # Create a provider
    provider = Provider(
        name="Test Provider",
        api_key="test_key_12345",
        endpoint="https://api.test-provider.com",
        model_name="test-model"
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
    
    # Verify the prompt-provider relationship
    fetched_prompt = db_session.query(Prompt).filter(Prompt.id == prompt.id).first()
    assert len(fetched_prompt.providers) == 1
    assert fetched_prompt.providers[0].provider_id == provider.id
    assert json.loads(fetched_prompt.providers[0].configuration)["temperature"] == 0.7
    
    # Verify the relationship from provider side
    fetched_provider = db_session.query(Provider).filter(Provider.id == provider.id).first()
    assert len(fetched_provider.prompts) == 1
    assert fetched_provider.prompts[0].prompt_id == prompt.id
    assert fetched_provider.prompts[0].prompt.name == "Provider Relationship Test Prompt"

def test_prompt_with_multiple_providers(db_session):
    """Test associating a prompt with multiple providers."""
    # Create multiple providers
    providers = [
        Provider(
            name=f"Provider {i}",
            api_key=f"key_{i}",
            endpoint=f"https://api.provider-{i}.com",
            model_name=f"model-{i}"
        )
        for i in range(3)
    ]
    db_session.add_all(providers)
    db_session.commit()
    
    # Create a prompt
    prompt = Prompt(
        name="Multiple Providers Test Prompt",
        template_text="Testing multiple provider relationships.",
        description="A prompt for testing multiple provider relationships."
    )
    db_session.add(prompt)
    db_session.commit()
    
    # Associate the prompt with all providers
    for provider in providers:
        prompt_provider = PromptProvider(
            prompt_id=prompt.id,
            provider_id=provider.id,
            configuration=json.dumps({"temperature": 0.7, "max_tokens": 100})
        )
        db_session.add(prompt_provider)
    db_session.commit()
    
    # Verify the relationships
    fetched_prompt = db_session.query(Prompt).filter(Prompt.id == prompt.id).first()
    assert len(fetched_prompt.providers) == 3
    
    # Check that all providers are associated with the prompt
    provider_ids = [provider.id for provider in providers]
    for provider in fetched_prompt.providers:
        assert provider.provider_id in provider_ids

def test_prompt_deletion_with_providers(db_session):
    """Test deleting a prompt that has provider relationships."""
    # Create a provider
    provider = Provider(
        name="Deletion Test Provider",
        api_key="deletion_test_key",
        endpoint="https://api.deletion-test.com",
        model_name="deletion-model"
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
    
    prompt_id = prompt.id
    
    # Delete the prompt
    db_session.delete(prompt)
    
    # This will either:
    # 1. Fail with IntegrityError if you have RESTRICT/NO ACTION foreign key
    # 2. Delete the prompt_provider if you have CASCADE
    # 3. Set prompt_id to NULL if you have SET NULL
    
    # Let's handle all possibilities
    try:
        db_session.commit()
        # If we get here, either CASCADE or SET NULL is in effect
        
        # Check if prompt_provider was deleted (CASCADE)
        prompt_provider_exists = db_session.query(PromptProvider).filter(PromptProvider.prompt_id == prompt_id).first() is not None
        if not prompt_provider_exists:
            # PromptProvider was deleted - CASCADE behavior
            pass
        else:
            # PromptProvider exists but with NULL prompt_id - SET NULL behavior
            updated_prompt_provider = db_session.query(PromptProvider).filter(PromptProvider.prompt_id == prompt_id).first()
            assert updated_prompt_provider.prompt_id is None
            
    except IntegrityError:
        # RESTRICT/NO ACTION behavior - can't delete prompt while prompt_providers reference it
        db_session.rollback()
        assert db_session.query(Prompt).filter(Prompt.id == prompt_id).first() is not None
        assert db_session.query(PromptProvider).filter(PromptProvider.prompt_id == prompt_id).first() is not None

def test_prompt_query_methods(db_session):
    """Test common query patterns for prompts."""
    # Create prompts with different attributes
    prompt_names = ["Prompt A", "Prompt B", "Prompt C"]
    
    # Create clearly differentiated creation times - use datetime to avoid timezone issues
    base_time = datetime.now(timezone.utc)
    prompts = []
    for i, name in enumerate(prompt_names):
        prompt = Prompt(
            name=name,
            template_text=f"Template for {name}",
            description=f"Description for {name}"
        )
        # We can't directly set created_at due to default value function
        prompts.append(prompt)
    
    db_session.add_all(prompts)
    db_session.commit()
    
    # Add slight delay between creation times
    for i, prompt in enumerate(prompts):
        # Update to modify timestamps
        prompt.description += f" Updated {i}"
        db_session.commit()
        time.sleep(0.1)  # Small delay to ensure different timestamps
    
    # Test sorting by created_at
    sorted_prompts = db_session.query(Prompt).order_by(desc(Prompt.created_at)).all()
    
    # Verify sort order
    for i in range(len(sorted_prompts) - 1):
        assert sorted_prompts[i].created_at >= sorted_prompts[i+1].created_at
    
    # Test filtering by name
    prompt_b = db_session.query(Prompt).filter(Prompt.name == "Prompt B").first()
    assert prompt_b is not None
    assert prompt_b.template_text == "Template for Prompt B"

def test_prompt_batch_operations(db_session):
    """Test batch operations on prompts."""
    # Batch create prompts
    batch_prompts = [
        Prompt(
            name=f"Batch Prompt {i}",
            template_text=f"This is the template for batch prompt {i}.",
            description=f"Description for batch prompt {i}."
        )
        for i in range(5)
    ]
    db_session.add_all(batch_prompts)
    db_session.commit()
    
    # Get all prompt IDs
    prompt_ids = [prompt.id for prompt in batch_prompts]
    
    # Batch update prompts - update description
    db_session.query(Prompt).filter(
        Prompt.id.in_(prompt_ids)
    ).update({"description": "Updated batch description"}, synchronize_session=False)
    db_session.commit()
    
    # Verify all were updated
    updated_count = db_session.query(Prompt).filter(
        and_(Prompt.id.in_(prompt_ids), Prompt.description == "Updated batch description")
    ).count()
    assert updated_count == 5
    
    # Batch delete
    db_session.query(Prompt).filter(Prompt.id.in_(prompt_ids)).delete(synchronize_session=False)
    db_session.commit()
    
    # Verify all were deleted
    remaining = db_session.query(Prompt).filter(Prompt.id.in_(prompt_ids)).count()
    assert remaining == 0