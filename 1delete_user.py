# delete_user_by_id.py

import os
from dotenv import load_dotenv

# Загружаем переменные окружения (если нужен ключ к Chroma и т.д.)
load_dotenv()

# Импорт функции удаления
from db import delete_user_completely

def main():
    try:
        user_id = int(input("Введите user_id для удаления: "))
        delete_user_completely(user_id)
        print(f"✅ Пользователь {user_id} успешно удалён из всех баз.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()