# app/models/__init__.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .topic import Topic as TopicModel