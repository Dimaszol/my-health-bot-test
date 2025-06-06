import sqlite3
from vector_db import get_recent_vector_documents

def check_sqlite_documents():
    print("📄 Последние 3 документа в SQLite:")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, title, file_type, uploaded_at
        FROM documents
        ORDER BY id DESC
        LIMIT 3
    """)
    rows = cursor.fetchall()
    for row in rows:
        doc_id, user_id, title, file_type, uploaded_at = row
        print(f"  ID: {doc_id}, user_id: {user_id}, type: {file_type}, title: {title}, uploaded: {uploaded_at}")

    conn.close()

def check_vector_documents(limit=3):
    print("\n🧠 Документы в ChromaDB (последние):")
    try:
        results = get_recent_vector_documents(limit=limit)
        for doc_id, metadata in results:
            print(f"  ID: {doc_id}, user_id: {metadata.get('user_id')}")
    except Exception as e:
        print("❌ Ошибка при доступе к векторной базе:", e)


if __name__ == "__main__":
    check_sqlite_documents()
    check_vector_documents(limit=3)
