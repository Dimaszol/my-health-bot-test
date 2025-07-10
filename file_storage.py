# file_storage.py - Универсальное файловое хранилище

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class FileStorage:
    """Универсальное файловое хранилище (Railway Volumes + подготовка к S3)"""
    
    def __init__(self):
        """Инициализация файлового хранилища"""
        # Проверяем, есть ли persistent storage (Railway Volumes)
        self.persistent_dir = "/app/persistent_files"
        self.temp_dir = "/app/files"
        
        # Определяем, где хранить файлы
        if os.path.exists(self.persistent_dir):
            self.storage_dir = self.persistent_dir
            self.storage_type = "persistent"
            logger.info("✅ Используем Railway Volumes для хранения файлов")
        else:
            self.storage_dir = self.temp_dir
            self.storage_type = "temporary"
            logger.warning("⚠️ Используем временное хранилище (файлы потеряются при рестарте)")
        
        # Создаем базовую структуру
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"📁 Хранилище инициализировано: {self.storage_dir}")
    
    def get_user_dir(self, user_id: int) -> str:
        """Получает путь к директории пользователя"""
        user_dir = os.path.join(self.storage_dir, f"users/{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    
    def save_file(self, user_id: int, filename: str, source_path: str) -> Tuple[bool, str]:
        """
        Сохраняет файл в постоянное хранилище
        
        Args:
            user_id: ID пользователя
            filename: Имя файла
            source_path: Путь к исходному файлу
            
        Returns:
            Tuple[bool, str]: (успех, путь_к_файлу_или_ошибка)
        """
        try:
            # Получаем директорию пользователя
            user_dir = self.get_user_dir(user_id)
            
            # Создаем безопасное имя файла
            safe_filename = self._sanitize_filename(filename)
            
            # Полный путь к файлу
            destination_path = os.path.join(user_dir, safe_filename)
            
            # Копируем файл
            shutil.copy2(source_path, destination_path)
            
            logger.info(f"✅ Файл сохранен: {destination_path}")
            return True, destination_path
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения файла: {e}")
            return False, f"Save error: {str(e)}"
    
    def file_exists(self, file_path: str) -> bool:
        """Проверяет существование файла"""
        try:
            return os.path.exists(file_path) and os.path.isfile(file_path)
        except Exception:
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """Удаляет файл"""
        try:
            if self.file_exists(file_path):
                os.remove(file_path)
                logger.info(f"✅ Файл удален: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка удаления файла: {e}")
            return False
    
    def delete_user_files(self, user_id: int) -> bool:
        """Удаляет все файлы пользователя (для GDPR)"""
        try:
            user_dir = os.path.join(self.storage_dir, f"users/{user_id}")
            
            if os.path.exists(user_dir):
                shutil.rmtree(user_dir)
                logger.info(f"✅ Все файлы пользователя {user_id} удалены")
                return True
            else:
                logger.info(f"📂 Папка пользователя {user_id} не найдена")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка удаления файлов пользователя {user_id}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """Получает информацию о файле"""
        try:
            if not self.file_exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'exists': True
            }
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о файле: {e}")
            return None
    
    def get_storage_stats(self) -> dict:
        """Получает статистику использования хранилища"""
        try:
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(self.storage_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except OSError:
                        continue
            
            # Конвертируем в MB
            total_size_mb = total_size / (1024 * 1024)
            
            return {
                'total_size_mb': round(total_size_mb, 2),
                'file_count': file_count,
                'storage_type': self.storage_type,
                'storage_path': self.storage_dir
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {
                'total_size_mb': 0,
                'file_count': 0,
                'storage_type': self.storage_type,
                'storage_path': self.storage_dir
            }
    
    def _sanitize_filename(self, filename: str) -> str:
        """Создает безопасное имя файла"""
        import re
        
        # Убираем опасные символы
        safe_name = re.sub(r'[^\w\.-]', '_', filename)
        
        # Ограничиваем длину
        if len(safe_name) > 100:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:90] + ext
        
        # Если нет расширения, добавляем .file
        if not os.path.splitext(safe_name)[1]:
            safe_name += '.file'
        
        return safe_name

# Глобальный экземпляр
file_storage = None

def get_file_storage() -> FileStorage:
    """Получает экземпляр FileStorage (ленивая инициализация)"""
    global file_storage
    if file_storage is None:
        file_storage = FileStorage()
    return file_storage

def check_storage_setup() -> dict:
    """Проверяет настройки хранилища"""
    try:
        storage = get_file_storage()
        stats = storage.get_storage_stats()
        
        logger.info(f"📊 Статистика хранилища: {stats}")
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки хранилища: {e}")
        return {
            'success': False,
            'error': str(e)
        }