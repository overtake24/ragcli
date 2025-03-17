#!/usr/bin/env python
"""
Mevcut belgeleri yeniden indexleyen araç.
"""
import argparse
import psycopg2
from app.embedding import get_embeddings
from app.db import get_vectorstore
from langchain_core.documents import Document


def reindex_documents():
    """document_chunks tablosundaki belgeleri yeniden indexler."""
    print("🔍 Mevcut belgeleri veritabanından yükleniyor...")

    try:
        # Veritabanı bağlantısı
        from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()

        # Belgeleri document_chunks tablosundan getir
        cursor.execute("SELECT document_id, title, content FROM document_chunks;")
        rows = cursor.fetchall()

        if not rows:
            print("❌ document_chunks tablosunda belge bulunamadı.")
            cursor.close()
            conn.close()
            return

        print(f"✅ {len(rows)} belge bulundu, indexleniyor...")

        # Belgeleri Document nesnelerine dönüştür
        documents = []
        for row in rows:
            doc_id, title, content = row
            if content:
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "document_id": doc_id,
                        "title": title,
                        "source": title or doc_id
                    }
                ))

        # Vektör deposunu hazırla
        embeddings = get_embeddings()
        db = get_vectorstore(embeddings)

        # langchain_pg_embedding tablosunu temizle
        cursor.execute("DELETE FROM langchain_pg_embedding;")
        conn.commit()
        print("✅ langchain_pg_embedding tablosu temizlendi.")

        # Belgeleri vektör deposuna ekle
        if documents:
            db.add_documents(documents)
            print(f"✅ {len(documents)} belge başarıyla vektör deposuna eklendi.")

        # Kontrol et
        cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding;")
        count = cursor.fetchone()[0]
        print(f"📊 langchain_pg_embedding tablosunda şimdi {count} satır var.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Yeniden indexleme hatası: {e}")


def main():
    parser = argparse.ArgumentParser(description="RAG Belge Yeniden İndexleme Aracı")
    parser.add_argument("--force", action="store_true", help="Mevcut index'i zorla sil ve yeniden oluştur")
    args = parser.parse_args()

    reindex_documents()

    print("✅ Yeniden indexleme tamamlandı.")


if __name__ == "__main__":
    main()