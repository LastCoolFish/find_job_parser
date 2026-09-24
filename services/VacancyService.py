from collectors.Collector import Collector
from repositories.VacancyRepository import VacancyRepository
from logging_config import get_logger
from scrapers.dto.VacancyDTO import VacancyDTO
from services.BaseService import BaseService

logger = get_logger(__name__)


class VacancyService(BaseService[VacancyDTO]):
    def __init__(self, collector: Collector[VacancyDTO], repository: type[VacancyRepository]):
        super().__init__(collector, logger)
        self.repository = repository

    async def _persist(self, entities: list[VacancyDTO]) -> None:
        company_ids = await self.repository.get_or_create_companies(entities)
        skill_ids = await self.repository.get_or_create_skills(entities)

        vacancy_ids = await self.repository.save_vacancies(entities, company_ids)
        new_entities = [
            entity for entity in entities
            if (entity.platform, entity.vacancy_id) in vacancy_ids
        ]

        if new_entities:
            await self.repository.save_vacancy_skills(new_entities, vacancy_ids, skill_ids)

        self.logger.info(f"Vacancies pipeline finished, {len(new_entities)} new vacancies saved")
