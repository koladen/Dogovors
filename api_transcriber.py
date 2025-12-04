#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для транскрибирования аудио через AssemblyAI API с поддержкой диаризации.

Функциональность:
- Загрузка аудиофайла в AssemblyAI
- Транскрибирование с автоматической диаризацией спикеров
- Преобразование результата в формат, совместимый с текущим кодом
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import assemblyai as aai
except ImportError:
    aai = None  # type: ignore


def transcribe_with_assemblyai(
    audio_path: Path,
    api_key: Optional[str] = None,
    language: str = "ru",
) -> Dict:
    """
    Выполняет транскрибирование через AssemblyAI API с диаризацией.

    Args:
        audio_path: Путь к аудиофайлу для транскрибирования
        api_key: API ключ AssemblyAI (если не указан, берется из переменной окружения)
        language: Язык распознавания (ru, en и т.д.)

    Returns:
        Словарь с ключом 'segments', где каждый сегмент содержит:
        - 'start': float - время начала в секундах
        - 'end': float - время окончания в секундах
        - 'text': str - текст транскрипции
        - 'speaker': str - идентификатор спикера (например, 'A', 'B', 'C')

    Raises:
        SystemExit: Если модуль assemblyai не установлен или API ключ не найден
    """
    if aai is None:
        raise SystemExit(
            "Модуль 'assemblyai' не найден. Установите его командой: pip install assemblyai"
        )

    # Получаем API ключ из параметра, переменной окружения или .env файла
    api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "Не указан API ключ AssemblyAI. "
            "Установите переменную ASSEMBLYAI_API_KEY в файле .env или передайте ключ через параметр --api-key"
        )

    # Настраиваем клиент
    aai.settings.api_key = api_key

    # Создаем транскрибер с диаризацией
    transcriber = aai.Transcriber()

    print(f"Загружаю файл в AssemblyAI: {audio_path}")
    
    # Загружаем и транскрибируем файл
    config = aai.TranscriptionConfig(
        language_code=language,
        speaker_labels=True,  # Включаем диаризацию
    )

    transcript = transcriber.transcribe(str(audio_path), config=config)

    # Ожидаем завершения транскрибации
    print("Ожидаю завершения транскрибации...")
    while transcript.status == aai.TranscriptStatus.queued or transcript.status == aai.TranscriptStatus.processing:
        time.sleep(1)
        transcript = transcriber.get_transcript(transcript.id)

    # Проверяем результат
    if transcript.status == aai.TranscriptStatus.error:
        raise SystemExit(f"Ошибка транскрибации: {transcript.error}")

    print("Транскрибация завершена успешно")

    # Преобразуем результат в нужный формат
    segments: List[Dict] = []
    
    if transcript.utterances:
        # Используем utterances (сегменты с диаризацией)
        for utterance in transcript.utterances:
            segments.append({
                "start": utterance.start / 1000.0,  # Конвертируем из миллисекунд в секунды
                "end": utterance.end / 1000.0,
                "text": utterance.text,
                "speaker": f"Speaker {utterance.speaker}",  # Форматируем как "Speaker A", "Speaker B" и т.д.
            })
    elif transcript.words:
        # Если utterances нет, используем words и группируем по спикерам
        current_speaker = None
        current_start = None
        current_text_parts = []
        
        for word in transcript.words:
            speaker_id = f"Speaker {word.speaker}" if word.speaker else "Speaker ?"
            
            if speaker_id != current_speaker and current_speaker is not None:
                # Сохраняем предыдущий сегмент
                if current_start is not None and current_text_parts:
                    segments.append({
                        "start": current_start / 1000.0,
                        "end": word.start / 1000.0,
                        "text": " ".join(current_text_parts),
                        "speaker": current_speaker,
                    })
                current_text_parts = []
            
            current_speaker = speaker_id
            if current_start is None:
                current_start = word.start
            current_text_parts.append(word.text)
        
        # Сохраняем последний сегмент
        if current_start is not None and current_text_parts:
            last_word = transcript.words[-1]
            segments.append({
                "start": current_start / 1000.0,
                "end": last_word.end / 1000.0,
                "text": " ".join(current_text_parts),
                "speaker": current_speaker or "Speaker ?",
            })
    else:
        # Если нет ни utterances, ни words, используем segments без диаризации
        for segment in transcript.segments:
            segments.append({
                "start": segment.start / 1000.0,
                "end": segment.end / 1000.0,
                "text": segment.text,
                "speaker": "Speaker ?",  # Диаризация недоступна
            })

    return {"segments": segments, "text": transcript.text}

