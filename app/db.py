# app/db.py
"""
Veritabanı işlemleri.
"""
import psycopg2
from psycopg2 import sql
from langchain_community.vectorstores import PGVector

from app.config import DB_CONNECTION, COLLECTION_NAME


def get_db_connection():
    """
    PostgreSQL veritabanı bağlantısı oluştur.
    """
    return psycopg2.connect(DB_CONNECTION)


def setup_db():
    """
    PostgreSQL veritabanını RAG için hazırla.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # pgvector uzantısını yükle
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Document chunks tablosunu oluştur
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id SERIAL PRIMARY KEY,
        document_id TEXT,
        title TEXT,
        content TEXT,
        chunk_index INTEGER,
        total_chunks INTEGER,
        embedding vector(384),
        embedding_model TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

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


def get_vectorstore(embeddings=None):
    """Vektör deposunu oluşturur ve döndürür"""
    from app.config import DB_CONNECTION, COLLECTION_NAME, EMBEDDING_MODEL
    if embeddings is None:
        embeddings = get_embeddings(EMBEDDING_MODEL)

    # Config.py'den gelen bağlantı dizesini kullan
    print(f"DEBUG - Veritabanı bağlantısı: {DB_CONNECTION}")

    return PGVector(
        connection_string=DB_CONNECTION,  # <-- BU SATIR ÇÖZÜM
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )