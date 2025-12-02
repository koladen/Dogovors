from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from backend.services.auth import get_user_by_ip

def get_client_ip(request: Request) -> str:
    """
    Получить реальный IP-адрес клиента.
  
    Args:
        request: FastAPI Request объект
  
    Returns:
        IP-адрес клиента
    """
    # Проверка заголовков прокси
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Берем первый IP из списка
        return forwarded_for.split(",")[0].strip()
  
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
  
    # Fallback на прямое подключение
    return request.client.host

async def require_auth(request: Request) -> dict:
    """
    Middleware для проверки авторизации по IP.
  
    Args:
        request: FastAPI Request объект
  
    Returns:
        Словарь с данными пользователя
  
    Raises:
        HTTPException: Если пользователь не авторизован
    """
    ip = get_client_ip(request)
    user = get_user_by_ip(ip)
  
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация. IP не авторизован."
        )
  
    return user

async def require_admin(request: Request) -> dict:
    """
    Middleware для проверки прав администратора.
  
    Args:
        request: FastAPI Request объект
  
    Returns:
        Словарь с данными пользователя
  
    Raises:
        HTTPException: Если пользователь не администратор
    """
    user = await require_auth(request)
  
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуются права администратора."
        )
  
    return user

