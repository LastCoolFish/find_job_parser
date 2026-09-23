from __future__ import annotations

from sqlalchemy import String, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import MONEY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Text, SmallInteger

from db.models.BaseModel import BaseModel
from db.models.CompanyModel import CompanyModel


class VacancyModel(BaseModel):
    __tablename__ = "vacancies"

    __table_args__ = (
        CheckConstraint(
            "grade BETWEEN 0 AND 4",
            name="ck_vacancy_grade",
        ),
        UniqueConstraint("platform", "platform_id", name="uq_vacancy_platform_id"),
    )

    job_title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    salary: Mapped[float | None] = mapped_column(
        MONEY
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    place: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    grade: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
    )

    format: Mapped[str] = mapped_column(
        String(75),
        nullable=False,
    )

    platform: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
    )

    platform_id: Mapped[int] = mapped_column(
        nullable=False,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey(
            "companies.id",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )

    company: Mapped[BaseModel] = relationship("CompanyModel",
                                              back_populates="vacancies"
                                              )

    skills: Mapped[list[BaseModel]] = relationship("SkillModel",
                                                   secondary="vacancies_skills",
                                                   back_populates="vacancies",
                                                   )

