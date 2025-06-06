import chromadb

def delete_chunks_with_null_document_id():
    client = chromadb.PersistentClient(path="vector_store")
    collection = client.get_or_create_collection(name="documents")

    print("🧹 Поиск чанков с document_id = None...")
    raw = collection.get(include=["metadatas"])
    ids = collection.get()["ids"]

    to_delete = [
        id_ for id_, meta in zip(ids, raw["metadatas"])
        if meta.get("document_id") is None
    ]

    if to_delete:
        collection.delete(ids=to_delete)
        print(f"✅ Удалено {len(to_delete)} чанков без document_id.")
    else:
        print("✅ Ничего не найдено — всё чисто.")

if __name__ == "__main__":
    delete_chunks_with_null_document_id()
