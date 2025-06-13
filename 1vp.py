def inspect_document_chunks(document_id: str, max_len: int = 400, show_all_metadata: bool = False):
    from chromadb import PersistentClient

    client = PersistentClient(path="vector_store")
    collection = client.get_or_create_collection(name="documents")
    results = collection.get(where={"document_id": document_id})

    if not results["ids"]:
        print(f"❌ Нет данных в векторной базе по document_id = {document_id}")
        return

    print(f"\n🔎 Документ содержит {len(results['ids'])} чанков\n")

    for i in range(len(results["ids"])):
        doc_id = results["ids"][i]
        text = results["documents"][i].strip()
        metadata = results["metadatas"][i]
        keywords = metadata.get("keywords", "")
        keyword_list = [w.strip() for w in keywords.split(",") if w.strip()]
        is_incomplete = not text.endswith((".", "!", "?", "»", "”", "…"))

        print(f"🔹 ID: {doc_id} {'⚠️' if is_incomplete else ''}")
        print(f"📏 Длина: {len(text)} символов")

        print("📝 TEXT:")
        if len(text) > max_len:
            print(text[:max_len] + "... [обрезано для отображения]")
        else:
            print(text)

        print("🧾 METADATA:", metadata if show_all_metadata else {
            k: metadata[k] for k in ['date_inside', 'created_at', 'user_id', 'source'] if k in metadata
        })
        print("🔑 KEYWORDS:", keyword_list)
        print("-" * 80)

inspect_document_chunks("105", max_len=500, show_all_metadata=True)
