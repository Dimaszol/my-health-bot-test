# create_payment_tables.py - Создание таблиц для системы лимитов и платежей

import sqlite3
from datetime import datetime

DB_PATH = "users.db"

def create_payment_tables():
    """Создает таблицы для системы лимитов и платежей"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔧 Создание таблиц для системы платежей...")
    
    # 1. Таблица лимитов пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_limits (
            user_id INTEGER PRIMARY KEY,
            documents_left INTEGER DEFAULT 2,
            gpt4o_queries_left INTEGER DEFAULT 10,
            subscription_type TEXT DEFAULT 'free',
            subscription_expires_at DATETIME NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)
    print("✅ Таблица user_limits создана")
    
    # 2. Таблица транзакций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stripe_session_id TEXT,
            amount_usd REAL NOT NULL,
            package_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)
    print("✅ Таблица transactions создана")
    
    # 3. Создаем индексы для быстрых запросов
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_limits_subscription ON user_limits(subscription_type)")
    print("✅ Индексы созданы")
    
    # 4. Создаем лимиты для всех существующих пользователей
    cursor.execute("""
        INSERT OR IGNORE INTO user_limits (user_id, created_at, updated_at)
        SELECT user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM users
    """)
    
    added_users = cursor.rowcount
    if added_users > 0:
        print(f"✅ Добавлены лимиты для {added_users} существующих пользователей")
    else:
        print("✅ Лимиты для существующих пользователей уже созданы")
    
    # 5. Добавляем тестовые данные (опционально, для проверки)
    cursor.execute("""
        INSERT OR IGNORE INTO transactions 
        (user_id, stripe_session_id, amount_usd, package_type, status, payment_method)
        VALUES (1, 'test_session_123', 3.99, 'basic_sub', 'completed', 'stripe')
    """)
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Все таблицы успешно созданы!")
    print("📊 Структура готова для:")
    print("   ├── Системы лимитов")
    print("   ├── Отслеживания платежей") 
    print("   └── Управления подписками")

def show_table_info():
    """Показать информацию о созданных таблицах"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n📋 Информация о таблицах:")
    print("=" * 50)
    
    # Информация о user_limits
    cursor.execute("SELECT COUNT(*) FROM user_limits")
    limits_count = cursor.fetchone()[0]
    print(f"👥 user_limits: {limits_count} записей")
    
    # Информация о transactions  
    cursor.execute("SELECT COUNT(*) FROM transactions")
    transactions_count = cursor.fetchone()[0]
    print(f"💳 transactions: {transactions_count} записей")
    
    # Показать структуру user_limits
    print("\n🏗️ Структура user_limits:")
    cursor.execute("PRAGMA table_info(user_limits)")
    for row in cursor.fetchall():
        col_name, col_type, not_null, default_val = row[1], row[2], row[3], row[4]
        print(f"   ├── {col_name}: {col_type} {f'DEFAULT {default_val}' if default_val else ''}")
    
    # Показать структуру transactions
    print("\n💰 Структура transactions:")
    cursor.execute("PRAGMA table_info(transactions)")
    for row in cursor.fetchall():
        col_name, col_type, not_null, default_val = row[1], row[2], row[3], row[4]
        print(f"   ├── {col_name}: {col_type} {f'DEFAULT {default_val}' if default_val else ''}")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 PulseBook - Настройка системы платежей")
    print("=" * 50)
    
    # Создаем таблицы
    create_payment_tables()
    
    # Показываем информацию
    show_table_info()
    
    print(f"\n✅ Готово! Можно запускать следующий этап разработки.")