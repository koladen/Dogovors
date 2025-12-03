import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from backend.middleware.auth import require_auth, require_admin
from backend.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.services.document import extract_text_from_file, check_text_size, create_word_document
from backend.services.llm import analyze_contract
from backend.services.queue import request_queue
from backend.models.schemas import AnalyzeResponse, ExportRequest
from backend.services.logger import log_user_action, log_error
from backend.services.settings import get_max_file_size_bytes
from backend.services.users import get_all_users, create_user, update_user, delete_user
from backend.models.schemas import UserCreate, UserUpdate
from backend.services.prompts import get_all_prompts, save_prompt, reset_prompt
from backend.models.schemas import PromptSaveRequest, PromptResetRequest
from backend.services.llm_config import get_llm_config, update_llm_config
from backend.models.schemas import LLMConfigUpdate
from backend.services.settings import get_settings, update_settings
from backend.services.tokens import get_tokens_stats, format_stats_for_display
from backend.services.logger import get_logs
from backend.models.schemas import SettingsUpdate
import tempfile
from pathlib import Path

# Создание приложения
app = FastAPI(
    title="Анализатор договоров",
    description="Локальный сервис анализа договоров через AI",
    version="1.0.0"
)

# Подключить Rate Limiter к приложению
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS для локальной сети
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Статические файлы (frontend)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# ===== РОУТИНГ СТРАНИЦ =====

@app.get("/")
async def root():
    """
    Главная страница - редирект на страницу авторизации.
    """
    return RedirectResponse(url="/static/login.html")

@app.get("/login")
async def login_page():
    """
    Страница авторизации.
    """
    return FileResponse(FRONTEND_DIR / "login.html")

@app.get("/app")
async def app_page():
    """
    Главная страница приложения (для авторизованных).
    """
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/admin")
async def admin_page():
    """
    Админ-панель.
    """
    return FileResponse(FRONTEND_DIR / "admin.html")

@app.get("/health")
async def health_check():
    """
    Проверка здоровья сервиса.
    """
    return {"status": "healthy"}

@app.get("/api/status")
async def api_status():
    """
    Статус API для проверки.
    """
    return {
        "status": "ok",
        "message": "Анализатор договоров запущен",
        "version": "1.0.0"
    }

# ===== АВТОРИЗАЦИЯ =====

from backend.middleware.auth import get_client_ip
from backend.services.auth import get_user_by_ip
from backend.models.schemas import AuthCheckResponse

@app.get("/api/check-auth", response_model=AuthCheckResponse)
async def check_auth(request: Request):
    """
    Проверить авторизацию по IP-адресу.
    """
    ip = get_client_ip(request)
    user = get_user_by_ip(ip)

    if user:
        return AuthCheckResponse(
            authorized=True,
            username=user["username"],
            role=user["role"],
            ip=ip
        )
    else:
        return AuthCheckResponse(
            authorized=False,
            ip=ip
        )

from backend.services.users import verify_credentials
from backend.services.auth import authorize_ip
from backend.services.logger import log_user_action
from backend.models.schemas import LoginRequest, LoginResponse

@app.post("/api/login", response_model=LoginResponse)
async def login(request: Request, credentials: LoginRequest):
    """
    Авторизовать пользователя по логину/паролю и сохранить IP.
    """
    ip = get_client_ip(request)

    # Проверить учетные данные
    user = verify_credentials(credentials.username, credentials.password)

    if user:
        # Авторизовать IP
        authorize_ip(ip, user["username"])

        # Логировать успешный вход
        log_user_action(user["username"], "login", f"IP: {ip}")

        return LoginResponse(
            success=True,
            message="Авторизация успешна",
            ip=ip
        )
    else:
        return LoginResponse(
            success=False,
            message="Неверный логин или пароль"
        )

from backend.services.auth import remove_ip_authorization

@app.post("/api/logout")
async def logout(request: Request):
    """
    Выход пользователя - удалить авторизацию IP-адреса.
    """
    ip = get_client_ip(request)

    # Получить пользователя перед удалением авторизации для логирования
    user = get_user_by_ip(ip)

    if user:
        # Удалить авторизацию IP
        success = remove_ip_authorization(ip)

        if success:
            # Логировать выход
            log_user_action(user["username"], "logout", f"IP: {ip}")
            return {"success": True, "message": "Выход выполнен успешно"}
        else:
            return {"success": False, "error": "Ошибка при выходе"}
    else:
        # IP не был авторизован
        return {"success": True, "message": "IP не был авторизован"}

# ===== АДМИН-ПАНЕЛЬ - УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ =====

@app.get("/api/admin/users")
async def admin_get_users(user: dict = Depends(require_admin)):
    """
    Получить список всех пользователей (только для admin).
    """
    users = get_all_users()
    return {"success": True, "users": users}

