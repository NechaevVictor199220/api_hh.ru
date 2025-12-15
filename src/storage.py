# src/storage.py - исправленная версия

import csv
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from vacancy import Vacancy


class DataStorage(ABC):
    """Абстрактный класс для работы с хранилищами данных"""

    @abstractmethod
    def add_vacancy(self, vacancy: Vacancy) -> None:
        """Добавление вакансии в хранилище"""
        pass

    @abstractmethod
    def get_vacancies(self, criteria: Optional[Dict[str, Any]] = None) -> List[Vacancy]:
        """Получение вакансий по критериям"""
        pass

    @abstractmethod
    def delete_vacancy(self, vacancy: Vacancy) -> None:
        """Удаление вакансии из хранилища"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Очистка хранилища"""
        pass


class JSONSaver(DataStorage):
    """Класс для сохранения вакансий в JSON-файл"""

    def __init__(self, filename: str = "vacancies.json"):
        """
        Инициализация JSON-хранилища

        Args:
            filename: Имя файла для сохранения
        """
        # Создаем папку data если её нет
        self._data_dir = "data"
        os.makedirs(self._data_dir, exist_ok=True)

        # Сохраняем файл в папку data
        self._filename = os.path.join(self._data_dir, filename)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Создание файла, если он не существует"""
        if not os.path.exists(self._filename):
            with open(self._filename, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _read_vacancies(self) -> List[Dict[str, Any]]:
        """Чтение вакансий из файла"""
        try:
            with open(self._filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_vacancies(self, vacancies: List[Dict[str, Any]]) -> None:
        """Запись вакансий в файл"""
        with open(self._filename, "w", encoding="utf-8") as f:
            json.dump(vacancies, f, ensure_ascii=False, indent=2)

    def _vacancy_exists(
        self, vacancy: Vacancy, vacancies_list: List[Dict[str, Any]]
    ) -> bool:
        """Проверка существования вакансии"""
        vacancy_dict = vacancy.to_dict()
        for existing_vacancy in vacancies_list:
            if (
                existing_vacancy.get("title") == vacancy_dict["title"]
                and existing_vacancy.get("url") == vacancy_dict["url"]
            ):
                return True
        return False

    def add_vacancy(self, vacancy: Vacancy) -> None:
        """Добавление вакансии в JSON-файл"""
        vacancies_list = self._read_vacancies()
        vacancy_dict = vacancy.to_dict()

        # Проверка на дубликаты
        if not self._vacancy_exists(vacancy, vacancies_list):
            vacancies_list.append(vacancy_dict)
            self._write_vacancies(vacancies_list)

    def add_vacancies(self, vacancies: List[Vacancy]) -> None:
        """Добавление списка вакансий"""
        for vacancy in vacancies:
            self.add_vacancy(vacancy)

    def get_vacancies(self, criteria: Optional[Dict[str, Any]] = None) -> List[Vacancy]:
        """
        Получение вакансий по критериям

        Args:
            criteria: Словарь с критериями фильтрации

        Returns:
            Список объектов Vacancy
        """
        vacancies_list = self._read_vacancies()
        vacancies = [Vacancy.from_dict(v) for v in vacancies_list]

        if not criteria:
            return vacancies

        # Фильтрация вакансий
        filtered_vacancies = []
        for vacancy in vacancies:
            match = True

            # Проверка ключевых слов в описании
            if "keywords" in criteria:
                keywords = criteria["keywords"]
                if keywords:
                    text_to_search = f"{vacancy.title} {vacancy.description} {vacancy.requirements}".lower()
                    for keyword in keywords:
                        if keyword and keyword.lower() not in text_to_search:
                            match = False
                            break

            # Проверка минимальной зарплаты
            if "salary_min" in criteria and criteria["salary_min"] > 0:
                if vacancy.salary_to > 0 and vacancy.salary_to < criteria["salary_min"]:
                    match = False
                elif (
                    vacancy.salary_from > 0
                    and vacancy.salary_from < criteria["salary_min"]
                ):
                    match = False

            # Проверка по работодателю
            if "employer" in criteria and criteria["employer"]:
                if criteria["employer"].lower() not in vacancy.employer.lower():
                    match = False

            # Проверка по региону
            if "area" in criteria and criteria["area"]:
                if criteria["area"].lower() not in vacancy.area.lower():
                    match = False

            if match:
                filtered_vacancies.append(vacancy)

        return filtered_vacancies

    def delete_vacancy(self, vacancy: Vacancy) -> None:
        """Удаление вакансии из JSON-файла"""
        vacancies_list = self._read_vacancies()
        vacancy_dict = vacancy.to_dict()

        # Удаление по заголовку и ссылке
        vacancies_list = [
            v
            for v in vacancies_list
            if not (
                v.get("title") == vacancy_dict["title"]
                and v.get("url") == vacancy_dict["url"]
            )
        ]

        self._write_vacancies(vacancies_list)

    def clear(self) -> None:
        """Очистка файла"""
        self._write_vacancies([])

    def get_file_path(self) -> str:
        """Получение пути к файлу"""
        return self._filename


class CSVSaver(DataStorage):
    """Класс для сохранения вакансий в CSV-файл (дополнительный формат)"""

    def __init__(self, filename: str = "vacancies.csv"):
        """
        Инициализация CSV-хранилища

        Args:
            filename: Имя файла для сохранения
        """
        # Создаем папку data если её нет
        self._data_dir = "data"
        os.makedirs(self._data_dir, exist_ok=True)

        # Сохраняем файл в папку data
        self._filename = os.path.join(self._data_dir, filename)

    def add_vacancy(self, vacancy: Vacancy) -> None:
        """Добавление вакансии в CSV-файл"""
        file_exists = os.path.exists(self._filename)

        with open(self._filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if not file_exists:
                # Записываем заголовки
                writer.writerow(
                    [
                        "title",
                        "url",
                        "salary_from",
                        "salary_to",
                        "currency",
                        "employer",
                        "experience",
                        "area",
                        "description",
                        "requirements",
                    ]
                )

            writer.writerow(
                [
                    vacancy.title,
                    vacancy.url,
                    vacancy.salary_from,
                    vacancy.salary_to,
                    vacancy.currency,
                    vacancy.employer,
                    vacancy.experience,
                    vacancy.area,
                    vacancy.description[:100] if vacancy.description else "",
                    vacancy.requirements[:100] if vacancy.requirements else "",
                ]
            )

    def get_vacancies(self, criteria: Optional[Dict[str, Any]] = None) -> List[Vacancy]:
        """Получение вакансий из CSV-файла"""
        vacancies = []

        if not os.path.exists(self._filename):
            return vacancies

        try:
            with open(self._filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Проверяем, есть ли заголовки
                if reader.fieldnames is None:
                    return vacancies

                for row in reader:
                    # Проверяем наличие необходимых полей
                    if "title" not in row or "url" not in row:
                        continue

                    # Обрабатываем зарплату с проверкой полей
                    salary_from = 0
                    salary_to = 0
                    currency = "Не указана"

                    if "salary_from" in row and row["salary_from"]:
                        try:
                            salary_from = int(row["salary_from"])
                        except ValueError:
                            salary_from = 0

                    if "salary_to" in row and row["salary_to"]:
                        try:
                            salary_to = int(row["salary_to"])
                        except ValueError:
                            salary_to = 0

                    if "currency" in row and row["currency"]:
                        currency = row["currency"]

                    salary_info = {
                        "from": salary_from,
                        "to": salary_to,
                        "currency": currency,
                    }

                    vacancy = Vacancy(
                        title=row.get("title", ""),
                        url=row.get("url", ""),
                        salary=salary_info,
                        description=row.get("description", ""),
                        requirements=row.get("requirements", ""),
                        employer=row.get("employer", ""),
                        experience=row.get("experience", ""),
                        area=row.get("area", ""),
                    )

                    vacancies.append(vacancy)
        except Exception as e:
            print(f"Ошибка при чтении CSV файла: {e}")
            return []

        # Применение фильтров
        if criteria:
            vacancies = self._filter_vacancies(vacancies, criteria)

        return vacancies

    def _filter_vacancies(
        self, vacancies: List[Vacancy], criteria: Dict[str, Any]
    ) -> List[Vacancy]:
        """Фильтрация вакансий"""
        filtered = []

        for vacancy in vacancies:
            match = True

            if "keywords" in criteria and criteria["keywords"]:
                text = f"{vacancy.title} {vacancy.description} {vacancy.requirements}".lower()
                for keyword in criteria["keywords"]:
                    if keyword and keyword.lower() not in text:
                        match = False
                        break

            if "salary_min" in criteria and criteria["salary_min"] > 0:
                if vacancy.salary_to > 0 and vacancy.salary_to < criteria["salary_min"]:
                    match = False
                elif (
                    vacancy.salary_from > 0
                    and vacancy.salary_from < criteria["salary_min"]
                ):
                    match = False

            if match:
                filtered.append(vacancy)

        return filtered

    def delete_vacancy(self, vacancy: Vacancy) -> None:
        """Удаление вакансии из CSV-файла"""
        vacancies = self.get_vacancies()

        # Фильтруем вакансии, исключая удаляемую
        filtered_vacancies = [
            v
            for v in vacancies
            if not (v.title == vacancy.title and v.url == vacancy.url)
        ]

        # Перезаписываем файл
        self.clear()
        for v in filtered_vacancies:
            self.add_vacancy(v)

    def clear(self) -> None:
        """Очистка файла"""
        if os.path.exists(self._filename):
            os.remove(self._filename)

    def get_file_path(self) -> str:
        """Получение пути к файлу"""
        return self._filename


class TXTSaver(DataStorage):
    """Класс для сохранения вакансий в TXT-файл"""

    def __init__(self, filename: str = "vacancies.txt"):
        """
        Инициализация TXT-хранилища

        Args:
            filename: Имя файла для сохранения
        """
        # Создаем папку data если её нет
        self._data_dir = "data"
        os.makedirs(self._data_dir, exist_ok=True)

        # Сохраняем файл в папку data
        self._filename = os.path.join(self._data_dir, filename)

    def add_vacancy(self, vacancy: Vacancy) -> None:
        """Добавление вакансии в TXT-файл"""
        with open(self._filename, "a", encoding="utf-8") as f:
            f.write(str(vacancy))
            f.write("\n" + "=" * 60 + "\n\n")

    def get_vacancies(self, criteria: Optional[Dict[str, Any]] = None) -> List[Vacancy]:
        """Получение вакансий из TXT-файла (упрощенное)"""
        # Для TXT файла это сложно реализовать полноценно,
        # поэтому возвращаем пустой список или делаем заглушку
        print("Внимание: Получение вакансий из TXT файла не поддерживается полноценно.")
        return []

    def delete_vacancy(self, vacancy: Vacancy) -> None:
        """Удаление вакансии из TXT-файла (заглушка)"""
        print("Внимание: Удаление конкретной вакансии из TXT файла не поддерживается.")

    def clear(self) -> None:
        """Очистка файла"""
        if os.path.exists(self._filename):
            os.remove(self._filename)

    def get_file_path(self) -> str:
        """Получение пути к файлу"""
        return self._filename
