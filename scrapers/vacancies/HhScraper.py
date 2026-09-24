import re
from typing import override

from playwright.async_api import Page

from scrapers.base_scraper import PlaywrightVacancyScraper, NoAvailableDataError
from scrapers.dto.CompanyDTO import CompanyDTO
from scrapers.dto.VacancyDTO import VacancyDTO
from logging_config import get_logger

logger = get_logger(__name__)


class HhScraper(PlaywrightVacancyScraper):
    vacancy_list_url = "https://hh.ru/search/vacancy?text=developer&area=1"  # text is keyword
    vacancy_url = "https://hh.ru/vacancy/{vacancy_id}"

    @classmethod
    @override
    async def get_vacancies_id(cls) -> list[int]:
        """
        scram: playwright

        Hh loads information onto the order page using JavaScript

        :return: list of id
        """

        logger.info("Start to get orders id")
        page: Page = cls._require_page()
        await page.goto(cls.vacancy_list_url)

        # In HTML, we search for all matches by vacancyId using re
        ids = list(map(int, re.findall(r'"vacancyId":(\d+)', await page.content())))

        logger.debug(f"Ids: {ids}, count: {len(ids)}")
        logger.info(f"Successfully")
        return ids

    @classmethod
    @override
    async def get_vacancy(cls, vacancy_id: int) -> VacancyDTO:
        '''
        scram: playwright

        Hh loads information onto the order page using JavaScript

        :param vacancy_id: vacancy id on site
        :return: dict with info about vacancy
        '''
        logger.info("Start to get order")
        logger.debug(f"Vacancy id: {vacancy_id}, href: {cls.vacancy_url.format(vacancy_id=vacancy_id)}")
        grades = {"не требуется": 0, "1–3 года": 1, "3–6 лет": 2, "более 6 лет": 3}

        page: Page = cls._require_page()
        await page.goto(cls.vacancy_url.format(vacancy_id=vacancy_id))

        title = page.locator('h1[data-qa="vacancy-title"] span span')

        # Sometimes  come across non-standard job page layouts; these are often unrelated to IT, skip them.
        if await title.count() == 0:
            logger.warning("An unusual way of presenting job vacancies")
            raise NoAvailableDataError("An unusual way of presenting job vacancies")

        salary_gross = page.locator('span[data-qa="vacancy-salary-compensation-type-gross"] data')
        salary_net = page.locator('span[data-qa="vacancy-salary-compensation-type-net"] data')

        if await salary_gross.count() > 0:
            gross_value = await salary_gross.first.get_attribute("value")
            # Deduction of 13% from pre-tax salary
            salary = round(int(gross_value) * 0.87) if gross_value is not None else None

        elif await salary_net.count() > 0:
            net_value = await salary_net.first.get_attribute("value")
            salary = int(net_value) if net_value is not None else None

        else:
            salary = None

        logger.debug(f"Salary: {salary}")

        place = page.locator('div[data-qa="vacancy-address-with-map"]')
        skills = await page.locator('li[data-qa="skills-element"]').all()

        rating = page.locator('div[data-qa="employer-review-small-widget-total-rating"]')
        accreditation = await page.locator('div[data-qa="vacancy-company"]').inner_text()

        work_format = page.locator('p[data-qa="work-formats-text"]')

        vacancy = VacancyDTO(
            job_title=await title.inner_text(),
            salary=salary,
            description=await page.locator('div[data-qa="vacancy-description"]').inner_text(),
            place=await place.inner_text() if await place.count() > 0 else None,
            grade=grades[await page.locator('span[data-qa="vacancy-experience"]').inner_text()],
            format=(await work_format.inner_text()).replace("Формат работы: ", "") if await work_format.count() == 1 else None,
            platform="hh",
            vacancy_id=vacancy_id,
            skills=[await widget.inner_text() for widget in skills],
            company=CompanyDTO(
                name=await page.locator('div[data-qa="vacancy-company__details"]').inner_text(),
                rating=round(float((await rating.inner_text()).replace(",", ".")) * 100) if await rating.count() == 1 else None,
                accreditation="У работодателя есть аккредитация" in accreditation
            )

        )
        logger.debug(f"vacancy: {vacancy}")

        logger.info(f"Successfully")
        return vacancy
