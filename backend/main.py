from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from pathlib import Path

# Создание приложения
app = FastAPI(
    title="Анализатор договоров",
    description="Локальный сервис анализа договоров через AI",
    version="1.0.0"
)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

