# ТЕХНИЧЕСКОЕ ЗАДАНИЕ: Интеграция транскрибации аудио в систему анализа договоров
## ФИНАЛЬНАЯ ВЕРСИЯ (v1.2 - с уточнениями)

---

## 1. ЦЕЛИ И ЗАДАЧИ

### 1.1. Основная цель
Интегрировать функционал автоматической транскрибации аудиозаписей совещаний в существующую систему анализа договоров с последующей генерацией протоколов совещаний через DeepSeek API.

### 1.2. Задачи
- Добавить вкладки на главной странице: "Анализ договоров" / "Расшифровка аудио"
- Реализовать загрузку и обработку аудиофайлов
- Интегрировать AssemblyAI API для транскрибации (используя существующий `api_transcriber.py`)
- Добавить генерацию протоколов через DeepSeek API
- Реализовать экспорт результатов в Word формат (два файла: транскрипция и протокол)
- Добавить управление промптом протокола в админ-панели
- Обеспечить безопасность и контроль доступа

---

## 2. АНАЛИЗ ТЕКУЩЕЙ СИСТЕМЫ

### 2.1. Технический стек
- **Python версия основного проекта**: 3.14.0
- **Python версия для транскрибации**: 3.12.10 (⚠️ ОБЯЗАТЕЛЬНО — AssemblyAI SDK несовместим с Python 3.14)
- **Backend**: FastAPI (Python 3.14)
- **Frontend**: HTML/CSS/JavaScript (Vanilla)
- **База данных**: JSON-файлы (users.json, settings.json, llm_config.json)
- **Аутентификация**: IP-based authorization
- **LLM интеграция**: DeepSeek API + LM Studio (опционально)

### 2.2. ⚠️ КРИТИЧЕСКОЕ ОГРАНИЧЕНИЕ: Версии Python

| Компонент | Python версия | Причина |
|-----------|---------------|---------|
| Основной backend (FastAPI) | 3.14.0 | Текущий проект |
| Транскрибация (AssemblyAI) | 3.12.10 | **SDK несовместим с Python 3.14** |

**Решение**: Subprocess-архитектура — транскрибация выполняется через отдельный процесс Python 3.12.

### 2.3. Существующие компоненты для переиспользования
| Компонент | Файл | Использование |
|-----------|------|---------------|
| Система промптов | `backend/services/prompts.py` | Расширить для `meeting_protocol` |
| LLM сервис | `backend/services/llm.py` | Добавить `generate_meeting_protocol()` |
| Экспорт в Word | `backend/services/document.py` | Переиспользовать `create_word_document()` |
| Rate limiting | `backend/middleware/rate_limit.py` | Применить к новому endpoint (2 запроса/минуту) |
| Очередь запросов | `backend/services/queue.py` | Применить для транскрибации (1 одновременный запрос) |
| Настройки | `backend/services/settings.py` | Расширить для аудио лимитов |
| Логирование | `backend/services/logger.py` | Использовать для ошибок транскрибации |
| API транскрибации | `api_transcriber.py` | **ГОТОВЫЙ КОД** - вызывается через subprocess Python 3.12 |

### 2.4. Ключ AssemblyAI
- **Хранение**: файл `.env` (переменная `ASSEMBLYAI_API_KEY`)
- **Доступ**: через `os.getenv("ASSEMBLYAI_API_KEY")` в `api_transcriber.py`

