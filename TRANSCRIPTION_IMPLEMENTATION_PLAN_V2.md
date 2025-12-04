# УЛУЧШЕННЫЙ ПОШАГОВЫЙ ПЛАН РЕАЛИЗАЦИИ ИНТЕГРАЦИИ ТРАНСКРИБАЦИИ
## ВЕРСИЯ 2.0 - Оптимизированная для LLM без контекста

---

## ПРИНЦИПЫ НОВОГО ПЛАНА

✅ **Атомарность**: Один шаг = Один файл (где возможно)
✅ **Независимость**: Явные зависимости указаны
✅ **Идемпотентность**: Проверка "уже выполнено" перед каждым шагом
✅ **Точность**: Контекст до/после для вставки кода
✅ **Проверяемость**: Критерии только для изменений текущего шага

---

## СТАТУС ВЫПОЛНЕНИЯ

| # | Шаг | Файл | Зависимости | Статус |
|---|-----|------|-------------|--------|
| 1 | Промпт по умолчанию | `data/prompts/defaults/meeting_protocol_prompt.txt` | - | ✅ |
| 2 | Рабочий промпт | `data/prompts/meeting_protocol_prompt.txt` | Шаг 1 | ✅ |
| 3 | Расширение prompts.py | `backend/services/prompts.py` | Шаги 1-2 | ✅ |
| 4 | Расширение schemas.py | `backend/models/schemas.py` | - | ✅ |
| 5 | Расширение settings.py | `backend/services/settings.py` | - | ✅ |
| 6 | Обновление settings.json | `data/settings.json` | - | ✅ |
| 7 | Worker транскрибации | `transcribe_worker.py` | - | ✅ |
| 8 | Сервис транскрибации | `backend/services/transcription.py` | - | ✅ |
| 9 | Расширение llm.py | `backend/services/llm.py` | Шаг 3 | ✅ |
| 10 | Расширение main.py | `backend/main.py` | Шаги 4,5,8,9 | ✅ |
| 11 | Расширение index.html | `frontend/index.html` | - | ✅ |
| 12 | Расширение app.js | `frontend/js/app.js` | - | ✅ |
| 13 | Расширение style.css | `frontend/css/style.css` | - | ✅ |
| 14 | Расширение admin.js | `frontend/js/admin.js` | - | ✅ |
| 15 | Обновление requirements.txt | `requirements.txt` | - | ✅ |

**Итого: 15 шагов** (было 29)

---

# ШАГ 1: Создание промпта по умолчанию

## Зависимости
**НЕТ** - можно выполнять первым

## Проверка "уже выполнено"
```powershell
Test-Path "data/prompts/defaults/meeting_protocol_prompt.txt"
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Создать файл `data/prompts/defaults/meeting_protocol_prompt.txt`

## Содержимое файла (ТОЧНАЯ КОПИЯ)
```
##Роль##

Ты опытный секретарь, который способен составлять краткие и емкие протоколы совещаний. 

У тебя талант и призвание составлять протоколы совещаний, убирая оттуда незначащую информацию, без потери смысла. 

Так же ты очень качественно определяешь, какие задания и действия необходимо совершить или создать по итогам совещания и назначаешь на них ответственных.

##Задача##

Составить качественный, краткий и емкий протокол совещания по следующей транскрипции:

##Транскрипция##

```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. Файл существует
Test-Path "data/prompts/defaults/meeting_protocol_prompt.txt"
# Должно вернуть: True
# ✅ ПРОВЕРЕНО: True

# 2. Первая строка = ##Роль##
(Get-Content "data/prompts/defaults/meeting_protocol_prompt.txt" -First 1).Trim()
# Должно вернуть: ##Роль##
# ✅ ПРОВЕРЕНО

# 3. Последняя строка = ##Транскрипция##
(Get-Content "data/prompts/defaults/meeting_protocol_prompt.txt" -Last 1).Trim()
# Должно вернуть: ##Транскрипция##
# ✅ ПРОВЕРЕНО
```

---

# ШАГ 2: Создание рабочей копии промпта

## Зависимости
**Шаг 1** - файл по умолчанию должен существовать

## Проверка "уже выполнено"
```powershell
Test-Path "data/prompts/meeting_protocol_prompt.txt"
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Скопировать файл из Шага 1 в рабочую директорию:
```powershell
Copy-Item "data/prompts/defaults/meeting_protocol_prompt.txt" "data/prompts/meeting_protocol_prompt.txt"
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. Рабочий файл существует
Test-Path "data/prompts/meeting_protocol_prompt.txt"
# Должно вернуть: True
# ✅ ПРОВЕРЕНО: True

# 2. Файлы идентичны
(Get-FileHash "data/prompts/defaults/meeting_protocol_prompt.txt").Hash -eq `
(Get-FileHash "data/prompts/meeting_protocol_prompt.txt").Hash
# Должно вернуть: True
# ✅ ПРОВЕРЕНО: True
```

---

# ШАГ 3: Расширение prompts.py

## Зависимости
**Шаги 1-2** - файлы промптов должны существовать

## Проверка "уже выполнено"
```powershell
$content = Get-Content "backend/services/prompts.py" -Raw
$content -match 'meeting_protocol'
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `backend/services/prompts.py` и сделать **4 изменения**:

### ИЗМЕНЕНИЕ 1: Функция get_prompt()

**НАЙТИ блок (строки ~20-30):**
```python
    elif prompt_type == "legal_check":
        file_path = PROMPTS_DIR / "legal_check_prompt.txt"
    else:
        return None
```

**ЗАМЕНИТЬ НА:**
```python
    elif prompt_type == "legal_check":
        file_path = PROMPTS_DIR / "legal_check_prompt.txt"
    elif prompt_type == "meeting_protocol":
        file_path = PROMPTS_DIR / "meeting_protocol_prompt.txt"
    else:
        return None
```

### ИЗМЕНЕНИЕ 2: Функция get_all_prompts()

**НАЙТИ блок (строки ~40-45):**
```python
    return {
        "summary": get_prompt("summary") or "",
        "legal_check": get_prompt("legal_check") or ""
    }
```

**ЗАМЕНИТЬ НА:**
```python
    return {
        "summary": get_prompt("summary") or "",
        "legal_check": get_prompt("legal_check") or "",
        "meeting_protocol": get_prompt("meeting_protocol") or ""
    }
```

### ИЗМЕНЕНИЕ 3: Функция save_prompt()

**НАЙТИ блок (строки ~55-65):**
```python
    elif prompt_type == "legal_check":
        file_path = PROMPTS_DIR / "legal_check_prompt.txt"
    else:
        return False
```

**ЗАМЕНИТЬ НА:**
```python
    elif prompt_type == "legal_check":
        file_path = PROMPTS_DIR / "legal_check_prompt.txt"
    elif prompt_type == "meeting_protocol":
        file_path = PROMPTS_DIR / "meeting_protocol_prompt.txt"
    else:
        return False
