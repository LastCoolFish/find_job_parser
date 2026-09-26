from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Text, DateTime, Integer

from db.models import CustomerModel
from db.models.BaseModels import BaseModel


class OrderModel(BaseModel):
    __tablename__ = "orders"

    __table_args__ = (
        UniqueConstraint("platform", "platform_id", name="uq_order_platform_id"),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
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

    site_href: Mapped[str] = mapped_column(
        String(255),
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

