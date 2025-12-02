import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from backend.services.settings import get_settings

class RequestQueue:
    """
    Менеджер очереди запросов на анализ договоров.
  
    Ограничения:
    - Максимум одновременных обработок: настраивается (по умолчанию 5)
    - Максимум в очереди ожидания: настраивается (по умолчанию 5)
    """
  
    def __init__(self):
        self._active_count = 0
        self._queue_count = 0
        self._lock = asyncio.Lock()
  
    async def acquire(self) -> Dict[str, Any]:
        """
        Попытаться получить слот для обработки.
    
        Returns:
            Словарь с результатом:
            - {"allowed": True} - можно обрабатывать сразу
            - {"allowed": True, "queued": True} - добавлено в очередь
            - {"allowed": False, "error": "..."} - отклонено
        """
        settings = get_settings()
        max_concurrent = settings.get("max_concurrent_requests", 5)
        max_queue = settings.get("max_queue_size", 5)
    
        async with self._lock:
            # Проверить, можно ли обработать сразу
            if self._active_count < max_concurrent:
                self._active_count += 1
                return {"allowed": True, "queued": False}
        
            # Проверить, можно ли добавить в очередь
            if self._queue_count < max_queue:
                self._queue_count += 1
                return {"allowed": True, "queued": True, "message": "Идет обработка запросов других пользователей. Ваш запрос в очереди."}
        
            # Очередь переполнена
            return {
                "allowed": False, 
                "error": "Система перегружена. Попробуйте позже (через 1-2 минуты)."
            }
  
    async def wait_for_slot(self) -> bool:
        """
        Ожидать освобождения слота (для запросов в очереди).
    
        Returns:
            True когда слот освободился
        """
        settings = get_settings()
        max_concurrent = settings.get("max_concurrent_requests", 5)
    
        # Ожидать с интервалом проверки
        while True:
            async with self._lock:
                if self._active_count < max_concurrent:
                    # Слот освободился, занимаем его
                    self._queue_count -= 1
                    self._active_count += 1
                    return True
        
            # Ждем перед следующей проверкой
            await asyncio.sleep(1)
  
    async def release(self):
        """
        Освободить слот после завершения обработки.
        """
        async with self._lock:
            if self._active_count > 0:
                self._active_count -= 1
  
    def get_status(self) -> Dict[str, int]:
        """
        Получить текущий статус очереди.
    
        Returns:
            Словарь с количеством активных и ожидающих запросов
        """
        return {
            "active": self._active_count,
            "queued": self._queue_count
        }

# Глобальный экземпляр очереди
request_queue = RequestQueue()

