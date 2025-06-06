import sqlite3

# Подключаемся к (или создаём) базу данных
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Создаём таблицу users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    birth_year INTEGER
);
""")

# Создаём таблицу documents
cursor.execute("""
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    file_path TEXT NOT NULL,
    file_type TEXT CHECK(file_type IN ('pdf', 'image')) NOT NULL,
    raw_text TEXT,
    summary TEXT,
    confirmed BOOLEAN DEFAULT 1,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    vector_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
""")

# Создаём таблицу chat_history
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT CHECK(role IN ('user', 'bot')) NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
""")

# Создаём таблицу conversation_summary
cursor.execute("""
CREATE TABLE IF NOT EXISTS conversation_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    summary_text TEXT,
    last_message_id INTEGER,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
""")

conn.commit()
conn.close()

print("✅ База данных создана.")