### 2.5. Конфигурация Python 3.12
- **Путь**: `py -3.12` (Windows py launcher)
- **AssemblyAI SDK**: v0.46.0 (установлен глобально для Python 3.12)
- **Расположение**: `C:\Users\Denis\AppData\Local\Programs\Python\Python312\`

---

## 3. ТРЕБОВАНИЯ К РЕАЛИЗАЦИИ

### 3.1. Технические требования
| Параметр | Значение |
|----------|----------|
| Python версия (backend) | 3.14.0 |
| Python версия (транскрибация) | **3.12.10** (ОБЯЗАТЕЛЬНО) |
| Способ вызова Python 3.12 | `py -3.12` (Windows py launcher, **уже установлен**) |
| API ключ AssemblyAI | Из `.env` (ASSEMBLYAI_API_KEY) |
| Язык транскрибации | **Только русский** (ru) - фиксированный параметр |
| Аудиоформаты | MP3, WAV, M4A, FLAC, AAC, OGG, WebM, MP4, MOV, AVI |
| Макс. размер файла | 100 МБ (настраивается в админке) |
| Хранение файлов | Временная директория (удаление после обработки) |
| Хранение результатов | **Не сохраняются**, только экспорт в Word |
| Формат транскрипции | **[HH:MM:SS] Speaker X: текст** (Вариант А) |

### 3.2. Архитектура Subprocess для транскрибации (УПРОЩЕННАЯ)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     ОСНОВНОЙ BACKEND (Python 3.14)                    │
│                         FastAPI endpoint                              │
│                                                                       │
│  1. Получение аудиофайла от пользователя                             │
│  2. Валидация (формат, размер)                                       │
│  3. Сохранение во временный файл (temp_audio_path)                   │
│                          │                                           │
│                          ▼                                           │
│  4. subprocess.run([                                                 │
│       "py", "-3.12",                                                 │
│       "transcribe_worker.py",         # Минимальный wrapper         │
│       "--audio", temp_audio_path,                                    │
│       "--output", temp_json_path                                     │
│     ])                                                               │
│                          │                                           │
│                          ▼                                           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              WORKER ПРОЦЕСС (Python 3.12)                      │  │
│  │                                                                │  │
│  │   transcribe_worker.py (НОВЫЙ - минимальный):                 │  │
│  │   - Импортирует готовый api_transcriber.py                    │  │
│  │   - Вызывает transcribe_with_assemblyai(audio_path, "ru")     │  │
│  │   - Форматирует сегменты в JSON                               │  │
│  │   - Сохраняет результат в temp_json_path                      │  │
│  │   - Exit code: 0 = успех, 1 = ошибка                          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                          │                                           │
│                          ▼                                           │
│  5. Чтение JSON результата (segments + text)                         │
│  6. Форматирование транскрипции:                                     │
│     "[HH:MM:SS] Speaker A: текст"                                    │
│  7. Отправка в DeepSeek для генерации протокола                      │
│  8. Возврат обоих результатов (транскрипция + протокол)              │
│  9. Удаление временных файлов (аудио + JSON)                         │
└──────────────────────────────────────────────────────────────────────┘
```

**⚠️ КЛЮЧЕВОЕ УПРОЩЕНИЕ:**
- **НЕ создаем новую логику транскрибации** - используем готовый `api_transcriber.py`
- `transcribe_worker.py` - это МИНИМАЛЬНЫЙ wrapper (~50 строк) для:
  1. Приема аргументов командной строки
  2. Вызова готовой функции `transcribe_with_assemblyai()`
  3. Сохранения результата в JSON
  
**Обмен данными:**
- **Вход**: `--audio <path>`, `--output <json_path>` (язык фиксирован = "ru")
- **Выход**: JSON файл с полями `{"success": bool, "segments": [...], "text": "..."}`

### 3.3. Функциональные требования

#### 3.3.1. UI/UX
- **Главная страница**: Вкладки "Анализ договоров" / "Расшифровка аудио"
- **Форма загрузки**: Выбор аудиофайла (только русский язык, без выбора)
- **Прогресс**: **Спиннер** с текстом "Идет транскрибация..." (не полноценный progress bar)
- **Результаты**: 
  - Отображение транскрипции в формате: **`[HH:MM:SS] Speaker A: текст`**
  - Отображение готового протокола от DeepSeek
  - Две кнопки экспорта в Word (транскрипция и протокол отдельно)
  - Кнопка копирования в буфер обмена
- **Важно**: Результаты НЕ сохраняются на сервере, только в памяти браузера до перезагрузки

#### 3.3.2. Экспорт в Word
Два отдельных файла с автоматическими именами:
- `Транскрипция_YYYY-MM-DD_HH-MM.docx`
- `Протокол_YYYY-MM-DD_HH-MM.docx`

Используется существующая функция `create_word_document()` из `backend/services/document.py`.

#### 3.3.3. Админ-панель
- **Промпты**: Добавить редактор "Промпт для протокола совещания" (аналогично summary/legal_check)
- **Настройки**: Добавить "Максимальный размер аудиофайла (МБ)" (по умолчанию 100)