@app.post("/api/admin/users")
async def admin_create_user(
    user_data: UserCreate,
    user: dict = Depends(require_admin)
):
    """
    Создать нового пользователя (только для admin).
    """
    success = create_user(
        username=user_data.username,
        password=user_data.password,
        role=user_data.role
    )

    if success:
        log_user_action(user["username"], "create_user", f"Создан пользователь: {user_data.username}")
        return {
            "success": True,
            "message": "Пользователь создан",
            "username": user_data.username
        }
    else:
        return {
            "success": False,
            "error": "Пользователь с таким логином уже существует"
        }

@app.put("/api/admin/users/{username}")
async def admin_update_user(
    username: str,
    user_data: UserUpdate,
    user: dict = Depends(require_admin)
):
    """
    Обновить данные пользователя (только для admin).
    """
    success = update_user(
        username=username,
        password=user_data.password,
        role=user_data.role
    )

    if success:
        log_user_action(user["username"], "update_user", f"Обновлен пользователь: {username}")
        return {
            "success": True,
            "message": "Пользователь обновлен"
        }
    else:
        return {
            "success": False,
            "error": "Пользователь не найден"
        }

@app.delete("/api/admin/users/{username}")
async def admin_delete_user(
    username: str,
    user: dict = Depends(require_admin)
):
    """
    Удалить пользователя (только для admin).
    """
    # Проверить, что пользователь не пытается удалить самого себя
    if username == user["username"]:
        return {
            "success": False,
            "error": "Невозможно удалить собственный аккаунт"
        }

    success, message = delete_user(username)

    if success:
        log_user_action(user["username"], "delete_user", f"Удален пользователь: {username}")
        return {
            "success": True,
            "message": message
        }
    else:
        return {
            "success": False,
            "error": message
        }

# ===== АДМИН-ПАНЕЛЬ - ПРОМПТЫ =====

@app.get("/api/admin/prompts")
async def admin_get_prompts(user: dict = Depends(require_admin)):
    """
    Получить текущие промпты (только для admin).
    """
    prompts = get_all_prompts()
    return {"success": True, "prompts": prompts}

@app.post("/api/admin/prompts")
async def admin_save_prompt(
    data: PromptSaveRequest,
    user: dict = Depends(require_admin)
):
    """
    Сохранить отредактированный промпт (только для admin).
    """
    success = save_prompt(data.prompt_type, data.content)

    if success:
        log_user_action(user["username"], "save_prompt", f"Тип: {data.prompt_type}")
        return {"success": True, "message": "Промпт успешно сохранён"}
    else:
        return {"success": False, "error": "Ошибка при сохранении промпта"}

@app.post("/api/admin/prompts/reset")
async def admin_reset_prompt(
    data: PromptResetRequest,
    user: dict = Depends(require_admin)
):
    """
    Сбросить промпт к исходному значению (только для admin).
    """
    content = reset_prompt(data.prompt_type)

    if content:
        log_user_action(user["username"], "reset_prompt", f"Тип: {data.prompt_type}")
        return {
            "success": True,
            "message": "Промпт сброшен к исходному значению",
            "content": content
        }
    else:
        return {"success": False, "error": "Ошибка при сбросе промпта"}

# ===== АНАЛИЗ ДОКУМЕНТОВ =====