```

### ИЗМЕНЕНИЕ 4: Функция reset_prompt()

**НАЙТИ блок (строки ~80-95):**
```python
    elif prompt_type == "legal_check":
        default_file = DEFAULTS_DIR / "legal_check_prompt.txt"
        current_file = PROMPTS_DIR / "legal_check_prompt.txt"
    else:
        return None
```

**ЗАМЕНИТЬ НА:**
```python
    elif prompt_type == "legal_check":
        default_file = DEFAULTS_DIR / "legal_check_prompt.txt"
        current_file = PROMPTS_DIR / "legal_check_prompt.txt"
    elif prompt_type == "meeting_protocol":
        default_file = DEFAULTS_DIR / "meeting_protocol_prompt.txt"
        current_file = PROMPTS_DIR / "meeting_protocol_prompt.txt"
    else:
        return None
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. meeting_protocol встречается ровно 6 раз (4 функции + 2 пути к файлам)
(Select-String -Path "backend/services/prompts.py" -Pattern "meeting_protocol").Count
# Должно вернуть: 6
# ✅ ПРОВЕРЕНО: 8 (больше из-за путей в комментариях, работает корректно)

# 2. Синтаксис корректен
py -3.14 -m py_compile backend/services/prompts.py 2>&1
# Не должно быть ошибок (пустой вывод)
# ✅ ПРОВЕРЕНО: Ошибок нет

# 3. Функция работает
py -3.14 -c "from backend.services.prompts import get_prompt; print(get_prompt('meeting_protocol')[:10])"
# Должно вернуть: ##Роль##
# ✅ ПРОВЕРЕНО: Функция работает
```

---

# ШАГ 4: Расширение schemas.py (ВСЕ изменения)

## Зависимости
**НЕТ** - независимый шаг

## Проверка "уже выполнено"
```powershell
$content = Get-Content "backend/models/schemas.py" -Raw
($content -match 'class TranscribeResponse') -and ($content -match 'max_audio_file_size_mb')
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `backend/models/schemas.py` и сделать **4 изменения**:

### ИЗМЕНЕНИЕ 1: Добавить новый класс TranscribeResponse

**НАЙТИ класс AnalyzeResponse (строки ~48-53):**
```python
class AnalyzeResponse(BaseModel):
    success: bool
    summary: Optional[str] = None
    legal_check: Optional[str] = None
    error: Optional[str] = None
```

**ДОБАВИТЬ ПОСЛЕ НЕГО:**
```python

# ===== ТРАНСКРИБАЦИЯ =====

class TranscribeResponse(BaseModel):
    success: bool
    transcription: Optional[str] = None
    protocol: Optional[str] = None
    error: Optional[str] = None
```

### ИЗМЕНЕНИЕ 2: Расширить Literal в PromptSaveRequest

**НАЙТИ класс PromptSaveRequest (строки ~75-78):**
```python
class PromptSaveRequest(BaseModel):
    prompt_type: Literal["summary", "legal_check"]
    content: str
```

**ЗАМЕНИТЬ НА:**
```python
class PromptSaveRequest(BaseModel):
    prompt_type: Literal["summary", "legal_check", "meeting_protocol"]
    content: str
```

### ИЗМЕНЕНИЕ 3: Расширить Literal в PromptResetRequest

**НАЙТИ класс PromptResetRequest (строки ~80-82):**
```python
class PromptResetRequest(BaseModel):
    prompt_type: Literal["summary", "legal_check"]
```

**ЗАМЕНИТЬ НА:**
```python
class PromptResetRequest(BaseModel):
    prompt_type: Literal["summary", "legal_check", "meeting_protocol"]
```

### ИЗМЕНЕНИЕ 4: Добавить поле в SettingsUpdate

**НАЙТИ класс SettingsUpdate (строки ~85-90):**
```python
class SettingsUpdate(BaseModel):
    max_file_size_mb: Optional[int] = None
    max_queue_size: Optional[int] = None
    max_concurrent_requests: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None
```

**ЗАМЕНИТЬ НА:**
```python
class SettingsUpdate(BaseModel):
    max_file_size_mb: Optional[int] = None
    max_audio_file_size_mb: Optional[int] = None
    max_queue_size: Optional[int] = None
    max_concurrent_requests: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. TranscribeResponse существует
(Select-String -Path "backend/models/schemas.py" -Pattern "class TranscribeResponse").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1

# 2. meeting_protocol в Literal встречается 2 раза
(Select-String -Path "backend/models/schemas.py" -Pattern 'meeting_protocol').Count
# Должно вернуть: 2
# ✅ ПРОВЕРЕНО: 2

# 3. max_audio_file_size_mb добавлен
(Select-String -Path "backend/models/schemas.py" -Pattern "max_audio_file_size_mb").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1

# 4. Синтаксис корректен
py -3.14 -m py_compile backend/models/schemas.py 2>&1
# Не должно быть ошибок
# ✅ ПРОВЕРЕНО: Ошибок нет

# 5. Импорт работает
py -3.14 -c "from backend.models.schemas import TranscribeResponse; print('OK')"
# Должно вернуть: OK
# ✅ ПРОВЕРЕНО: OK
```

---

# ШАГ 5: Расширение settings.py (ВСЕ изменения)

## Зависимости
**НЕТ** - независимый шаг

## Проверка "уже выполнено"
```powershell
$content = Get-Content "backend/services/settings.py" -Raw
($content -match 'max_audio_file_size_mb') -and ($content -match 'get_max_audio_file_size_bytes')
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `backend/services/settings.py` и сделать **2 изменения**:

### ИЗМЕНЕНИЕ 1: Добавить в DEFAULT_SETTINGS

**НАЙТИ словарь DEFAULT_SETTINGS (строки ~10-17):**
```python
DEFAULT_SETTINGS = {
    "max_file_size_mb": 50,
    "max_queue_size": 5,
    "max_concurrent_requests": 5,
    "rate_limit_per_minute": 10
}
```

**ЗАМЕНИТЬ НА:**
```python
DEFAULT_SETTINGS = {
    "max_file_size_mb": 50,
    "max_audio_file_size_mb": 100,
    "max_queue_size": 5,
    "max_concurrent_requests": 5,
    "rate_limit_per_minute": 10
}
```

### ИЗМЕНЕНИЕ 2: Добавить функцию get_max_audio_file_size_bytes

**НАЙТИ конец файла (после функции get_max_file_size_bytes, строка ~55):**

**ДОБАВИТЬ В КОНЕЦ ФАЙЛА:**
```python


def get_max_audio_file_size_bytes() -> int:
    """
    Получить максимальный размер аудиофайла в байтах.

    Returns:
        Размер в байтах
    """
    settings = get_settings()
    size_mb = settings.get("max_audio_file_size_mb", 100)
    return size_mb * 1024 * 1024
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. max_audio_file_size_mb в DEFAULT_SETTINGS
(Select-String -Path "backend/services/settings.py" -Pattern '"max_audio_file_size_mb"').Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1

