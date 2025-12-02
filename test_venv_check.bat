@echo off
if not exist "test_venv\" (
    echo ERROR: Virtual environment not found
    exit /b 1
) else (
    echo OK: Virtual environment found
)
