from abc import ABC, abstractmethod
from typing import Any, Dict, List

import requests


class VacancyAPI(ABC):
    """Абстрактный класс для работы с API сервисов вакансий"""

    @abstractmethod
    def get_vacancies(self, search_query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Получение вакансий по поисковому запросу

        Args:
            search_query: Поисковый запрос
            **kwargs: Дополнительные параметры

        Returns:
            Список словарей с данными вакансий
        """
        pass


class HeadHunterAPI(VacancyAPI):
    """Класс для работы с API HeadHunter """

    def __init__(self):
        self._base_url = "https://api.hh.ru/vacancies"
        self._per_page = 100  # Количество вакансий на странице

    def _connect_to_api(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Подключение к API hh.ru

        Args:
            params: Параметры запроса

        Returns:
            Ответ от API в формате JSON или пустой словарь при ошибке
        """
        try:
            response = requests.get(self._base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:  # Ловим все исключения
            print(f"Ошибка при подключении к API: {e}")
            return {"items": []}  # Возвращаем пустой список вакансий

    def get_vacancies(
        self,
        search_query: str,
        area: str = "113",
        only_with_salary: bool = False,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Получение вакансий с hh.ru

        Args:
            search_query: Поисковый запрос
            area: ID региона (113 - Россия)
            only_with_salary: Только вакансии с указанной зарплатой
            **kwargs: Дополнительные параметры

        Returns:
            Список словарей с данными вакансий
        """
        params = {
            "text": search_query,
            "area": area,
            "per_page": self._per_page,
            "page": 0,
            "only_with_salary": only_with_salary,
            **kwargs,
        }

        vacancies = []
        data = self._connect_to_api(params)

        # Получаем вакансии из ответа
        if "items" in data:
            vacancies = data["items"]

            # Получаем дополнительные страницы, если есть
            pages = data.get("pages", 1)
            for page in range(1, min(pages, 5)):  # Ограничим 5 страницами
                params["page"] = page
                page_data = self._connect_to_api(params)
                if "items" in page_data:
                    vacancies.extend(page_data["items"])

        return vacancies
