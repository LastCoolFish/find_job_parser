from typing import ClassVar, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import request
from db.models.BaseModels import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class BaseRepository(Generic[TModel]):
    model: ClassVar[type[BaseModel]]

    @classmethod
    @request
    async def get_existing_ids(cls, platform: str, session: AsyncSession) -> list[int]:
        """
        Gets platform_id of every row already stored for the given platform.

        :param platform: platform to scope the lookup to (platform_id is only unique per platform)
        :param session: sqlalchemy.ext.asyncio.AsyncSession
        :return: list of platform_id of existing rows on that platform
        """
        query = select(cls.model.platform_id).where(cls.model.platform == platform)

        result = (await session.execute(query)).scalars().all()
        return list(result)
