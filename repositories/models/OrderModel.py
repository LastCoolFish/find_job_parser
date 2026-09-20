from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import MONEY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Text, DateTime

from datasources.entities.order_entity import OrderEntity
from db.models import CustomerModel
from repositories.models.BaseModel import BaseModel


class OrderModel(BaseModel):
    __tablename__ = "orders"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    price: Mapped[float] = mapped_column(
        MONEY,
        nullable=False,
    )

    publication_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    platform: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
    )

    platform_id: Mapped[int] = mapped_column(
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )

    customer: Mapped[BaseModel] = relationship("CustomerModel",
                                               back_populates="orders"
                                               )

    @staticmethod
    def fromEntity(entity: OrderEntity) -> OrderModel:
        customer_model = CustomerModel(
            name=entity.customer.name,
            href=entity.customer.href,
        )

        order_model = OrderModel(
            name=entity.name,
            description=entity.description,
            price=entity.price,
            publication_timestamp=entity.publication_timestamp,
            platform=entity.platform,
            platform_id=entity.order_id,
            customer=customer_model
        )

        raise order_model
