# file_utils.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с более гибкой проверкой путей
import os
import re
from pathlib import Path
from typing import Optional

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.webp'}
# Максимальный размер файла (5 MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

def validate_filename(filename: str) -> str:
    """
    Очищает имя файла от опасных символов
    """
    if not filename:
        raise ValueError("Empty filename")
    
    # ✅ БЛОКИРУЕМ ОПАСНЫЕ ПАТТЕРНЫ
    dangerous_patterns = [
        r"\.\./",  # path traversal
        r"\.\.\\",  # path traversal Windows
        r"[<>:\"|?*]",  # недопустимые символы Windows
        r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])(\.|$)",  # зарезервированные имена Windows
        r"<script",  # XSS
        r"javascript:",  # XSS
    ]
    
    filename_lower = filename.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, filename_lower):
            raise ValueError("Invalid filename: contains dangerous characters")
    
    # Очищаем остальные символы
    safe_name = re.sub(r'[^a-zA-Z0-9._\-\s]', '_', filename)
    
    # Убираем множественные точки
    safe_name = re.sub(r'\.{2,}', '.', safe_name)
    
    # ✅ ПРОВЕРЯЕМ ДЛИНУ
    if len(safe_name) > 100:
        name_part, ext = os.path.splitext(safe_name)
        safe_name = name_part[:95] + ext
        raise ValueError("Filename too long")
    
    return safe_name

def validate_file_extension(filename: str) -> bool:
    """
    Проверяет, разрешено ли расширение файла
    
    Args:
        filename: Имя файла
        
    Returns:
        True если расширение разрешено
    """
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS

def create_safe_file_path(user_id: int, filename: str) -> str:
    """
    Создает безопасный путь к файлу пользователя
    
    Args:
        user_id: ID пользователя
        filename: Имя файла
        
    Returns:
        Безопасный путь к файлу
        
    Raises:
        ValueError: Если путь небезопасен или расширение не разрешено
    """
    try:
        # ✅ ИСПРАВЛЕНИЕ: Более гибкая проверка расширения
        # Если нет расширения, добавляем .jpg по умолчанию
        if not os.path.splitext(filename)[1]:
            filename = f"{filename}.jpg"
        
        # Проверяем расширение файла
        if not validate_file_extension(filename):
            # ✅ ИСПРАВЛЕНИЕ: Попробуем исправить расширение автоматически
            name_without_ext = os.path.splitext(filename)[0]
            filename = f"{name_without_ext}.jpg"
        
        # Очищаем имя файла
        safe_filename = validate_filename(filename)
        
        # Создаем директорию пользователя
        user_dir = Path(f"files/{user_id}")
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем полный путь
        file_path = user_dir / safe_filename
        
        # ✅ ИСПРАВЛЕНИЕ: Упрощенная проверка безопасности
        # Проверяем только что путь начинается с files/{user_id}
        absolute_path = file_path.resolve()
        expected_prefix = Path(f"files/{user_id}").resolve()
        
        # Проверяем, что файл будет создан в правильной директории
        if not str(absolute_path).startswith(str(expected_prefix)):
            raise ValueError("File path outside allowed directory")
        
        return str(file_path)
        
    except Exception as e:
        raise ValueError(f"Failed to create safe path: {e}")

def validate_file_size(file_path: str) -> bool:
    """
    Проверяет размер файла
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        True если размер допустимый
    """
    try:
        size = os.path.getsize(file_path)
        return size <= MAX_FILE_SIZE
    except OSError:
        return False

def safe_file_exists(file_path: str, user_id: int) -> bool:
    """
    Безопасно проверяет существование файла в директории пользователя
    
    Args:
        file_path: Путь к файлу
        user_id: ID пользователя
        
    Returns:
        True если файл существует в разрешенной директории
    """
    try:
        path = Path(file_path)
        user_dir = Path(f"files/{user_id}").resolve()
        
        # Проверяем, что файл находится в директории пользователя
        if not str(path.resolve()).startswith(str(user_dir)):
            return False
            
        return path.exists()
    except Exception:
        return False

# ✅ НОВАЯ ФУНКЦИЯ: Простая версия для отладки
def create_simple_file_path(user_id: int, filename: str) -> str:
    """
    Упрощенная версия создания пути файла для отладки
    """
    # Создаем директорию
    user_dir = f"files/{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    
    # Очищаем имя файла от опасных символов
    safe_name = re.sub(r'[^\w\.-]', '_', filename)
    
    # Если нет расширения, добавляем .jpg
    if not os.path.splitext(safe_name)[1]:
        safe_name += '.jpg'
    
    full_path = os.path.join(user_dir, safe_name)
    return full_path