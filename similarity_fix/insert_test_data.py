#!/usr/bin/env python3
"""
Yeni test verilerini veritabanına eklemek için örnek betik.
Bu betik, "document_chunks" tablosuna yeni belgeler ekler.
"""

import os
import psycopg2

# Veritabanı ayarları (ortam değişkenlerinden veya doğrudan tanımlayabilirsiniz)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "ragdb")
DB_USER = os.getenv("DB_USER", "raguser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ragpassword")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def insert_document(title, content, embedding):
    """
    Belirtilen belge verilerini document_chunks tablosuna ekler.
    "metadata" sütunu bulunmadığından sadece title, content ve embedding eklenir.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            query = """
            INSERT INTO document_chunks (title, content, embedding)
            VALUES (%s, %s, %s)
            RETURNING document_id;
            """
            cur.execute(query, (title, content, embedding))
            doc_id = cur.fetchone()[0]
            conn.commit()
            return doc_id
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        conn.close()

def main():
    # Örnek test verileri; embedding vektörleri 384 boyutlu dummy değerlerden oluşuyor.
    test_data = [
        {
            "title": "Inception (2010)",
            "content": "Inception is a 2010 science fiction action film written and directed by Christopher Nolan.",
            "embedding": [0.5] * 384  # Örnek dummy embedding
        },
        {
            "title": "The Lord of the Rings: The Fellowship of the Ring",
            "content": "The Fellowship of the Ring is the first volume of J. R. R. Tolkien's epic novel The Lord of the Rings.",
            "embedding": [0.3] * 384
        },
        {
            "title": "Marie Curie",
            "content": "Marie Curie was a physicist and chemist who conducted pioneering research on radioactivity.",
            "embedding": [0.7] * 384
        }
    ]

    for doc in test_data:
        doc_id = insert_document(doc["title"], doc["content"], doc["embedding"])
        if doc_id:
            print(f"Belge eklendi, ID: {doc_id}")

if __name__ == "__main__":
    main()
