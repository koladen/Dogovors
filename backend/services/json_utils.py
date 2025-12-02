import json
from pathlib import Path
from typing import Any, Dict
import threading

# Блокировки для безопасного доступа к файлам
_locks: Dict[str, threading.Lock] = {}
_locks_lock = threading.Lock()

def _get_lock(file_path: Path) -> threading.Lock:
    """Получить блокировку для файла."""
    with _locks_lock:
        key = str(file_path)
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]

def read_json(file_path: Path, default: Any = None) -> Any:
    """
    Безопасное чтение JSON файла.

    Args:
        file_path: Путь к файлу
        default: Значение по умолчанию, если файл не существует или поврежден

    Returns:
        Содержимое JSON файла или default
    """
    lock = _get_lock(file_path)
    with lock:
        try:
            if not file_path.exists():
                return default

            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка чтения {file_path}: {e}")
            return default

def write_json(file_path: Path, data: Any, indent: int = 2) -> bool:
    """
    Безопасная запись JSON файла.

    Args:
        file_path: Путь к файлу
        data: Данные для записи
        indent: Отступ для форматирования (по умолчанию 2)

    Returns:
        True если запись успешна, False в случае ошибки
    """
    lock = _get_lock(file_path)
    with lock:
        try:
            # Создать директорию если не существует
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Записать во временный файл
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)

            # Атомарно заменить оригинальный файл
            temp_path.replace(file_path)
            return True
        except (IOError, TypeError) as e:
            print(f"Ошибка записи {file_path}: {e}")
            return False

def update_json(file_path: Path, updates: Dict, default: Any = None) -> bool:
    """
    Обновить JSON файл (merge).

    Args:
        file_path: Путь к файлу
        updates: Словарь с обновлениями
        default: Значение по умолчанию для нового файла

    Returns:
        True если обновление успешно, False в случае ошибки
    """
    lock = _get_lock(file_path)
    with lock:
        # Читаем данные
        try:
            if not file_path.exists():
                data = default or {}
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка чтения {file_path}: {e}")
            data = default or {}

        # Обновляем данные
        if isinstance(data, dict):
            data.update(updates)
        else:
            data = updates

        # Записываем обновленные данные
        try:
            # Создать директорию если не существует
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Записать во временный файл
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Атомарно заменить оригинальный файл
            temp_path.replace(file_path)
            return True
        except (IOError, TypeError) as e:
            print(f"Ошибка записи {file_path}: {e}")
            return False
