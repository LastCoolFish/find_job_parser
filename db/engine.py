from functools import wraps

from decouple import config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models import Base

DATABASE_URL = f"postgresql+asyncpg://{config('USER')}:{config('USER_PASSWORD')}@{config('HOST')}:{config('PORT')}/{config('DB_NAME')}"

engine = create_async_engine(DATABASE_URL, echo=True)

SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def request(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        async with SessionFactory() as session:
            try:
                self.session = session

                result = await func(self, *args, **kwargs, session)

                await session.commit()
                return result

            except Exception:
                await session.rollback()
                raise

    return wrapper


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda connection: Base.metadata.create_all(connection)
        )