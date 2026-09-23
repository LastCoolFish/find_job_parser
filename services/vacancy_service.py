from repositories.vacancy_repository import VacancyRepository
from logging_config import get_logger

logger = get_logger(__name__)


class VacancyService:
    """Orchestrates scraping and persisting vacancies end to end."""

    @classmethod
    async def run(cls) -> None:
        logger.info("Starting vacancies pipeline")

        entities = await VacancyRepository.get_vacancies()
        logger.info(f"Scraped {len(entities)} vacancies")

        if not entities:
            return

        company_ids = await VacancyRepository.get_or_create_companies(entities)
        skill_ids = await VacancyRepository.get_or_create_skills(entities)

        # save_vacancies only returns ids for newly inserted vacancies - existing ones
        # are skipped untouched and already have their skills linked from a previous run.
        vacancy_ids = await VacancyRepository.save_vacancies(entities, company_ids)
        new_entities = [entity for entity in entities if (entity.platform, entity.vacancy_id) in vacancy_ids]

        if new_entities:
            await VacancyRepository.save_vacancy_skills(new_entities, vacancy_ids, skill_ids)

        logger.info(f"Vacancies pipeline finished, {len(new_entities)} new vacancies saved")