#### 3.3.4. Безопасность и ограничения
- **Доступ**: Все авторизованные пользователи (role: user или admin)
- **Rate limiting**: **2 запроса/минуту** (транскрибация дольше анализа договоров)
- **Очередь**: **Максимум 1 одновременный запрос** (транскрибацию делает только 1 пользователь за раз)
- **Валидация**: Проверка типа и размера файлов
- **Логирование**: Все ошибки логируются через `backend/services/logger.py`

---

## 4. БИЗНЕС-ЛОГИКА

### 4.1. Процесс транскрибации (пошаговый)

```
1. Пользователь выбирает вкладку "Расшифровка аудио"
2. Загружает аудиофайл (язык = русский, автоматически)
3. Система валидирует файл (формат, размер)
4. Проверка rate limit (2 запроса/минуту)
5. Проверка очереди (максимум 1 одновременный запрос)
6. Файл сохраняется во временную директорию
7. Показывается спиннер "Идет транскрибация..."
8. Вызывается subprocess Python 3.12 (transcribe_worker.py)
   → который вызывает готовый api_transcriber.transcribe_with_assemblyai()
9. Получен результат с сегментами (спикер, время, текст)
10. Форматирование: "[HH:MM:SS] Speaker A: текст"
11. Транскрипция отправляется в DeepSeek для генерации протокола
12. Результаты отображаются пользователю в браузере
13. Временные файлы удаляются (аудио + JSON)
14. Пользователь может:
    - Скопировать в буфер обмена
    - Экспортировать в Word (2 отдельных файла)
15. После закрытия страницы результаты теряются (не сохраняются на сервере)
```

### 4.2. Промпт для генерации протокола

**Тип**: `meeting_protocol`
**Файл**: `data/prompts/meeting_protocol_prompt.txt`
**Файл по умолчанию**: `data/prompts/defaults/meeting_protocol_prompt.txt`

**Содержимое промпта по умолчанию**:
```
##Роль##

Ты опытный секретарь, который способен составлять краткие и емкие протоколы совещаний. 

У тебя талант и призвание составлять протоколы совещаний, убирая оттуда незначащую информацию, без потери смысла. 

Так же ты очень качественно определяешь, какие задания и действия необходимо совершить или создать по итогам совещания и назначаешь на них ответственных.

##Задача##

Составить качественный, краткий и емкий протокол совещания по следующей транскрипции:

##Транскрипция##

```

**Примечание**: Текст транскрипции добавляется после `##Транскрипция##` при вызове LLM.

---

## 5. АРХИТЕКТУРНЫЕ РЕШЕНИЯ

### 5.1. Структура изменений

```
./
├── transcribe_worker.py       # НОВЫЙ: Worker для Python 3.12 (subprocess)

backend/
├── services/
│   ├── transcription.py       # НОВЫЙ: сервис транскрибации (вызов subprocess)
│   ├── prompts.py             # МОДИФИКАЦИЯ: +meeting_protocol
│   ├── llm.py                 # МОДИФИКАЦИЯ: +generate_meeting_protocol()
│   └── settings.py            # МОДИФИКАЦИЯ: +max_audio_file_size_mb
├── models/
│   └── schemas.py             # МОДИФИКАЦИЯ: +TranscribeResponse, расширение Literal
└── main.py                    # МОДИФИКАЦИЯ: +endpoints транскрибации

data/
├── prompts/
│   ├── defaults/
│   │   └── meeting_protocol_prompt.txt  # НОВЫЙ
│   └── meeting_protocol_prompt.txt      # НОВЫЙ (копия defaults)
└── settings.json              # МОДИФИКАЦИЯ: +max_audio_file_size_mb

frontend/
├── index.html                 # МОДИФИКАЦИЯ: +вкладки
├── js/
│   ├── app.js                 # МОДИФИКАЦИЯ: +логика вкладок и транскрибации
│   └── admin.js               # МОДИФИКАЦИЯ: +промпт meeting_protocol в UI
└── css/
    └── style.css              # МОДИФИКАЦИЯ: +стили для вкладок (при необходимости)

api_transcriber.py             # БЕЗ ИЗМЕНЕНИЙ (вызывается из transcribe_worker.py)
```

### 5.2. Новые API endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/transcribe` | Загрузка и обработка аудиофайла |
| POST | `/api/export-transcript` | Экспорт транскрипции в Word |
| POST | `/api/export-protocol` | Экспорт протокола в Word |

**Примечание**: Можно использовать существующий `/api/export` с параметром `type` для определения типа экспорта.