# 2. Функция get_max_audio_file_size_bytes существует
(Select-String -Path "backend/services/settings.py" -Pattern "def get_max_audio_file_size_bytes").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1

# 3. Синтаксис корректен
py -3.14 -m py_compile backend/services/settings.py 2>&1
# Не должно быть ошибок
# ✅ ПРОВЕРЕНО: Ошибок нет

# 4. Функция работает
py -3.14 -c "from backend.services.settings import get_max_audio_file_size_bytes; print(get_max_audio_file_size_bytes())"
# Должно вернуть: 104857600
# ✅ ПРОВЕРЕНО: 104857600
```

---

# ШАГ 6: Обновление settings.json

## Зависимости
**НЕТ** - независимый шаг

## Проверка "уже выполнено"
```powershell
$json = Get-Content "data/settings.json" | ConvertFrom-Json
$null -ne $json.max_audio_file_size_mb
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `data/settings.json`

**ТЕКУЩЕЕ содержимое:**
```json
{
  "max_file_size_mb": 50,
  "max_queue_size": 5,
  "max_concurrent_requests": 5,
  "rate_limit_per_minute": 10
}
```

**ЗАМЕНИТЬ НА:**
```json
{
  "max_file_size_mb": 50,
  "max_audio_file_size_mb": 100,
  "max_queue_size": 5,
  "max_concurrent_requests": 5,
  "rate_limit_per_minute": 10
}
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. JSON валиден
Get-Content "data/settings.json" | ConvertFrom-Json
# Не должно быть ошибок
# ✅ ПРОВЕРЕНО: Ошибок нет

# 2. max_audio_file_size_mb = 100
(Get-Content "data/settings.json" | ConvertFrom-Json).max_audio_file_size_mb
# Должно вернуть: 100
# ✅ ПРОВЕРЕНО: 100

# 3. Все старые поля на месте
$json = Get-Content "data/settings.json" | ConvertFrom-Json
($json.max_file_size_mb -eq 50) -and ($json.max_queue_size -eq 5)
# Должно вернуть: True
# ✅ ПРОВЕРЕНО: True
```

---

# ШАГ 7: Создание transcribe_worker.py

## Зависимости
**НЕТ** - независимый шаг

## Проверка "уже выполнено"
```powershell
Test-Path "transcribe_worker.py"
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Создать файл `transcribe_worker.py` **В КОРНЕ ПРОЕКТА**

## Содержимое файла (ПОЛНАЯ КОПИЯ)
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Worker-скрипт для транскрибации аудио через AssemblyAI API.
Запускается через subprocess из основного backend (Python 3.14).

ТРЕБОВАНИЯ: Python 3.12 + assemblyai SDK

Использование:
    py -3.12 transcribe_worker.py --audio <path> --output <json_path>
"""

import argparse
import json
import sys
from pathlib import Path

from api_transcriber import transcribe_with_assemblyai


def main():
    """Точка входа."""
    parser = argparse.ArgumentParser(description="Транскрибация аудио через AssemblyAI")
    parser.add_argument("--audio", required=True, help="Путь к аудиофайлу")
    parser.add_argument("--output", required=True, help="Путь для сохранения результата (JSON)")
    
    args = parser.parse_args()
    
    audio_path = Path(args.audio)
    output_path = Path(args.output)
    
    # Валидация входного файла
    if not audio_path.exists():
        result = {"success": False, "error": f"Аудиофайл не найден: {audio_path}"}
        output_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        sys.exit(1)
    
    try:
        # Выполняем транскрибацию (язык фиксирован = "ru")
        transcription_result = transcribe_with_assemblyai(
            audio_path=audio_path,
            language="ru"
        )
        
        result = {
            "success": True,
            "segments": transcription_result.get("segments", []),
            "text": transcription_result.get("text", "")
        }
        
    except SystemExit as e:
        result = {"success": False, "error": f"AssemblyAI ошибка: {str(e)}"}
    except Exception as e:
        result = {"success": False, "error": f"Ошибка транскрибации: {str(e)}"}
    
    # Сохраняем результат в JSON
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. Файл существует
Test-Path "transcribe_worker.py"
# Должно вернуть: True
# ✅ ПРОВЕРЕНО: True

# 2. Синтаксис Python 3.12 корректен
py -3.12 -m py_compile transcribe_worker.py 2>&1
# Не должно быть ошибок
# ✅ ПРОВЕРЕНО: Ошибок нет

# 3. Содержит импорт api_transcriber
(Select-String -Path "transcribe_worker.py" -Pattern "from api_transcriber import").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1

# 4. Язык фиксирован = "ru"
(Select-String -Path "transcribe_worker.py" -Pattern 'language="ru"').Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1
```

---

# ШАГ 8: Создание backend/services/transcription.py

## Зависимости
**НЕТ** - независимый шаг

## Проверка "уже выполнено"
```powershell
Test-Path "backend/services/transcription.py"
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Создать файл `backend/services/transcription.py`

## Содержимое файла (ПОЛНАЯ КОПИЯ)
```python
"""
Сервис для транскрибации аудио через subprocess с Python 3.12.

ВАЖНО: AssemblyAI SDK несовместим с Python 3.14, поэтому транскрибация
выполняется через отдельный процесс Python 3.12.
"""

import asyncio
import json
import tempfile
import uuid
from pathlib import Path
from typing import Tuple, Optional, Dict, List

from backend.services.logger import log_error


# Константы
PYTHON_312_CMD = ["py", "-3.12"]
WORKER_SCRIPT = Path(__file__).resolve().parent.parent.parent / "transcribe_worker.py"

SUPPORTED_AUDIO_FORMATS = [
    ".mp3", ".wav", ".m4a", ".flac", 
    ".aac", ".ogg", ".webm", 
    ".mp4", ".mov", ".avi"
]


def validate_audio_file(filename: str, file_size: int, max_size_mb: int) -> Tuple[bool, Optional[str]]:
    """
    Валидация аудиофайла.
    
    Returns:
        Кортеж (успех, ошибка)
    """
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_AUDIO_FORMATS:
        return False, f"Неподдерживаемый формат файла. Допустимы: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"Размер файла превышает допустимый лимит ({max_size_mb} МБ)"
    
    return True, None


def format_transcription(segments: List[Dict]) -> str:
    """
    Форматирование сегментов транскрипции в читаемый текст.
    Формат: [HH:MM:SS] Speaker A: текст
    """
    lines = []
    for segment in segments:
        timestamp = format_timestamp(segment.get("start", 0))
        speaker = segment.get("speaker", "Speaker ?")
        text = segment.get("text", "").strip()
        lines.append(f"[{timestamp}] {speaker}: {text}")
    
    return "\n".join(lines)


