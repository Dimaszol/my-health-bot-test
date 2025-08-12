# supabase_storage.py - Обновленная система хранения файлов на Supabase

import os
import uuid
import logging
from typing import Tuple, Optional
try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Библиотека supabase не найдена. Установите: pip install supabase==2.8.1")
    raise
from pathlib import Path

logger = logging.getLogger(__name__)

class SupabaseStorage:
    """Менеджер файлов на Supabase Storage для медицинского бота"""
    
    def __init__(self):
        # Получаем данные подключения из переменных окружения
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            raise Exception("❌ SUPABASE_URL и SUPABASE_SERVICE_KEY должны быть в .env файле")
        
        # Создаем клиент Supabase
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.bucket_name = "medical-documents"
        
        # 📋 ДОПУСТИМЫЕ РАСШИРЕНИЯ для медицинского бота
        self.allowed_extensions = {
            '.pdf', '.jpg', '.jpeg', '.png', '.webp', 
            '.docx', '.doc', '.txt', '.rtf'
        }
        
        logger.info(f"✅ Supabase Storage инициализирован: {self.bucket_name}")
    
    def _generate_safe_filename(self, original_filename: str, user_id: int) -> str:
        """
        🎯 ПРОСТАЯ ГЕНЕРАЦИЯ БЕЗОПАСНОГО ИМЕНИ ФАЙЛА
        
        Args:
            original_filename: Оригинальное имя (любые символы)
            user_id: ID пользователя для логирования
            
        Returns:
            str: Безопасное имя файла medical_doc_abc123.pdf
        """
        # 🔍 Извлекаем расширение
        name, extension = os.path.splitext(original_filename.lower())
        
        # ✅ Проверяем расширение
        if extension not in self.allowed_extensions:
            logger.warning(f"⚠️ [USER:{user_id}] Неподдерживаемое расширение: {extension}")
            extension = '.pdf'  # Fallback на PDF
        
        # 🎯 Генерируем безопасное имя: medical_doc_UUID.расширение
        file_uuid = uuid.uuid4().hex[:12]  # 12 символов достаточно
        safe_filename = f"medical_doc_{file_uuid}{extension}"
        
        # 🔒 БЕЗОПАСНОЕ ЛОГИРОВАНИЕ (без оригинального имени файла)
        logger.info(f"✅ [USER:{user_id}] Сгенерировано безопасное имя: {safe_filename}")
        logger.debug(f"🔍 [USER:{user_id}] Оригинал: {len(original_filename)} символов, расширение: {extension}")
        
        return safe_filename
    
    def _generate_file_path(self, user_id: int, filename: str) -> str:
        """
        Генерирует безопасный путь к файлу - ОБНОВЛЕННАЯ ВЕРСИЯ
        Формат: users/{user_id}/medical_doc_{uuid}.{ext}
        """
        # 🎯 ИСПОЛЬЗУЕМ ПРОСТУЮ ГЕНЕРАЦИЮ БЕЗОПАСНОГО ИМЕНИ
        safe_filename = self._generate_safe_filename(filename, user_id)
        
        # 📁 Формируем путь: users/123456/medical_doc_abc123.pdf
        storage_path = f"users/{user_id}/{safe_filename}"
        
        logger.info(f"✅ [STORAGE] Путь сгенерирован: {storage_path}")
        
        return storage_path
    
    async def upload_file(self, user_id: int, file_path: str, filename: str) -> Tuple[bool, str]:
        """
        Загружает файл в Supabase Storage
        
        Args:
            user_id: ID пользователя
            file_path: Локальный путь к файлу
            filename: Оригинальное имя файла
            
        Returns:
            Tuple[bool, str]: (успех, путь_к_файлу_или_ошибка)
        """
        try:
            # Проверяем что файл существует
            if not os.path.exists(file_path):
                return False, f"Файл не найден: {file_path}"
            
            # Генерируем путь в хранилище
            storage_path = self._generate_file_path(user_id, filename)
            
            # ✅ ЧИТАЕМ ФАЙЛ
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            # ✅ ПРОВЕРЯЕМ ЧТО file_data это bytes
            if not isinstance(file_data, bytes):
                return False, f"Ошибка чтения файла: неверный тип данных"
            
            logger.info(f"🔍 [DEBUG] Читаем файл: {len(file_data)} bytes")
            
            # ✅ ЗАГРУЖАЕМ В SUPABASE
            try:
                response = self.supabase.storage.from_(self.bucket_name).upload(
                    path=storage_path,
                    file=file_data
                )
                
                logger.info(f"🔍 [DEBUG] Supabase response type: {type(response)}")
                
                # ✅ ПРОВЕРЯЕМ РЕЗУЛЬТАТ
                if response is None:
                    return False, "Supabase вернул None"
                
                # Supabase должен вернуть словарь с путем к файлу
                if isinstance(response, dict):
                    if 'error' in response and response['error']:
                        return False, f"Supabase error: {response['error']}"
                    
                    logger.info(f"✅ [SUPABASE] Файл загружен: {storage_path}")
                    return True, storage_path
                else:
                    logger.info(f"✅ [SUPABASE] Файл загружен: {storage_path}")
                    return True, storage_path
                
            except Exception as upload_error:
                logger.error(f"❌ [SUPABASE] Ошибка API: {upload_error}")
                return False, f"Upload failed: {str(upload_error)}"
            
        except Exception as e:
            logger.error(f"❌ [SUPABASE] Ошибка загрузки файла: {e}")
            return False, str(e)
    
    async def download_file(self, storage_path: str, local_path: str) -> bool:
        """
        Скачивает файл из Supabase Storage
        
        Args:
            storage_path: Путь к файлу в хранилище
            local_path: Локальный путь для сохранения
            
        Returns:
            bool: Успех операции
        """
        try:
            # Скачиваем файл
            response = self.supabase.storage.from_(self.bucket_name).download(storage_path)
            
            # ✅ ПРОВЕРЯЕМ ЧТО ПОЛУЧИЛИ BYTES
            if not isinstance(response, bytes):
                logger.error(f"❌ [SUPABASE] Неверный тип ответа: {type(response)}")
                return False
            
            # Сохраняем локально
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, 'wb') as file:
                file.write(response)
            
            logger.info(f"✅ [SUPABASE] Файл скачан: {storage_path} → {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [SUPABASE] Ошибка скачивания файла: {e}")
            return False
    
    async def delete_file(self, storage_path: str) -> bool:
        """
        Удаляет файл из Supabase Storage
        
        Args:
            storage_path: Путь к файлу в хранилище
            
        Returns:
            bool: Успех операции
        """
        try:
            self.supabase.storage.from_(self.bucket_name).remove([storage_path])
            
            logger.info(f"✅ [SUPABASE] Файл удален: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [SUPABASE] Ошибка удаления файла: {e}")
            return False
    
    def get_public_url(self, storage_path: str) -> str:
        """
        Получает публичную ссылку на файл (если bucket публичный)
        
        Args:
            storage_path: Путь к файлу в хранилище
            
        Returns:
            str: Публичная ссылка
        """
        try:
            response = self.supabase.storage.from_(self.bucket_name).get_public_url(storage_path)
            return response
        except Exception as e:
            logger.error(f"❌ [SUPABASE] Ошибка получения URL: {e}")
            return ""
    
    def _get_content_type(self, filename: str) -> str:
        """Определяет MIME-тип файла по расширению"""
        ext = Path(filename).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.txt': 'text/plain',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        Получает подписанную ссылку на приватный файл
        
        Args:
            storage_path: Путь к файлу в хранилище
            expires_in: Время жизни ссылки в секундах (по умолчанию 1 час)
            
        Returns:
            str: Подписанная ссылка или пустая строка при ошибке
        """
        try:
            # Для приватных bucket используем signed URL
            response = self.supabase.storage.from_(self.bucket_name).create_signed_url(
                path=storage_path,
                expires_in=expires_in
            )
            
            if isinstance(response, dict) and 'signedURL' in response:
                return response['signedURL']
            else:
                logger.error(f"❌ [SUPABASE] Неожиданный формат ответа signed URL: {response}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ [SUPABASE] Ошибка получения signed URL: {e}")
            return ""

# Глобальный экземпляр для использования в приложении
storage_manager = None

def get_storage_manager() -> SupabaseStorage:
    """Получить менеджер хранилища (Singleton)"""
    global storage_manager
    if storage_manager is None:
        storage_manager = SupabaseStorage()
    return storage_manager