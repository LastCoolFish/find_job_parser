from typing import TypeVar, Generic

from logging_config import get_logger
from scrapers.base_scraper import Scraper

TDto = TypeVar("TDto")

logger = get_logger(__name__)


class Collector(Generic[TDto]):
    def __init__(self, sources: list[type[Scraper]]):
        self.sources: list[type[Scraper]] = sources

    async def collect(self, existing_ids_by_platform: dict[str, set[int]]) -> list[TDto]:
        items: list[TDto] = []
        for source in self.sources:
            try:
                known_ids = existing_ids_by_platform.get(source.platform, set())
                items.extend(await source.collect(known_ids))
            except Exception:
                logger.exception(f"Source {source.__name__} failed, skipping it")
        return items