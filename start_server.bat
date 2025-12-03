@echo off
echo ========================================
echo Запуск сервера "Анализатор договоров"
echo ========================================

cd /d "%~dp0"

if not exist "venv\" (
    echo Виртуальное окружение не найдено!
    echo Сначала создайте окружение: python -m venv venv
    echo Затем установите зависимости: venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

call venv\Scripts\activate

echo Запуск сервера на http://0.0.0.0:8000 с 4 рабочими процессами
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4 --reload

pause
