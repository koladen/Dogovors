#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для автоматической расшифровки аудиозаписи совещания через AssemblyAI API.

Функциональность:
1. Расшифровка аудио через AssemblyAI API с автоматической диаризацией.
2. Формирование текстовой расшифровки в MD файле с временными метками и разделением по спикерам.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from api_transcriber import transcribe_with_assemblyai
except ImportError:
    transcribe_with_assemblyai = None  # type: ignore

# try:
#     from summary_generator import generate_summary
# except ImportError:
#     generate_summary = None  # type: ignore


def _parse_args() -> argparse.Namespace:
    """Возвращает параметры командной строки."""

    parser = argparse.ArgumentParser(
        description="Расшифровка совещания и подготовка протокола через AssemblyAI API."
    )
    parser.add_argument(
        "--audio",
        default="Conversation/19.12.2018 - Совещание на объекте ЖК СК.mp3",
        help="Путь к аудиофайлу для расшифровки.",
    )
    parser.add_argument(
        "--language",
        default="ru",
        help="Язык распознавания (например, ru, en).",
    )
    parser.add_argument(
        "--output-dir",
        default="Conversation/output",
        help="Каталог для сохранения результатов.",
    )
    parser.add_argument(
        "--summary-sentences",
        type=int,
        default=5,
        help="Максимальное число предложений в саммари (используется как подсказка для модели).",
    )
    parser.add_argument(
        "--roles-mapping",
        default="",
        help=(
            "Список соответствий ролей формата 'Роль=Speaker A;Техдир=Speaker B'. "
            "Если не задан, используются имена спикеров из диаризации AssemblyAI."
        ),
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API ключ AssemblyAI (по умолчанию из файла .env или переменной окружения ASSEMBLYAI_API_KEY).",
    )
    parser.add_argument(
        "--hf-token",
        default=None,
        help="Токен Hugging Face API (по умолчанию из файла .env или переменной окружения HUGGINGFACE_API_TOKEN или HF_TOKEN).",
    )
    # parser.add_argument(
    #     "--no-summary",
    #     action="store_true",
    #     help="Пропустить генерацию саммари и плана действий, выполнить только транскрибацию.",
    # )

    return parser.parse_args()


def _map_roles(enriched_segments: List[Dict], mapping: str) -> List[Dict]:
    """Переименовывает спикеров в соответствии с пользовательскими ролями."""

    if not mapping.strip():
        return enriched_segments

    role_map = {}
    for pair in mapping.split(";"):
        if "=" in pair:
            role, speaker = pair.split("=", maxsplit=1)
            role_map[speaker.strip()] = role.strip()

    rewritten: List[Dict] = []
    for segment in enriched_segments:
        speaker = segment["speaker"]
        rewritten.append({**segment, "speaker": role_map.get(speaker, speaker)})
    return rewritten


