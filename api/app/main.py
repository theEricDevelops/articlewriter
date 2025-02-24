from fastapi import FastAPI
from .routes import topics_router

app = FastAPI()

# Include the topics router with a prefix
app.include_router(topics_router, prefix="/topics")