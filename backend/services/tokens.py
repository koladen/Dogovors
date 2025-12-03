from datetime import datetime
from typing import Dict
from backend.config import DATA_DIR
from backend.services.json_utils import read_json, write_json

TOKENS_FILE = DATA_DIR / "tokens_usage.json"

# Тарифы DeepSeek (на декабрь 2025)
PROMPT_TOKEN_COST = 0.0014 / 1000  # $0.0014 за 1K токенов
COMPLETION_TOKEN_COST = 0.0028 / 1000  # $0.0028 за 1K токенов

DEFAULT_STATS = {
    "total_prompt_tokens": 0,
    "total_completion_tokens": 0,
    "total_cost_usd": 0.0,
    "users": {},
    "last_updated": ""
}

def get_tokens_stats() -> Dict:
    """
    Получить статистику использования токенов.

    Returns:
        Словарь со статистикой
    """
    return read_json(TOKENS_FILE, DEFAULT_STATS.copy())

def track_tokens(username: str, prompt_tokens: int, completion_tokens: int):
    """
    Учесть использование токенов пользователем.

    Args:
        username: Имя пользователя
        prompt_tokens: Количество токенов в промпте
        completion_tokens: Количество токенов в ответе
    """
    stats = get_tokens_stats()

    # Рассчитать стоимость
    cost = (prompt_tokens * PROMPT_TOKEN_COST) + (completion_tokens * COMPLETION_TOKEN_COST)

    # Обновить общую статистику
    stats["total_prompt_tokens"] += prompt_tokens
    stats["total_completion_tokens"] += completion_tokens
    stats["total_cost_usd"] += cost
    stats["last_updated"] = datetime.now().isoformat()

    # Обновить статистику пользователя
    if username not in stats["users"]:
        stats["users"][username] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "requests_count": 0,
            "cost_usd": 0.0
        }

    user_stats = stats["users"][username]
    user_stats["prompt_tokens"] += prompt_tokens
    user_stats["completion_tokens"] += completion_tokens
    user_stats["requests_count"] += 1
    user_stats["cost_usd"] += cost
    user_stats["last_used"] = datetime.now().isoformat()

    write_json(TOKENS_FILE, stats)

def format_stats_for_display(stats: Dict) -> Dict:
    """
    Отформатировать статистику для отображения.

    Args:
        stats: Сырая статистика

    Returns:
        Отформатированная статистика
    """
    formatted_users = {}
    for username, user_stats in stats.get("users", {}).items():
        formatted_users[username] = {
            "prompt_tokens": user_stats["prompt_tokens"],
            "completion_tokens": user_stats["completion_tokens"],
            "requests_count": user_stats["requests_count"],
            "cost_usd": round(user_stats["cost_usd"], 4),
            "last_used": user_stats.get("last_used", "")
        }

    return {
        "total_prompt_tokens": stats.get("total_prompt_tokens", 0),
        "total_completion_tokens": stats.get("total_completion_tokens", 0),
        "total_cost_usd": round(stats.get("total_cost_usd", 0.0), 4),
        "users": formatted_users,
        "last_updated": stats.get("last_updated", "")
    }
