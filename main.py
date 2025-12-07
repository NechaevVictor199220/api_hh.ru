# main.py
import os
import sys

from api import HeadHunterAPI
from storage import CSVSaver, JSONSaver, TXTSaver
from utils import (filter_vacancies, get_top_vacancies,
                   get_vacancies_by_salary, print_vacancies,
                   save_vacancies_to_file, sort_vacancies)
from vacancy import Vacancy

# Для работы с Poetry и структурой проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def user_interaction() -> None:
    """Функция взаимодействия с пользователем"""
    print("=" * 60)
    print("ПОИСК ВАКАНСИЙ НА HH.RU")
    print("=" * 60)

    # Инициализация API и хранилища
    hh_api = HeadHunterAPI()
    json_saver = JSONSaver()  # По умолчанию сохраняет в data/vacancies.json

    while True:
        print("\nМЕНЮ:")
        print("1. Поиск вакансий")
        print("2. Показать сохраненные вакансии")
        print("3. Фильтрация сохраненных вакансий")
        print("4. Удалить вакансию")
        print("5. Очистить сохраненные вакансии")
        print("6. Экспорт в CSV")
        print("7. Экспорт в TXT")
        print("8. Показать путь к файлам данных")
        print("9. Выход")

        choice = input("\nВыберите действие (1-9): ").strip()

        if choice == "1":
            search_vacancies(hh_api, json_saver)
        elif choice == "2":
            show_saved_vacancies(json_saver)
        elif choice == "3":
            filter_saved_vacancies(json_saver)
        elif choice == "4":
            delete_vacancy(json_saver)
        elif choice == "5":
            clear_vacancies(json_saver)
        elif choice == "6":
            export_to_csv(json_saver)
        elif choice == "7":
            export_to_txt(json_saver)
        elif choice == "8":
            show_data_paths(json_saver)
        elif choice == "9":
            print("Выход из программы.")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


def search_vacancies(hh_api: HeadHunterAPI, json_saver: JSONSaver) -> None:
    """Поиск и сохранение вакансий"""
    print("\n" + "=" * 60)
    print("ПОИСК ВАКАНСИЙ")
    print("=" * 60)

    search_query = input(
        "Введите поисковый запрос (например: Python разработчик): "
    ).strip()

    if not search_query:
        print("Поисковый запрос не может быть пустым.")
        return

    # Получение дополнительных параметров
    only_with_salary = (
        input("Показывать только вакансии с зарплатой? (да/нет): ").strip().lower()
        == "да"
    )
    area = input("Введите регион (по умолчанию: Россия): ").strip()
    area = area if area else "113"  # 113 - Россия

    try:
        print("\nЗагружаем вакансии...")
        vacancies_data = hh_api.get_vacancies(
            search_query=search_query,
            area=area,
            only_with_salary=only_with_salary,
            per_page=50,  # Ограничим для быстрого тестирования
        )

        # Преобразование в объекты Vacancy
        vacancies = Vacancy.cast_to_object_list(vacancies_data)

        if not vacancies:
            print("По вашему запросу вакансий не найдено.")
            return

        print(f"\nНайдено вакансий: {len(vacancies)}")

        # Фильтрация по ключевым словам
        filter_words_input = input(
            "\nВведите ключевые слова для фильтрации (через запятую): "
        ).strip()
        filter_words = (
            [word.strip() for word in filter_words_input.split(",")]
            if filter_words_input
            else []
        )

        if filter_words:
            vacancies = filter_vacancies(vacancies, filter_words)
            print(f"После фильтрации осталось: {len(vacancies)} вакансий")

        # Фильтрация по зарплате
        salary_range = input(
            "\nВведите диапазон зарплат (например: 100000-150000): "
        ).strip()
        if salary_range:
            vacancies = get_vacancies_by_salary(vacancies, salary_range)
            print(f"После фильтрации по зарплате осталось: {len(vacancies)} вакансий")

        # Сортировка
        vacancies = sort_vacancies(vacancies, reverse=True)

        # Выбор топ N
        try:
            top_n = int(
                input("\nСколько вакансий показать? (по умолчанию: 10): ").strip()
                or "10"
            )
            top_vacancies = get_top_vacancies(vacancies, top_n)
        except ValueError:
            top_vacancies = get_top_vacancies(vacancies, 10)

        # Вывод результатов
        print_vacancies(top_vacancies)

        # Сохранение в файл
        save_option = input("\nСохранить результаты в файл? (да/нет): ").strip().lower()
        if save_option == "да":
            save_vacancies_to_file(top_vacancies)

        # Сохранение в JSON
        save_json = input("\nСохранить вакансии в базу? (да/нет): ").strip().lower()
        if save_json == "да":
            json_saver.add_vacancies(top_vacancies)
            print(
                f"Сохранено {len(top_vacancies)} вакансий в базу (файл: {json_saver.get_file_path()})."
            )

    except Exception as e:
        print(f"Произошла ошибка: {e}")


def show_saved_vacancies(json_saver: JSONSaver) -> None:
    """Показать сохраненные вакансии"""
    print("\n" + "=" * 60)
    print("СОХРАНЕННЫЕ ВАКАНСИИ")
    print("=" * 60)

    vacancies = json_saver.get_vacancies()

    if not vacancies:
        print("Нет сохраненных вакансий.")
        return

    # Сортировка по зарплате
    vacancies = sort_vacancies(vacancies, reverse=True)

    # Ограничение вывода
    try:
        limit = int(
            input("Сколько вакансий показать? (по умолчанию: все): ").strip()
            or str(len(vacancies))
        )
        vacancies_to_show = get_top_vacancies(vacancies, limit)
    except ValueError:
        vacancies_to_show = vacancies

    print_vacancies(vacancies_to_show)
    print(f"\nВсего сохранено вакансий: {len(vacancies)}")
    print(f"Файл данных: {json_saver.get_file_path()}")


