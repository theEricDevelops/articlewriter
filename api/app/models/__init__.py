# app/models/__init__.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .topic import Topic
from .source import Source
from .article import Article
from .outline import Outline