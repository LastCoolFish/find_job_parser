from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.BaseModels import BaseModel


class SkillModel(BaseModel):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    vacancies: Mapped[list[BaseModel]] = relationship("VacancyModel",
                                                      secondary="vacancies_skills",
                                                      back_populates="skills",
                                                      )