def _format_timestamp(seconds: float) -> str:
    """Возвращает строку с временной меткой HH:MM:SS."""

    delta = dt.timedelta(seconds=int(seconds))
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ACTION_KEYWORDS = (
#     "поруч",
#     "нужно",
#     "надо",
#     "срок",
#     "ответствен",
#     "подготов",
#     "провер",
#     "закупить",
#     "соглас",
# )


# def _extract_action_items(segments: List[Dict]) -> List[str]:
#     """Выделяет потенциальные поручения на основании ключевых слов."""

#     items: List[str] = []
#     for segment in segments:
#         text = segment["text"].strip()
#         lowered = text.lower()
#         if any(keyword in lowered for keyword in ACTION_KEYWORDS):
#             timestamp = _format_timestamp(segment["start"])
#             items.append(f"{timestamp} {segment['speaker']}: {text}")
#     return items


def _save_transcript(segments: List[Dict], output_dir: Path) -> None:
    """Сохраняет полную транскрипцию в файл transcript.md."""

    output_dir.mkdir(parents=True, exist_ok=True)
    transcript_file = output_dir / "transcript.md"

    lines = ["# Транскрипция совещания", ""]
    lines.append(f"- Дата подготовки: {dt.datetime.now().strftime('%d.%m.%Y %H:%M')}")
    lines.append(f"- Количество реплик: {len(segments)}")
    lines.append("")

    for segment in segments:
        timestamp = _format_timestamp(segment["start"])
        speaker = segment["speaker"]
        text = segment["text"].strip().replace("  ", " ")
        lines.append(f"[{timestamp}] {speaker}: {text}")

    transcript_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


# def _save_summary(summary: str, output_dir: Path) -> None:
#     """Сохраняет краткое саммари в файл summary.md."""

#     output_dir.mkdir(parents=True, exist_ok=True)
#     summary_file = output_dir / "summary.md"

#     lines = ["# Краткое саммари совещания", ""]
#     lines.append(f"- Дата подготовки: {dt.datetime.now().strftime('%d.%m.%Y %H:%M')}")
#     lines.append("")
#     lines.append(summary)

#     summary_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


# def _summarize_action_items(action_items: List[str], hf_token: Optional[str] = None) -> str:
#     """
#     Суммирует список поручений, если их слишком много.
#
#     Args:
#         action_items: Список поручений
#         hf_token: Токен Hugging Face API для суммаризации
#
#     Returns:
#         Суммированный текст поручений или исходный список, если суммаризация не требуется
#     """
#     # Если поручений меньше 10, не суммируем
#     if len(action_items) < 10:
#         return "\n".join(f"- {item}" for item in action_items)
#
#     # Формируем текст для суммаризации
#     action_text = "\n".join(action_items)
#
#     # Если текст слишком длинный (больше 4000 символов), суммируем
#     if len(action_text) > 4000 or len(action_items) > 20:
#         if generate_summary is not None:
#             try:
#                 # Используем функцию суммаризации текста
#                 from summary_generator import summarize_text
#
#                 summary = summarize_text(action_text, hf_token)
#                 if summary and summary.strip():
#                     return summary
#             except Exception as e:
#                 print(f"Предупреждение: не удалось создать саммари для плана действий: {e}")
#
#     # Если суммаризация не удалась или не требуется, возвращаем исходный список
#     return "\n".join(f"- {item}" for item in action_items)


# def _save_action_plan(action_items: List[str], output_dir: Path, hf_token: Optional[str] = None) -> None:
#     """Сохраняет план действий в файл action_plan.md."""

#     output_dir.mkdir(parents=True, exist_ok=True)
#     action_plan_file = output_dir / "action_plan.md"

#     lines = ["# План действий", ""]
#     lines.append(f"- Дата подготовки: {dt.datetime.now().strftime('%d.%m.%Y %H:%M')}")
#     lines.append("")
#     lines.append("## Поручения")
#     lines.append("")

#     if not action_items:
#         lines.append("- Поручения не обнаружены.")
#     else:
#         # Применяем суммаризацию, если поручений слишком много
#         action_content = _summarize_action_items(action_items, hf_token)
#         lines.append(action_content)

#     action_plan_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


# def _save_outputs(segments: List[Dict], summary: str, action_items: List[str], output_dir: Path, hf_token: Optional[str] = None) -> None:
#     """Сохраняет все результаты в отдельные MD файлы."""

#     _save_transcript(segments, output_dir)
#     _save_summary(summary, output_dir)
#     _save_action_plan(action_items, output_dir, hf_token)

#     # Также сохраняем JSON для совместимости
#     output_dir.mkdir(parents=True, exist_ok=True)
#     segments_file = output_dir / "transcript_segments.json"
#     segments_file.write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    """Точка входа сценария."""

    args = _parse_args()
    audio_path = Path(args.audio)
    if not audio_path.exists():
        raise SystemExit(f"Аудиофайл не найден: {audio_path}")

    # Проверяем наличие модулей
    if transcribe_with_assemblyai is None:
        raise SystemExit(
            "Модуль api_transcriber не найден. Убедитесь, что файл Conversation/api_transcriber.py существует."
        )

    # if generate_summary is None:
    #     raise SystemExit(
    #         "Модуль summary_generator не найден. Убедитесь, что файл Conversation/summary_generator.py существует."
    #     )

    # Транскрибирование через AssemblyAI API
    print(f"Начинаю расшифровку файла через AssemblyAI API: {audio_path}")
    result = transcribe_with_assemblyai(
        audio_path=audio_path,
        api_key=args.api_key,
        language=args.language,
    )
    segments = result.get("segments", [])

    if not segments:
        raise SystemExit("Не удалось получить сегменты транскрипции.")

    print(f"Получено {len(segments)} сегментов транскрипции")

    # Применяем маппинг ролей
    enriched_segments = _map_roles(segments, args.roles_mapping)

    # Нормализуем путь output_dir относительно директории скрипта
    output_dir = Path(args.output_dir)
    # Если путь начинается с "Conversation/", убираем этот префикс
    if output_dir.parts[0] == "Conversation" and len(output_dir.parts) > 1:
        output_dir = Path(*output_dir.parts[1:])
    # Если путь относительный и не начинается с текущей директории, делаем его относительно директории скрипта
    if not output_dir.is_absolute():
        script_dir = Path(__file__).parent
        output_dir = (script_dir / output_dir).resolve()

    # Сохраняем только транскрипцию
    _save_transcript(enriched_segments, output_dir)

    # Также сохраняем JSON для совместимости
    output_dir.mkdir(parents=True, exist_ok=True)
    segments_file = output_dir / "transcript_segments.json"
    segments_file.write_text(json.dumps(enriched_segments, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nГотово! Результаты сохранены в {output_dir}:")
    print(f"  - Транскрипция: {output_dir / 'transcript.md'}")
    print(f"  - JSON сегменты: {output_dir / 'transcript_segments.json'}")


if __name__ == "__main__":
    main()

