import re
from typing import override

import httpx
import xml.etree.ElementTree as etree

from bs4 import BeautifulSoup

from datasources.base_parsers import RequestsVacancyParser, NoAvailableDataError
from datasources.entities.CompanyEntity import CompanyEntity
from datasources.entities.VacancyEntity import VacancyEntity
from logging_config import get_logger

logger = get_logger(__name__)


class HabrParser(RequestsVacancyParser):
    vacancy_list_url = "https://career.habr.com/vacancies/rss?currency=RUR&sort=relevance&type=all"
    vacancy_url = "https://career.habr.com/vacancies/{vacancy_id}"

    @classmethod
    @override
    async def get_vacancies_id(cls):
        """
        rss

        Habr allows you to retrieve job listing data in XML format

        :return: list of id
        """

        logger.info("Start to get vacancies id")
        async with httpx.AsyncClient() as client:
            response = await client.get(cls.vacancy_list_url, headers=cls.headers)

        logger.log(logging.INFO if response.status_code == 200 else logging.ERROR,
                   f"Status code: {response.status_code}")
        if response.status_code == 200:
            # Search by XML tree
            data = etree.fromstring(response.content).findall("channel/item/guid")

            logger.debug(data)
            logger.info(f"Successfully")
            return list(map(lambda xml: xml.text, data))

        return []

    @classmethod
    @override
    async def get_vacancy(cls, vacancy_id: int) -> VacancyEntity:
        """
        scram: requests, BS4

        The job listing page is pretty simple — BS4 is all you need here.

        :param vacancy_id:
        :return:
        """
        logger.info("Start to get vacancy info")
        logger.debug(f"Vacancy id: {vacancy_id}")

        async with httpx.AsyncClient() as client:
            response = await client.get(cls.vacancy_url.format(vacancy_id=vacancy_id), headers=cls.headers)

        if response.status_code != 200:
            logger.warning(f"Response status code {response.status_code}")
            logger.debug(f"Vacancy id: {vacancy_id}, href: {cls.vacancy_url.format(vacancy_id=vacancy_id)}")
            raise NoAvailableDataError(f"Response status code {response.status_code}")
        logger.info(f"Response status code {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        # First check to see if the salary widget is present
        salary = soup.select_one("div.basic-salary")
        # Searching by number pattern if the widget is present
        salary_pattern = r"\d{1,3}(?:\s\d{3})+"
        salary = re.search(salary_pattern, salary.text) if salary else None
        # Once the pattern is found, the first salary figure is recorded.
        salary = int(salary.group(0).replace(" ", "")) if salary else None
        logger.debug(f"Salary {salary}")

        place = soup.select("svg.svg-icon--icon-placemark")

        # How the grades are labeled on the website
        grades = {"Intern": 0, "Junior": 1, "Middle": 2, "Senior": 3, "Lead": 4}
        grade = soup.select_one("svg.svg-icon--icon-grade")

        rating = soup.select_one("span.rating")


        vacancy = VacancyEntity(
            job_title=soup.select_one("h1.page-title__title").text,
            salary=salary,
            description=soup.select_one("div.style-ugc").text,
            place=place[0].parent.parent.text if place else None,
            grade=grades[grade.parent.parent.text] if grade else None,
            format="Можно удаленно" if soup.select_one("svg.svg-icon--icon-format") else "На месте работадателя",
            platform="habr",
            vacancy_id=vacancy_id,
            skills=list(map(lambda widget: widget.text, soup.select("div.chip-without-icon__text"))),
            company=CompanyEntity(
                name=soup.select_one("div.company_name").text,
                # Extracting only the digits from the rating, resulting in a three-digit number up to 500.
                rating=int("".join([char for char in rating.text if char.isdigit()])) if rating else None,
                accreditation=soup.select_one("svg.svg-icon--icon-accredited") is not None
            )
        )

        logger.info(f"Successfully")
        logger.debug(f"vacancy: {vacancy}")
        return vacancy