### 5.3. Новые Pydantic схемы

```python
# backend/models/schemas.py

class TranscribeResponse(BaseModel):
    success: bool
    transcription: Optional[str] = None   # Форматированная транскрипция
    protocol: Optional[str] = None        # Готовый протокол от DeepSeek
    error: Optional[str] = None
    
# Расширение существующих схем:
class PromptSaveRequest(BaseModel):
    prompt_type: Literal["summary", "legal_check", "meeting_protocol"]
    
class PromptResetRequest(BaseModel):
    prompt_type: Literal["summary", "legal_check", "meeting_protocol"]
    
class SettingsUpdate(BaseModel):
    max_file_size_mb: Optional[int] = None
    max_audio_file_size_mb: Optional[int] = None  # НОВОЕ
    max_queue_size: Optional[int] = None
    max_concurrent_requests: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None
```

### 5.4. Worker скрипт для Python 3.12

```python
# transcribe_worker.py (в корне проекта)
# ВАЖНО: Выполняется через Python 3.12!

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МИНИМАЛЬНЫЙ Worker-скрипт для транскрибации аудио через AssemblyAI API.
Запускается через subprocess из основного backend (Python 3.14).

НАЗНАЧЕНИЕ:
  - Wrapper для готового api_transcriber.py
  - Обмен данными через JSON файл
  
ТРЕБОВАНИЯ: Python 3.12 + assemblyai SDK (уже установлены)

Использование:
    py -3.12 transcribe_worker.py --audio <path> --output <json_path>
"""

import argparse
import json
import sys
from pathlib import Path

# Импорт ГОТОВОГО модуля транскрибации
from api_transcriber import transcribe_with_assemblyai


def main():
    """Точка входа - минимальная обработка, максимум переиспользования."""
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
        # Выполняем транскрибацию (вызов ГОТОВОЙ функции)
        # Язык фиксирован = "ru" (только русский по требованию)
        transcription_result = transcribe_with_assemblyai(
            audio_path=audio_path,
            language="ru"
        )
        
        # Формируем результат для backend
        result = {
            "success": True,
            "segments": transcription_result.get("segments", []),
            "text": transcription_result.get("text", "")
        }
        
    except SystemExit as e:
        # AssemblyAI API выбросил ошибку
        result = {"success": False, "error": f"AssemblyAI ошибка: {str(e)}"}
    except Exception as e:
        # Любая другая ошибка
        result = {"success": False, "error": f"Ошибка транскрибации: {str(e)}"}
    
    # Сохраняем результат в JSON
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Exit code для subprocess
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
```

**Ключевые особенности:**
- **Минимальный код** (~45 строк вместо сложной логики)
- **Максимальное переиспользование** готового `api_transcriber.py`
- **Язык фиксирован** = "ru" (не принимается из параметров)
- **Простая обработка ошибок** с логированием в JSON

### 5.5. Сервис транскрибации (вызов subprocess)

```python
# backend/services/transcription.py

"""
Сервис для транскрибации аудио через subprocess с Python 3.12.

ВАЖНО: AssemblyAI SDK несовместим с Python 3.14, поэтому транскрибация
выполняется через отдельный процесс Python 3.12.
"""

import asyncio
import json
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Tuple, Optional, Dict, List
import datetime as dt

from backend.services.logger import log_error


# Константы
PYTHON_312_CMD = ["py", "-3.12"]  # Windows py launcher
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
    # Проверка расширения
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_AUDIO_FORMATS:
        return False, f"Неподдерживаемый формат файла. Допустимы: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
    
    # Проверка размера
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"Размер файла превышает допустимый лимит ({max_size_mb} МБ)"
    
    return True, None


def format_transcription(segments: List[Dict]) -> str:
    """
    Форматирование сегментов транскрипции в читаемый текст.
    """
    lines = []
    for segment in segments:
        timestamp = format_timestamp(segment["start"])
        speaker = segment["speaker"]
        text = segment["text"].strip()
        lines.append(f"[{timestamp}] {speaker}: {text}")
    
    return "\n".join(lines)


def format_timestamp(seconds: float) -> str:
    """Форматирование времени в HH:MM:SS."""
    delta = dt.timedelta(seconds=int(seconds))
    total_seconds = int(delta.total_seconds())
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
    
    Note:
        Язык фиксирован = "ru" (только русский по требованию)
    """
    # Создаем временный файл для результата
    output_json = Path(tempfile.gettempdir()) / f"transcription_{uuid.uuid4().hex}.json"
    
    try:
        # Формируем команду (язык не передаем, он фиксирован в worker)
        cmd = [
            *PYTHON_312_CMD,
            str(WORKER_SCRIPT),
            "--audio", str(file_path),
            "--output", str(output_json)
        ]
        
        # Запускаем subprocess асинхронно
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Проверяем результат
        if not output_json.exists():
            error_msg = stderr.decode("utf-8", errors="replace") if stderr else "Результат не получен"
            return None, f"Ошибка транскрибации: {error_msg}"
        
        # Читаем результат
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
        # Удаляем временный файл результата
        if output_json.exists():
            try:
                output_json.unlink()
            except OSError:
                pass
```

