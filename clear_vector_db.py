import chromadb

def clear_vector_database():
    client = chromadb.PersistentClient(path="vector_store")
    collection = client.get_or_create_collection(name="documents")

    print("⚠️ ВНИМАНИЕ: начинается полная очистка векторной базы...")
    all_ids = collection.get()["ids"]

    if not all_ids:
        print("✅ Векторная база уже пуста.")
        return

    collection.delete(ids=all_ids)
    print(f"🧹 Удалено {len(all_ids)} записей из векторной базы ChromaDB.")
    print("✅ Очистка завершена.")

if __name__ == "__main__":
    clear_vector_database()
