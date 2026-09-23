from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.session import AsyncSession

from datasources.entities.VacancyEntity import VacancyEntity
from datasources.vacancies.habr_parser import HabrParser
from datasources.vacancies.hh_parser import HhParser

from db.engine import request

from db.models.CompanyModel import CompanyModel
from db.models.SkillModel import SkillModel
from db.models.VacancyModel import VacancyModel
from db.models.VacancySkillModel import VacancySkill
from logging_config import get_logger

logger = get_logger(__name__)


class VacancyRepository:
    # List of websites from which data is being scraped
    sites_datasource = [HabrParser, HhParser]

    @classmethod
    async def get_vacancies(cls) -> list[VacancyEntity]:
        """
        Get all vacancies.

        :return: list of datasources.entities.VacancyEntity
        """
        vacancies = []
        for site in cls.sites_datasource:
            vacancies.extend(await site.get_vacancies())

        logger.info(f"Collected {len(vacancies)} vacancies from {len(cls.sites_datasource)} sources")
        return vacancies

    @staticmethod
    @request
    async def get_or_create_companies(entities: list[VacancyEntity], session: AsyncSession) -> dict[str, int]:
        """
        When populating the VacancyEntity with data from the database, it is necessary to retrieve the company IDs or create them if they do not exist.

        :param entities: list of datasources.entities.VacancyEntity
        :param session: sqlalchemy.ext.asyncio.AsyncSession
        :return: dict of {company.name: company.id in db}
        """

        logger.info(f"Resolving company ids for {len(entities)} vacancies")

        # A database query is being executed to retrieve companies by name.
        companies = {entity.company.name: {"rating": entity.company.rating, "accreditation": entity.company.accreditation}
                     for entity in entities}

        existing = await session.execute(
            select(CompanyModel).where(CompanyModel.name.in_(companies.keys()))
        )

        name_to_id = {company.name: company.id for company in existing.scalars().all()}

        missing = companies.keys() - name_to_id.keys()
        if missing:
            logger.debug(f"Creating {len(missing)} new companies: {missing}")
            new_companies = [CompanyModel(name=name, **companies[name]) for name in missing]
            # Adding all companies in a single transaction
            session.add_all(new_companies)
            await session.flush()
            name_to_id.update({company.name: company.id for company in new_companies})

        logger.info(f"Successfully resolved {len(name_to_id)} companies")
        return name_to_id

    @staticmethod
    @request
    async def get_or_create_skills(entities: list[VacancyEntity], session: AsyncSession) -> dict[str, int]:
        """
        Skills are shared between vacancies and stored separately; existing skill ids are looked up,
        missing ones are created.

        :param entities: list of datasources.entities.VacancyEntity
        :param session: sqlalchemy.ext.asyncio.AsyncSession
        :return: dict of {skill.name: skill.id in db}
        """

        skill_names = {skill for entity in entities for skill in entity.skills}
        logger.info(f"Resolving ids for {len(skill_names)} distinct skills")

        existing = await session.execute(
            select(SkillModel).where(SkillModel.name.in_(skill_names))
        )

        name_to_id = {skill.name: skill.id for skill in existing.scalars().all()}

        missing = skill_names - name_to_id.keys()
        if missing:
            logger.debug(f"Creating {len(missing)} new skills: {missing}")
            new_skills = [SkillModel(name=name) for name in missing]
            # Adding all skills in a single transaction
            session.add_all(new_skills)
            await session.flush()
            name_to_id.update({skill.name: skill.id for skill in new_skills})

        logger.info(f"Successfully resolved {len(name_to_id)} skills")
        return name_to_id

    @staticmethod
    @request
    async def save_vacancies(
            entities: list[VacancyEntity],
            company_ids: dict[str, int],
            session: AsyncSession,
    ) -> dict[tuple[str, int], int]:
        """
        Saves the passed VacancyEntity to the database; company identifier data is required.
        Existing vacancies are left untouched - since they don't change, there's nothing to
        update, and their skill links already exist from the run that first inserted them.

        Only newly inserted vacancies are returned; save_vacancy_skills only needs to link
        skills for those, not for ones that were already in the database.

        :param entities: list of datasources.entities.VacancyEntity
        :param company_ids: dict of company id, key is company.name
        :param session: sqlalchemy.ext.asyncio.AsyncSession
        :return: dict of ids of newly inserted vacancies, key is tuple of vacancy.platform and vacancy.vacancy_id
        """

        logger.info(f"Saving {len(entities)} vacancies")

        rows = [
            {
                "job_title": entity.job_title,
                "salary": entity.salary,
                "description": entity.description,
                "place": entity.place,
                "grade": entity.grade,
                "format": entity.format,
                "platform": entity.platform,
                "platform_id": entity.vacancy_id,
                "company_id": company_ids[entity.company.name],
            }
            for entity in entities
        ]

        # Inserting all vacancies in a single transaction; existing ones are skipped untouched
        stmt = insert(VacancyModel).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["platform", "platform_id"]
        ).returning(VacancyModel.id, VacancyModel.platform, VacancyModel.platform_id)

        result = await session.execute(stmt)
        inserted = {(platform, platform_id): vacancy_id for vacancy_id, platform, platform_id in result.all()}

        logger.info(f"Successfully inserted {len(inserted)} new vacancies out of {len(entities)}")
        return inserted

    @staticmethod
    @request
    async def save_vacancy_skills(
            entities: list[VacancyEntity],
            vacancy_ids: dict[tuple[str, int], int],
            skill_ids: dict[str, int],
            session: AsyncSession,
    ) -> None:
        """
        Links vacancies with their skills through the vacancies_skills table.

        :param entities: list of datasources.entities.VacancyEntity
        :param vacancy_ids: dict of vacancy id, key is tuple of vacancy.platform and vacancy.vacancy_id
        :param skill_ids: dict of skill id, key is skill name
        :param session: sqlalchemy.ext.asyncio.AsyncSession
        :return: None
        """

        rows = [
            {
                "vacancy_id": vacancy_ids[(entity.platform, entity.vacancy_id)],
                "skill_id": skill_ids[skill],
            }
            for entity in entities
            for skill in entity.skills
        ]

        if not rows:
            logger.info("No new vacancy-skill links to save")
            return

        logger.info(f"Saving {len(rows)} vacancy-skill links")

        # Inserting all vacancy-skill links in a single transaction
        stmt = insert(VacancySkill).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["vacancy_id", "skill_id"]
        )
        await session.execute(stmt)

        logger.info("Successfully")
