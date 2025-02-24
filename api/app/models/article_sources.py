from sqlalchemy import Column, Integer, ForeignKey
from . import Base

class ArticleSource(Base):
    __tablename__ = 'article_sources'
    article_id = Column(Integer, ForeignKey('articles.id'), primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'), primary_key=True)