import os
from dotenv import load_dotenv
from app.constants import PROJECT_ROOT, API_ROOT

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List, Dict
from contextlib import asynccontextmanager
from app.models import *

class DatabaseManager:
    def __init__(self, **engine_options):
        load_dotenv()

        db_type = os.getenv("DB_TYPE", "sqlite")
        if db_type == "sqlite":
            db_path = os.getenv("DB_PATH", "app.db")  # Default to app.db if not specified

    async def get_session(self) -> AsyncSession:
        if not self.engine:
            self.engine = create_async_engine(self.database_url, **self.engine_options)
            self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        return self.session_factory()
    
    def get_db(self):
        """Synchronous version for FastAPI dependency injection"""
        # This is a generator function that FastAPI can use as a dependency
        async def get_db_session():
            async with self.get_session() as session:
                yield session
        return get_db_session

    async def close(self):
        if self.engine:
            await self.engine.dispose()

    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def health_check(self) -> bool:
        try:
            async with self.get_session() as session:
                await session.execute(select(1))
                return True
        except Exception:
            return False

    @asynccontextmanager
    async def transaction(self):
        async with self.get_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

    async def get_topic_with_articles(self, topic_id: int) -> Topic:
        async with self.get_session() as session:
            result = await session.execute(
                select(Topic)
                .options(joinedload(Topic.articles))
                .where(Topic.id == topic_id)
            )
            return result.scalars().first()

    async def get_article_full(self, article_id: int) -> Article:
        async with self.get_session() as session:
            result = await session.execute(
                select(Article)
                .options(
                    joinedload(Article.outline),
                    joinedload(Article.sources).joinedload(ArticleSource.source)
                )
                .where(Article.id == article_id)
            )
            return result.scalars().first()

    async def create_article_with_deps(self, article_data: Dict, outline_data: Dict, source_ids: List[int]) -> Article:
        async with self.transaction() as session:
            article = Article(**article_data)
            outline = Outline(**outline_data, article=article)
            session.add_all([article, outline])
            await session.flush()  # Get article.id for relationships
            source_links = [ArticleSource(article_id=article.id, source_id=sid) for sid in source_ids]
            session.add_all(source_links)
            await session.flush()
            return article

    async def bulk_link_sources(self, article_id: int, source_ids: List[int]):
        async with self.transaction() as session:
            links = [{"article_id": article_id, "source_id": sid} for sid in source_ids]
            await session.execute(ArticleSource.__table__.insert(), links)

    async def get_prompt_with_providers(self, prompt_id: int) -> Prompt:
        async with self.get_session() as session:
            result = await session.execute(
                select(Prompt)
                .options(joinedload(Prompt.providers).joinedload(PromptProvider.provider))
                .where(Prompt.id == prompt_id)
            )
            return result.scalars().first()

    async def save_job(self, job_data: Dict) -> Job:
        async with self.transaction() as session:
            job = Job(**job_data)
            session.add(job)
            await session.flush()
            return job

# Usage
db_manager = DatabaseManager()