from abc import ABC, abstractmethod
from logging import Logger
from typing import Generic, TypeVar

from collectors.Collector import Collector

TDto = TypeVar("TDto")


class BaseService(ABC, Generic[TDto]):
    def __init__(self, collector: Collector[TDto], logger: Logger):
        self.collector = collector
        self.logger = logger

    async def collect_existing_ids(self) -> dict[str, set[int]]:
        platforms = {source.platform for source in self.collector.sources}
        return {
            platform: set(await self.repository.get_existing_ids(platform))
            for platform in platforms
        }

    async def run(self) -> None:
        name = type(self).__name__
        self.logger.info(f"Starting {name}")
        existing_ids = await self.collect_existing_ids()
        entities = await self.collector.collect(existing_ids)
        self.logger.info(f"Scraped {len(entities)} entities")

        if not entities:
            return

        await self._persist(entities)

    @abstractmethod
    async def _persist(self, entities: list[TDto]) -> None:
        ...
