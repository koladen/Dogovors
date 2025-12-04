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
        # Проверка существования worker-скрипта
        if not WORKER_SCRIPT.exists():
            return None, f"Worker-скрипт не найден: {WORKER_SCRIPT}"
        
        # Проверка существования аудиофайла
        if not file_path.exists():
            return None, f"Аудиофайл не найден: {file_path}"
        
        cmd = [
            *PYTHON_312_CMD,
            str(WORKER_SCRIPT),
            "--audio", str(file_path),
            "--output", str(output_json)
        ]
        
        # Используем синхронный subprocess.run в отдельном потоке (работает надёжно на Windows)
        def run_subprocess():
            return subprocess.run(
                cmd,
                capture_output=True,
                text=False
            )
        
        result = await asyncio.to_thread(run_subprocess)
        
        # Проверка кода возврата процесса
        if result.returncode != 0:
            error_msg = result.stderr.decode("utf-8", errors="replace") if result.stderr else "Неизвестная ошибка subprocess"
            stdout_msg = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
            return None, f"Worker завершился с ошибкой (код {result.returncode}):\nSTDERR: {error_msg}\nSTDOUT: {stdout_msg}"
        
        if not output_json.exists():
            error_msg = result.stderr.decode("utf-8", errors="replace") if result.stderr else "Результат не получен"
            stdout_msg = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
            return None, f"Ошибка транскрибации - файл результата не создан:\nSTDERR: {error_msg}\nSTDOUT: {stdout_msg}"
        
        result = json.loads(output_json.read_text(encoding="utf-8"))
        
        if not result.get("success"):
            return None, result.get("error", "Неизвестная ошибка")
        
        segments = result.get("segments", [])
        if not segments:
            return None, "Не удалось получить транскрипцию"
        
        formatted = format_transcription(segments)
        return formatted, None
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = str(e) if str(e) else repr(e)
        return None, f"Ошибка при запуске транскрибации: {error_msg}\n{error_details}"
    
    finally:
        if output_json.exists():
            try:
                output_json.unlink()
            except OSError:
                pass

