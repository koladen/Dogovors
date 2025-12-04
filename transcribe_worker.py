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

