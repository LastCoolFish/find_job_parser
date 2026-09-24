from dataclasses import dataclass

from scrapers.dto.CompanyDTO import CompanyDTO


@dataclass
class VacancyDTO:
    job_title: str
    salary: int | None
    description: str
    place: str | None
    grade: int | None
    format: str | None
    platform: str
    vacancy_id: int
    skills: list[str]
    company: CompanyDTO