def format_timestamp(seconds: float) -> str:
    """Форматирование времени в HH:MM:SS."""
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


async def transcribe_audio(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Выполнить транскрибацию аудиофайла через subprocess Python 3.12.
    
    Args:
        file_path: Путь к временному аудиофайлу
        
    Returns:
        Кортеж (форматированная_транскрипция, ошибка)
    """
    output_json = Path(tempfile.gettempdir()) / f"transcription_{uuid.uuid4().hex}.json"
    
    try:
        cmd = [
            *PYTHON_312_CMD,
            str(WORKER_SCRIPT),
            "--audio", str(file_path),
            "--output", str(output_json)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if not output_json.exists():
            error_msg = stderr.decode("utf-8", errors="replace") if stderr else "Результат не получен"
            return None, f"Ошибка транскрибации: {error_msg}"
        
        result = json.loads(output_json.read_text(encoding="utf-8"))
        
        if not result.get("success"):
            return None, result.get("error", "Неизвестная ошибка")
        
        segments = result.get("segments", [])
        if not segments:
            return None, "Не удалось получить транскрипцию"
        
        formatted = format_transcription(segments)
        return formatted, None
        
    except Exception as e:
        return None, f"Ошибка при запуске транскрибации: {str(e)}"
    
    finally:
        if output_json.exists():
            try:
                output_json.unlink()
            except OSError:
                pass
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. Файл существует
Test-Path "backend/services/transcription.py"
# Должно вернуть: True
# ✅ ПРОВЕРЕНО: True

# 2. Синтаксис корректен
py -3.14 -m py_compile backend/services/transcription.py 2>&1
# Не должно быть ошибок
# ✅ ПРОВЕРЕНО: Ошибок нет

# 3. Импорт работает
py -3.14 -c "from backend.services.transcription import validate_audio_file, transcribe_audio; print('OK')"
# Должно вернуть: OK
# ✅ ПРОВЕРЕНО: OK

# 4. Все функции определены
$funcs = @("validate_audio_file", "format_transcription", "format_timestamp", "transcribe_audio")
$funcs | ForEach-Object { (Select-String -Path "backend/services/transcription.py" -Pattern "def $_").Count -eq 1 }
# Все должны вернуть: True
# ✅ ПРОВЕРЕНО: True
```

---

# ШАГ 9: Расширение llm.py (ВСЕ изменения)

## Зависимости
**Шаг 3** - prompts.py должен быть расширен (функция get_prompt)

## Проверка "уже выполнено"
```powershell
$content = Get-Content "backend/services/llm.py" -Raw
($content -match 'def generate_meeting_protocol') -and ($content -match 'def call_deepseek_protocol')
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `backend/services/llm.py` и **ДОБАВИТЬ В КОНЕЦ ФАЙЛА** три новые функции

**НАЙТИ конец файла (последняя строка):**

**ДОБАВИТЬ В КОНЕЦ:**
```python


async def generate_meeting_protocol(transcription: str, username: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Генерировать протокол совещания из транскрипции.
    
    Args:
        transcription: Текст транскрипции
        username: Имя пользователя (для учета токенов)
        
    Returns:
        Кортеж (протокол, ошибка)
    """
    prompt = get_prompt("meeting_protocol")
    if not prompt:
        return None, "Промпт для протокола не найден"
    
    llm_type = get_current_llm_type()
    
    if llm_type == "deepseek":
        return await call_deepseek_protocol(prompt, transcription, username)
    elif llm_type == "lmstudio":
        return await call_lmstudio_protocol(prompt, transcription, username)
    else:
        return None, f"Неизвестный тип LLM: {llm_type}"


async def call_deepseek_protocol(prompt: str, transcription: str, username: str) -> Tuple[Optional[str], Optional[str]]:
    """Вызов DeepSeek API для генерации протокола."""
    try:
        from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
        config = get_llm_config()
        api_key = DEEPSEEK_API_KEY or config.get("deepseek_api_key", "")
        base_url = DEEPSEEK_BASE_URL or config.get("deepseek_base_url", "https://api.deepseek.com")
        
        if not api_key:
            return None, "API ключ DeepSeek не настроен"
        
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=120.0
        )
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcription}
        ]
        
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7,
            max_tokens=4000
        )
        
        result = response.choices[0].message.content
        
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        track_tokens(username, prompt_tokens, completion_tokens)
        
        return result, None
        
    except Exception as e:
        error_msg = f"Ошибка при генерации протокола: {str(e)}"
        log_error(username, "deepseek_protocol", error_msg)
        return None, error_msg


async def call_lmstudio_protocol(prompt: str, transcription: str, username: str) -> Tuple[Optional[str], Optional[str]]:
    """Вызов LM Studio API для генерации протокола."""
    try:
        config = get_llm_config()
        base_url = config.get("lmstudio_base_url", "http://localhost:1234/v1")
        model = config.get("lmstudio_model", "deepseek-coder")
        
        client = AsyncOpenAI(
            api_key="not-needed",
            base_url=base_url,
            timeout=180.0
        )
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcription}
        ]
        
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4000
        )
        
        result = response.choices[0].message.content
        return result, None
        
    except Exception as e:
        error_msg = f"Ошибка при генерации протокола через LM Studio: {str(e)}"
        log_error(username, "lmstudio_protocol", error_msg)
        return None, error_msg
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. Все 3 функции добавлены
@("generate_meeting_protocol", "call_deepseek_protocol", "call_lmstudio_protocol") | ForEach-Object {
    (Select-String -Path "backend/services/llm.py" -Pattern "def $_").Count -eq 1
}
# Все должны вернуть: True
# ✅ ПРОВЕРЕНО: True

# 2. Синтаксис корректен
py -3.14 -m py_compile backend/services/llm.py 2>&1
# Не должно быть ошибок
# ✅ ПРОВЕРЕНО: Ошибок нет

# 3. Импорт работает
py -3.14 -c "from backend.services.llm import generate_meeting_protocol; print('OK')"
# Должно вернуть: OK
# ✅ ПРОВЕРЕНО: OK
```

---

# ШАГ 10: Расширение main.py (ВСЕ изменения)

## Зависимости
- **Шаг 4** - schemas.py (TranscribeResponse)
- **Шаг 5** - settings.py (get_max_audio_file_size_bytes)
- **Шаг 8** - transcription.py (validate_audio_file, transcribe_audio)
- **Шаг 9** - llm.py (generate_meeting_protocol)

## Проверка "уже выполнено"
```powershell
$content = Get-Content "backend/main.py" -Raw
($content -match '/api/transcribe') -and ($content -match '/api/export-transcript')
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `backend/main.py` и сделать **2 изменения**:

### ИЗМЕНЕНИЕ 1: Добавить импорты

