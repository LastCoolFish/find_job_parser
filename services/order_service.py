from repositories.orders_repository import OrdersRepository
from logging_config import get_logger

logger = get_logger(__name__)


class OrderService:
    """Orchestrates scraping and persisting orders end to end."""

    @classmethod
    async def run(cls) -> None:
        logger.info("Starting orders pipeline")

        entities = await OrdersRepository.get_orders()
        logger.info(f"Scraped {len(entities)} orders")

        if not entities:
            return

        customer_ids = await OrdersRepository.get_or_create_customers(entities)
        await OrdersRepository.save_orders(entities, customer_ids)

        logger.info("Orders pipeline finished")