### 5.6. Расширение LLM сервиса

```python
# Добавить в backend/services/llm.py

async def generate_meeting_protocol(transcription: str, username: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Генерировать протокол совещания из транскрипции.
    
    Args:
        transcription: Текст транскрипции
        username: Имя пользователя (для учета токенов)
        
    Returns:
        Кортеж (протокол, ошибка)
    """
    # Получить промпт
    prompt = get_prompt("meeting_protocol")
    if not prompt:
        return None, "Промпт для протокола не найден"
    
    # Формируем полный текст запроса
    full_text = transcription
    
    # Определить тип LLM
    llm_type = get_current_llm_type()
    
    if llm_type == "deepseek":
        return await call_deepseek_protocol(prompt, full_text, username)
    elif llm_type == "lmstudio":
        return await call_lmstudio_protocol(prompt, full_text, username)
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
            timeout=120.0  # Увеличенный таймаут для длинных транскрипций
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
        
        # Учет токенов
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        track_tokens(username, prompt_tokens, completion_tokens)
        
        return result, None
        
    except Exception as e:
        error_msg = f"Ошибка при генерации протокола: {str(e)}"
        log_error(username, "deepseek_protocol", error_msg)
        return None, error_msg
```

### 5.7. Расширение системы промптов

```python
# Модификация backend/services/prompts.py

def get_prompt(prompt_type: str) -> Optional[str]:
    """Получить текущий промпт."""
    if prompt_type == "summary":
        file_path = PROMPTS_DIR / "summary_prompt.txt"
    elif prompt_type == "legal_check":
        file_path = PROMPTS_DIR / "legal_check_prompt.txt"
    elif prompt_type == "meeting_protocol":  # НОВОЕ
        file_path = PROMPTS_DIR / "meeting_protocol_prompt.txt"
    else:
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except IOError:
        return None


def get_all_prompts() -> Dict[str, str]:
    """Получить все промпты."""
    return {
        "summary": get_prompt("summary") or "",
        "legal_check": get_prompt("legal_check") or "",
        "meeting_protocol": get_prompt("meeting_protocol") or ""  # НОВОЕ
    }


def save_prompt(prompt_type: str, content: str) -> bool:
    """Сохранить промпт."""
    if prompt_type == "summary":
        file_path = PROMPTS_DIR / "summary_prompt.txt"
    elif prompt_type == "legal_check":
        file_path = PROMPTS_DIR / "legal_check_prompt.txt"
    elif prompt_type == "meeting_protocol":  # НОВОЕ
        file_path = PROMPTS_DIR / "meeting_protocol_prompt.txt"
    else:
        return False
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except IOError:
        return False


def reset_prompt(prompt_type: str) -> Optional[str]:
    """Сбросить промпт к исходному значению."""
    if prompt_type == "summary":
        default_file = DEFAULTS_DIR / "summary_prompt.txt"
        current_file = PROMPTS_DIR / "summary_prompt.txt"
    elif prompt_type == "legal_check":
        default_file = DEFAULTS_DIR / "legal_check_prompt.txt"
        current_file = PROMPTS_DIR / "legal_check_prompt.txt"
    elif prompt_type == "meeting_protocol":  # НОВОЕ
        default_file = DEFAULTS_DIR / "meeting_protocol_prompt.txt"
        current_file = PROMPTS_DIR / "meeting_protocol_prompt.txt"
    else:
        return None
    
    try:
        with open(default_file, "r", encoding="utf-8") as f:
            default_content = f.read()
        with open(current_file, "w", encoding="utf-8") as f:
            f.write(default_content)
        return default_content
    except IOError:
        return None
```

