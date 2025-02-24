# app/models/__init__.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .topic import Topic
from .source import Source
from .article import Article
from .article_sources import ArticleSource
from .outline import Outline
from .prompt import Prompt
from .provider import Provider
from .prompt_provider import PromptProvider
from .job import Job