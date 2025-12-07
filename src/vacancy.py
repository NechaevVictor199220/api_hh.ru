import re
from typing import Any, Dict, List, Optional


class Vacancy:
    """Класс для представления вакансии"""

    __slots__ = (
        "_title",
        "_url",
        "_salary_from",
        "_salary_to",
        "_currency",
        "_description",
        "_requirements",
        "_experience",
        "_employer",
        "_area",
    )

    def __init__(
        self,
        title: str,
        url: str,
        salary: Optional[Dict[str, Any]] = None,
        description: str = "",
        requirements: str = "",
        experience: str = "",
        employer: str = "",
        area: str = "",
    ):
        """
        Инициализация объекта вакансии

        Args:
            title: Название вакансии
            url: Ссылка на вакансию
            salary: Информация о зарплате
            description: Описание вакансии
            requirements: Требования
            experience: Требуемый опыт
            employer: Работодатель
            area: Регион
        """
        self._title = self._validate_title(title)
        self._url = self._validate_url(url)

        # Валидация и парсинг зарплаты
        salary_info = self._validate_salary(salary)
        self._salary_from = salary_info["from"]
        self._salary_to = salary_info["to"]
        self._currency = salary_info["currency"]

        self._description = description
        self._requirements = requirements
        self._experience = experience
        self._employer = employer
        self._area = area

    def _validate_title(self, title: str) -> str:
        """Валидация названия вакансии"""
        if not title or not isinstance(title, str):
            return "Название не указано"
        return title.strip()

    def _validate_url(self, url: str) -> str:
        """Валидация URL"""
        if not url or not isinstance(url, str):
            return ""
        return url.strip()

    def _validate_salary(self, salary: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Валидация и обработка зарплаты"""
        if not salary:
            return {"from": 0, "to": 0, "currency": "Не указана"}

        salary_from = salary.get("from")
        salary_to = salary.get("to")
        currency = salary.get("currency", "Не указана")

        # Если зарплата не указана, но есть gross информация
        if salary_from is None and salary_to is None:
            return {"from": 0, "to": 0, "currency": currency}

        return {
            "from": salary_from if salary_from is not None else 0,
            "to": salary_to if salary_to is not None else 0,
            "currency": currency if currency else "Не указана",
        }

    @property
    def title(self) -> str:
        return self._title

    @property
    def url(self) -> str:
        return self._url

    @property
    def salary_from(self) -> int:
        return self._salary_from

    @property
    def salary_to(self) -> int:
        return self._salary_to

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def description(self) -> str:
        return self._description

    @property
    def requirements(self) -> str:
        return self._requirements

    @property
    def experience(self) -> str:
        return self._experience

    @property
    def employer(self) -> str:
        return self._employer

    @property
    def area(self) -> str:
        return self._area

    def get_average_salary(self) -> float:
        """Получение средней зарплаты"""
        if self._salary_from > 0 and self._salary_to > 0:
            return (self._salary_from + self._salary_to) / 2
        elif self._salary_from > 0:
            return float(self._salary_from)
        elif self._salary_to > 0:
            return float(self._salary_to)
        return 0.0

    def __str__(self) -> str:
        """Строковое представление вакансии"""
        salary_str = ""
        if self._salary_from > 0 or self._salary_to > 0:
            if self._salary_from > 0 and self._salary_to > 0:
                salary_str = (
                    f"{self._salary_from:,} - {self._salary_to:,} {self._currency}"
                )
            elif self._salary_from > 0:
                salary_str = f"от {self._salary_from:,} {self._currency}"
            elif self._salary_to > 0:
                salary_str = f"до {self._salary_to:,} {self._currency}"
        else:
            salary_str = "Зарплата не указана"

        return (
            f"{self._title}\n"
            f"Работодатель: {self._employer}\n"
            f"Зарплата: {salary_str}\n"
            f"Требуемый опыт: {self._experience}\n"
            f"Регион: {self._area}\n"
            f"Ссылка: {self._url}\n"
            f"{'-' * 50}"
        )

    # Методы сравнения по зарплате
    def __lt__(self, other: "Vacancy") -> bool:
        return self.get_average_salary() < other.get_average_salary()

    def __le__(self, other: "Vacancy") -> bool:
        return self.get_average_salary() <= other.get_average_salary()

    def __gt__(self, other: "Vacancy") -> bool:
        return self.get_average_salary() > other.get_average_salary()

    def __ge__(self, other: "Vacancy") -> bool:
        return self.get_average_salary() >= other.get_average_salary()

    def __eq__(self, other: "Vacancy") -> bool:
        if not isinstance(other, Vacancy):
            return False
        return (
            self._title == other._title
            and self._url == other._url
            and self.get_average_salary() == other.get_average_salary()
        )

    @classmethod
    def cast_to_object_list(
        cls, vacancies_data: List[Dict[str, Any]]
    ) -> List["Vacancy"]:
        """
        Преобразование списка словарей в список объектов Vacancy

        Args:
            vacancies_data: Список словарей с данными вакансий

        Returns:
            Список объектов Vacancy
        """
        vacancies = []

        for vacancy_data in vacancies_data:
            try:
                # Извлечение данных из структуры hh.ru
                salary_info = vacancy_data.get("salary")

                # Подготовка описания
                snippet = vacancy_data.get("snippet", {})
                description = f"{snippet.get('requirement', '')} {snippet.get('responsibility', '')}".strip()

                # Подготовка требований
                experience = vacancy_data.get("experience", {}).get("name", "Не указан")

                # Работодатель
                employer = vacancy_data.get("employer", {}).get("name", "Не указан")

                # Регион
                area = vacancy_data.get("area", {}).get("name", "Не указан")

                vacancy = cls(
                    title=vacancy_data.get("name", ""),
                    url=vacancy_data.get("alternate_url", ""),
                    salary=salary_info,
                    description=description,
                    requirements=vacancy_data.get("snippet", {}).get("requirement", ""),
                    experience=experience,
                    employer=employer,
                    area=area,
                )

                vacancies.append(vacancy)
            except Exception as e:
                print(f"Ошибка при создании вакансии: {e}")
                continue

        return vacancies

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование вакансии в словарь"""
        return {
            "title": self._title,
            "url": self._url,
            "salary_from": self._salary_from,
            "salary_to": self._salary_to,
            "currency": self._currency,
            "description": self._description,
            "requirements": self._requirements,
            "experience": self._experience,
            "employer": self._employer,
            "area": self._area,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Vacancy":
        """Создание вакансии из словаря"""
        salary_info = {
            "from": data.get("salary_from", 0),
            "to": data.get("salary_to", 0),
            "currency": data.get("currency", "Не указана"),
        }

        return cls(
            title=data.get("title", ""),
            url=data.get("url", ""),
            salary=salary_info,
            description=data.get("description", ""),
            requirements=data.get("requirements", ""),
            experience=data.get("experience", ""),
            employer=data.get("employer", ""),
            area=data.get("area", ""),
        )
