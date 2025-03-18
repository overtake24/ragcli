#!/usr/bin/env python3
"""
Veritabanındaki belgeleri yeniden indeksleyen özel araç.
document_chunks tablosundan belgeleri alır ve LangChain vektör veritabanına ekler.
"""
import os
import sys
import argparse
import psycopg2
from langchain_core.documents import Document
from app.config import DB_CONNECTION, COLLECTION_NAME, EMBEDDING_MODEL
from app.embedding import get_embeddings
from app.db import get_vectorstore


def reindex_documents(verbose=False):
    """
    document_chunks tablosundaki belgeleri LangChain vektör deposuna yeniden ekler.
    """
    print("🔄 Belgeler yeniden indeksleniyor...")

    try:
        # Veritabanına bağlan
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # Belge sayısını kontrol et
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        count = cursor.fetchone()[0]

        if count == 0:
            print("❌ document_chunks tablosunda belge yok!")
            return False

        print(f"📊 document_chunks tablosunda {count} belge bulundu.")

        # LangChain tablolarını kontrol et
        try:
            cursor.execute("DROP TABLE IF EXISTS langchain_pg_embedding")
            cursor.execute("DROP TABLE IF EXISTS langchain_pg_collection")
            conn.commit()
            print("🗑️ Eski LangChain tabloları silindi.")
        except:
            pass

        # Belgeleri al
        cursor.execute("""
        SELECT document_id, title, content 
        FROM document_chunks 
        ORDER BY document_id, chunk_index
        """)

        rows = cursor.fetchall()

        # LangChain Document nesneleri oluştur
        docs = []
        doc_count = 0

        for doc_id, title, content in rows:
            doc = Document(
                page_content=content,
                metadata={
                    "source": doc_id,
                    "title": title,
                    "document_id": doc_id
                }
            )
            docs.append(doc)
            doc_count += 1

            if verbose:
                print(f"📄 Belge eklendi: {doc_id} - {title}")

        print(f"📊 {doc_count} belge hazırlandı.")

        # Embeddings ve vector store oluştur
        embeddings = get_embeddings(EMBEDDING_MODEL)
        vector_store = get_vectorstore(embeddings)

        # Belgeleri vector store'a ekle
        print("🔄 Belgeler vektör deposuna ekleniyor...")
        vector_store.add_documents(docs)

        # Kontrol et
        try:
            cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding")
            embedding_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM langchain_pg_collection")
            collection_count = cursor.fetchone()[0]

            print(f"✅ Yeniden indeksleme tamamlandı.")
            print(f"📊 langchain_pg_embedding: {embedding_count} belge")
            print(f"📊 langchain_pg_collection: {collection_count} koleksiyon")

            return True
        except Exception as e:
            print(f"❌ Tablo kontrolü sırasında hata: {e}")
            return False

    except Exception as e:
        print(f"❌ Yeniden indeksleme sırasında hata: {e}")
        return False


def test_query(query_text="test"):
    """
    Vektör deposunun düzgün çalıştığını doğrulamak için test sorgusu yapar.
    """
    print(f"\n🔍 Test sorgusu yapılıyor: '{query_text}'")

    try:
        embeddings = get_embeddings(EMBEDDING_MODEL)
        db = get_vectorstore(embeddings)

        results = db.similarity_search(query_text, k=3)

        if results:
            print(f"✅ {len(results)} sonuç bulundu:")
            for i, doc in enumerate(results, 1):
                print(f"  {i}. {doc.metadata.get('document_id', 'N/A')} - {doc.page_content[:50]}...")
            return True
        else:
            print("❌ Sonuç bulunamadı!")
            return False

    except Exception as e:
        print(f"❌ Sorgu testi sırasında hata: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Belgeleri yeniden indeksleme aracı")
    parser.add_argument("--verbose", "-v", action="store_true", help="Ayrıntılı çıktı")
    parser.add_argument("--query", "-q", type=str, help="Test sorgusu")
    args = parser.parse_args()

    # Belgeleri yeniden indeksle
    success = reindex_documents(args.verbose)

    # Test sorgusu yap
    if success and args.query:
        test_query(args.query)
    elif success:
        test_query()


if __name__ == "__main__":
    main()