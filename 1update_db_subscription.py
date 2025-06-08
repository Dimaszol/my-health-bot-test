# update_db_subscription.py - Обновление БД для системы подписок

import sqlite3
import os
from datetime import datetime

DB_PATH = "users.db"

def backup_database():
    """Создает резервную копию базы данных"""
    backup_name = f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        # Копируем файл базы данных
        import shutil
        shutil.copy2(DB_PATH, backup_name)
        print(f"✅ Резервная копия создана: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
        return None

def update_database():
    """Обновляет структуру базы данных"""
    
    print("🔧 Начинаем обновление базы данных...")
    print("=" * 50)
    
    # Проверяем существование файла БД
    if not os.path.exists(DB_PATH):
        print(f"❌ Файл базы данных {DB_PATH} не найден!")
        return False
    
    # Создаем резервную копию
    backup_file = backup_database()
    if not backup_file:
        print("❌ Не удалось создать резервную копию. Прерываем обновление.")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n📦 Шаг 1: Создаем таблицу пакетов подписок...")
        
        # Создаем таблицу пакетов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscription_packages (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price_usd REAL NOT NULL,
                documents_included INTEGER NOT NULL,
                gpt4o_queries_included INTEGER NOT NULL,
                type TEXT NOT NULL, -- 'subscription' или 'one_time'
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Таблица subscription_packages создана")
        
        print("\n💰 Шаг 2: Добавляем готовые пакеты...")
        
        # Добавляем пакеты
        packages = [
            ('basic_sub', 'Basic Subscription', 3.99, 5, 100, 'subscription'),
            ('premium_sub', 'Premium Subscription', 9.99, 20, 400, 'subscription'),
            ('extra_pack', 'Extra Pack', 1.99, 3, 30, 'one_time')
        ]
        
        for package in packages:
            cursor.execute("""
                INSERT OR REPLACE INTO subscription_packages 
                (id, name, price_usd, documents_included, gpt4o_queries_included, type, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'))
            """, package)
            print(f"   ✅ Добавлен пакет: {package[1]} (${package[2]})")
        
        print("\n🔗 Шаг 3: Обновляем таблицу транзакций...")
        
        # Проверяем и добавляем новые колонки в transactions
        cursor.execute("PRAGMA table_info(transactions)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        if 'package_id' not in existing_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN package_id TEXT")
            print("   ✅ Добавлена колонка package_id")
        else:
            print("   ⚪ Колонка package_id уже существует")
            
        if 'documents_granted' not in existing_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN documents_granted INTEGER DEFAULT 0")
            print("   ✅ Добавлена колонка documents_granted")
        else:
            print("   ⚪ Колонка documents_granted уже существует")
            
        if 'queries_granted' not in existing_columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN queries_granted INTEGER DEFAULT 0")
            print("   ✅ Добавлена колонка queries_granted")
        else:
            print("   ⚪ Колонка queries_granted уже существует")
        
        print("\n👥 Шаг 4: Проверяем существующих пользователей...")
        
        # Проверяем пользователей без записей в user_limits
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE user_id NOT IN (SELECT user_id FROM user_limits)
        """)
        users_without_limits = cursor.fetchone()[0]
        
        if users_without_limits > 0:
            # Создаем записи для пользователей без лимитов
            cursor.execute("""
                INSERT INTO user_limits (user_id, documents_left, gpt4o_queries_left, subscription_type)
                SELECT user_id, 2, 10, 'free'
                FROM users 
                WHERE user_id NOT IN (SELECT user_id FROM user_limits)
            """)
            print(f"   ✅ Созданы лимиты для {users_without_limits} пользователей")
        else:
            print("   ⚪ Все пользователи уже имеют лимиты")
        
        # Сохраняем изменения
        conn.commit()
        
        print("\n📊 Шаг 5: Проверяем результат...")
        
        # Показываем созданные пакеты
        cursor.execute("""
            SELECT id, name, '$' || price_usd as price, 
                   documents_included || ' docs' as documents,
                   gpt4o_queries_included || ' queries' as queries,
                   type
            FROM subscription_packages 
            WHERE is_active = 1
        """)
        
        packages = cursor.fetchall()
        print("\n📦 Доступные пакеты:")
        for pkg in packages:
            print(f"   • {pkg[1]}: {pkg[2]} - {pkg[3]}, {pkg[4]} ({pkg[5]})")
        
        # Показываем статистику пользователей
        cursor.execute("SELECT COUNT(*) FROM user_limits")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_transactions = cursor.fetchone()[0]
        
        print(f"\n📈 Статистика:")
        print(f"   • Пользователей с лимитами: {total_users}")
        print(f"   • Всего транзакций: {total_transactions}")
        print(f"   • Резервная копия: {backup_file}")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ База данных готова для системы подписок")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА при обновлении базы данных: {e}")
        print(f"💡 Восстановите из резервной копии: {backup_file}")
        
        if conn:
            conn.rollback()
            conn.close()
            
        return False

def show_current_structure():
    """Показывает текущую структуру важных таблиц"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n📋 Текущая структура таблиц:")
        print("=" * 40)
        
        # Структура user_limits
        print("\n🔸 user_limits:")
        cursor.execute("PRAGMA table_info(user_limits)")
        for row in cursor.fetchall():
            print(f"   {row[1]}: {row[2]}")
        
        # Структура transactions
        print("\n🔸 transactions:")
        cursor.execute("PRAGMA table_info(transactions)")
        for row in cursor.fetchall():
            print(f"   {row[1]}: {row[2]}")
        
        # Структура subscription_packages (если существует)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='subscription_packages'
        """)
        
        if cursor.fetchone():
            print("\n🔸 subscription_packages:")
            cursor.execute("PRAGMA table_info(subscription_packages)")
            for row in cursor.fetchall():
                print(f"   {row[1]}: {row[2]}")
        else:
            print("\n🔸 subscription_packages: НЕ СУЩЕСТВУЕТ")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при получении структуры: {e}")

if __name__ == "__main__":
    print("🚀 ОБНОВЛЕНИЕ БАЗЫ ДАННЫХ - СИСТЕМА ПОДПИСОК")
    print("=" * 55)
    
    # Показываем текущую структуру
    show_current_structure()
    
    # Спрашиваем подтверждение
    print("\n⚠️  ВНИМАНИЕ: Будет создана резервная копия БД")
    confirm = input("\n🔄 Продолжить обновление? (y/N): ").lower().strip()
    
    if confirm in ['y', 'yes', 'да']:
        success = update_database()
        
        if success:
            print("\n🎯 Что дальше:")
            print("1. Интегрировать логику в бота")  
            print("2. Создать интерфейс покупки")
            print("3. Подключить платежную систему")
        else:
            print("\n💡 Рекомендации:")
            print("- Проверьте права доступа к файлу БД")
            print("- Убедитесь что БД не используется другим процессом")
            print("- Восстановите из резервной копии при необходимости")
    else:
        print("❌ Обновление отменено")