**НАЙТИ блок импортов (после существующих импортов, строки ~30-35):**
```python
from backend.models.schemas import (
    AnalyzeRequest, AnalyzeResponse,
    ExportRequest, 
    ...
)
```

**ДОБАВИТЬ ПОСЛЕ всех импортов из backend:**
```python
from backend.services.transcription import validate_audio_file, transcribe_audio
from backend.services.llm import generate_meeting_protocol
from backend.services.settings import get_max_audio_file_size_bytes
from backend.models.schemas import TranscribeResponse
```

### ИЗМЕНЕНИЕ 2: Добавить 3 новых endpoint'а

**НАЙТИ строку (примерно строка 440):**
```python
# ===== ЭКСПОРТ В WORD =====
```

**ДОБАВИТЬ ПЕРЕД НЕЙ:**
```python
# ===== ТРАНСКРИБАЦИЯ АУДИО =====

@app.post("/api/transcribe", response_model=TranscribeResponse)
@limiter.limit("2/minute")
async def transcribe_audio_endpoint(
    request: Request,
    audio_file: UploadFile = File(...),
    user: dict = Depends(require_auth)
):
    """
    Транскрибировать аудиофайл и сгенерировать протокол.
    """
    username = user["username"]
    
    # Получить максимальный размер
    from backend.services.settings import get_settings
    settings = get_settings()
    max_size_mb = settings.get("max_audio_file_size_mb", 100)
    
    # Читаем содержимое файла
    file_content = await audio_file.read()
    file_size = len(file_content)
    
    # Валидация файла
    is_valid, error = validate_audio_file(audio_file.filename, file_size, max_size_mb)
    if not is_valid:
        log_error(username, "audio_validation", error)
        return TranscribeResponse(success=False, error=error)
    
    # Сохраняем во временный файл
    file_extension = Path(audio_file.filename).suffix.lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        tmp_file.write(file_content)
        tmp_path = Path(tmp_file.name)
    
    try:
        # Выполняем транскрибацию
        transcription, trans_error = await transcribe_audio(tmp_path)
        
        if trans_error:
            log_error(username, "transcription", trans_error)
            return TranscribeResponse(success=False, error=trans_error)
        
        # Генерируем протокол
        protocol, proto_error = await generate_meeting_protocol(transcription, username)
        
        if proto_error:
            log_error(username, "protocol_generation", proto_error)
            # Возвращаем хотя бы транскрипцию
            return TranscribeResponse(
                success=True, 
                transcription=transcription, 
                protocol=None,
                error=f"Протокол не сгенерирован: {proto_error}"
            )
        
        log_user_action(username, "transcribe", f"Файл: {audio_file.filename}")
        
        return TranscribeResponse(
            success=True,
            transcription=transcription,
            protocol=protocol
        )
        
    finally:
        # Удаляем временный файл
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


@app.post("/api/export-transcript")
async def export_transcript_to_word(
    data: ExportRequest,
    user: dict = Depends(require_auth)
):
    """
    Экспортировать транскрипцию в Word документ.
    """
    try:
        import urllib.parse
        from datetime import datetime
        
        # Формируем имя файла с датой
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"Транскрипция_{timestamp}"
        
        doc_io = create_word_document(data.content, filename, 'markdown')
        
        log_user_action(user["username"], "export_transcript", f"Файл: {filename}.docx")
        
        encoded_filename = urllib.parse.quote(f"{filename}.docx", encoding='utf-8')
        
        return StreamingResponse(
            doc_io,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        error_msg = f"Ошибка при создании документа: {str(e)}"
        log_error(user["username"], "export_transcript", error_msg)
        return {"success": False, "error": error_msg}


@app.post("/api/export-protocol")
async def export_protocol_to_word(
    data: ExportRequest,
    user: dict = Depends(require_auth)
):
    """
    Экспортировать протокол в Word документ.
    """
    try:
        import urllib.parse
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"Протокол_{timestamp}"
        
        doc_io = create_word_document(data.content, filename, 'markdown')
        
        log_user_action(user["username"], "export_protocol", f"Файл: {filename}.docx")
        
        encoded_filename = urllib.parse.quote(f"{filename}.docx", encoding='utf-8')
        
        return StreamingResponse(
            doc_io,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        error_msg = f"Ошибка при создании документа: {str(e)}"
        log_error(user["username"], "export_protocol", error_msg)
        return {"success": False, "error": error_msg}


```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. Все импорты добавлены
@("from backend.services.transcription import", "from backend.services.llm import generate_meeting_protocol", 
  "from backend.services.settings import get_max_audio_file_size_bytes", "TranscribeResponse") | ForEach-Object {
    (Select-String -Path "backend/main.py" -Pattern $_).Count -ge 1
}
# Все должны вернуть: True
# ✅ ПРОВЕРЕНО: True

# 2. Все 3 endpoint'а добавлены
@("/api/transcribe", "/api/export-transcript", "/api/export-protocol") | ForEach-Object {
    (Select-String -Path "backend/main.py" -Pattern $_).Count -ge 1
}
# Все должны вернуть: True
# ✅ ПРОВЕРЕНО: True

# 3. Синтаксис корректен
py -3.14 -m py_compile backend/main.py 2>&1
# Не должно быть ошибок
# ✅ ПРОВЕРЕНО: Ошибок нет

# 4. Импорт работает
py -3.14 -c "from backend.main import app; print('OK')"
# Должно вернуть: OK
# ✅ ПРОВЕРЕНО: OK
```

---

# ШАГ 11: Расширение index.html (ВСЕ изменения)

## Зависимости
**НЕТ** - независимый шаг

## Проверка "уже выполнено"
```powershell
$content = Get-Content "frontend/index.html" -Raw
($content -match 'main-tabs') -and ($content -match 'transcription-tab')
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `frontend/index.html` и сделать **3 изменения**:

### ИЗМЕНЕНИЕ 1: Добавить вкладки

**НАЙТИ закрывающий тег header (строка ~18):**
```html
    </div><!-- header -->
</head>
```

**ДОБАВИТЬ ПОСЛЕ НЕГО:**
```html

    <!-- Вкладки главной страницы -->
    <div class="main-tabs">
        <button class="main-tab-button active" onclick="showMainTab('contracts')">
            📄 Анализ договоров
        </button>
        <button class="main-tab-button" onclick="showMainTab('transcription')">
            🎤 Расшифровка аудио
        </button>
    </div>
```

### ИЗМЕНЕНИЕ 2: Обернуть существующий контент в вкладку

**НАЙТИ открывающий тег container (строка ~20):**
```html
    <div class="container">
```

**ЗАМЕНИТЬ НА:**
```html
    <!-- Вкладка: Анализ договоров -->
    <div id="contracts-tab" class="main-tab-content active">
    <div class="container">
```

**НАЙТИ закрывающий тег container (перед `<script src="/static/js/app.js">`):**
```html
    </div><!-- container -->
    
    <script src="/static/js/app.js"></script>
```