---

## 6. ПЛАН РЕАЛИЗАЦИИ

### 6.1. Этап 1: Подготовка инфраструктуры (Backend)

| # | Задача | Файл |
|---|--------|------|
| 1.1 | Создать промпт по умолчанию | `data/prompts/defaults/meeting_protocol_prompt.txt` |
| 1.2 | Скопировать в рабочую директорию | `data/prompts/meeting_protocol_prompt.txt` |
| 1.3 | Расширить сервис промптов | `backend/services/prompts.py` |
| 1.4 | Расширить Pydantic схемы | `backend/models/schemas.py` |
| 1.5 | Расширить настройки системы | `backend/services/settings.py` |
| 1.6 | Обновить `settings.json` | `data/settings.json` |

### 6.2. Этап 2: Сервис транскрибации (Backend)

| # | Задача | Файл |
|---|--------|------|
| 2.1 | Создать worker для Python 3.12 | `transcribe_worker.py` |
| 2.2 | Создать сервис транскрибации (subprocess) | `backend/services/transcription.py` |
| 2.3 | Добавить `generate_meeting_protocol()` | `backend/services/llm.py` |
| 2.4 | Добавить endpoint `/api/transcribe` | `backend/main.py` |
| 2.5 | Добавить логику экспорта (2 файла) | `backend/main.py` |

### 6.3. Этап 3: Frontend - Главная страница

| # | Задача | Файл |
|---|--------|------|
| 3.1 | Добавить вкладки на главную страницу | `frontend/index.html` |
| 3.2 | Добавить HTML для формы транскрибации | `frontend/index.html` |
| 3.3 | Добавить логику переключения вкладок | `frontend/js/app.js` |
| 3.4 | Добавить логику загрузки и обработки аудио | `frontend/js/app.js` |
| 3.5 | Добавить логику экспорта (2 кнопки) | `frontend/js/app.js` |
| 3.6 | Добавить стили для вкладок | `frontend/css/style.css` |

### 6.4. Этап 4: Frontend - Админ-панель

| # | Задача | Файл |
|---|--------|------|
| 4.1 | Добавить редактор промпта протокола | `frontend/js/admin.js` |
| 4.2 | Добавить поле настройки размера аудио | `frontend/js/admin.js` |

### 6.5. Этап 5: Зависимости

| # | Задача | Файл |
|---|--------|------|
| 5.1 | Добавить `assemblyai` в requirements.txt | `requirements.txt` |

---

## 7. ДЕТАЛИ FRONTEND

### 7.1. Структура вкладок (index.html)

```html
<!-- Вкладки -->
<div class="main-tabs">
    <button class="main-tab-button active" onclick="showMainTab('contracts')">
        📄 Анализ договоров
    </button>
    <button class="main-tab-button" onclick="showMainTab('transcription')">
        🎤 Расшифровка аудио
    </button>
</div>

<!-- Контент вкладки "Анализ договоров" -->
<div id="contracts-tab" class="main-tab-content active">
    <!-- Существующий контент формы загрузки договора -->
</div>

<!-- Контент вкладки "Расшифровка аудио" -->
<div id="transcription-tab" class="main-tab-content">
    <!-- Форма загрузки аудио -->
    <!-- Прогресс -->
    <!-- Результаты: транскрипция + протокол -->
    <!-- Кнопки экспорта (2 кнопки) -->
</div>
```

### 7.2. Форма транскрибации

```html
<div class="upload-section">
    <h2>Загрузить аудио для расшифровки</h2>
    
    <form id="transcribeForm" enctype="multipart/form-data">
        <div class="form-group">
            <label for="audio-file">Выберите аудиофайл:</label>
            <input type="file" id="audio-file" name="audio_file" 
                   accept=".mp3,.wav,.m4a,.flac,.aac,.ogg,.webm,.mp4,.mov,.avi" required>
            <span id="audio-file-name"></span>
            <small>Поддерживаемые форматы: MP3, WAV, M4A, FLAC, AAC, OGG, WebM, MP4, MOV, AVI</small>
            <small>Язык распознавания: Русский (автоматически)</small>
        </div>
        
        <button type="submit" class="btn btn-primary">Расшифровать</button>
    </form>
    
    <!-- Спиннер (показывается во время транскрибации) -->
    <div id="transcribe-spinner" style="display: none;">
        <div class="spinner"></div>
        <p>Идет транскрибация... Это может занять несколько минут.</p>
    </div>
</div>
```

