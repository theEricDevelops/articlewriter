from fastapi import FastAPI
from .routes import topics, sources, articles, outlines, prompts, providers, prompt_providers, jobs

app = FastAPI()

# Include the topics router with a prefix
app.include_router(topics.router, prefix="/topics", tags=["topics"])
app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(outlines.router, prefix="/outlines", tags=["outlines"])
app.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
app.include_router(providers.router, prefix="/providers", tags=["providers"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])