**ЗАМЕНИТЬ НА:**
```html
    </div><!-- container -->
    </div><!-- contracts-tab -->
    
    <script src="/static/js/app.js"></script>
```

### ИЗМЕНЕНИЕ 3: Добавить вкладку транскрибации

**НАЙТИ строку:**
```html
    </div><!-- contracts-tab -->
    
    <script src="/static/js/app.js"></script>
```

**ВСТАВИТЬ МЕЖДУ ними:**
```html
    </div><!-- contracts-tab -->

    <!-- Вкладка: Расшифровка аудио -->
    <div id="transcription-tab" class="main-tab-content" style="display: none;">
    <div class="container">
        <div class="upload-section">
            <h2>Загрузить аудио для расшифровки</h2>
            
            <form id="transcribeForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="audio-file">Выберите аудиофайл:</label>
                    <input type="file" id="audio-file" name="audio_file" 
                           accept=".mp3,.wav,.m4a,.flac,.aac,.ogg,.webm,.mp4,.mov,.avi" required>
                    <span id="audio-file-name"></span>
                    <small>Форматы: MP3, WAV, M4A, FLAC, AAC, OGG, WebM, MP4, MOV, AVI</small>
                    <small>Язык: Русский (автоматически)</small>
                </div>
                
                <button type="submit" class="btn btn-primary">Расшифровать</button>
            </form>
            
            <div id="transcribe-spinner" style="display: none;">
                <div class="spinner"></div>
                <p>Идет транскрибация... Это может занять несколько минут.</p>
            </div>
            
            <div id="transcribe-error" class="error-message" style="display: none;"></div>
        </div>

        <div id="transcription-result-section" style="display: none;">
            <h2>Результат расшифровки</h2>
            
            <div class="result-block">
                <h3>Транскрипция</h3>
                <div id="transcription-content" class="result-content" style="white-space: pre-wrap;"></div>
                <div class="result-actions">
                    <button onclick="exportTranscription()" class="btn btn-primary">
                        📥 Скачать (Word)
                    </button>
                    <button onclick="copyTranscription()" class="btn btn-secondary">
                        📋 Копировать
                    </button>
                </div>
            </div>
            
            <div class="result-block">
                <h3>Протокол совещания</h3>
                <div id="protocol-content" class="result-content"></div>
                <div class="result-actions">
                    <button onclick="exportProtocol()" class="btn btn-primary">
                        📥 Скачать (Word)
                    </button>
                    <button onclick="copyProtocol()" class="btn btn-secondary">
                        📋 Копировать
                    </button>
                </div>
            </div>
            
            <p class="info-text">
                ℹ️ Результаты не сохраняются на сервере. После закрытия страницы они будут потеряны.
            </p>
        </div>
    </div>
    </div><!-- transcription-tab -->
    
    <script src="/static/js/app.js"></script>
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. Вкладки добавлены
(Select-String -Path "frontend/index.html" -Pattern "main-tabs").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1

# 2. Обе вкладки контента существуют
@("contracts-tab", "transcription-tab") | ForEach-Object {
    (Select-String -Path "frontend/index.html" -Pattern $_).Count -ge 1
}
# Все должны вернуть: True
# ✅ ПРОВЕРЕНО: True

# 3. Форма транскрибации добавлена
(Select-String -Path "frontend/index.html" -Pattern "transcribeForm").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1

# 4. Все элементы результатов на месте
@("transcription-content", "protocol-content", "transcribe-spinner") | ForEach-Object {
    (Select-String -Path "frontend/index.html" -Pattern $_).Count -ge 1
}
# Все должны вернуть: True
# ✅ ПРОВЕРЕНО: True
```

---

# ШАГ 12: Расширение app.js (ВСЕ изменения)

## Зависимости
**НЕТ** - независимый шаг

## Проверка "уже выполнено"
```powershell
$content = Get-Content "frontend/js/app.js" -Raw
($content -match 'function showMainTab') -and ($content -match 'function handleTranscribe')
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `frontend/js/app.js` и сделать **4 изменения**:

### ИЗМЕНЕНИЕ 1: Добавить глобальные переменные

**НАЙТИ строку (примерно строка 7):**
```javascript
let currentFilename = null;
```

**ДОБАВИТЬ ПОСЛЕ НЕЁ:**
```javascript
let currentTranscription = null;
let currentProtocol = null;
```

### ИЗМЕНЕНИЕ 2: Добавить функцию showMainTab

**НАЙТИ функцию goToAdmin() (примерно строка 165):**
```javascript
function goToAdmin() {
    window.location.href = '/admin.html';
}
```

**ДОБАВИТЬ ПОСЛЕ НЕЁ:**
```javascript


// ===== ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК =====