### 7.3. Отображение результатов

```html
<div id="transcription-result-section" style="display: none;">
    <h2>Результат расшифровки</h2>
    
    <!-- Транскрипция -->
    <div class="result-block">
        <h3>Транскрипция</h3>
        <!-- Формат: [HH:MM:SS] Speaker A: текст -->
        <div id="transcription-content" class="result-content" style="white-space: pre-wrap;"></div>
        <div class="result-actions">
            <button onclick="exportTranscription()" class="btn btn-primary">
                📥 Скачать транскрипцию (Word)
            </button>
            <button onclick="copyTranscription()" class="btn btn-secondary">
                📋 Копировать
            </button>
        </div>
    </div>
    
    <!-- Протокол -->
    <div class="result-block">
        <h3>Протокол совещания</h3>
        <div id="protocol-content" class="result-content"></div>
        <div class="result-actions">
            <button onclick="exportProtocol()" class="btn btn-primary">
                📥 Скачать протокол (Word)
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
```

**Формат транскрипции (Вариант А):**
```
[00:00:15] Speaker A: Добрый день, коллеги, начинаем совещание
[00:00:18] Speaker B: Здравствуйте
[00:00:22] Speaker A: Первый вопрос повестки...
```

### 7.4. Админ-панель: редактор промпта протокола

Добавить в `renderPromptsEditor()`:

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

---

## 8. ОБРАБОТКА ОШИБОК

| Ошибка | Сообщение пользователю | Логирование |
|--------|------------------------|-------------|
| Неподдерживаемый формат | "Неподдерживаемый формат файла. Допустимы: MP3, WAV, M4A..." | `log_error(user, "audio_validation", msg)` |
| Превышен размер файла | "Размер файла превышает допустимый лимит (100 МБ)" | `log_error(user, "audio_size", msg)` |
| Ошибка AssemblyAI API | "Ошибка транскрибации: [текст ошибки]" | `log_error(user, "assemblyai_api", error)` |
| API ключ AssemblyAI не настроен | "API ключ AssemblyAI не настроен" | `log_error(user, "assemblyai_config", msg)` |
| Таймаут subprocess | "Транскрибация превысила лимит времени (10 минут)" | `log_error(user, "transcription_timeout", msg)` |
| Ошибка DeepSeek API | "Ошибка при генерации протокола: [текст ошибки]" | `log_error(user, "deepseek_protocol", error)` |
| Rate limit превышен | "Слишком много запросов (лимит: 2/минуту)" | `log_user_action(user, "rate_limit_hit", "transcribe")` |
| Очередь занята | "Транскрибация уже выполняется. Попробуйте через минуту" | `log_user_action(user, "queue_busy", "transcribe")` |

**Примечание**: Все ошибки логируются через существующую систему `backend/services/logger.py`

### 8.1. Упрощения по обработке ошибок

| Что убрано из ТЗ | Причина |
|------------------|---------|
| Проверка Python 3.12 | **Python 3.12 уже установлен**, проверка не требуется |
| Проверка worker скрипта | Проверяется при первом запросе, не критично |
| Сложная обработка в UI | Просто текст ошибки, без рекомендаций |

---

## 9. КРИТЕРИИ ПРИЕМКИ

### 9.1. Функциональные критерии
- [ ] Вкладки на главной странице работают корректно
- [ ] Загрузка аудиофайлов до 100 МБ
- [ ] Валидация формата и размера файла
- [ ] Транскрибация через AssemblyAI API
- [ ] Отображение транскрипции с разбивкой по спикерам
- [ ] Генерация протокола через DeepSeek API
- [ ] Экспорт транскрипции в Word (`Транскрипция_YYYY-MM-DD_HH-MM.docx`)
- [ ] Экспорт протокола в Word (`Протокол_YYYY-MM-DD_HH-MM.docx`)
- [ ] Копирование в буфер обмена
- [ ] Редактирование промпта протокола в админке
- [ ] Сброс промпта к значению по умолчанию
- [ ] Настройка максимального размера аудио в админке

