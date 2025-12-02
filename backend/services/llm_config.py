from pathlib import Path
from typing import Dict
from backend.config import DATA_DIR
from backend.services.json_utils import read_json, write_json, update_json

LLM_CONFIG_FILE = DATA_DIR / "llm_config.json"

DEFAULT_CONFIG = {
    "llm_type": "deepseek",
    "deepseek_api_key": "",
    "deepseek_base_url": "https://api.deepseek.com",
    "lmstudio_base_url": "http://localhost:1234/v1",
    "lmstudio_model": "deepseek-coder"
}

def get_llm_config() -> Dict:
    """
    Получить текущую конфигурацию LLM.

    Returns:
        Словарь с настройками LLM
    """
    return read_json(LLM_CONFIG_FILE, DEFAULT_CONFIG.copy())

def update_llm_config(updates: Dict) -> bool:
    """
    Обновить конфигурацию LLM.

    Args:
        updates: Словарь с обновлениями

    Returns:
        True если обновление успешно
    """
    return update_json(LLM_CONFIG_FILE, updates, DEFAULT_CONFIG.copy())

def get_current_llm_type() -> str:
    """
    Получить текущий тип LLM.

    Returns:
        "deepseek" или "lmstudio"
    """
    config = get_llm_config()
    return config.get("llm_type", "deepseek")
