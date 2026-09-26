from functools import wraps

from decouple import config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models.BaseModels import BaseModel
from logging_config import get_logger

logger = get_logger(__name__)

DATABASE_URL = f"postgresql+asyncpg://{config('DB_USER')}:{config('DB_PASSWORD')}@{config('HOST')}:{config('PORT')}/{config('DB_NAME')}"

engine = create_async_engine(DATABASE_URL, echo=True)

SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with SessionFactory() as session:
            try:
                result = await func(*args, session=session, **kwargs)

                await session.commit()
                return result

            except Exception as e:
                logger.error(f"Rolling back: {e}")
                await session.rollback()
                raise

    return wrapper
