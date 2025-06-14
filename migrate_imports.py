#!/usr/bin/env python3
# migrate_imports.py - Автоматическая миграция импортов с SQLite на PostgreSQL

import os
import re
import shutil
from datetime import datetime

# 🎯 КАРТА ЗАМЕН ИМПОРТОВ
IMPORT_REPLACEMENTS = {
    # Замены из db.py на db_postgresql.py
    'from db import': 'from db_postgresql import',
    'import db': 'import db_postgresql as db',
    
    # Замены из vector_db.py на vector_db_postgresql.py  
    'from vector_db import': 'from vector_db_postgresql import',
    'import vector_db': 'import vector_db_postgresql as vector_db',
    
    # Замены из vector_utils.py (функции перенесены в vector_db_postgresql.py)
    'from vector_utils import': 'from vector_db_postgresql import',
    'import vector_utils': 'import vector_db_postgresql as vector_utils',
    
    # Замены из db_pool.py (функции перенесены в db_postgresql.py)
    'from db_pool import': 'from db_postgresql import',
    'import db_pool': 'import db_postgresql as db_pool',
}

# 🔧 ДОПОЛНИТЕЛЬНЫЕ ЗАМЕНЫ ФУНКЦИЙ (когда функции изменили названия)
FUNCTION_REPLACEMENTS = {
    # Если в PostgreSQL версии функции переименованы
    'user_exists(': 'get_user(',  # user_exists заменена на get_user
    'add_chunks_to_vector_db(': 'await add_chunks_to_vector_db(',  # стала async
    'search_similar_chunks(': 'await search_similar_chunks(',  # стала async
    'keyword_search_chunks(': 'await keyword_search_chunks(',  # стала async
}

# 📁 ФАЙЛЫ ДЛЯ МИГРАЦИИ
FILES_TO_MIGRATE = [
    'main.py',
    'upload.py', 
    'profile_manager.py',
    'save_utils.py',
    'registration.py',
    'documents.py',
    'subscription_manager.py',
    'notification_system.py',
    'gpt.py',
    'keyboards.py',
    'error_handler.py'
]

def backup_file(file_path):
    """Создает резервную копию файла"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"📁 Создана резервная копия: {backup_path}")
        return backup_path
    return None

def migrate_imports_in_file(file_path):
    """Мигрирует импорты в одном файле"""
    if not os.path.exists(file_path):
        print(f"⚠️  Файл не найден: {file_path}")
        return False
    
    print(f"\n🔄 Мигрирую файл: {file_path}")
    
    # Читаем содержимое файла
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    original_content = content
    changes_made = []
    
    # Применяем замены импортов
    for old_import, new_import in IMPORT_REPLACEMENTS.items():
        if old_import in content:
            content = content.replace(old_import, new_import)
            changes_made.append(f"  ✅ {old_import} → {new_import}")
    
    # Применяем замены функций (более осторожно)
    for old_func, new_func in FUNCTION_REPLACEMENTS.items():
        # Используем regex для более точной замены
        pattern = re.escape(old_func)
        if re.search(pattern, content):
            content = re.sub(pattern, new_func, content)
            changes_made.append(f"  🔧 {old_func} → {new_func}")
    
    # Сохраняем файл только если были изменения
    if changes_made:
        # Создаем резервную копию
        backup_path = backup_file(file_path)
        
        # Записываем обновленное содержимое
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print(f"✅ Файл обновлен: {file_path}")
        for change in changes_made:
            print(change)
        
        return True
    else:
        print(f"⏭️  Изменения не требуются: {file_path}")
        return False

def check_async_functions(file_path):
    """Проверяет, нужно ли добавить await к функциям"""
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Список функций, которые теперь async
    async_functions = [
        'get_user(',
        'create_user(',
        'save_document(',
        'get_user_documents(',
        'update_user_profile(',
        'search_similar_chunks(',
        'keyword_search_chunks(',
        'add_chunks_to_vector_db(',
        'delete_document_from_vector_db('
    ]
    
    missing_awaits = []
    
    for func in async_functions:
        # Ищем функции без await
        pattern = rf'(?<!await\s){re.escape(func)}'
        matches = re.findall(pattern, content)
        if matches:
            missing_awaits.append(func)
    
    return missing_awaits

def main():
    """Основная функция миграции"""
    print("🚀 Начинаю автоматическую миграцию импортов...")
    print("🔄 SQLite → PostgreSQL")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    migrated_files = []
    
    # Мигрируем каждый файл
    for file_name in FILES_TO_MIGRATE:
        if migrate_imports_in_file(file_name):
            migrated_files.append(file_name)
        
        # Проверяем async функции
        missing_awaits = check_async_functions(file_name)
        if missing_awaits:
            print(f"⚠️  В файле {file_name} возможно нужно добавить await к:")
            for func in missing_awaits:
                print(f"    - {func}")
    
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТЫ МИГРАЦИИ:")
    print(f"✅ Успешно мигрировано файлов: {len(migrated_files)}")
    
    if migrated_files:
        print("\n📁 Мигрированные файлы:")
        for file_name in migrated_files:
            print(f"  - {file_name}")
    
    print("\n🔍 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Проверьте логи выше на предупреждения об await")
    print("2. Запустите бота для тестирования")
    print("3. При ошибках восстановите из резервных копий (.backup_*)")
    print("4. Удалите старые файлы: db.py, db_pool.py, vector_db.py, vector_utils.py")

if __name__ == "__main__":
    main()