@app.post("/api/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")  # Rate limiting: 10 запросов в минуту
async def analyze_document(
    request: Request,
    file: UploadFile = File(...),
    analysis_type: str = Form(...),
    user: dict = Depends(require_auth)
):
    """
    Анализировать загруженный договор.

    Включает:
    - Rate Limiting: 10 запросов в минуту
    - Очередь: до 5 одновременных обработок + 5 в очереди
    """
    username = user["username"]

    # ===== ПРОВЕРКА ОЧЕРЕДИ =====
    queue_result = await request_queue.acquire()

    if not queue_result["allowed"]:
        # Очередь переполнена
        return AnalyzeResponse(
            success=False,
            error=queue_result.get("error", "Система перегружена. Попробуйте позже.")
        )

    if queue_result.get("queued"):
        # Запрос в очереди - ждем слот
        await request_queue.wait_for_slot()

    try:
        # ===== ВАЛИДАЦИЯ ФАЙЛА =====

        # Проверка расширения файла
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in [".doc", ".docx", ".pdf"]:
            return AnalyzeResponse(
                success=False,
                error="Неподдерживаемый формат файла. Допустимы: .doc, .docx, .pdf"
            )

        # Проверка размера файла
        max_size = get_max_file_size_bytes()
        file_content = await file.read()
        if len(file_content) > max_size:
            max_size_mb = max_size // (1024 * 1024)
            return AnalyzeResponse(
                success=False,
                error=f"Размер файла превышает допустимый лимит ({max_size_mb} МБ)."
            )

        # ===== ОБРАБОТКА ФАЙЛА =====

        # Сохранить во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = Path(tmp_file.name)

        try:
            # Извлечь текст
            text, error = extract_text_from_file(tmp_path, file_extension)

            if error:
                log_error(username, "document_extract", error)
                return AnalyzeResponse(success=False, error=error)

            # Проверить размер текста
            size_ok, size_error = check_text_size(text)
            if not size_ok:
                log_error(username, "document_size_check", size_error)
                return AnalyzeResponse(success=False, error=size_error)

            # ===== АНАЛИЗ ЧЕРЕЗ LLM =====

            result, llm_error = await analyze_contract(text, analysis_type, username)

            if llm_error:
                log_error(username, "llm_analyze", llm_error)
                return AnalyzeResponse(success=False, error=llm_error)

            # Логировать успешный анализ
            log_user_action(username, "analyze", f"{file.filename} ({analysis_type})")

            return AnalyzeResponse(
                success=True,
                analysis_type=analysis_type,
                result=result,
                filename=file.filename
            )

        finally:
            # Удалить временный файл
            if tmp_path.exists():
                tmp_path.unlink()

    except Exception as e:
        error_msg = f"Произошла ошибка при обработке файла: {str(e)}"
        log_error(username, "analyze_unexpected", error_msg)
        return AnalyzeResponse(success=False, error=error_msg)

    finally:
        # ===== ОСВОБОЖДЕНИЕ СЛОТА В ОЧЕРЕДИ =====
        await request_queue.release()

# ===== ЭКСПОРТ В WORD =====

@app.post("/api/export")
async def export_to_word(
    data: ExportRequest,
    user: dict = Depends(require_auth)
):
    """
    Экспортировать результат анализа в Word документ.
    """
    try:
        # Создать Word документ
        doc_io = create_word_document(data.content, data.filename)

        # Логировать экспорт
        log_user_action(user["username"], "export", f"Файл: {data.filename}.docx")

        # Вернуть файл
        return StreamingResponse(
            doc_io,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{data.filename}.docx"'
            }
        )
    except Exception as e:
        error_msg = f"Ошибка при создании документа: {str(e)}"
        log_error(user["username"], "export", error_msg)
        return {"success": False, "error": error_msg}

# ===== АДМИН-ПАНЕЛЬ - НАСТРОЙКИ LLM =====

@app.get("/api/admin/llm-config")
async def admin_get_llm_config(user: dict = Depends(require_admin)):
    """
    Получить настройки LLM (только для admin).
    """
    config = get_llm_config()
    return {"success": True, "config": config}

@app.post("/api/admin/llm-config")
async def admin_update_llm_config(
    data: LLMConfigUpdate,
    user: dict = Depends(require_admin)
):
    """
    Обновить настройки LLM (только для admin).
    """
    updates = data.dict(exclude_unset=True)
    success = update_llm_config(updates)

    if success:
        log_user_action(user["username"], "update_llm_config", f"Обновлено полей: {len(updates)}")
        return {"success": True, "message": "Настройки LLM обновлены"}
    else:
        return {"success": False, "error": "Ошибка при обновлении настроек"}

# ===== АДМИН-ПАНЕЛЬ - НАСТРОЙКИ СИСТЕМЫ =====

@app.get("/api/admin/settings")
async def admin_get_settings(user: dict = Depends(require_admin)):
    """
    Получить настройки системы (только для admin).
    """
    settings = get_settings()
    return {"success": True, "settings": settings}

@app.post("/api/admin/settings")
async def admin_update_settings(
    data: SettingsUpdate,
    user: dict = Depends(require_admin)
):
    """
    Обновить настройки системы (только для admin).
    """
    updates = data.dict(exclude_unset=True)
    success = update_settings(updates)

    if success:
        log_user_action(user["username"], "update_settings", f"Обновлено полей: {len(updates)}")
        return {"success": True, "message": "Настройки обновлены"}
    else:
        return {"success": False, "error": "Ошибка при обновлении настроек"}

@app.get("/api/admin/tokens-stats")
async def admin_get_tokens_stats(user: dict = Depends(require_admin)):
    """
    Получить статистику использования токенов (только для admin).
    """
    stats = get_tokens_stats()
    formatted_stats = format_stats_for_display(stats)
    return {"success": True, "stats": formatted_stats}

@app.get("/api/admin/logs")
async def admin_get_logs(
    type: str = "app",
    limit: int = 100,
    user: dict = Depends(require_admin)
):
    """
    Получить логи системы (только для admin).
    """
    logs = get_logs(type, limit)
    return {"success": True, "logs": logs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

