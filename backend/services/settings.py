from pathlib import Path
from typing import Dict
from backend.config import DATA_DIR
from backend.services.json_utils import read_json, write_json, update_json

SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "max_file_size_mb": 50,
    "max_audio_file_size_mb": 100,
    "max_queue_size": 5,
    "max_concurrent_requests": 5,
    "rate_limit_per_minute": 10
}

def get_settings() -> Dict:
    """
    Получить текущие настройки системы.

    Returns:
        Словарь с настройками
    """
    return read_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())

def update_settings(updates: Dict) -> bool:
    """
    Обновить настройки системы.

    Args:
        updates: Словарь с обновлениями

    Returns:
        True если обновление успешно
    """
    return update_json(SETTINGS_FILE, updates, DEFAULT_SETTINGS.copy())

def get_max_file_size_bytes() -> int:
    """
    Получить максимальный размер файла в байтах.

    Returns:
        Размер в байтах
    """
    settings = get_settings()
    size_mb = settings.get("max_file_size_mb", 50)
    return size_mb * 1024 * 1024


def get_max_audio_file_size_bytes() -> int:
    """
    Получить максимальный размер аудиофайла в байтах.

    Returns:
        Размер в байтах
    """
    settings = get_settings()
    size_mb = settings.get("max_audio_file_size_mb", 100)
    return size_mb * 1024 * 1024

