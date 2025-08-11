# supabase_storage.py - Новая система хранения файлов на Supabase

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
        
        logger.info(f"✅ Supabase Storage инициализирован: {self.bucket_name}")
    
    def _generate_file_path(self, user_id: int, filename: str) -> str:
        """
        Генерирует безопасный путь к файлу
        Формат: users/{user_id}/{uuid}_{filename}
        """
        # Генерируем уникальный ID для файла
        file_uuid = str(uuid.uuid4())[:8]
        
        # Очищаем имя файла от опасных символов
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ".-_").strip()
        if not safe_filename:
            safe_filename = "document"
        
        # Формируем путь: users/123456/abc12345_document.pdf
        return f"users/{user_id}/{file_uuid}_{safe_filename}"
    
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
            
            # Читаем файл
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            # Загружаем в Supabase Storage
            response = self.supabase.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options={
                    "content-type": self._get_content_type(filename),
                    "upsert": False  # Не перезаписывать существующие файлы
                }
            )
            
            logger.info(f"✅ [SUPABASE] Файл загружен: {storage_path}")
            return True, storage_path
            
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

# Глобальный экземпляр для использования в приложении
storage_manager = None

def get_storage_manager() -> SupabaseStorage:
    """Получить менеджер хранилища (Singleton)"""
    global storage_manager
    if storage_manager is None:
        storage_manager = SupabaseStorage()
    return storage_manager