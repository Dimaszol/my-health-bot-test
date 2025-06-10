import sqlite3
from datetime import datetime

def create_subscriptions_table():
    """Создает таблицу для отслеживания подписок"""
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    print("🔧 Создание таблицы user_subscriptions...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stripe_subscription_id TEXT NOT NULL,
            package_id TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            cancelled_at DATETIME NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
            UNIQUE(user_id, stripe_subscription_id)
        )
    """)
    
    # Создаем индексы
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_stripe_id ON user_subscriptions(stripe_subscription_id)")
    
    conn.commit()
    conn.close()
    
    print("✅ Таблица user_subscriptions создана")

if __name__ == "__main__":
    create_subscriptions_table()