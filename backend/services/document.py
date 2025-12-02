from pathlib import Path
from typing import Optional, Tuple
import tempfile
import os

def extract_text_from_file(file_path: Path, file_extension: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Извлечь текст из файла в зависимости от расширения.

    Args:
        file_path: Путь к файлу
        file_extension: Расширение файла (.doc, .docx, .pdf)

    Returns:
        Кортеж (текст, ошибка). Если успешно - (текст, None), если ошибка - (None, текст_ошибки)
    """
    try:
        if file_extension == ".docx":
            return extract_from_docx(file_path)
        elif file_extension == ".doc":
            return extract_from_doc(file_path)
        elif file_extension == ".pdf":
            return extract_from_pdf(file_path)
        else:
            return None, "Неподдерживаемый формат файла. Допустимы: .doc, .docx, .pdf"
    except Exception as e:
        return None, f"Произошла ошибка при обработке файла: {str(e)}"

def extract_from_docx(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Извлечь текст из .docx файла.

    Args:
        file_path: Путь к файлу

    Returns:
        Кортеж (текст, ошибка)
    """
    try:
        from docx import Document

        doc = Document(str(file_path))

        # Извлечь текст из параграфов
        paragraphs_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs_text.append(para.text)

        # Извлечь текст из таблиц
        tables_text = []
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        row_text.append(cell.text)
                if row_text:
                    tables_text.append(" | ".join(row_text))

        # Объединить весь текст
        full_text = "\n".join(paragraphs_text)
        if tables_text:
            full_text += "\n\n=== ТАБЛИЦЫ ===\n\n" + "\n".join(tables_text)

        if not full_text.strip():
            return None, "Файл не содержит текста или пуст."

        return full_text, None

    except Exception as e:
        error_msg = str(e).lower()
        if "password" in error_msg or "encrypted" in error_msg:
            return None, "Файл защищен паролем. Снимите защиту и попробуйте снова."
        elif "corrupt" in error_msg or "invalid" in error_msg:
            return None, "Файл поврежден и не может быть обработан. Попробуйте другой файл."
        else:
            return None, f"Ошибка при чтении файла: {str(e)}"

def extract_from_doc(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Извлечь текст из .doc файла через COM (pywin32).

    ВАЖНО: Работает только на Windows с установленным Microsoft Word!

    Args:
        file_path: Путь к файлу

    Returns:
        Кортеж (текст, ошибка)
    """
    try:
        import pythoncom
        import win32com.client

        # Инициализация COM для текущего потока
        pythoncom.CoInitialize()

        try:
            # Создать экземпляр Word
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False  # Не показывать окно Word

            # Открыть документ
            # Преобразуем путь в абсолютный для COM
            abs_path = str(file_path.resolve())

            try:
                doc = word.Documents.Open(abs_path, ReadOnly=True, PasswordDocument="")
            except Exception as e:
                if "password" in str(e).lower():
                    return None, "Файл защищен паролем. Снимите защиту и попробуйте снова."
                raise

            try:
                # Извлечь весь текст
                full_text = doc.Content.Text

                # Извлечь текст из таблиц (они могут не попасть в Content.Text)
                tables_text = []
                for table in doc.Tables:
                    table_content = []
                    for row in table.Rows:
                        row_text = []
                        for cell in row.Cells:
                            cell_text = cell.Range.Text.strip()
                            # Убрать служебные символы Word
                            cell_text = cell_text.replace('\r', '').replace('\x07', '')
                            if cell_text:
                                row_text.append(cell_text)
                        if row_text:
                            table_content.append(" | ".join(row_text))
                    if table_content:
                        tables_text.append("\n".join(table_content))

                # Объединить текст
                result_text = full_text.strip()
                if tables_text:
                    result_text += "\n\n=== ТАБЛИЦЫ ===\n\n" + "\n\n".join(tables_text)

                if not result_text.strip():
                    return None, "Файл не содержит текста или пуст."

                return result_text, None

            finally:
                # Закрыть документ без сохранения
                doc.Close(SaveChanges=False)

        finally:
            # Закрыть Word
            word.Quit()
            pythoncom.CoUninitialize()

    except ImportError:
        return None, "Модуль pywin32 не установлен. Установите: pip install pywin32"
    except Exception as e:
        error_msg = str(e).lower()
        if "password" in error_msg:
            return None, "Файл защищен паролем. Снимите защиту и попробуйте снова."
        elif "corrupt" in error_msg or "cannot open" in error_msg:
            return None, "Файл поврежден и не может быть обработан. Попробуйте другой файл."
        elif "word" in error_msg and ("not found" in error_msg or "failed" in error_msg):
            return None, "Microsoft Word не установлен на сервере. Используйте .docx или .pdf формат."
        else:
            return None, f"Ошибка при чтении .doc файла: {str(e)}"

def extract_from_pdf(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Извлечь текст из .pdf файла.

    Args:
        file_path: Путь к файлу

    Returns:
        Кортеж (текст, ошибка)
    """
    try:
        import PyPDF2

        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)

            # Проверка на защиту паролем
            if pdf_reader.is_encrypted:
                return None, "Файл защищен паролем. Снимите защиту и попробуйте снова."

            # Извлечь текст со всех страниц
            text_parts = []
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                page_text = page.extract_text()
                if page_text.strip():
                    text_parts.append(f"=== Страница {page_num} ===\n{page_text}")

            full_text = "\n\n".join(text_parts)

            if not full_text.strip():
                return None, "PDF не содержит текстового слоя (возможно, это скан). Используйте .docx"

            return full_text, None

    except Exception as e:
        error_msg = str(e).lower()
        if "password" in error_msg or "encrypted" in error_msg:
            return None, "Файл защищен паролем. Снимите защиту и попробуйте снова."
        elif "corrupt" in error_msg or "invalid" in error_msg or "damaged" in error_msg:
            return None, "Файл поврежден и не может быть обработан. Попробуйте другой файл."
        else:
            return None, f"Ошибка при чтении PDF: {str(e)}"

def estimate_token_count(text: str) -> int:
    """
    Оценить количество токенов в тексте.

    Используем простую эвристику: ~1 токен = 4 символа для русского текста.

    Args:
        text: Текст для оценки

    Returns:
        Примерное количество токенов
    """
    return len(text) // 4

def check_text_size(text: str, max_tokens: int = 128000) -> Tuple[bool, Optional[str]]:
    """
    Проверить размер текста на превышение лимита токенов.

    Args:
        text: Текст для проверки
        max_tokens: Максимальное количество токенов (по умолчанию 128K)

    Returns:
        Кортеж (результат, ошибка). True если размер допустим, False если превышен
    """
    token_count = estimate_token_count(text)

    if token_count > max_tokens:
        pages_estimate = token_count // 1500  # Примерно 1500 токенов = 1 страница
        return False, f"Документ слишком большой для обработки (примерно {pages_estimate} страниц, лимит: 100 страниц)."

    return True, None


def create_word_document(content: str, filename: str = "Анализ_договора") -> BytesIO:
    """
    Создать Word документ из markdown-контента.

    Args:
        content: Содержимое в формате Markdown
        filename: Имя файла (без расширения)

    Returns:
        BytesIO объект с содержимым .docx файла
    """
    from docx import Document
    from docx.shared import Pt, RGBColor
    from io import BytesIO
    import re

    doc = Document()

    # Разбить контент на строки
    lines = content.split('\n')

    for line in lines:
        line = line.strip()

        if not line:
            # Пустая строка - добавить параграф
            doc.add_paragraph()
            continue

        # Заголовки (начинаются с #)
        if line.startswith('#'):
            level = len(re.match(r'^#+', line).group())
            title = line.lstrip('#').strip()

            heading = doc.add_heading(title, level=min(level, 3))
            continue

        # Таблицы (строки с |)
        if '|' in line:
            # Простая обработка таблиц - будет добавлена в следующем шаге
            doc.add_paragraph(line)
            continue

        # Обычный текст
        doc.add_paragraph(line)

    # Сохранить в BytesIO
    doc_io = BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)

    return doc_io