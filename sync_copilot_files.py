"""Синхронизация файлов инструкций GitHub Copilot из awesome-copilot репозитория.

Скрипт загружает .instructions.md файлы и размещает их в правильной папке для VS Code.
VS Code автоматически подхватит их через настройку chat.instructionsFilesLocations.
"""

import os
from pathlib import Path

import requests


def get_github_files() -> list[str]:
    """Fetch the list of .instructions.md files from the GitHub repository."""
    url = "https://api.github.com/repos/github/awesome-copilot/contents/instructions"
    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        print(
            f"Error: Could not fetch files from GitHub. Status code: {response.status_code}"
        )
        return []

    files = []
    for item in response.json():
        if item["name"].endswith(".instructions.md"):
            files.append(item["name"])

    return files


def get_local_files(instructions_dir: str) -> list[str]:
    """Get the list of .instructions.md files from the local instructions directory.

    Args:
        instructions_dir: Path to the instructions directory.

    Returns:
        List of .instructions.md file names.
    """
    if not os.path.exists(instructions_dir):
        return []

    local_files: list[str] = []
    for file in os.listdir(instructions_dir):
        if file.endswith(".instructions.md"):
            local_files.append(file)

    return local_files


def download_file(file_name: str, download_url: str, save_path: str) -> bool:
    """Download a file from GitHub and save it locally."""
    try:
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"Downloaded: {file_name}")
        return True
    except Exception as e:
        print(f"Error downloading {file_name}: {str(e)}")
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
    # Используем %APPDATA% для универсальности
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise ValueError("APPDATA environment variable is not set")

    # Папка prompts для VS Code Insiders (как было изначально)
    prompts_dir = os.path.join(appdata, r"Code - Insiders\User\prompts")

    print("=" * 70)
    print("Синхронизация инструкций GitHub Copilot")
    print("=" * 70)
    print(f"\nЦелевая директория: {prompts_dir}")
    print("Режим: Обновление только существующих файлов")
    print()

    sync_copilot_files(prompts_dir)
