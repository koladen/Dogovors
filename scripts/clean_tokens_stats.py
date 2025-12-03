#!/usr/bin/env python3
"""
Скрипт для очистки статистики токенов от некорректных пользователей.
"""

import json
import os
from pathlib import Path

# Путь к файлу статистики токенов
DATA_DIR = Path(__file__).parent.parent / "data"
TOKENS_FILE = DATA_DIR / "tokens_usage.json"

def clean_tokens_stats():
    """Очистить статистику токенов от некорректных пользователей."""

    if not TOKENS_FILE.exists():
        print("Файл статистики токенов не найден")
        return

    # Загрузить данные
    with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
        stats = json.load(f)

    # Список корректных пользователей (проверка по users.json)
    valid_users = ["admin", "vim"]  # Только реальные пользователи из users.json

    # Очистить статистику пользователей
    cleaned_users = {}
    removed_users = []

    for username, user_stats in stats.get("users", {}).items():
        # Исправить имя пользователя vit -> vim
        corrected_username = "vim" if username == "vit" else username

        if corrected_username in valid_users:
            # Обновить last_used для пользователей с пустой датой
            if not user_stats.get("last_used"):
                # Устанавливаем дату создания файла как приблизительную дату
                user_stats["last_used"] = stats.get("last_updated", "")

            # Если имя было исправлено, объединить статистику
            if corrected_username in cleaned_users:
                existing_stats = cleaned_users[corrected_username]
                existing_stats["prompt_tokens"] += user_stats["prompt_tokens"]
                existing_stats["completion_tokens"] += user_stats["completion_tokens"]
                existing_stats["requests_count"] += user_stats["requests_count"]
                existing_stats["cost_usd"] += user_stats["cost_usd"]
                # Оставить более позднюю дату
                if user_stats["last_used"] > existing_stats["last_used"]:
                    existing_stats["last_used"] = user_stats["last_used"]
            else:
                cleaned_users[corrected_username] = user_stats
        else:
            removed_users.append(username)
            # Вычесть статистику удаленного пользователя из общих данных
            stats["total_prompt_tokens"] -= user_stats["prompt_tokens"]
            stats["total_completion_tokens"] -= user_stats["completion_tokens"]
            stats["total_cost_usd"] -= user_stats["cost_usd"]

    stats["users"] = cleaned_users

    # Сохранить очищенные данные
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"Удалены пользователи: {', '.join(removed_users)}")
    print(f"Оставлены пользователи: {', '.join(cleaned_users.keys())}")
    print("Статистика токенов очищена")

if __name__ == "__main__":
    clean_tokens_stats()
