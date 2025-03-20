#!/usr/bin/env python3
"""
LangChain tablolarını oluşturma ve başlatma scripti.
Bu sürüm, langchain_pg_collection ve langchain_pg_embedding tablolarını oluşturur.
langchain_pg_embedding tablosu, 384 boyutlu vektör için chunk_index sütunu dahil olmak üzere oluşturulur.
"""
import psycopg2
import json
from app.config import DB_CONNECTION

def setup_langchain_tables():
    """LangChain için gerekli tabloları oluşturur."""
    print("🔄 LangChain tabloları oluşturuluyor...")
    try:
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # pgvector uzantısını kontrol et ve yükle
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # LangChain koleksiyon tablosunu oluştur
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS langchain_pg_collection (
            uuid UUID PRIMARY KEY,
            name VARCHAR(255),
            cmetadata JSON
        )
        """)

        # LangChain embedding tablosunu oluştur (chunk_index sütunu eklenmiştir)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
    uuid UUID PRIMARY KEY,
    collection_id UUID REFERENCES langchain_pg_collection(uuid),
    document TEXT,
    embedding vector(384),
    cmetadata JSON,
    custom_id VARCHAR(255),
    chunk_index INTEGER -- EKLENEN SÜTUN
)


        conn.commit()
        print("✅ LangChain tabloları başarıyla oluşturuldu")

        # Koleksiyon oluştur: Eğer koleksiyon yoksa, "document_chunks" koleksiyonunu oluşturuyoruz.
        cursor.execute("SELECT COUNT(*) FROM langchain_pg_collection")
        collection_count = cursor.fetchone()[0]
        if collection_count == 0:
            import uuid
            collection_id = str(uuid.uuid4())
            empty_metadata = json.dumps({})
            cursor.execute("""
            INSERT INTO langchain_pg_collection (uuid, name, cmetadata)
            VALUES (%s, %s, %s)
            """, (collection_id, "document_chunks", empty_metadata))
            conn.commit()
            print(f"✅ 'document_chunks' koleksiyonu oluşturuldu (UUID: {collection_id})")
        else:
            print("ℹ️ Koleksiyon zaten mevcut")

        # Opsiyonel: document_chunks tablosunda birleşik indeks oluşturulması (sorgu performansını artırır)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_doc_chunk ON document_chunks (document_id, chunk_index)
        """)
        conn.commit()

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ LangChain tabloları oluşturulurken hata: {e}")
        return False

if __name__ == "__main__":
    setup_langchain_tables()
