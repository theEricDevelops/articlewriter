from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils.db_utils import db_manager
from app.models.article import Article
from app.models.source import Source
from app.schemas.articles import ArticleCreate, ArticleUpdate, ArticleResponse
import json

router = APIRouter()

@router.post("/", response_model=ArticleResponse)
async def create_article(article: ArticleCreate, db: Session = Depends(db_manager.get_db)):
    db_article = Article(
        title=article.title,
        status=article.status,
        article_metadata=json.dumps(article.article_metadata) if article.article_metadata else None,
        topic_id=article.topic_id,
        outline_id=article.outline_id
    )
    if article.source_ids:
        db_article.sources = db.query(Source).filter(Source.id.in_(article.source_ids)).all()
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

@router.get("/", response_model=List[ArticleResponse])
async def read_articles(skip: int = 0, limit: int = 100, db: Session = Depends(db_manager.get_db)):
    articles = db.query(Article).offset(skip).limit(limit).all()
    return articles

@router.get("/{article_id}", response_model=ArticleResponse)
async def read_article(article_id: int, db: Session = Depends(db_manager.get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(article_id: int, article_update: ArticleUpdate, db: Session = Depends(db_manager.get_db)):
    db_article = db.query(Article).filter(Article.id == article_id).first()
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    update_data = article_update.dict(exclude_unset=True)
    if "article_metadata" in update_data:
        update_data["article_metadata"] = json.dumps(update_data["article_metadata"]) if update_data["article_metadata"] else None
    if "source_ids" in update_data:
        db_article.sources = db.query(Source).filter(Source.id.in_(article_update.source_ids)).all() if article_update.source_ids else []
    for key, value in update_data.items():
        if key != "source_ids":
            setattr(db_article, key, value)
    db.commit()
    db.refresh(db_article)
    return db_article

@router.delete("/{article_id}", response_model=ArticleResponse)
async def delete_article(article_id: int, db: Session = Depends(db_manager.get_db)):
    db_article = db.query(Article).filter(Article.id == article_id).first()
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(db_article)
    db.commit()
    return db_article