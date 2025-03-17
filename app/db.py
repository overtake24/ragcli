# app/db.py
"""
Veritabanı işlemleri.
"""
import psycopg2
from psycopg2 import sql
from langchain_community.vectorstores import PGVector

from app.config import DB_CONNECTION, COLLECTION_NAME


def setup_db():
    """
    PostgreSQL veritabanını RAG için hazırla.
    """
    conn = psycopg2.connect(DB_CONNECTION)
    cursor = conn.cursor()

    # pgvector uzantısını yükle
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # İşlenmiş veri tablosunu oluştur
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_data (
        id SERIAL PRIMARY KEY,
        title TEXT,
        summary TEXT,
        key_points TEXT[],
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    return True


def get_vectorstore(embedding_function):
    """
    PGVector vektör deposunu döndür.
    """
    return PGVector(
        embedding_function=embedding_function,
        connection_string=DB_CONNECTION,
        collection_name=COLLECTION_NAME,
        distance_strategy="cosine"
    )