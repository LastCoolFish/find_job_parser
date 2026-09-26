from __future__ import annotations

from sqlalchemy import String, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Text, SmallInteger, Integer

from db.models.BaseModels import BaseModel


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
        String(255),
        nullable=False,
    )

    salary: Mapped[int | None] = mapped_column(
        Integer
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    place: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    grade: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=True,
    )

    format: Mapped[str | None] = mapped_column(
        String(75),
        nullable=True,
    )

    platform: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
    )

    platform_id: Mapped[int] = mapped_column(
        nullable=False,
    )

    site_href: Mapped[str] = mapped_column(
        String(255),
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

