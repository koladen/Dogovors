from typing import Optional, Tuple
import asyncio
from openai import AsyncOpenAI
from backend.services.llm_config import get_llm_config, get_current_llm_type
from backend.services.prompts import get_prompt
from backend.services.tokens import track_tokens
from backend.services.logger import log_error

async def analyze_contract(text: str, analysis_type: str, username: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Анализировать договор через LLM.

    Args:
        text: Текст договора
        analysis_type: Тип анализа ("summary" или "legal_check")
        username: Имя пользователя (для учета токенов)

    Returns:
        Кортеж (результат, ошибка)
    """
    # Получить промпт
    prompt = get_prompt(analysis_type)
    if not prompt:
        return None, "Промпт не найден"

    # Определить тип LLM
    llm_type = get_current_llm_type()

    if llm_type == "deepseek":
        return await call_deepseek_api(prompt, text, username)
    elif llm_type == "lmstudio":
        return await call_lmstudio_api(prompt, text, username)
    else:
        return None, f"Неизвестный тип LLM: {llm_type}"

async def call_deepseek_api(prompt: str, text: str, username: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Вызвать DeepSeek API.

    Args:
        prompt: Системный промпт
        text: Текст договора
        username: Имя пользователя

    Returns:
        Кортеж (результат, ошибка)
    """
    try:
        from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
        config = get_llm_config()
        api_key = DEEPSEEK_API_KEY or config.get("deepseek_api_key", "")
        base_url = DEEPSEEK_BASE_URL or config.get("deepseek_base_url", "https://api.deepseek.com")

        if not api_key:
            return None, "API ключ DeepSeek не настроен"

        # Создать асинхронный клиент OpenAI (совместимость с DeepSeek)
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=60.0
        )

        # Формирование запроса
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Проанализируйте следующий договор:\n\n{text}"}
        ]

        # Вызов API асинхронно
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7,
            max_tokens=4000
        )

        # Извлечение результата
        result = response.choices[0].message.content

        # Учет токенов
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        track_tokens(username, prompt_tokens, completion_tokens)

        return result, None

    except Exception as e:
        error_msg = f"Ошибка при обращении к DeepSeek API: {str(e)}"
        log_error(username, "deepseek_api_call", error_msg)
        return None, error_msg

async def call_lmstudio_api(prompt: str, text: str, username: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Вызвать LM Studio API.

    Args:
        prompt: Системный промпт
        text: Текст договора
        username: Имя пользователя (токены не учитываются для локальной LLM)

    Returns:
        Кортеж (результат, ошибка)
    """
    try:
        config = get_llm_config()
        base_url = config.get("lmstudio_base_url", "http://localhost:1234/v1")
        model = config.get("lmstudio_model", "deepseek-coder")

        # Создать асинхронный клиент OpenAI (совместимость с LM Studio)
        client = AsyncOpenAI(
            api_key="not-needed",  # LM Studio не требует ключ
            base_url=base_url,
            timeout=180.0  # Увеличенный таймаут для локальной обработки
        )

        # Формирование запроса
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Проанализируйте следующий договор:\n\n{text}"}
        ]

        # Вызов API асинхронно
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4000
        )

        # Извлечение результата
        result = response.choices[0].message.content

        # Примечание: токены НЕ учитываются для локальной LLM

        return result, None

    except Exception as e:
        error_msg = f"Ошибка при обращении к LM Studio: {str(e)}"
        log_error(username, "lmstudio_api_call", error_msg)

        # Дополнительная информация для пользователя
        if "Connection" in str(e) or "refused" in str(e):
            error_msg += "\n\nУбедитесь, что LM Studio запущен и сервер активен."

        return None, error_msg
