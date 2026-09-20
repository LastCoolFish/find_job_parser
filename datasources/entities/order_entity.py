from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from datasources.entities.customer_entity import CustomerEntity


@dataclass
class OrderEntity:
    name: str
    description: str

    order_id: int
    platform: str

    publication_timestamp: datetime

    customer: CustomerEntity

    price: int | None
