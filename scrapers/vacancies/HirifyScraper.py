import asyncio
import logging
import re
from typing import ClassVar, override

import httpx
from bs4 import BeautifulSoup

from scrapers.base_scraper import RequestsVacancyScraper, NoAvailableDataError
from scrapers.dto.CompanyDTO import CompanyDTO
from scrapers.dto.VacancyDTO import VacancyDTO
from logging_config import get_logger

logger = get_logger(__name__)


class HirifyScraper(RequestsVacancyScraper):
    platform: ClassVar[str] = "hirify"
    sitemap_index_url = "https://hirify.me/sitemap.xml"
    vacancy_url = "https://hirify.me/jobs/{vacancy_id}"

    # The sitemap holds the whole history (~256k vacancies), so only the newest ones are taken
    max_vacancies = 300
    # Hirify blocks the IP for about an hour after a burst of requests
    request_delay = 3
    usd_to_rub = 85

    # How the grades are labeled on the website
    grades = {"trainee": 0, "junior": 1, "middle": 2, "senior": 3, "lead": 4}

    @classmethod
    @override
    async def get_vacancies_id(cls) -> list[int]:
        """
        sitemap

        Hirify lists vacancies in jobs-N.xml sitemaps, ids ascend, so the newest ones are at the end of the last file.

        :return: list of id
        """

        logger.info("Start to get vacancies id")
        async with httpx.AsyncClient(headers=cls.headers, timeout=60) as client:
            index = await client.get(cls.sitemap_index_url)
            logger.log(logging.INFO if index.status_code == 200 else logging.ERROR,
                       f"Status code: {index.status_code}")
            if index.status_code != 200:
                return []

            files = re.findall(r"<loc>(https://hirify\.me/sitemaps/jobs-(\d+)\.xml)</loc>", index.text)
            last_file = max(files, key=lambda file: int(file[1]))[0]

            sitemap = await client.get(last_file)
            logger.log(logging.INFO if sitemap.status_code == 200 else logging.ERROR,
                       f"Status code: {sitemap.status_code}")
            if sitemap.status_code != 200:
                return []

        ids = list(map(int, re.findall(r"/jobs/(\d+)-", sitemap.text)))[-cls.max_vacancies:]

        logger.debug(f"Ids: {ids}, count: {len(ids)}")
        logger.info("Successfully")
        return ids

    @classmethod
    def _parse_salary(cls, text: str) -> int | None:
        match = re.search(r"\d[\d\s]*", text)
        if match is None:
            return None

        # The first figure of the range is recorded
        salary = int(re.sub(r"\s", "", match.group(0)))
        if "₽" in text:
            return salary
        if "$" in text:
            # Dollar salaries are yearly, while the other platforms quote monthly RUB
            return round(salary * cls.usd_to_rub / 12)
        return None

    @classmethod
    @override
    async def get_vacancy(cls, vacancy_id: int) -> VacancyDTO:
        """
        scram: requests, BS4

        The vacancy page is server-rendered, so BS4 is all you need here.

        :param vacancy_id: vacancy id on site
        :return: VacancyDTO
        """
        logger.info("Start to get vacancy info")
        href = cls.vacancy_url.format(vacancy_id=vacancy_id)
        logger.debug(f"Vacancy id: {vacancy_id}, href: {href}")

        await asyncio.sleep(cls.request_delay)
        async with httpx.AsyncClient() as client:
            response = await client.get(href, headers=cls.headers)

        if response.status_code != 200:
            logger.warning(f"Response status code {response.status_code}")
            raise NoAvailableDataError(f"Response status code {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        header = soup.select_one("div.vacancy-detail")
        description = header.select_one("div.description") if header else None
        if description is None:
            logger.warning("An unusual way of presenting job vacancies")
            raise NoAvailableDataError("An unusual way of presenting job vacancies")

        details = {
            item.select_one("div.label").get_text(strip=True): item.select_one("div.value").get_text(" ", strip=True)
            for item in header.select("div.common-detail-item")
        }

        salary = header.select_one("div.vacancy-header-content .font-bold")
        salary = cls._parse_salary(salary.get_text(" ", strip=True)) if salary else None
        logger.debug(f"Salary {salary}")

        vacancy = VacancyDTO(
            job_title=header.select_one("h1").get_text(strip=True),
            salary=salary,
            description=description.get_text("\n", strip=True),
            place=details.get("Страна"),
            grade=cls.grades.get(details.get("Грейд", "").lower()),
            # Free text, and one value over the column length would fail the whole batch insert
            format=details["Формат работы"][:75] if "Формат работы" in details else None,
            platform=cls.platform,
            vacancy_id=vacancy_id,
            href=href,
            skills=[tag.get_text(strip=True) for tag in header.select("div.vacancy-detail-tags .tag")],
            company=CompanyDTO(
                # Hidden companies are literally named "Company hidden", so they share one company row
                name=header.select_one("div.company-name").get_text(strip=True),
                rating=None,
                accreditation=False
            )
        )

        logger.info("Successfully")
        logger.debug(f"vacancy: {vacancy}")
        return vacancy
