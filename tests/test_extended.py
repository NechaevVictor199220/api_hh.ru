import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from api import HeadHunterAPI
from storage import CSVSaver, JSONSaver
from utils import save_vacancies_to_file
from vacancy import Vacancy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestExtendedCoverage(unittest.TestCase):
    """Тесты для улучшения покрытия кода"""

    def test_vacancy_cast_to_object_list(self):
        """Тест преобразования списка вакансий"""
        vacancies_data = [
            {
                "name": "Python Dev",
                "alternate_url": "https://hh.ru/1",
                "salary": {"from": 100000, "to": 150000, "currency": "RUR"},
                "snippet": {"requirement": "Python", "responsibility": "Dev"},
                "experience": {"name": "1-3 года"},
                "employer": {"name": "Company A"},
                "area": {"name": "Москва"},
            },
            {
                "name": "Java Dev",
                "alternate_url": "https://hh.ru/2",
                "salary": None,
                "snippet": {"requirement": "Java", "responsibility": "Dev"},
                "experience": {"name": "Нет опыта"},
                "employer": {"name": "Company B"},
                "area": {"name": "СПб"},
            },
        ]

        vacancies = Vacancy.cast_to_object_list(vacancies_data)

        self.assertEqual(len(vacancies), 2)
        self.assertEqual(vacancies[0].title, "Python Dev")
        self.assertEqual(vacancies[1].title, "Java Dev")
        self.assertEqual(vacancies[1].salary_from, 0)  # Без зарплаты

    def test_vacancy_cast_to_object_list_empty(self):
        """Тест преобразования пустого списка"""
        vacancies = Vacancy.cast_to_object_list([])
        self.assertEqual(vacancies, [])

    def test_vacancy_cast_to_object_list_invalid(self):
        """Тест преобразования с неполными данными"""
        vacancies_data = [{"name": "Invalid", "alternate_url": "https://test.com"}]

        vacancies = Vacancy.cast_to_object_list(vacancies_data)
        self.assertEqual(len(vacancies), 1)
        self.assertEqual(vacancies[0].title, "Invalid")

    def test_json_saver_edge_cases(self):
        """Тест граничных случаев JSONSaver"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        saver = JSONSaver(temp_file)

        # Тест с пустым файлом
        saver.clear()
        vacancies = saver.get_vacancies()
        self.assertEqual(vacancies, [])

        # Тест с поврежденным JSON
        with open(temp_file, "w") as f:
            f.write("invalid json")

        # Должен создать новый файл
        saver2 = JSONSaver(temp_file)
        vacancies = saver2.get_vacancies()
        self.assertEqual(vacancies, [])

        os.unlink(temp_file)

    def test_csv_saver_edge_cases(self):
        """Тест граничных случаев CSVSaver"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем папку data внутри временной директории
            data_dir = os.path.join(temp_dir, "data")
            os.makedirs(data_dir, exist_ok=True)

            temp_file = os.path.join(data_dir, "test_vacancies.csv")

            # Создаем saver напрямую с путем к файлу
            class TestCSVSaver(CSVSaver):
                def __init__(self, filename):
                    # Переопределяем конструктор для теста
                    self._filename = filename
                    self._data_dir = os.path.dirname(filename)
                    os.makedirs(self._data_dir, exist_ok=True)

            saver = TestCSVSaver(temp_file)

            # Тест с несуществующим файлом
            vacancies = saver.get_vacancies()
            self.assertEqual(vacancies, [])

            # Тест очистки
            vacancy = Vacancy(
                "Test",
                "https://test.com",
                salary={"from": 100000, "to": 150000, "currency": "RUR"},
            )
            saver.add_vacancy(vacancy)

            # Проверяем, что файл создался и содержит данные
            self.assertTrue(os.path.exists(temp_file))

            vacancies = saver.get_vacancies()
            self.assertEqual(len(vacancies), 1)

            # Тест очистки - метод clear удаляет файл
            saver.clear()
            self.assertFalse(os.path.exists(temp_file))

    def test_api_with_parameters(self):
        """Тест API с различными параметрами"""
        api = HeadHunterAPI()

        # Мокаем запрос
        with patch("api.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"items": [], "pages": 1}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Тест с различными параметрами
            vacancies = api.get_vacancies(
                "Python", area="1", only_with_salary=True, per_page=50
            )

            self.assertEqual(vacancies, [])

    def test_save_vacancies_to_file(self):
        """Тест сохранения вакансий в файл"""
        vacancies = [
            Vacancy(
                title="Test Vacancy",
                url="https://test.com",
                salary={"from": 100000, "to": 150000, "currency": "RUR"},
            )
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_file = f.name

        # Тест с вакансиями
        save_vacancies_to_file(vacancies, temp_file)

        with open(temp_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Test Vacancy", content)
        self.assertIn("100,000 - 150,000 RUR", content)

        # Тест с пустым списком
        save_vacancies_to_file([], temp_file)

        with open(temp_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Вакансий не найдено", content)

        os.unlink(temp_file)


class TestVacancyValidation(unittest.TestCase):
    """Тесты валидации вакансий"""

    def test_vacancy_validation_empty_title(self):
        """Тест валидации пустого заголовка"""
        vacancy = Vacancy("", "https://test.com")
        self.assertEqual(vacancy.title, "Название не указано")

    def test_vacancy_validation_none_title(self):
        """Тест валидации None заголовка"""
        vacancy = Vacancy(None, "https://test.com")
        self.assertEqual(vacancy.title, "Название не указано")

    def test_vacancy_validation_empty_url(self):
        """Тест валидации пустого URL"""
        vacancy = Vacancy("Test", "")
        self.assertEqual(vacancy.url, "")

    def test_vacancy_salary_validation(self):
        """Тест различных вариантов зарплаты"""
        # Зарплата без currency
        vacancy1 = Vacancy(
            "Test1", "https://test.com", salary={"from": 100000, "to": 150000}
        )
        self.assertEqual(vacancy1.currency, "Не указана")

        # Пустая зарплата
        vacancy2 = Vacancy("Test2", "https://test.com", salary={})
        self.assertEqual(vacancy2.salary_from, 0)
        self.assertEqual(vacancy2.salary_to, 0)

        # Зарплата только с currency
        vacancy3 = Vacancy("Test3", "https://test.com", salary={"currency": "USD"})
        self.assertEqual(vacancy3.currency, "USD")
        self.assertEqual(vacancy3.salary_from, 0)


class TestStorageMethods(unittest.TestCase):
    """Тесты методов хранилища"""

    def test_json_saver_file_creation(self):
        """Тест создания файла JSONSaver"""
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, "new_file.json")

            # Файл не должен существовать
            self.assertFalse(os.path.exists(filename))

            # Создаем saver - файл должен создаться
            JSONSaver(filename)
            self.assertTrue(os.path.exists(filename))

            # Проверяем, что файл содержит пустой список
            with open(filename, "r") as f:
                content = json.load(f)

            self.assertEqual(content, [])

    def test_csv_saver_multiple_additions(self):
        """Тест множественного добавления в CSV"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем папку data
            data_dir = os.path.join(temp_dir, "data")
            os.makedirs(data_dir, exist_ok=True)

            temp_file = os.path.join(data_dir, "test_vacancies.csv")

            # Создаем saver с нашим файлом
            saver = CSVSaver(filename="test_vacancies.csv")
            saver._filename = temp_file  # Переопределяем путь для теста

            vacancy1 = Vacancy(
                "Job1",
                "https://test.com/1",
                salary={"from": 100000, "to": 150000, "currency": "RUR"},
            )
            vacancy2 = Vacancy(
                "Job2",
                "https://test.com/2",
                salary={"from": 120000, "to": 180000, "currency": "RUR"},
            )

            saver.add_vacancy(vacancy1)
            saver.add_vacancy(vacancy2)

            # Проверяем, что файл создан
            self.assertTrue(os.path.exists(temp_file))

            # Читаем файл и проверяем содержимое
            with open(temp_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Проверяем заголовок и две строки данных
            self.assertEqual(len(lines), 3)  # Заголовок + 2 строки данных

            # Теперь получаем вакансии через метод get_vacancies
            vacancies = saver.get_vacancies()
            self.assertEqual(len(vacancies), 2)

            # Проверяем порядок
            self.assertEqual(vacancies[0].title, "Job1")
            self.assertEqual(vacancies[1].title, "Job2")


if __name__ == "__main__":
    unittest.main()
