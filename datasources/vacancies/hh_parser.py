import logging
import re
from typing import override

from playwright.sync_api import Page

from datasources.base_parsers import PlaywrightVacancyParser, NoAvailableDataError
from datasources.entities.company_entity import CompanyEntity
from datasources.entities.vacancy_entity import VacancyEntity

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(f"logs/{__name__}.log", mode='w', encoding="utf-8")
formatter = logging.Formatter("%(asctime)s | %(name)s %(funcName)s %(lineno)d | %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class HhParser(PlaywrightVacancyParser):
    vacancy_list_url = "https://hh.ru/search/vacancy?text=developer&area=1"  # text is keyword
    vacancy_url = "https://hh.ru/vacancy/{vacancy_id}"

    @classmethod
    @override
    def get_vacancies_id(cls, page: Page) -> list[int]:
        """
        scram: playwright

        Hh loads information onto the order page using JavaScript

        :param page: playwright.sync_api Page
        :return: list of id
        """

        logger.info("Start to get orders id")
        page.goto(cls.vacancy_list_url)

        # In HTML, we search for all matches by vacancyId using re
        ids = list(map(int, re.findall(r'"vacancyId":(\d+)', page.content())))

        logger.debug(f"Ids: {ids}, count: {len(ids)}")
        logger.info(f"Successfully")
        return ids

    @classmethod
    @override
    def get_vacancy(cls, page: Page, vacancy_id: int) -> VacancyEntity:
        '''
        scram: playwright

        Hh loads information onto the order page using JavaScript

        :param page: playwright.sync_api Page
        :param vacancy_id: vacancy id on site
        :return: dict with info about vacancy
        '''
        logger.info("Start to get order")
        logger.debug(f"Vacancy id: {vacancy_id}, href: {cls.vacancy_url.format(vacancy_id=vacancy_id)}")
        grades = {"не требуется": 0, "1–3 года": 1, "3–6 лет": 2, "более 6 лет": 3}

        page.goto(cls.vacancy_url.format(vacancy_id=vacancy_id))

        title = page.locator('h1[data-qa="vacancy-title"] span span')

        # Sometimes  come across non-standard job page layouts; these are often unrelated to IT, skip them.
        if title.count() == 0:
            logger.warning("An unusual way of presenting job vacancies")
            raise NoAvailableDataError("An unusual way of presenting job vacancies")

        salary_gross = page.locator('span[data-qa="vacancy-salary-compensation-type-gross"] data')
        salary_net = page.locator('span[data-qa="vacancy-salary-compensation-type-net"] data')

        if salary_gross.count() > 0:
            # Deduction of 13% from pre-tax salary
            salary = round(int(salary_gross.first.get_attribute("value")) * 0.87)

        elif salary_net.count() > 0:
            salary = int(salary_net.first.get_attribute("value"))

        else:
            salary = None

        logger.debug(f"Salary: {salary}")

        place = page.locator('div[data-qa="vacancy-address-with-map"]')
        skills = page.locator('li[data-qa="skills-element"]').all()

        rating = page.locator('div[data-qa="employer-review-small-widget-total-rating"]')
        accreditation = page.locator('div[data-qa="vacancy-company"]').inner_text()

        work_format = page.locator('p[data-qa="work-formats-text"]')

        vacancy = VacancyEntity(
            job_title=title.inner_text(),
            salary=salary,
            description=page.locator('div[data-qa="vacancy-description"]').inner_text(),
            place=place.inner_text() if place.count() > 0 else None,
            grade=grades[page.locator('span[data-qa="vacancy-experience"]').inner_text()],
            format=work_format.inner_text().replace("Формат работы: ", "") if work_format.count() == 1 else None,
            platform="hh",
            vacancy_id=vacancy_id,
            skills=list(map(lambda widget: widget.inner_text(), skills)),
            company=CompanyEntity(
                name=page.locator('div[data-qa="vacancy-company__details"]').inner_text(),
                rating=int(rating.inner_text().replace(",", "")) * 100 if rating.count() == 1 else None,
                accreditation="У работодателя есть аккредитация" in accreditation
            )

        )
        logger.debug(f"vacancy: {vacancy}")

        logger.info(f"Successfully")
        return vacancy
