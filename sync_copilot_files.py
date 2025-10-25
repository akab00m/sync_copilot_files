"""Синхронизация файлов инструкций GitHub Copilot из awesome-copilot репозитория.

Скрипт загружает .instructions.md файлы и размещает их в правильной папке для VS Code.
VS Code автоматически подхватит их через настройку chat.instructionsFilesLocations.
"""

import os
from pathlib import Path
from typing import Any

import requests

# ============================================================================
# НАСТРОЙКА ВЕРСИИ VS CODE
# ============================================================================
# Раскомментируйте нужную версию:

# VS Code Insiders (используется по умолчанию)
VSCODE_VERSION = "Code - Insiders"

# VS Code Stable (стабильная версия)
# VSCODE_VERSION = "Code"
# ============================================================================


def get_github_files() -> list[str]:
    """Получение списка .instructions.md файлов из GitHub репозитория.

    Returns:
        Список имён файлов инструкций с расширением .instructions.md
    """
    url = "https://api.github.com/repos/github/awesome-copilot/contents/instructions"
    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        print(
            f"Ошибка: Не удалось получить файлы с GitHub. Код: {response.status_code}"
        )
        return []

    files: list[str] = []
    data: Any = response.json()  # GitHub API возвращает список словарей
    for item in data:
        if isinstance(item, dict) and item.get("name", "").endswith(".instructions.md"):
            files.append(item["name"])

    return files


def get_local_files(instructions_dir: str) -> list[str]:
    """Получение списка .instructions.md файлов из локальной директории.

    Args:
        instructions_dir: Путь к директории с инструкциями

    Returns:
        Список имён файлов с расширением .instructions.md
    """
    if not os.path.exists(instructions_dir):
        return []

    local_files: list[str] = []
    for file in os.listdir(instructions_dir):
        if file.endswith(".instructions.md"):
            local_files.append(file)

    return local_files


def download_file(file_name: str, download_url: str, save_path: str) -> bool:
    """Загрузка файла с GitHub и сохранение локально.

    Args:
        file_name: Имя файла для отображения в логах
        download_url: URL для загрузки файла
        save_path: Путь для сохранения файла

    Returns:
        True если загрузка успешна, False в случае ошибки
    """
    try:
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"Загружено: {file_name}")
        return True
    except Exception as e:
        print(f"Ошибка загрузки {file_name}: {e!s}")
        return False


def sync_copilot_files(prompts_dir: str) -> None:
    """Синхронизация .instructions.md файлов с GitHub репозиторием.

    Обновляет ТОЛЬКО те файлы, которые уже есть в локальной папке prompts.
    Не загружает новые файлы, не удаляет локальные.

    Args:
        prompts_dir: Путь к директории prompts в профиле VS Code.
    """
    # Создаём директорию если её нет
    Path(prompts_dir).mkdir(parents=True, exist_ok=True)

    # Получаем списки файлов (только имена, без загрузки)
    print("Получение списка файлов с GitHub...")
    github_files = set(get_github_files())
    print(f"  Найдено на GitHub: {len(github_files)} файлов")

    print("\nПроверка локальных файлов...")
    local_files = set(get_local_files(prompts_dir))
    print(f"  Найдено локально: {len(local_files)} файлов")

    # Определяем что нужно обновить - ТОЛЬКО файлы которые есть и там и там
    files_to_update = github_files.intersection(local_files)
    files_to_preserve = local_files - github_files

    # Показываем план действий
    print("\n" + "=" * 70)
    print("План синхронизации:")
    print("=" * 70)

    if files_to_update:
        print(f"  • Файлы для обновления: {len(files_to_update)}")
    else:
        print("  • Нет файлов для обновления")

    if files_to_preserve:
        print(f"  • Локальные файлы (будут сохранены): {len(files_to_preserve)}")

    print("=" * 70)

    # Обновляем ТОЛЬКО те файлы, которые есть локально
    total_downloaded = 0

    if files_to_update:
        print(f"\nОбновление файлов ({len(files_to_update)}):")
        for file_name in sorted(files_to_update):
            download_url = f"https://raw.githubusercontent.com/github/awesome-copilot/main/instructions/{file_name}"
            save_path = os.path.join(prompts_dir, file_name)
            if download_file(file_name, download_url, save_path):
                total_downloaded += 1

    if files_to_preserve:
        print("\nСохранены локальные файлы (нет на GitHub):")
        for file_name in sorted(files_to_preserve):
            print(f"  • {file_name}")

    # Итоговая статистика
    print("\n" + "=" * 70)
    print("✓ Синхронизация завершена!")
    print("=" * 70)
    print(f"  Обновлено файлов: {total_downloaded}")
    print(f"  Всего файлов инструкций: {len(get_local_files(prompts_dir))}")
    print(f"  Директория: {prompts_dir}")


if __name__ == "__main__":
    # Используем %APPDATA% для кросс-платформенности Windows
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise ValueError("Переменная окружения APPDATA не установлена")

    # Формируем путь к папке prompts для выбранной версии VS Code
    prompts_dir = os.path.join(appdata, VSCODE_VERSION, "User", "prompts")

    print("=" * 70)
    print("Синхронизация инструкций GitHub Copilot")
    print("=" * 70)
    print(f"Версия VS Code: {VSCODE_VERSION}")
    print(f"Целевая директория: {prompts_dir}")
    print("Режим: Обновление только существующих файлов")
    print()

    sync_copilot_files(prompts_dir)
