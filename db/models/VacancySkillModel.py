from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.models.BaseModels import SkillAssociationModel


class VacancySkillModel(SkillAssociationModel):
    __tablename__ = "vacancies_skills"

    vacancy_id: Mapped[int] = mapped_column(
        ForeignKey("vacancies.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
