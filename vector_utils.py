import re
import tiktoken
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from datetime import datetime
from gpt import extract_keywords

client = chromadb.PersistentClient(path="vector_store")
collection = client.get_or_create_collection(name="documents")
embedding_func = embedding_functions.OpenAIEmbeddingFunction(model_name="text-embedding-3-small")

def extract_date_from_text(text: str) -> str:
    match = re.match(r"\[(\d{2})[./](\d{2})[./](\d{4})\]", text.strip())
    if match:
        try:
            date = datetime.strptime(".".join(match.groups()), "%d.%m.%Y")
            return date.strftime("%Y-%m-%d")
        except:
            pass
    return None

async def split_into_chunks(summary, document_id, user_id):
    encoder = tiktoken.encoding_for_model("gpt-4")
    paragraphs = summary.strip().split("\n\n")
    now_str = datetime.now().strftime("%Y-%m-%d")

    chunks = []
    chunk_index = 0

    for para in paragraphs:
        clean_text = para.strip()
        if len(clean_text) < 20:
            continue

        token_count = len(encoder.encode(clean_text))
        #if token_count > 300:
        #   continue  # слишком длинный, возможно ошибка — лучше пропустить

        found_date = extract_date_from_text(clean_text)
        chunk_date = found_date if found_date else now_str

        # 🔹 Извлекаем ключевые слова для этого абзаца
        keywords = await extract_keywords(clean_text)

        chunks.append({
            "chunk_text": clean_text,
            "chunk_index": chunk_index,
            "metadata": {
                "user_id": str(user_id),
                "document_id": str(document_id),
                "confirmed": 1,
                "source": "summary",
                "token_count": token_count,
                "created_at": chunk_date,
                "date_inside": found_date or "",
                "keywords": ", ".join(keywords)  # ✅ теперь ключевые слова как строка
            }
        })
        chunk_index += 1
    
    # ❗ Удаляем последний чанк, если их больше одного
    if len(chunks) > 1:
        chunks = chunks[:-1]

    return chunks

def add_chunks_to_vector_db(chunks):
    """✅ ИСПРАВЛЕНО: batch insert вместо по одному"""
    if not chunks:
        return
    
    documents = []
    ids = []
    metadatas = []
    
    for chunk in chunks:
        doc_id = chunk["metadata"].get("document_id")
        if not doc_id:
            print(f"⚠️ Пропущен чанк без document_id:\n{chunk['chunk_text'][:100]}")
            continue
            
        documents.append(chunk["chunk_text"])
        ids.append(f"{chunk['metadata']['document_id']}_{chunk['chunk_index']}")
        metadatas.append(chunk["metadata"])
    
    if documents:
        try:
            collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            print(f"✅ Добавлено {len(documents)} чанков в векторную базу batch-ом")
        except Exception as e:
            print(f"❌ Ошибка batch insert: {e}")
            # Fallback: добавляем по одному
            for i, chunk in enumerate(chunks):
                try:
                    collection.add(
                        documents=[documents[i]],
                        ids=[ids[i]],
                        metadatas=[metadatas[i]]
                    )
                except Exception as single_error:
                    print(f"❌ Не удалось добавить чанк {i}: {single_error}")

def search_similar_chunks(user_id, query, exclude_doc_id=None, exclude_texts=None, limit=5):
    results = collection.query(
        query_texts=[query],
        n_results=limit + 10,
        where={"$and": [
            {"user_id": str(user_id)},
            {"confirmed": 1}
        ]}
    )
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    filtered = []
    for text, meta in zip(documents, metadatas):
        doc_id = meta.get("document_id")
        print(f"🔍 Проверка мета: document_id = {doc_id}")

        if exclude_doc_id and str(doc_id) == str(exclude_doc_id):
            print(f"⛔ Пропущен чанк из документа {doc_id}")
            continue
        if exclude_texts and text.strip() in exclude_texts:
            print(f"⛔ Пропущен чанк по совпадению текста")
            continue

        filtered.append((text.strip(), doc_id))
        if len(filtered) == limit:
            break

    print("\n🧠 Итоговые чанки, которые пойдут в промт:")
    for i, (text, doc_id) in enumerate(filtered):
        print(f"\n📄 CHUNK {i+1} (document_id = {doc_id}):\n{text.strip()[:500]}")

    return [text for text, _ in filtered]

async def keyword_search_chunks(user_id: int, user_question: str, exclude_doc_id=None, exclude_texts=None, limit=5):
    """✅ ИСПРАВЛЕНО: не загружаем все документы сразу"""
    from gpt import extract_keywords
    keywords = await extract_keywords(user_question)
    print(f"🔎 Ключевые слова из вопроса: {keywords}")

    # Приводим ключевые слова запроса к нижнему регистру и убираем пробелы
    query_keywords = [k.strip().lower() for k in keywords]

    # ✅ ИСПРАВЛЕНИЕ: используем where для фильтрации по user_id
    try:
        raw = collection.get(
            where={"user_id": str(user_id), "confirmed": 1},  # Фильтруем сразу
            include=["documents", "metadatas"]
        )
    except Exception as e:
        print(f"❌ Ошибка поиска в векторной базе: {e}")
        return []

    documents = raw.get("documents", [])
    metadatas = raw.get("metadatas", [])

    results = []
    seen_docs = set()

    for text, meta in zip(documents, metadatas):
        # Дополнительные проверки (на случай если where не сработал)
        if str(meta.get("user_id")) != str(user_id):
            continue
        if meta.get("confirmed") != 1:
            continue
        if exclude_doc_id and str(meta.get("document_id")) == str(exclude_doc_id):
            continue
        if exclude_texts and text.strip() in exclude_texts:
            continue

        raw_keywords = meta.get("keywords", "")
        if isinstance(raw_keywords, str):
            chunk_keywords = [kw.strip().lower() for kw in raw_keywords.split(",")]
        elif isinstance(raw_keywords, list):
            chunk_keywords = [kw.strip().lower() for kw in raw_keywords]
        else:
            chunk_keywords = []

        if any(qk in chunk_keywords for qk in query_keywords):
            doc_id = meta.get("document_id")
            if doc_id not in seen_docs:
                results.append((text.strip(), doc_id))
                seen_docs.add(doc_id)
        if len(results) >= limit:
            break

    print(f"📚 Keyword-поиск дал {len(results)} совпадений.")
    return [text for text, _ in results]