# tests/test_vacancy_app.py - исправленная версия

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from api import HeadHunterAPI
from storage import CSVSaver, JSONSaver
from utils import (filter_vacancies, get_top_vacancies,
                   get_vacancies_by_salary, print_vacancies, sort_vacancies)
from vacancy import Vacancy

# Импортируем из src


# Добавляем src в путь Python для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestVacancy(unittest.TestCase):
    """Тесты для класса Vacancy"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.vacancy_data = {
            "title": "Python Developer",
            "url": "https://hh.ru/vacancy/123456",
            "salary": {"from": 100000, "to": 150000, "currency": "RUR"},
            "description": "Разработка на Python",
            "requirements": "Опыт работы от 3 лет",
            "experience": "От 1 года до 3 лет",
            "employer": "Test Company",
            "area": "Москва",
        }

        self.vacancy_no_salary = {
            "title": "Developer",
            "url": "https://hh.ru/vacancy/789",
            "salary": None,
            "description": "Разработка",
            "requirements": "",
            "experience": "",
            "employer": "",
            "area": "",
        }

    def test_vacancy_creation_with_salary(self):
        """Тест создания вакансии с зарплатой"""
        vacancy = Vacancy(**self.vacancy_data)

        self.assertEqual(vacancy.title, "Python Developer")
        self.assertEqual(vacancy.url, "https://hh.ru/vacancy/123456")
        self.assertEqual(vacancy.salary_from, 100000)
        self.assertEqual(vacancy.salary_to, 150000)
        self.assertEqual(vacancy.currency, "RUR")
        self.assertEqual(vacancy.employer, "Test Company")

    def test_vacancy_creation_without_salary(self):
        """Тест создания вакансии без зарплаты"""
        vacancy = Vacancy(**self.vacancy_no_salary)

        self.assertEqual(vacancy.salary_from, 0)
        self.assertEqual(vacancy.salary_to, 0)
        self.assertEqual(vacancy.currency, "Не указана")

    def test_average_salary(self):
        """Тест расчета средней зарплаты"""
        vacancy = Vacancy(**self.vacancy_data)
        self.assertEqual(vacancy.get_average_salary(), 125000.0)

        vacancy2 = Vacancy(
            title="Test",
            url="https://test.com",
            salary={"from": 100000, "to": 0, "currency": "RUR"},
        )
        self.assertEqual(vacancy2.get_average_salary(), 100000.0)

    def test_comparison_operators(self):
        """Тест операторов сравнения"""
        vacancy1 = Vacancy(**self.vacancy_data)

        vacancy2_data = self.vacancy_data.copy()
        vacancy2_data["salary"] = {"from": 200000, "to": 250000, "currency": "RUR"}
        vacancy2 = Vacancy(**vacancy2_data)

        self.assertTrue(vacancy1 < vacancy2)
        self.assertTrue(vacancy2 > vacancy1)
        self.assertTrue(vacancy1 <= vacancy2)
        self.assertTrue(vacancy2 >= vacancy1)

    def test_to_dict_and_from_dict(self):
        """Тест преобразования в словарь и обратно"""
        vacancy = Vacancy(**self.vacancy_data)
        vacancy_dict = vacancy.to_dict()

        vacancy_from_dict = Vacancy.from_dict(vacancy_dict)

        self.assertEqual(vacancy.title, vacancy_from_dict.title)
        self.assertEqual(vacancy.url, vacancy_from_dict.url)
        self.assertEqual(vacancy.salary_from, vacancy_from_dict.salary_from)
        self.assertEqual(vacancy.salary_to, vacancy_from_dict.salary_to)

    def test_vacancy_str_representation(self):
        """Тест строкового представления вакансии"""
        vacancy = Vacancy(**self.vacancy_data)
        str_repr = str(vacancy)

        self.assertIn("Python Developer", str_repr)
        self.assertIn("Test Company", str_repr)
        self.assertIn("100,000 - 150,000 RUR", str_repr)
        self.assertIn("Москва", str_repr)

    def test_vacancy_with_only_from_salary(self):
        """Тест вакансии с зарплатой только 'от'"""
        vacancy = Vacancy(
            title="Test",
            url="https://test.com",
            salary={"from": 100000, "to": None, "currency": "RUR"},
        )

        self.assertEqual(vacancy.salary_from, 100000)
        self.assertEqual(vacancy.salary_to, 0)
        self.assertEqual(vacancy.get_average_salary(), 100000.0)

    def test_vacancy_with_only_to_salary(self):
        """Тест вакансии с зарплатой только 'до'"""
        vacancy = Vacancy(
            title="Test",
            url="https://test.com",
            salary={"from": None, "to": 150000, "currency": "RUR"},
        )

        self.assertEqual(vacancy.salary_from, 0)
        self.assertEqual(vacancy.salary_to, 150000)
        self.assertEqual(vacancy.get_average_salary(), 150000.0)

    def test_vacancy_no_salary_str(self):
        """Тест строкового представления вакансии без зарплаты"""
        vacancy = Vacancy(title="Test", url="https://test.com", salary=None)

        str_repr = str(vacancy)
        self.assertIn("Зарплата не указана", str_repr)


class TestHeadHunterAPI(unittest.TestCase):
    """Тесты для класса HeadHunterAPI"""

    def setUp(self):
        self.api = HeadHunterAPI()

    @patch("api.requests.get")
    def test_get_vacancies_success(self, mock_get):
        """Тест успешного получения вакансий"""
        # Мокируем ответ API
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "name": "Python Developer",
                    "alternate_url": "https://hh.ru/vacancy/123",
                    "salary": {"from": 100000, "to": 150000, "currency": "RUR"},
                    "snippet": {
                        "requirement": "Python опыт",
                        "responsibility": "Разработка",
                    },
                    "experience": {"name": "От 1 года до 3 лет"},
                    "employer": {"name": "Test Company"},
                    "area": {"name": "Москва"},
                }
            ],
            "pages": 1,
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        vacancies = self.api.get_vacancies("Python")

        self.assertIsInstance(vacancies, list)
        self.assertEqual(len(vacancies), 1)
        self.assertEqual(vacancies[0]["name"], "Python Developer")

    @patch("api.requests.get")
    def test_get_vacancies_error(self, mock_get):
        """Тест ошибки при получении вакансий"""
        # Создаем mock, который вызывает исключение при вызове
        mock_get.side_effect = Exception("Connection error")

        # API должно вернуть пустой список при ошибке
        vacancies = self.api.get_vacancies("Python")

        self.assertEqual(vacancies, [])


class TestJSONSaver(unittest.TestCase):
    """Тесты для класса JSONSaver"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        # Создаем временный файл
        self.test_file = os.path.join(self.temp_dir, "test_vacancies.json")

        # Создаем saver с нашим файлом
        self.saver = JSONSaver()
        # Переопределяем путь к файлу для теста
        self.saver._filename = self.test_file

        # Создаем файл если не существует
        if not os.path.exists(self.test_file):
            with open(self.test_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

        self.vacancy = Vacancy(
            title="Test Vacancy",
            url="https://test.com/vacancy/1",
            salary={"from": 100000, "to": 150000, "currency": "RUR"},
            description="Test description",
            employer="Test Company",
        )

    def tearDown(self):
        """Очистка после тестов"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_add_and_get_vacancies(self):
        """Тест добавления и получения вакансий"""
        # Проверяем, что файл создался
        self.assertTrue(os.path.exists(self.test_file))

        # Добавляем вакансию
        self.saver.add_vacancy(self.vacancy)

        # Проверяем, что файл содержит данные
        with open(self.test_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Test Vacancy")

        # Получаем вакансии
        vacancies = self.saver.get_vacancies()

        self.assertEqual(len(vacancies), 1)
        self.assertEqual(vacancies[0].title, "Test Vacancy")

    def test_file_creation_in_data_folder(self):
        """Тест создания файла в папке data"""
        # Создаем saver - должен создать папку data и файл
        saver = JSONSaver()

        # Проверяем стандартный путь
        expected_path = os.path.join("data", "vacancies.json")
        self.assertTrue(saver._filename.endswith(expected_path))

        # Проверяем, что папка data создана
        data_dir = os.path.dirname(saver._filename)
        self.assertTrue(os.path.exists(data_dir))

        # Проверяем, что файл создан
        self.assertTrue(os.path.exists(saver._filename))

    def test_duplicate_vacancy(self):
        """Тест добавления дубликата вакансии"""
        self.saver.add_vacancy(self.vacancy)
        self.saver.add_vacancy(self.vacancy)  # Дубликат

        vacancies = self.saver.get_vacancies()

        # Дубликат не должен добавляться
        self.assertEqual(len(vacancies), 1)

    def test_delete_vacancy(self):
        """Тест удаления вакансии"""
        self.saver.add_vacancy(self.vacancy)

        # Удаляем вакансию
        self.saver.delete_vacancy(self.vacancy)

        vacancies = self.saver.get_vacancies()
        self.assertEqual(len(vacancies), 0)

    def test_filter_vacancies(self):
        """Тест фильтрации вакансий"""
        # Добавляем тестовые вакансии
        vacancy1 = Vacancy(
            title="Python Developer",
            url="https://test.com/1",
            salary={"from": 100000, "to": 150000, "currency": "RUR"},
            description="Python разработка",
            employer="Company A",
        )

        vacancy2 = Vacancy(
            title="Java Developer",
            url="https://test.com/2",
            salary={"from": 120000, "to": 180000, "currency": "RUR"},
            description="Java разработка",
            employer="Company B",
        )

        self.saver.add_vacancy(vacancy1)
        self.saver.add_vacancy(vacancy2)

        # Фильтруем по ключевому слову
        filtered = self.saver.get_vacancies({"keywords": ["Python"]})

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Python Developer")

        # Фильтруем по минимальной зарплате
        filtered_by_salary = self.saver.get_vacancies({"salary_min": 110000})
        self.assertEqual(len(filtered_by_salary), 1)  # Только Java Developer

    def test_clear_method(self):
        """Тест метода очистки"""
        self.saver.add_vacancy(self.vacancy)
        self.assertEqual(len(self.saver.get_vacancies()), 1)

        self.saver.clear()
        self.assertEqual(len(self.saver.get_vacancies()), 0)

    def test_get_vacancies_no_criteria(self):
        """Тест получения всех вакансий без критериев"""
        self.saver.add_vacancy(self.vacancy)
        vacancies = self.saver.get_vacancies()  # Без параметров

        self.assertEqual(len(vacancies), 1)
        self.assertEqual(vacancies[0].title, "Test Vacancy")


class TestCSVSaver(unittest.TestCase):
    """Тесты для класса CSVSaver"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_vacancies.csv")

        # Создаем saver с нашим файлом
        self.saver = CSVSaver()
        # Переопределяем путь к файлу для теста
        self.saver._filename = self.test_file

        self.vacancy = Vacancy(
            title="Test Vacancy",
            url="https://test.com/vacancy/1",
            salary={"from": 100000, "to": 150000, "currency": "RUR"},
            description="Test description",
            employer="Test Company",
            experience="3 года",
            area="Москва",
        )

    def tearDown(self):
        """Очистка после тестов"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_add_and_get_vacancies(self):
        """Тест добавления и получения вакансий из CSV"""
        self.saver.add_vacancy(self.vacancy)

        vacancies = self.saver.get_vacancies()

        self.assertEqual(len(vacancies), 1)
        self.assertEqual(vacancies[0].title, "Test Vacancy")

    def test_delete_vacancy(self):
        """Тест удаления вакансии из CSV"""
        self.saver.add_vacancy(self.vacancy)
        self.assertEqual(len(self.saver.get_vacancies()), 1)

        self.saver.delete_vacancy(self.vacancy)
        self.assertEqual(len(self.saver.get_vacancies()), 0)


class TestUtils(unittest.TestCase):
    """Тесты вспомогательных функций"""

    def setUp(self):
        """Создание тестовых вакансий"""
        self.vacancies = [
            Vacancy(
                title="Junior Python",
                url="https://test.com/1",
                salary={"from": 50000, "to": 80000, "currency": "RUR"},
                description="Python разработка junior",
                employer="Company A",
            ),
            Vacancy(
                title="Senior Python",
                url="https://test.com/2",
                salary={"from": 150000, "to": 200000, "currency": "RUR"},
                description="Python разработка senior",
                employer="Company B",
            ),
            Vacancy(
                title="Middle Python",
                url="https://test.com/3",
                salary={"from": 100000, "to": 150000, "currency": "RUR"},
                description="Python разработка middle",
                employer="Company C",
            ),
            Vacancy(
                title="No Salary Python",
                url="https://test.com/4",
                salary=None,
                description="Python без зарплаты",
                employer="Company D",
            ),
        ]

    def test_sort_vacancies(self):
        """Тест сортировки вакансий"""
        sorted_vacancies = sort_vacancies(self.vacancies, reverse=True)

        # Проверяем порядок сортировки (по убыванию зарплаты)
        self.assertEqual(sorted_vacancies[0].title, "Senior Python")
        self.assertEqual(sorted_vacancies[1].title, "Middle Python")
        self.assertEqual(sorted_vacancies[2].title, "Junior Python")
        self.assertEqual(sorted_vacancies[3].title, "No Salary Python")

        # Тест сортировки по возрастанию
        sorted_asc = sort_vacancies(self.vacancies, reverse=False)
        self.assertEqual(sorted_asc[0].title, "No Salary Python")
        self.assertEqual(sorted_asc[1].title, "Junior Python")

    def test_get_top_vacancies(self):
        """Тест получения топ N вакансий"""
        top_2 = get_top_vacancies(self.vacancies, 2)

        self.assertEqual(len(top_2), 2)

        # Тест с N больше чем список
        top_10 = get_top_vacancies(self.vacancies, 10)
        self.assertEqual(len(top_10), 4)

        # Тест с N=0
        top_0 = get_top_vacancies(self.vacancies, 0)
        self.assertEqual(len(top_0), 0)

    def test_filter_vacancies_by_keywords(self):
        """Тест фильтрации по ключевым словам"""
        filtered = filter_vacancies(self.vacancies, ["senior"])

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Senior Python")

        # Фильтрация по нескольким ключевым словам
        filtered_multi = filter_vacancies(self.vacancies, ["Python", "junior"])
        self.assertEqual(len(filtered_multi), 1)
        self.assertEqual(filtered_multi[0].title, "Junior Python")

        # Фильтрация без ключевых слов
        filtered_none = filter_vacancies(self.vacancies, [])
        self.assertEqual(len(filtered_none), 4)

        # Фильтрация с несуществующим словом
        filtered_nonexistent = filter_vacancies(self.vacancies, ["nonexistent"])
        self.assertEqual(len(filtered_nonexistent), 0)

    def test_get_vacancies_by_salary(self):
        """Тест фильтрации по диапазону зарплат"""
        # Тест с диапазоном - ИСПРАВЛЕНО
        ranged = get_vacancies_by_salary(self.vacancies, "60000-120000")
        # Попадают: Junior (средняя 65к)
        # No Salary НЕ попадает (средняя 0 < 60000)
        # Middle не попадает (средняя 125к > 120к)
        # Senior не попадает (средняя 175к > 120к)
        self.assertEqual(len(ranged), 1)  # Только Junior

        # Тест только с минимальной зарплатой
        ranged_min = get_vacancies_by_salary(self.vacancies, "90000")
        # Попадают: Middle (средняя 125к) и Senior (средняя 175к)
        # Junior не попадает (средняя 65к < 90к)
        # No Salary не попадает (средняя 0 < 90к)
        self.assertEqual(len(ranged_min), 2)

        # Тест с неверным форматом - должна быть обработка ошибки
        # Мокаем print чтобы не выводить сообщение об ошибке
        import builtins

        original_print = builtins.print

        printed_messages = []

        def mock_print(*args, **kwargs):
            printed_messages.append(" ".join(str(arg) for arg in args))

        builtins.print = mock_print

        try:
            ranged_invalid = get_vacancies_by_salary(self.vacancies, "invalid")
            # При ошибке должны вернуться все вакансии
            self.assertEqual(len(ranged_invalid), 4)

            # Проверяем, что сообщение об ошибке было выведено
            self.assertTrue(any("Неверный формат" in msg for msg in printed_messages))
        finally:
            builtins.print = original_print

        # Тест без диапазона
        ranged_none = get_vacancies_by_salary(self.vacancies, None)
        self.assertEqual(len(ranged_none), 4)

        # Тест с высоким диапазоном
        ranged_high = get_vacancies_by_salary(self.vacancies, "200000-300000")
        self.assertEqual(len(ranged_high), 0)

        # Тест с диапазоном 0-100000 (попадает Junior и No Salary)
        ranged_low = get_vacancies_by_salary(self.vacancies, "0-100000")
        self.assertEqual(
            len(ranged_low), 2
        )  # Junior (средняя 65к) и No Salary (средняя 0)

        # Тест с диапазоном, включающим 0
        ranged_with_zero = get_vacancies_by_salary(self.vacancies, "0-70000")
        self.assertEqual(len(ranged_with_zero), 2)  # Junior (65к) и No Salary (0)

    def test_print_vacancies(self):
        """Тест вывода вакансий"""
        # Просто проверяем, что функция не вызывает ошибок
        try:
            print_vacancies(self.vacancies)
            print_vacancies([])
            success = True
        except Exception as e:
            success = False
            print(f"Ошибка: {e}")

        self.assertTrue(success, "print_vacancies вызвала исключение")


if __name__ == "__main__":
    unittest.main()
