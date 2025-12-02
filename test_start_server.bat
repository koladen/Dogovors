@echo off
echo ========================================
echo Запуск сервера "Анализатор договоров"
echo ========================================

cd /d "%~dp0"

if not exist "test_venv\" (
    echo Виртуальное окружение не найдено!
    echo Сначала создайте окружение: python -m venv venv
    echo Затем установите зависимости: venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

call test_venv\Scripts\activate

echo Запуск сервера на http://0.0.0.0:8000
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
