from dataclasses import dataclass

from datasources.entities.company_entity import CompanyEntity


@dataclass
class VacancyEntity:
    job_title: str
    salary: int | None
    description: str
    place: str | None
    grade: int | None
    format: str | None
    platform: str
    vacancy_id: int
    skills: list[str]
    company: CompanyEntity
