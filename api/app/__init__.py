# app/__init__.py
import os
from fastapi import FastAPI
from .constants import PROJECT_ROOT, API_ROOT
from .models import Base
from .routes import topics, sources, articles, outlines, prompts, providers, jobs

app = FastAPI()


# Include the routers with prefixes
app.include_router(topics.router, prefix="/topics", tags=["topics"])
app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(outlines.router, prefix="/outlines", tags=["outlines"])
app.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
app.include_router(providers.router, prefix="/providers", tags=["providers"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])