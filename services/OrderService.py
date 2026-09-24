from collectors.Collector import Collector
from repositories.OrdersRepository import OrdersRepository
from logging_config import get_logger
from scrapers.dto.OrderDTO import OrderDTO
from services.BaseService import BaseService

logger = get_logger(__name__)


class OrderService(BaseService[OrderDTO]):
    def __init__(self, collector: Collector[OrderDTO], repository: type[OrdersRepository]):
        super().__init__(collector, logger)
        self.repository = repository

    async def _persist(self, entities: list[OrderDTO]) -> None:
        customer_ids = await self.repository.get_or_create_customers(entities)
        await self.repository.save_orders(entities, customer_ids)
