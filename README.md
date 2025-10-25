# Sync Copilot Files

Синхронизация файлов `.instructions.md` из [github/awesome-copilot](https://github.com/github/awesome-copilot) с VS Code.

## Что делает

Обновляет **только существующие** локальные файлы инструкций, не трогая ваши кастомные.

## Установка

```bash
git clone https://github.com/akab00m/sync_copilot_files.git
cd sync_copilot_files
pip install requests
```

## Использование

```bash
python sync_copilot_files.py
```

### Переключение VS Code Insiders ↔ Stable

В `sync_copilot_files.py` раскомментируйте нужную версию:

```python
VSCODE_VERSION = "Code - Insiders"  # По умолчанию
# VSCODE_VERSION = "Code"           # Для Stable
```

## Лицензия

MIT