### 9.2. Нефункциональные критерии
- [ ] Rate limiting работает корректно
- [ ] Временные файлы удаляются после обработки (аудио + JSON результата)
- [ ] Логирование ошибок
- [ ] Учет токенов для DeepSeek
- [ ] **Subprocess Python 3.12 работает корректно**
- [ ] Worker скрипт обрабатывает ошибки и возвращает понятные сообщения

---

## 10. ЗАВИСИМОСТИ (requirements.txt)

Добавить:
```
assemblyai>=0.48.0
```

---

## 11. ФАЙЛ ПРОМПТА ПО УМОЛЧАНИЮ

**Путь**: `data/prompts/defaults/meeting_protocol_prompt.txt`

**Содержимое**:
```
##Роль##

Ты опытный секретарь, который способен составлять краткие и емкие протоколы совещаний. 

У тебя талант и призвание составлять протоколы совещаний, убирая оттуда незначащую информацию, без потери смысла. 

Так же ты очень качественно определяешь, какие задания и действия необходимо совершить или создать по итогам совещания и назначаешь на них ответственных.

##Задача##

Составить качественный, краткий и емкий протокол совещания по следующей транскрипции:

##Транскрипция##

```

---

## 12. КЛЮЧЕВЫЕ РЕШЕНИЯ И УПРОЩЕНИЯ (v1.2)

### 12.1. Что упрощено по сравнению с v1.1:

1. **Архитектура**: `transcribe_worker.py` — это МИНИМАЛЬНЫЙ wrapper (~45 строк), максимум переиспользует готовый `api_transcriber.py`
2. **Язык**: Фиксирован = "ru", без выбора в UI и параметров
3. **Прогресс**: Простой спиннер вместо полноценного progress bar
4. **Rate limiting**: 2 запроса/минуту (вместо 10)
5. **Очередь**: Максимум 1 одновременный запрос (вместо 5)
6. **Проверки**: Python 3.12 НЕ проверяется (уже установлен)
7. **Ошибки**: Простой текст + логирование, без рекомендаций

### 12.2. Критические требования:

1. **⚠️ AssemblyAI SDK несовместим с Python 3.14** — транскрибация ОБЯЗАТЕЛЬНО через subprocess Python 3.12
2. **Python 3.12** доступен через `py -3.12` (Windows py launcher), **уже установлен**, проверка не нужна
3. **API ключ AssemblyAI** хранится в `.env` (ASSEMBLYAI_API_KEY)
4. **Временные файлы** удаляются после обработки (try/finally)
5. **Результаты НЕ сохраняются** на сервере — только в памяти браузера + экспорт в Word
6. **Формат транскрипции**: `[HH:MM:SS] Speaker A: текст` (Вариант А)
7. **Логирование**: Все ошибки через `backend/services/logger.py`

### 12.3. Готовый код для переиспользования:

- ✅ `api_transcriber.py` — готовая транскрибация (не менять!)
- ✅ `backend/services/document.py` — экспорт в Word
- ✅ `backend/services/prompts.py` — система промптов (расширить)
- ✅ `backend/services/llm.py` — вызов DeepSeek (расширить)
- ✅ `backend/services/logger.py` — логирование
- ✅ `backend/services/settings.py` — настройки (расширить)

---

## 13. ТЕСТИРОВАНИЕ WORKER СКРИПТА

Для проверки работоспособности транскрибации можно запустить worker напрямую:

```powershell
# Проверка Python 3.12 (должен быть установлен)
py -3.12 --version

# Тестовый запуск транскрибации (язык фиксирован = ru)
py -3.12 transcribe_worker.py --audio "test_audio.mp3" --output "test_result.json"

# Проверка результата
Get-Content test_result.json

# Ожидаемый формат JSON:
# {
#   "success": true,
#   "segments": [
#     {"start": 15.2, "end": 18.5, "speaker": "Speaker A", "text": "Добрый день"},
#     ...
#   ],
#   "text": "Полный текст транскрипции"
# }
```

---

**Дата создания**: 03.12.2025  
**Версия**: 1.2 (финальная с уточнениями и упрощениями)  
**Изменения v1.2**:
- Упрощена архитектура (минимальный wrapper)
- Язык фиксирован (только русский)
- Rate limit: 2 запроса/минуту, 1 одновременный
- Спиннер вместо progress bar
- Формат транскрипции: `[HH:MM:SS] Speaker: текст`
- Убраны избыточные проверки

