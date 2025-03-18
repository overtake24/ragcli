#!/usr/bin/env python3
"""
Veritabanı temizleme ve yeniden oluşturma scripti.
"""
import psycopg2
import json
import logging
from app.config import DB_CONNECTION
from app.embedding import get_embeddings
from langchain_core.documents import Document
from app.db import get_vectorstore
import uuid

logging.basicConfig(level=logging.INFO)

def clear_and_rebuild():
    logging.info("🔄 Veritabanı tutarlılığı sağlanıyor...")
    conn = psycopg2.connect(DB_CONNECTION)
    cursor = conn.cursor()

    try:
        # 1) Mevcut langchain tablolarını sil
        cursor.execute("DROP TABLE IF EXISTS langchain_pg_embedding CASCADE")
        cursor.execute("DROP TABLE IF EXISTS langchain_pg_collection CASCADE")

        # 2) langchain_pg_collection tablosunu yeniden oluştur
        cursor.execute("""
        CREATE TABLE langchain_pg_collection (
            uuid UUID PRIMARY KEY,
            name VARCHAR(255),
            cmetadata JSON
        )
        """)

        # 3) langchain_pg_embedding tablosunu chunk_index sütunu dahil oluştur
        cursor.execute("""
        CREATE TABLE langchain_pg_embedding (
            uuid UUID PRIMARY KEY,
            collection_id UUID REFERENCES langchain_pg_collection(uuid),
            document TEXT,
            embedding vector(384),
            cmetadata JSON,
            custom_id VARCHAR(255),
            chunk_index INTEGER
        )
        """)

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM langchain_pg_collection")
        if cursor.fetchone()[0] == 0:
            collection_id = str(uuid.uuid4())
            cursor.execute("""
            INSERT INTO langchain_pg_collection (uuid, name, cmetadata)
            VALUES (%s, %s, %s)
            """, (collection_id, "document_chunks", json.dumps({})))
            conn.commit()

        # 4) document_chunks tablosundan verileri çek
        cursor.execute("""
        SELECT document_id, title, content, embedding, chunk_index
        FROM document_chunks
        ORDER BY document_id, chunk_index
        """)

        rows = cursor.fetchall()

        documents = []
        ids = []

        # 5) Her satırdan Document ve custom_id oluştur
        for row_data in rows:
            doc_id, title, content, embedding, chunk_idx = row_data

            doc = Document(
                page_content=content,
                metadata={
                    "document_id": doc_id,
                    "chunk_index": chunk_idx,
                    "title": title
                }
            )
            documents.append(doc)

            # Burada doc_id__chunkX formatıyla custom_id oluşturuyoruz.
            # Örnek: "inception__chunk0"
            custom_id = f"{doc_id}__chunk{chunk_idx}"
            ids.append(custom_id)

        # 6) Embeddings ve vectorstore
        embeddings = get_embeddings()
        vectorstore = get_vectorstore(embeddings)

        # 7) Belgeleri eklerken ids parametresi ile custom_id değerlerini atıyoruz
        vectorstore.add_documents(documents, ids=ids)
        logging.info(f"✅ {len(rows)} belge LangChain vektör deposuna eklendi.")

    except Exception as e:
        logging.error(f"❌ Veritabanı işlemi sırasında hata: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

    cursor.close()
    conn.close()
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    clear_and_rebuild()
