from pathlib import Path
from typing import Dict, Optional
from backend.config import PROMPTS_DIR, DEFAULTS_DIR

def get_prompt(prompt_type: str) -> Optional[str]:
    """
    Получить текущий промпт.

    Args:
        prompt_type: Тип промпта ("summary" или "legal_check")

    Returns:
        Текст промпта или None
    """
    if prompt_type == "summary":
        file_path = PROMPTS_DIR / "summary_prompt.txt"
    elif prompt_type == "legal_check":
        file_path = PROMPTS_DIR / "legal_check_prompt.txt"
    elif prompt_type == "meeting_protocol":
        file_path = PROMPTS_DIR / "meeting_protocol_prompt.txt"
    else:
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except IOError:
        return None

def get_all_prompts() -> Dict[str, str]:
    """
    Получить все промпты.

    Returns:
        Словарь с промптами {"summary": "...", "legal_check": "..."}
    """
    return {
        "summary": get_prompt("summary") or "",
        "legal_check": get_prompt("legal_check") or "",
        "meeting_protocol": get_prompt("meeting_protocol") or ""
    }

def save_prompt(prompt_type: str, content: str) -> bool:
    """
    Сохранить промпт.

    Args:
        prompt_type: Тип промпта ("summary" или "legal_check")
        content: Новый текст промпта

    Returns:
        True если сохранение успешно
    """
    if prompt_type == "summary":
        file_path = PROMPTS_DIR / "summary_prompt.txt"
    elif prompt_type == "legal_check":
        file_path = PROMPTS_DIR / "legal_check_prompt.txt"
    elif prompt_type == "meeting_protocol":
        file_path = PROMPTS_DIR / "meeting_protocol_prompt.txt"
    else:
        return False

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except IOError:
        return False

def reset_prompt(prompt_type: str) -> Optional[str]:
    """
    Сбросить промпт к исходному значению из defaults.

    Args:
        prompt_type: Тип промпта ("summary" или "legal_check")

    Returns:
        Новый текст промпта или None
    """
    if prompt_type == "summary":
        default_file = DEFAULTS_DIR / "summary_prompt.txt"
        current_file = PROMPTS_DIR / "summary_prompt.txt"
    elif prompt_type == "legal_check":
        default_file = DEFAULTS_DIR / "legal_check_prompt.txt"
        current_file = PROMPTS_DIR / "legal_check_prompt.txt"
    elif prompt_type == "meeting_protocol":
        default_file = DEFAULTS_DIR / "meeting_protocol_prompt.txt"
        current_file = PROMPTS_DIR / "meeting_protocol_prompt.txt"
    else:
        return None

    try:
        # Читаем дефолтный промпт
        with open(default_file, "r", encoding="utf-8") as f:
            default_content = f.read()

        # Записываем в текущий
        with open(current_file, "w", encoding="utf-8") as f:
            f.write(default_content)

        return default_content
    except IOError:
        return None
