import sys
from loguru import logger
from pathlib import Path
from backend.config import LOGS_DIR, LOG_LEVEL, LOG_ROTATION

# Удалить стандартный handler
logger.remove()

# Добавить вывод в консоль
logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)

# Добавить логирование действий пользователей
logger.add(
    LOGS_DIR / "app.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    rotation=LOG_ROTATION,
    retention="30 days",
    encoding="utf-8"
)

# Добавить логирование ошибок
logger.add(
    LOGS_DIR / "error.log",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation=LOG_ROTATION,
    retention="30 days",
    encoding="utf-8"
)

def log_user_action(username: str, action: str, details: str = ""):
    """
    Логировать действие пользователя.

    Args:
        username: Имя пользователя
        action: Действие (login, analyze, export и т.д.)
        details: Дополнительные детали
    """
    message = f"USER:{username} | ACTION:{action}"
    if details:
        message += f" | DETAILS:{details}"
    logger.info(message)

def log_error(username: str, action: str, error: str):
    """
    Логировать ошибку.

    Args:
        username: Имя пользователя
        action: Действие, при котором произошла ошибка
        error: Описание ошибки
    """
    message = f"USER:{username} | ACTION:{action} | ERROR:{error}"
    logger.error(message)

def get_logs(log_type: str = "app", limit: int = 100) -> list:
    """
    Получить последние записи из лога.

    Args:
        log_type: Тип лога ("app" или "error")
        limit: Количество записей

    Returns:
        Список записей лога
    """
    if log_type == "app":
        log_file = LOGS_DIR / "app.log"
    elif log_type == "error":
        log_file = LOGS_DIR / "error.log"
    else:
        return []

    try:
        if not log_file.exists():
            return []

        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Вернуть последние limit строк
        return [line.strip() for line in lines[-limit:]]
    except IOError:
        return []
