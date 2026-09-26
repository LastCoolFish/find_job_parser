from __future__ import annotations

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.BaseModels import BaseModel


class CustomerModel(BaseModel):
    __tablename__ = "customers"

    __table_args__ = (
        UniqueConstraint("name", "platform", name="uq_customer_name_platform"),
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    href: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )

    platform: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
    )

    orders: Mapped[list[BaseModel]] = relationship("OrderModel",
                                                   back_populates="customer"
                                                   )
