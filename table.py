import sqlite3

# Путь к твоей базе данных (замени, если другой)
db_path = "users.db"

# SQL-команда для добавления новых столбцов
alter_query = """
ALTER TABLE users ADD COLUMN gender TEXT;
ALTER TABLE users ADD COLUMN height_cm INTEGER;
ALTER TABLE users ADD COLUMN weight_kg REAL;
ALTER TABLE users ADD COLUMN chronic_conditions TEXT;
ALTER TABLE users ADD COLUMN medications TEXT;
ALTER TABLE users ADD COLUMN allergies TEXT;
ALTER TABLE users ADD COLUMN smoking TEXT;
ALTER TABLE users ADD COLUMN alcohol TEXT;
ALTER TABLE users ADD COLUMN physical_activity TEXT;
ALTER TABLE users ADD COLUMN family_history TEXT;
ALTER TABLE users ADD COLUMN last_updated DATETIME;
"""

# Выполнение
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Разделяем по командам и выполняем каждую по отдельности
for statement in alter_query.strip().split(";"):
    if statement.strip():
        cursor.execute(statement.strip() + ";")

conn.commit()
conn.close()

print("✅ Таблица 'users' успешно обновлена.")
