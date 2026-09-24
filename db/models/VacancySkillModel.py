from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.models.BaseModel import BaseModel


class VacancySkill(BaseModel):
    __tablename__ = "vacancies_skills"

    # Pure association table - exclude the surrogate id inherited from BaseModel
    # so (vacancy_id, skill_id) alone is the primary key, matching ON CONFLICT.
    id = None

    vacancy_id: Mapped[int] = mapped_column(
        ForeignKey("vacancies.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT", onupdate="CASCADE"),
        primary_key=True,
    )