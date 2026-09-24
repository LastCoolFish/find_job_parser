from __future__ import annotations

from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Boolean, SmallInteger

from db.models.BaseModel import BaseModel


class CompanyModel(BaseModel):
    __tablename__ = "companies"

    __table_args__ = (
        CheckConstraint(
            "rating BETWEEN 0 AND 500",
            name="ck_company_rating",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    rating: Mapped[int | None] = mapped_column(
        SmallInteger
    )

    accreditation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    vacancies: Mapped[list[BaseModel]] = relationship("VacancyModel",
                                                      back_populates="company"
                                                      )
