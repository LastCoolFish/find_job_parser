from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repositories.models.BaseModel import BaseModel


class CustomerModel(BaseModel):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    href: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )

    orders: Mapped[list[BaseModel]] = relationship("OrderModel",
                                                   back_populates="customer"
                                                   )
