from pathlib import Path
from typing import Optional, Dict
from backend.config import DATA_DIR
from backend.services.json_utils import read_json, write_json
from backend.services.users import get_user_by_username

AUTH_IPS_FILE = DATA_DIR / "auth_ips.json"

def get_user_by_ip(ip: str) -> Optional[Dict]:
    """
    Получить пользователя по IP-адресу.

    Args:
        ip: IP-адрес

    Returns:
        Словарь с данными пользователя или None
    """
    data = read_json(AUTH_IPS_FILE, {"authorized_ips": {}})
    authorized_ips = data.get("authorized_ips", {})

    username = authorized_ips.get(ip)
    if not username:
        return None

    user = get_user_by_username(username)
    if user:
        return {
            "username": user["username"],
            "role": user["role"],
            "ip": ip
        }

    return None

def authorize_ip(ip: str, username: str) -> bool:
    """
    Авторизовать IP-адрес для пользователя.

    Args:
        ip: IP-адрес
        username: Имя пользователя

    Returns:
        True если авторизация успешна
    """
    data = read_json(AUTH_IPS_FILE, {"authorized_ips": {}})
    authorized_ips = data.get("authorized_ips", {})

    authorized_ips[ip] = username
    data["authorized_ips"] = authorized_ips

    return write_json(AUTH_IPS_FILE, data)

def is_ip_authorized(ip: str) -> bool:
    """
    Проверить, авторизован ли IP-адрес.

    Args:
        ip: IP-адрес

    Returns:
        True если IP авторизован
    """
    user = get_user_by_ip(ip)
    return user is not None

def remove_ip_authorization(ip: str) -> bool:
    """
    Удалить авторизацию IP-адреса.

    Args:
        ip: IP-адрес

    Returns:
        True если удаление успешно
    """
    data = read_json(AUTH_IPS_FILE, {"authorized_ips": {}})
    authorized_ips = data.get("authorized_ips", {})

    if ip in authorized_ips:
        del authorized_ips[ip]
        data["authorized_ips"] = authorized_ips
        return write_json(AUTH_IPS_FILE, data)

    return False
