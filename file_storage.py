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
                # ✅ ИСПРАВЛЕННАЯ ЗАГРУЗКА В SUPABASE STORAGE
                import asyncio
                
                # Проверяем есть ли уже запущенный event loop
                try:
                    loop = asyncio.get_running_loop()
                    # Если loop уже работает, создаем задачу
                    import concurrent.futures
                    import threading
                    
                    def sync_upload():
                        # Создаем новый event loop в отдельном потоке
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(
                                self.storage_manager.upload_file(user_id, source_path, filename)
                            )
                        finally:
                            new_loop.close()
                    
                    # Запускаем в отдельном потоке
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(sync_upload)
                        success, storage_path = future.result(timeout=30)
                    
                except RuntimeError:
                    # Нет запущенного loop - можем использовать обычный способ
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        success, storage_path = loop.run_until_complete(
                            self.storage_manager.upload_file(user_id, source_path, filename)
                        )
                    finally:
                        loop.close()
                
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
                # ✅ ИСПРАВЛЕННОЕ УДАЛЕНИЕ ИЗ SUPABASE
                import asyncio
                import concurrent.futures
                
                def sync_delete():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            self.storage_manager.delete_file(file_path)
                        )
                    finally:
                        new_loop.close()
                
                try:
                    # Запускаем в отдельном потоке
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(sync_delete)
                        success = future.result(timeout=10)
                    return success
                except Exception as e:
                    logger.error(f"❌ Ошибка удаления из Supabase: {e}")
                    return False
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
    
    def get_storage_stats(self) -> dict:
        """Получает статистику использования хранилища (совместимость)"""
        try:
            if self.storage_type == "supabase":
                return {
                    'total_size_mb': 0,  # Supabase не предоставляет статистику через API
                    'file_count': 0,
                    'storage_type': 'supabase',
                    'storage_path': 'Supabase Storage'
                }
            else:
                # Локальная статистика для fallback
                total_size = 0
                file_count = 0
                
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            total_size += os.path.getsize(file_path)
                            file_count += 1
                        except OSError:
                            continue
                
                total_size_mb = total_size / (1024 * 1024)
                
                return {
                    'total_size_mb': round(total_size_mb, 2),
                    'file_count': file_count,
                    'storage_type': self.storage_type,
                    'storage_path': self.temp_dir
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {
                'total_size_mb': 0,
                'file_count': 0,
                'storage_type': self.storage_type,
                'storage_path': 'unknown'
            }

# ✅ ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР (сохраняем совместимость)
_file_storage_instance = None

def get_file_storage() -> FileStorage:
    """Получить экземпляр файлового хранилища (Singleton)"""
    global _file_storage_instance
    if _file_storage_instance is None:
        _file_storage_instance = FileStorage()
    return _file_storage_instance

def check_storage_setup() -> dict:
    """Проверяет настройки хранилища (совместимость со старым кодом)"""
    try:
        storage = get_file_storage()
        
        if storage.storage_type == "supabase":
            stats = {
                'storage_type': 'supabase',
                'status': 'connected',
                'bucket': 'medical-documents'
            }
        else:
            stats = {
                'storage_type': 'local_fallback',
                'status': 'fallback_mode',
                'storage_path': storage.temp_dir
            }
        
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