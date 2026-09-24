from abc import ABC, abstractmethod
from logging import Logger
from typing import Generic, TypeVar

from collectors.Collector import Collector

TDto = TypeVar("TDto")


class BaseService(ABC, Generic[TDto]):
    def __init__(self, collector: Collector[TDto], logger: Logger):
        self.collector = collector
        self.logger = logger

    async def run(self) -> None:
        name = type(self).__name__
        self.logger.info(f"Starting {name}")
        entities = await self.collector.collect()
        self.logger.info(f"Scraped {len(entities)} entities")

        if not entities:
            return

        await self._persist(entities)

    @abstractmethod
    async def _persist(self, entities: list[TDto]) -> None:
        ...
