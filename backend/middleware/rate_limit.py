from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from backend.services.settings import get_settings

# Создать limiter с функцией получения IP
limiter = Limiter(key_func=get_remote_address)

def get_rate_limit_string() -> str:
    """
    Получить строку лимита из настроек.
  
    Returns:
        Строка вида "10/minute"
    """
    settings = get_settings()
    limit = settings.get("rate_limit_per_minute", 10)
    return f"{limit}/minute"

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Обработчик превышения лимита запросов.
  
    Args:
        request: FastAPI Request объект
        exc: Исключение RateLimitExceeded
  
    Returns:
        JSONResponse с сообщением об ошибке
    """
    # Извлечь время до сброса из заголовка
    retry_after = exc.detail.split("retry after ")[1] if "retry after" in exc.detail else "60"
  
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": f"Превышен лимит запросов (10 анализов в минуту). Повторите через {retry_after} секунд."
        }
    )

