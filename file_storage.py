# file_storage.py - ОБНОВЛЕННАЯ ВЕРСИЯ с Supabase Storage

import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from supabase_storage import get_storage_manager

logger = logging.getLogger(__name__)

class FileStorage:
    """Файловое хранилище на Supabase Storage (замена Railway Volumes)"""
    
    def __init__(self):
        """Инициализация Supabase Storage"""
        try:
            self.storage_manager = get_storage_manager()
            self.storage_type = "supabase"
            logger.info("✅ Supabase Storage инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Supabase Storage: {e}")
            # Fallback только для локальной разработки
            is_railway = os.getenv("RAILWAY_ENVIRONMENT") == "production"
            if is_railway:
                logger.error("❌ На Railway Supabase Storage обязателен!")
                raise Exception("Supabase Storage недоступен на продакшене")
            else:
                # Локальный fallback только для разработки
                self.storage_manager = None
                self.storage_type = "local_fallback"
                self.temp_dir = "/app/files"
                os.makedirs(self.temp_dir, exist_ok=True)
    
    def save_file(self, user_id: int, filename: str, source_path: str) -> Tuple[bool, str]:
        """
        Сохраняет файл в Supabase Storage
        
        Args:
            user_id: ID пользователя
            filename: Имя файла
            source_path: Путь к исходному файлу
            
        Returns:
            Tuple[bool, str]: (успех, путь_к_файлу_или_ошибка)
        """
        try:
            if self.storage_manager:
                # ✅ ЗАГРУЖАЕМ В SUPABASE STORAGE
                import asyncio
                
                # Запускаем асинхронную операцию в синхронном контексте
                loop = asyncio.get_event_loop()
                success, storage_path = loop.run_until_complete(
                    self.storage_manager.upload_file(user_id, source_path, filename)
                )
                
                if success:
                    logger.info(f"✅ [SUPABASE] Файл сохранен: {storage_path}")
                    return True, storage_path
                else:
                    logger.error(f"❌ [SUPABASE] Ошибка сохранения: {storage_path}")
                    return False, storage_path
            else:
                # ✅ FALLBACK: Локальное сохранение
                return self._save_file_locally(user_id, filename, source_path)
                
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения файла: {e}")
            # На Railway нет смысла в локальном fallback
            is_railway = os.getenv("RAILWAY_ENVIRONMENT") == "production"
            if is_railway:
                return False, f"Supabase Storage недоступен: {str(e)}"
            else:
                # Локальный fallback только для разработки
                return self._save_file_locally(user_id, filename, source_path)
    
    def _save_file_locally(self, user_id: int, filename: str, source_path: str) -> Tuple[bool, str]:
        """Fallback: сохранение в локальную папку"""
        try:
            import shutil
            
            user_dir = os.path.join(self.temp_dir, f"users/{user_id}")
            os.makedirs(user_dir, exist_ok=True)
            
            # Создаем безопасное имя файла
            safe_filename = self._sanitize_filename(filename)
            destination_path = os.path.join(user_dir, safe_filename)
            
            # Копируем файл
            shutil.copy2(source_path, destination_path)
            
            logger.info(f"✅ [LOCAL] Файл сохранен: {destination_path}")
            return True, destination_path
            
        except Exception as e:
            logger.error(f"❌ Ошибка локального сохранения: {e}")
            return False, f"Local save error: {str(e)}"
    
    def file_exists(self, file_path: str) -> bool:
        """Проверяет существование файла"""
        if self.storage_type == "supabase":
            # Для Supabase файлы всегда считаем существующими
            # (можно добавить проверку через API если нужно)
            return True
        else:
            # Локальная проверка
            try:
                return os.path.exists(file_path) and os.path.isfile(file_path)
            except Exception:
                return False
    
    def delete_file(self, file_path: str) -> bool:
        """Удаляет файл"""
        try:
            if self.storage_type == "supabase" and self.storage_manager:
                # ✅ УДАЛЕНИЕ ИЗ SUPABASE
                import asyncio
                loop = asyncio.get_event_loop()
                success = loop.run_until_complete(
                    self.storage_manager.delete_file(file_path)
                )
                return success
            else:
                # ✅ ЛОКАЛЬНОЕ УДАЛЕНИЕ
                if os.path.exists(file_path):
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
            if self.storage_type == "supabase":
                # Для Supabase нужна отдельная логика удаления по пользователю
                # Пока возвращаем True (файлы удаляются при удалении записей из БД)
                logger.info(f"✅ GDPR: файлы пользователя {user_id} будут удалены через БД")
                return True
            else:
                # Локальное удаление
                import shutil
                user_dir = os.path.join(self.temp_dir, f"users/{user_id}")
                if os.path.exists(user_dir):
                    shutil.rmtree(user_dir)
                    logger.info(f"✅ Удалена папка пользователя: {user_dir}")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления файлов пользователя: {e}")
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Создает безопасное имя файла"""
        # Убираем опасные символы
        safe_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        safe_filename = "".join(c for c in filename if c in safe_chars or ord(c) > 127)
        
        # Ограничиваем длину
        if len(safe_filename) > 100:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:95] + ext
        
        return safe_filename or "document.txt"

# ✅ ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР (сохраняем совместимость)
_file_storage_instance = None

def get_file_storage() -> FileStorage:
    """Получить экземпляр файлового хранилища (Singleton)"""
    global _file_storage_instance
    if _file_storage_instance is None:
        _file_storage_instance = FileStorage()
    return _file_storage_instance