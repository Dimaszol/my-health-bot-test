# check_vector_db.py

from vector_utils import collection  # импорт коллекции из твоего проекта

def main():
    total = collection.count()
    print(f"🔍 Всего записей в векторной базе: {total}")

if __name__ == "__main__":
    main()