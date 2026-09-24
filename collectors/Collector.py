from typing import TypeVar, Generic

from scrapers.base_scraper import Scraper

TDto = TypeVar("TDto")

class Collector(Generic[TDto]):
    def __init__(self, sources: list[type[Scraper]]):
        self.sources: list[type[Scraper]] = sources

    async def collect(self) -> list[TDto]:
        items: list[TDto] = []
        for source in self.sources:
            items.extend(await source.collect())
        return items