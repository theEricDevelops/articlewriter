import json

def get_provider_model(provider, task_type):
    if provider.default_model != "auto":
        return provider.default_model
    models = json.loads(provider.model_name)
    # Simple task-based logic (expand as needed)
    if task_type == "creative" and "gpt-4" in models:
        return "gpt-4"
    return models[0]  # Default to first model if no match