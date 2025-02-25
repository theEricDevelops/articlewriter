import pytest
import json
from app.models.prompt import Prompt
from app.models.provider import Provider
from app.models.prompt_provider import PromptProvider

def test_prompt_provider_relationship(db_session):
    """Test the many-to-many relationship between Prompt and Provider."""
    # Create prompts
    prompt1 = Prompt(
        name="Test Prompt 1",
        template_text="This is a test prompt template 1",
        description="Test description 1"
    )
    prompt2 = Prompt(
        name="Test Prompt 2",
        template_text="This is a test prompt template 2",
        description="Test description 2"
    )
    
    # Create providers
    provider1 = Provider(
        name="Test Provider 1",
        api_key="test_key_1",
        endpoint="https://api.example.com/v1",
        model_name=json.dumps(["model1", "model2"]),
        default_model="model1"
    )
    provider2 = Provider(
        name="Test Provider 2",
        api_key="test_key_2",
        endpoint="https://api.example.com/v2",
        model_name=json.dumps(["model3", "model4"]),
        default_model="auto"
    )
    
    db_session.add_all([prompt1, prompt2, provider1, provider2])
    db_session.commit()
    
    # Create prompt-provider relationships with metadata
    pp1 = PromptProvider(
        prompt_id=prompt1.id,
        provider_id=provider1.id,
        prompt_metadata=json.dumps({"tone": "formal"})
    )
    pp2 = PromptProvider(
        prompt_id=prompt1.id,
        provider_id=provider2.id,
        prompt_metadata=json.dumps({"tone": "casual"})
    )
    pp3 = PromptProvider(
        prompt_id=prompt2.id,
        provider_id=provider1.id,
        prompt_metadata=json.dumps({"tone": "technical"})
    )
    
    db_session.add_all([pp1, pp2, pp3])
    db_session.commit()
    
    # Verify relationships
    fetched_prompt1 = db_session.query(Prompt).filter(Prompt.id == prompt1.id).first()
    fetched_prompt2 = db_session.query(Prompt).filter(Prompt.id == prompt2.id).first()
    fetched_provider1 = db_session.query(Provider).filter(Provider.id == provider1.id).first()
    
    assert len(fetched_prompt1.providers) == 2
    assert len(fetched_prompt2.providers) == 1
    assert len(fetched_provider1.prompts) == 2
    
    # Check metadata is stored correctly
    assert json.loads(fetched_prompt1.providers[0].prompt_metadata)["tone"] in ["formal", "casual"]
    assert json.loads(fetched_prompt2.providers[0].prompt_metadata)["tone"] == "technical"
