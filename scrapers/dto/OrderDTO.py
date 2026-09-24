from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from scrapers.dto.CustomerDTO import CustomerDTO


@dataclass
class OrderDTO:
    name: str
    description: str

    order_id: int
    platform: str

    publication_timestamp: datetime

    customer: CustomerDTO

    price: int | None