def filter_saved_vacancies(json_saver: JSONSaver) -> None:
    """Фильтрация сохраненных вакансий"""
    print("\n" + "=" * 60)
    print("ФИЛЬТРАЦИЯ ВАКАНСИЙ")
    print("=" * 60)

    criteria = {}

    # Ключевые слова
    keywords_input = input(
        "Введите ключевые слова для поиска (через запятую): "
    ).strip()
    if keywords_input:
        criteria["keywords"] = [word.strip() for word in keywords_input.split(",")]

    # Минимальная зарплата
    salary_min_input = input("Минимальная зарплата: ").strip()
    if salary_min_input:
        try:
            criteria["salary_min"] = int(salary_min_input)
        except ValueError:
            print("Неверный формат зарплаты.")

    # Работодатель
    employer_input = input("Работодатель: ").strip()
    if employer_input:
        criteria["employer"] = employer_input

    # Регион
    area_input = input("Регион: ").strip()
    if area_input:
        criteria["area"] = area_input

    vacancies = json_saver.get_vacancies(criteria)

    if not vacancies:
        print("Вакансий не найдено по указанным критериям.")
        return

    vacancies = sort_vacancies(vacancies, reverse=True)
    print_vacancies(vacancies)
    print(f"\nНайдено вакансий: {len(vacancies)}")


def delete_vacancy(json_saver: JSONSaver) -> None:
    """Удаление вакансии"""
    print("\n" + "=" * 60)
    print("УДАЛЕНИЕ ВАКАНСИИ")
    print("=" * 60)

    vacancies = json_saver.get_vacancies()

    if not vacancies:
        print("Нет сохраненных вакансий для удаления.")
        return

    # Показываем список для выбора
    for i, vacancy in enumerate(vacancies[:10], 1):  # Покажем первые 10
        print(
            f"{i}. {vacancy.title} - {vacancy.employer} - {vacancy.salary_from}-{vacancy.salary_to} {vacancy.currency}"
        )

    try:
        choice = int(input("\nВведите номер вакансии для удаления: ").strip())
        if 1 <= choice <= len(vacancies):
            vacancy_to_delete = vacancies[choice - 1]
            json_saver.delete_vacancy(vacancy_to_delete)
            print(f"Вакансия '{vacancy_to_delete.title}' удалена.")
        else:
            print("Неверный номер вакансии.")
    except ValueError:
        print("Неверный ввод.")


def clear_vacancies(json_saver: JSONSaver) -> None:
    """Очистка всех вакансий"""
    confirm = (
        input("\nВы уверены, что хотите удалить все сохраненные вакансии? (да/нет): ")
        .strip()
        .lower()
    )
    if confirm == "да":
        json_saver.clear()
        print("Все вакансии удалены.")
    else:
        print("Операция отменена.")


def export_to_csv(json_saver: JSONSaver) -> None:
    """Экспорт вакансий в CSV"""
    print("\n" + "=" * 60)
    print("ЭКСПОРТ В CSV")
    print("=" * 60)

    vacancies = json_saver.get_vacancies()

    if not vacancies:
        print("Нет сохраненных вакансий для экспорта.")
        return

    csv_saver = CSVSaver("exported_vacancies.csv")

    for vacancy in vacancies:
        csv_saver.add_vacancy(vacancy)

    print(
        f"Экспортировано {len(vacancies)} вакансий в файл {csv_saver.get_file_path()}"
    )


def export_to_txt(json_saver: JSONSaver) -> None:
    """Экспорт вакансий в TXT"""
    print("\n" + "=" * 60)
    print("ЭКСПОРТ В TXT")
    print("=" * 60)

    vacancies = json_saver.get_vacancies()

    if not vacancies:
        print("Нет сохраненных вакансий для экспорта.")
        return

    txt_saver = TXTSaver("exported_vacancies.txt")

    for vacancy in vacancies:
        txt_saver.add_vacancy(vacancy)

    print(
        f"Экспортировано {len(vacancies)} вакансий в файл {txt_saver.get_file_path()}"
    )


def show_data_paths(json_saver: JSONSaver, json=None) -> None:
    """Показать пути к файлам данных"""
    print("\n" + "=" * 60)
    print("ПУТИ К ФАЙЛАМ ДАННЫХ")
    print("=" * 60)

    print(f"JSON файл: {json_saver.get_file_path()}")

    # Проверим существование файлов
    if os.path.exists(json_saver.get_file_path()):
        with open(json_saver.get_file_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  - Количество вакансий: {len(data)}")
        print(f"  - Размер файла: {os.path.getsize(json_saver.get_file_path())} байт")
    else:
        print("  - Файл не существует")

    # Проверим CSV файл если есть
    csv_file = os.path.join("data", "vacancies.csv")
    if os.path.exists(csv_file):
        print(f"\nCSV файл: {csv_file}")
        print(f"  - Размер файла: {os.path.getsize(csv_file)} байт")

    # Проверим TXT файл если есть
    txt_file = os.path.join("data", "vacancies.txt")
    if os.path.exists(txt_file):
        print(f"\nTXT файл: {txt_file}")
        print(f"  - Размер файла: {os.path.getsize(txt_file)} байт")


if __name__ == "__main__":
    user_interaction()
