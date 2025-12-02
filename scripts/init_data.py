"""
Скрипт инициализации начальных данных.
Создает необходимые файлы и директории.
"""

import sys
from pathlib import Path

# Добавить корневую директорию в путь
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.config import DATA_DIR, PROMPTS_DIR, DEFAULTS_DIR, LOGS_DIR
from backend.services.json_utils import write_json

def init_directories():
    """Создать необходимые директории."""
    print("Создание директорий...")
    DATA_DIR.mkdir(exist_ok=True)
    PROMPTS_DIR.mkdir(exist_ok=True)
    DEFAULTS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    print("OK: Директории созданы")

def init_users():
    """Создать файл пользователей с начальным админом."""
    users_file = DATA_DIR / "users.json"
    if users_file.exists():
        print("SKIP: Файл пользователей уже существует, пропускаем")
        return

    print("Создание файла пользователей...")
    data = {
        "users": [
            {
                "username": "admin",
                "password": "admin",
                "role": "admin"
            }
        ]
    }
    write_json(users_file, data)
    print("OK: Создан пользователь: admin / admin")

def init_auth_ips():
    """Создать файл авторизованных IP."""
    auth_file = DATA_DIR / "auth_ips.json"
    if auth_file.exists():
        print("SKIP: Файл авторизованных IP уже существует, пропускаем")
        return

    print("Создание файла авторизованных IP...")
    write_json(auth_file, {"authorized_ips": {}})
    print("OK: Файл создан")

def init_llm_config():
    """Создать файл конфигурации LLM."""
    config_file = DATA_DIR / "llm_config.json"
    if config_file.exists():
        print("SKIP: Файл конфигурации LLM уже существует, пропускаем")
        return

    print("Создание конфигурации LLM...")
    data = {
        "llm_type": "deepseek",
        "deepseek_api_key": "",
        "deepseek_base_url": "https://api.deepseek.com",
        "lmstudio_base_url": "http://localhost:1234/v1",
        "lmstudio_model": "deepseek-coder"
    }
    write_json(config_file, data)
    print("OK: Конфигурация создана")

def init_settings():
    """Создать файл настроек системы."""
    settings_file = DATA_DIR / "settings.json"
    if settings_file.exists():
        print("SKIP: Файл настроек уже существует, пропускаем")
        return

    print("Создание настроек системы...")
    data = {
        "max_file_size_mb": 50,
        "max_queue_size": 5,
        "max_concurrent_requests": 5,
        "rate_limit_per_minute": 10
    }
    write_json(settings_file, data)
    print("OK: Настройки созданы")

def init_tokens_stats():
    """Создать файл статистики токенов."""
    tokens_file = DATA_DIR / "tokens_usage.json"
    if tokens_file.exists():
        print("SKIP: Файл статистики токенов уже существует, пропускаем")
        return

    print("Создание файла статистики токенов...")
    data = {
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_cost_usd": 0.0,
        "users": {},
        "last_updated": ""
    }
    write_json(tokens_file, data)
    print("OK: Файл создан")

def main():
    """Основная функция инициализации."""
    print("=" * 50)
    print("ИНИЦИАЛИЗАЦИЯ ДАННЫХ")
    print("=" * 50)

    init_directories()
    init_users()
    init_auth_ips()
    init_llm_config()
    init_settings()
    init_tokens_stats()

    print("\n" + "=" * 50)
    print("ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА")
    print("=" * 50)
    print("\nВажно:")
    print("1. Настройте API ключ DeepSeek в .env файле")
    print("2. Убедитесь, что файлы промптов созданы в data/prompts/")
    print("3. Запустите сервер: start_server.bat")
    print("\nНачальные учетные данные:")
    print("  Логин: admin")
    print("  Пароль: admin")

if __name__ == "__main__":
    main()
