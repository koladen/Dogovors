from pathlib import Path
from typing import List, Optional, Dict
from backend.config import DATA_DIR
from backend.services.json_utils import read_json, write_json

USERS_FILE = DATA_DIR / "users.json"

def get_all_users() -> List[Dict]:
    """
    Получить список всех пользователей.

    Returns:
        Список пользователей (без паролей для безопасности)
    """
    data = read_json(USERS_FILE, {"users": []})
    users = data.get("users", [])

    # Убрать пароли из ответа
    return [
        {"username": u["username"], "role": u["role"]}
        for u in users
    ]

def get_user_by_username(username: str) -> Optional[Dict]:
    """
    Получить пользователя по имени.

    Args:
        username: Имя пользователя

    Returns:
        Словарь с данными пользователя или None
    """
    data = read_json(USERS_FILE, {"users": []})
    users = data.get("users", [])

    for user in users:
        if user["username"] == username:
            return user

    return None

def create_user(username: str, password: str, role: str = "user") -> bool:
    """
    Создать нового пользователя.

    Args:
        username: Имя пользователя
        password: Пароль
        role: Роль (admin или user)

    Returns:
        True если создание успешно, False если пользователь уже существует
    """
    data = read_json(USERS_FILE, {"users": []})
    users = data.get("users", [])

    # Проверка существования
    if any(u["username"] == username for u in users):
        return False

    # Добавить нового пользователя
    users.append({
        "username": username,
        "password": password,
        "role": role
    })

    data["users"] = users
    return write_json(USERS_FILE, data)

def update_user(username: str, password: Optional[str] = None,
                role: Optional[str] = None) -> bool:
    """
    Обновить данные пользователя.

    Args:
        username: Имя пользователя
        password: Новый пароль (опционально)
        role: Новая роль (опционально)

    Returns:
        True если обновление успешно, False если пользователь не найден
    """
    data = read_json(USERS_FILE, {"users": []})
    users = data.get("users", [])

    for user in users:
        if user["username"] == username:
            if password is not None:
                user["password"] = password
            if role is not None:
                user["role"] = role

            data["users"] = users
            return write_json(USERS_FILE, data)

    return False

def verify_credentials(username: str, password: str) -> Optional[Dict]:
    """
    Проверить учетные данные пользователя.

    Args:
        username: Имя пользователя
        password: Пароль

    Returns:
        Словарь с данными пользователя (без пароля) или None
    """
    user = get_user_by_username(username)

    if user and user["password"] == password:
        return {
            "username": user["username"],
            "role": user["role"]
        }

    return None