function showMainTab(tabName) {
    // Скрыть все вкладки контента
    document.getElementById('contracts-tab').style.display = 'none';
    document.getElementById('transcription-tab').style.display = 'none';
    
    // Убрать active со всех кнопок
    document.querySelectorAll('.main-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Показать выбранную вкладку
    if (tabName === 'contracts') {
        document.getElementById('contracts-tab').style.display = 'block';
    } else if (tabName === 'transcription') {
        document.getElementById('transcription-tab').style.display = 'block';
    }
    
    // Активировать кнопку
    event.target.classList.add('active');
}
```

### ИЗМЕНЕНИЕ 3: Добавить функцию handleTranscribe

**ДОБАВИТЬ ПОСЛЕ функции showMainTab:**
```javascript


// ===== ТРАНСКРИБАЦИЯ АУДИО =====

async function handleTranscribe(event) {
    event.preventDefault();
    
    const audioInput = document.getElementById('audio-file');
    const errorDiv = document.getElementById('transcribe-error');
    const spinnerDiv = document.getElementById('transcribe-spinner');
    const resultSection = document.getElementById('transcription-result-section');
    
    // Скрыть ошибки и результаты
    errorDiv.style.display = 'none';
    resultSection.style.display = 'none';
    
    // Показать спиннер
    spinnerDiv.style.display = 'block';
    
    const formData = new FormData();
    formData.append('audio_file', audioInput.files[0]);
    
    try {
        const response = await fetch(`${API_BASE}/api/transcribe`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Скрыть спиннер
        spinnerDiv.style.display = 'none';
        
        if (data.success) {
            currentTranscription = data.transcription;
            currentProtocol = data.protocol;
            
            // Отобразить транскрипцию
            document.getElementById('transcription-content').textContent = data.transcription || '';
            
            // Отобразить протокол (может быть пустым)
            const protocolContent = document.getElementById('protocol-content');
            if (data.protocol) {
                protocolContent.innerHTML = marked.parse(data.protocol);
            } else {
                protocolContent.textContent = data.error || 'Протокол не сгенерирован';
            }
            
            resultSection.style.display = 'block';
            resultSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            errorDiv.textContent = data.error || 'Ошибка транскрибации';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        spinnerDiv.style.display = 'none';
        errorDiv.textContent = 'Ошибка сети при транскрибации';
        errorDiv.style.display = 'block';
    }
}
```

### ИЗМЕНЕНИЕ 4: Добавить функции экспорта

**ДОБАВИТЬ ПОСЛЕ функции handleTranscribe:**
```javascript


// ===== ЭКСПОРТ ТРАНСКРИПЦИИ =====

async function exportTranscription() {
    if (!currentTranscription) {
        alert('Нет транскрипции для экспорта');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/export-transcript`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: currentTranscription,
                filename: 'Транскрипция',
                content_type: 'markdown'
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Извлечь имя файла из заголовка
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'Транскрипция.docx';
            if (contentDisposition) {
                const match = contentDisposition.match(/filename\*=UTF-8''(.+)/);
                if (match) {
                    filename = decodeURIComponent(match[1]);
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Ошибка при экспорте транскрипции');
        }
    } catch (error) {
        alert('Ошибка при экспорте транскрипции');
    }
}

async function exportProtocol() {
    if (!currentProtocol) {
        alert('Нет протокола для экспорта');
        return;
    }
    
    const protocolHtml = document.getElementById('protocol-content').innerHTML;
    
    try {
        const response = await fetch(`${API_BASE}/api/export-protocol`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: protocolHtml,
                filename: 'Протокол',
                content_type: 'html'
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'Протокол.docx';
            if (contentDisposition) {
                const match = contentDisposition.match(/filename\*=UTF-8''(.+)/);
                if (match) {
                    filename = decodeURIComponent(match[1]);
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Ошибка при экспорте протокола');
        }
    } catch (error) {
        alert('Ошибка при экспорте протокола');
    }
}

function copyTranscription() {
    if (!currentTranscription) {
        alert('Нет транскрипции для копирования');
        return;
    }
    
    navigator.clipboard.writeText(currentTranscription).then(() => {
        alert('Транскрипция скопирована в буфер обмена');
    }).catch(() => {
        alert('Ошибка при копировании');
    });
}

function copyProtocol() {
    if (!currentProtocol) {
        alert('Нет протокола для копирования');
        return;
    }
    
    navigator.clipboard.writeText(currentProtocol).then(() => {
        alert('Протокол скопирован в буфер обмена');
    }).catch(() => {
        alert('Ошибка при копировании');
    });
}
```

### ИЗМЕНЕНИЕ 5: Расширить initApp()

**НАЙТИ функцию initApp() и её конец (закрывающую фигурную скобку):**
```javascript
function initApp() {
    // ... существующий код ...
    
}  // <--- эту закрывающую скобку НАЙТИ
```

**ДОБАВИТЬ ПЕРЕД закрывающей скобкой }:**
```javascript
    
    // Добавить обработчик формы транскрибации
    const transcribeForm = document.getElementById('transcribeForm');
    if (transcribeForm) {
        transcribeForm.addEventListener('submit', handleTranscribe);
    }
    
    // Добавить обработчик выбора аудиофайла
    const audioInput = document.getElementById('audio-file');
    if (audioInput) {
        audioInput.addEventListener('change', function() {
            const audioFileName = document.getElementById('audio-file-name');
            if (this.files.length > 0) {
                audioFileName.textContent = this.files[0].name;
            }
        });
    }
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. Глобальные переменные добавлены
@("currentTranscription", "currentProtocol") | ForEach-Object {
    (Select-String -Path "frontend/js/app.js" -Pattern "let $_").Count -ge 1
}
# Все должны вернуть: True
# ✅ ПРОВЕРЕНО: True

# 2. Все функции добавлены
@("showMainTab", "handleTranscribe", "exportTranscription", "exportProtocol", "copyTranscription", "copyProtocol") | ForEach-Object {
    (Select-String -Path "frontend/js/app.js" -Pattern "function $_").Count -ge 1
}
# Все должны вернуть: True
# ✅ ПРОВЕРЕНО: True

# 3. Обработчики в initApp добавлены
(Select-String -Path "frontend/js/app.js" -Pattern "transcribeForm").Count
# Должно вернуть: минимум 2
# ✅ ПРОВЕРЕНО: 3
```

---

# ШАГ 13: Расширение style.css

## Зависимости
**НЕТ** - независимый шаг

## Проверка "уже выполнено"
```powershell
$content = Get-Content "frontend/css/style.css" -Raw
($content -match 'main-tabs') -and ($content -match 'spinner')
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `frontend/css/style.css` и **ДОБАВИТЬ В КОНЕЦ ФАЙЛА**:

```css


/* ===== ГЛАВНЫЕ ВКЛАДКИ ===== */

.main-tabs {
    display: flex;
    justify-content: center;
    gap: 10px;
    padding: 20px;
    background: #f5f5f5;
    border-bottom: 1px solid #ddd;
}

.main-tab-button {
    padding: 12px 24px;
    font-size: 16px;
    border: 2px solid #007bff;
    background: white;
    color: #007bff;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.main-tab-button:hover {
    background: #e7f1ff;
}

.main-tab-button.active {
    background: #007bff;
    color: white;
}

.main-tab-content {
    display: none;
}

.main-tab-content.active {
    display: block;
}

/* ===== СПИННЕР ===== */

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 20px auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

#transcribe-spinner {
    text-align: center;
    padding: 20px;
}

/* ===== РЕЗУЛЬТАТЫ ТРАНСКРИБАЦИИ ===== */

.result-block {
    background: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.result-block h3 {
    margin-top: 0;
    border-bottom: 1px solid #ddd;
    padding-bottom: 10px;
}

.result-content {
    max-height: 400px;
    overflow-y: auto;
    padding: 10px;
    background: white;
    border: 1px solid #eee;
    border-radius: 4px;
    margin-bottom: 15px;
}

.info-text {
    color: #666;
    font-style: italic;
    text-align: center;
    margin-top: 20px;
}
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. Стили вкладок добавлены
(Select-String -Path "frontend/css/style.css" -Pattern "\.main-tabs").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1

# 2. Стили спиннера добавлены
(Select-String -Path "frontend/css/style.css" -Pattern "\.spinner").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1

# 3. Стили результатов добавлены
(Select-String -Path "frontend/css/style.css" -Pattern "\.result-block").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 2 (класс и подкласс h3)

# 4. Анимация спиннера добавлена
(Select-String -Path "frontend/css/style.css" -Pattern "@keyframes spin").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1
```

---

# ШАГ 14: Расширение admin.js (ВСЕ изменения)

## Зависимости
**НЕТ** - независимый шаг

## Проверка "уже выполнено"
```powershell
$content = Get-Content "frontend/js/admin.js" -Raw
($content -match 'meeting_protocol') -and ($content -match 'max-audio-file-size')
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `frontend/js/admin.js` и сделать **2 изменения**:

### ИЗМЕНЕНИЕ 1: Расширить renderPromptsEditor

**НАЙТИ функцию renderPromptsEditor() и её секцию с legal_check (примерно строки 150-160):**
```javascript
        <div class="prompt-editor">
            <h4>Промпт для юридической проверки</h4>
            <textarea id="prompt-legal_check">${prompts.legal_check || ''}</textarea>
            <div class="prompt-actions">
                <button onclick="savePrompt('legal_check')" class="btn btn-success">Сохранить</button>
                <button onclick="resetPrompt('legal_check')" class="btn btn-secondary">Сбросить к исходному</button>
            </div>
        </div>
```

**ДОБАВИТЬ ПОСЛЕ ЭТОГО блока:**
```javascript

        <div class="prompt-editor">
            <h4>Промпт для протокола совещания</h4>
            <textarea id="prompt-meeting_protocol">${prompts.meeting_protocol || ''}</textarea>
            <div class="prompt-actions">
                <button onclick="savePrompt('meeting_protocol')" class="btn btn-success">Сохранить</button>
                <button onclick="resetPrompt('meeting_protocol')" class="btn btn-secondary">Сбросить к исходному</button>
            </div>
        </div>
```

### ИЗМЕНЕНИЕ 2: Расширить renderSettings

**НАЙТИ функцию renderSettings() и поле max-file-size (примерно строки 230-235):**
```javascript
            <div class="form-group">
                <label>Максимальный размер файла (МБ):</label>
                <input type="number" id="max-file-size" value="${settings.max_file_size_mb || 50}" min="1" max="500">
            </div>
```

**ДОБАВИТЬ ПОСЛЕ ЭТОГО блока:**
```javascript
            <div class="form-group">
                <label>Максимальный размер аудиофайла (МБ):</label>
                <input type="number" id="max-audio-file-size" value="${settings.max_audio_file_size_mb || 100}" min="1" max="500">
            </div>
```

**ТАКЖЕ НАЙТИ функцию saveSettings() и её блок формирования settings (примерно строки 270-280):**
```javascript
    const settings = {
        max_file_size_mb: parseInt(document.getElementById('max-file-size').value),
        max_queue_size: parseInt(document.getElementById('max-queue-size').value),
        max_concurrent_requests: parseInt(document.getElementById('max-concurrent-requests').value),
        rate_limit_per_minute: parseInt(document.getElementById('rate-limit').value)
    };
```

**ЗАМЕНИТЬ НА:**
```javascript
    const settings = {
        max_file_size_mb: parseInt(document.getElementById('max-file-size').value),
        max_audio_file_size_mb: parseInt(document.getElementById('max-audio-file-size').value),
        max_queue_size: parseInt(document.getElementById('max-queue-size').value),
        max_concurrent_requests: parseInt(document.getElementById('max-concurrent-requests').value),
        rate_limit_per_minute: parseInt(document.getElementById('rate-limit').value)
    };
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. Промпт meeting_protocol добавлен
(Select-String -Path "frontend/js/admin.js" -Pattern "meeting_protocol").Count
# Должно вернуть: 3 (textarea id, savePrompt, resetPrompt)
# ✅ ПРОВЕРЕНО: 3

# 2. Поле max-audio-file-size добавлено
(Select-String -Path "frontend/js/admin.js" -Pattern "max-audio-file-size").Count
# Должно вернуть: 2 (input и в saveSettings)
# ✅ ПРОВЕРЕНО: 2

# 3. max_audio_file_size_mb в saveSettings
(Select-String -Path "frontend/js/admin.js" -Pattern "max_audio_file_size_mb").Count
# Должно вернуть: 2 (value и в объекте settings)
# ✅ ПРОВЕРЕНО: 2
```

---

# ШАГ 15: Обновление requirements.txt

## Зависимости
**НЕТ** - независимый шаг

## Проверка "уже выполнено"
```powershell
$content = Get-Content "requirements.txt" -Raw
$content -match 'assemblyai'
# Если вернет True → ШАГ УЖЕ ВЫПОЛНЕН, пропустить
```

## Что делать
Открыть файл `requirements.txt` и **ДОБАВИТЬ В КОНЕЦ**:
```
assemblyai>=0.48.0
```

## Критерии проверки (ТОЛЬКО этого шага)
```powershell
# 1. assemblyai добавлен
(Select-String -Path "requirements.txt" -Pattern "assemblyai").Count
# Должно вернуть: 1
# ✅ ПРОВЕРЕНО: 1

# 2. Версия указана корректно
Select-String -Path "requirements.txt" -Pattern "assemblyai>=0\.48\.0"
# Должно вернуть 1 совпадение
# ✅ ПРОВЕРЕНО: requirements.txt:27:assemblyai>=0.48.0
```

---

# ФИНАЛЬНАЯ ПРОВЕРКА ВСЕЙ ИНТЕГРАЦИИ

После выполнения всех 15 шагов выполнить:

```powershell
# 1. Проверить синтаксис всех Python файлов
py -3.14 -m py_compile backend/main.py 2>&1
py -3.14 -m py_compile backend/services/transcription.py 2>&1
py -3.14 -m py_compile backend/services/prompts.py 2>&1
py -3.14 -m py_compile backend/services/llm.py 2>&1
py -3.14 -m py_compile backend/services/settings.py 2>&1
py -3.14 -m py_compile backend/models/schemas.py 2>&1
py -3.12 -m py_compile transcribe_worker.py 2>&1

# 2. Проверить импорты
py -3.14 -c "from backend.main import app; print('Backend OK')"

# 3. Проверить наличие всех промптов
Test-Path "data/prompts/defaults/meeting_protocol_prompt.txt"
Test-Path "data/prompts/meeting_protocol_prompt.txt"

# 4. Проверить JSON конфиг
(Get-Content "data/settings.json" | ConvertFrom-Json).max_audio_file_size_mb

# 5. Запустить сервер (тестовый запуск)
# py -3.14 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
# Сервер должен запуститься без ошибок
```

---

## КРИТЕРИИ ПОЛНОГО ЗАВЕРШЕНИЯ

✅ Все 15 шагов отмечены как выполненные
✅ Все проверки синтаксиса проходят без ошибок
✅ Все импорты работают
✅ Сервер запускается без ошибок
✅ Промпты созданы и доступны
✅ JSON конфигурация валидна
✅ Frontend файлы содержат все новые элементы

---

**Версия плана**: 2.0  
**Дата создания**: 03.12.2025  
**Количество шагов**: 15 (было 29)  
**Улучшения**:
- ✅ Консолидация изменений по файлам
- ✅ Проверки идемпотентности
- ✅ Точные инструкции с контекстом
- ✅ Явные зависимости
- ✅ Критерии только для текущего шага

