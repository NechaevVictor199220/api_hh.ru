from typing import List, Optional

from vacancy import Vacancy


def sort_vacancies(vacancies: List[Vacancy], reverse: bool = True) -> List[Vacancy]:
    """
    Сортировка вакансий по зарплате

    Args:
        vacancies: Список вакансий
        reverse: Сортировка по убыванию (True) или возрастанию (False)

    Returns:
        Отсортированный список вакансий
    """
    return sorted(vacancies, reverse=reverse)


def get_top_vacancies(vacancies: List[Vacancy], top_n: int) -> List[Vacancy]:
    """
    Получение топ N вакансий

    Args:
        vacancies: Список вакансий
        top_n: Количество вакансий для вывода

    Returns:
        Список топ N вакансий
    """
    return vacancies[:top_n]


def filter_vacancies(
    vacancies: List[Vacancy], filter_words: List[str]
) -> List[Vacancy]:
    """
    Фильтрация вакансий по ключевым словам

    Args:
        vacancies: Список вакансий
        filter_words: Список ключевых слов

    Returns:
        Отфильтрованный список вакансий
    """
    if not filter_words:
        return vacancies

    filtered = []

    for vacancy in vacancies:
        text_to_search = (
            f"{vacancy.title} {vacancy.description} {vacancy.requirements}".lower()
        )

        # Проверяем, есть ли все ключевые слова в тексте
        all_keywords_present = all(
            keyword.lower() in text_to_search
            for keyword in filter_words
            if keyword.strip()
        )

        if all_keywords_present:
            filtered.append(vacancy)

    return filtered


def get_vacancies_by_salary(
    vacancies: List[Vacancy], salary_range: Optional[str] = None
) -> List[Vacancy]:
    """
    Фильтрация вакансий по диапазону зарплат

    Args:
        vacancies: Список вакансий
        salary_range: Диапазон зарплат в формате "min-max" или "min"

    Returns:
        Отфильтрованный список вакансий
    """
    if not salary_range:
        return vacancies

    try:
        min_salary = 0
        max_salary = float("inf")

        if salary_range.strip():
            if "-" in salary_range:
                parts = salary_range.split("-")
                min_salary = int(parts[0].strip()) if parts[0].strip() else 0
                max_salary = (
                    int(parts[1].strip())
                    if len(parts) > 1 and parts[1].strip()
                    else float("inf")
                )
            else:
                min_salary = int(salary_range.strip())
                max_salary = float("inf")

        filtered = []

        for vacancy in vacancies:
            avg_salary = vacancy.get_average_salary()

            # Проверяем, попадает ли средняя зарплата в диапазон
            if min_salary <= avg_salary <= max_salary:
                filtered.append(vacancy)

        return filtered
    except ValueError:
        print(
            "Неверный формат диапазона зарплат. Используйте формат: 100000-150000 или 100000"
        )
        return vacancies  # При ошибке возвращаем все вакансии


def print_vacancies(vacancies: List[Vacancy]) -> None:
    """
    Вывод вакансий в консоль

    Args:
        vacancies: Список вакансий для вывода
    """
    if not vacancies:
        print("Вакансий не найдено.")
        return

    print(f"\nНайдено вакансий: {len(vacancies)}")
    print("=" * 60)

    for i, vacancy in enumerate(vacancies, 1):
        print(f"\n{i}. {vacancy}")


def save_vacancies_to_file(
    vacancies: List[Vacancy], filename: str = "results.txt"
) -> None:
    """
    Сохранение вакансий в текстовый файл

    Args:
        vacancies: Список вакансий
        filename: Имя файла для сохранения
    """
    with open(filename, "w", encoding="utf-8") as f:
        if not vacancies:
            f.write("Вакансий не найдено.\n")
            return

        f.write(f"Найдено вакансий: {len(vacancies)}\n")
        f.write("=" * 60 + "\n")

        for i, vacancy in enumerate(vacancies, 1):
            f.write(f"\n{i}. {vacancy}\n")

    print(f"\nРезультаты сохранены в файл: {filename}")
