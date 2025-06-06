# vector_db.py - ИСПРАВЛЕННАЯ ВЕРСИЯ без утечек памяти

import chromadb
from chromadb import PersistentClient
import logging

logger = logging.getLogger(__name__)

# Создаём клиент ChromaDB
chroma_client = PersistentClient(path="./vector_store")
# Создаём или получаем коллекцию
collection = chroma_client.get_or_create_collection(name="documents")

def get_recent_vector_documents(limit=3):
    """✅ ИСПРАВЛЕНО: используем count() + лимит, не загружаем всё"""
    try:
        # Получаем общее количество через count()
        total_count = collection.count()
        logger.info(f"📦 Всего векторных записей: {total_count}")

        if total_count == 0:
            logger.warning("⚠️ В ChromaDB нет ни одного документа.")
            return []

        # Получаем только нужное количество документов
        recent_docs = collection.get(
            limit=min(limit, total_count),  # Не больше чем есть
            include=["documents", "metadatas"]
        )
        
        return list(zip(recent_docs['ids'], recent_docs['metadatas']))

    except Exception as e:
        logger.error(f"❌ Ошибка при доступе к векторной базе: {e}")
        return []

def delete_document_from_vector_db(document_id: int):
    """Удаляет документ из векторной базы"""
    try:
        # ✅ ИСПРАВЛЕНО: используем where для поиска по document_id
        results = collection.get(
            where={"document_id": str(document_id)},
            include=["metadatas"]
        )
        
        ids_to_delete = results['ids']
        
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(f"🧠 Document {document_id} удалён из ChromaDB ({len(ids_to_delete)} чанков).")
        else:
            logger.warning(f"⚠️ Документ {document_id} не найден в векторной базе")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении документа {document_id} из ChromaDB: {e}")

def delete_all_chunks_by_user(user_id: int):
    """✅ ИСПРАВЛЕНО: используем where для эффективного поиска"""
    try:
        logger.info(f"🧹 Удаление всех векторов пользователя {user_id}")
        
        # Ищем документы пользователя через where
        results = collection.get(
            where={"user_id": str(user_id)},
            include=["metadatas"]
        )
        
        ids_to_delete = results['ids']

        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(f"✅ Удалены векторы пользователя {user_id}: {len(ids_to_delete)} записей")
        else:
            logger.warning(f"⚠️ Нет векторов для пользователя {user_id}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении векторов пользователя {user_id}: {e}")

def mark_chunks_unconfirmed(document_id: int):
    """✅ ИСПРАВЛЕНО: используем where + batch update"""
    try:
        # Находим чанки документа
        results = collection.get(
            where={"document_id": str(document_id)},
            include=["metadatas"]
        )
        
        ids_to_update = results['ids']
        
        if ids_to_update:
            # Обновляем метаданные всех чанков
            updated_metadatas = []
            for metadata in results['metadatas']:
                updated_metadata = metadata.copy()
                updated_metadata["confirmed"] = 0
                updated_metadatas.append(updated_metadata)
            
            collection.update(
                ids=ids_to_update,
                metadatas=updated_metadatas
            )
            logger.info(f"🟡 Векторы документа {document_id} помечены как unconfirmed ({len(ids_to_update)} чанков).")
        else:
            logger.warning(f"⚠️ Документ {document_id} не найден в векторной базе")

    except Exception as e:
        logger.error(f"❌ Ошибка при снятии подтверждения векторов {document_id}: {e}")

def get_collection_stats():
    """Новая функция для мониторинга состояния базы"""
    try:
        total_count = collection.count()
        return {
            "total_documents": total_count,
            "status": "healthy" if total_count >= 0 else "error"
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return {"total_documents": -1, "status": "error"}