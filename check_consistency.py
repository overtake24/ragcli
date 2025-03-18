#!/usr/bin/env python3
"""
Veritabanı tutarlılığını kontrol eden ve düzeltmeye yardımcı olan araç.
LangChain PGVector ve document_chunks tabloları arasındaki tutarlılığı kontrol eder.
"""
import os
import sys
import argparse
import psycopg2
import time
from psycopg2 import sql
from app.config import DB_CONNECTION, COLLECTION_NAME, EMBEDDING_MODEL
from app.embedding import get_embeddings


def check_db_tables():
    """Veritabanındaki tabloları kontrol eder"""
    print("🔍 Belge tabloları tutarlılığını kontrol ediliyor...")
    try:
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # document_chunks tablosunu kontrol et
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        count = cursor.fetchone()[0]
        print(f"📊 document_chunks: {count} belge")

        # langchain_pg_embedding tablosunu kontrol et
        try:
            cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding")
            embedding_count = cursor.fetchone()[0]
            print(f"📊 langchain_pg_embedding: {embedding_count} belge")

            # langchain_pg_collection tablosunu kontrol et
            cursor.execute("SELECT COUNT(*) FROM langchain_pg_collection")
            collection_count = cursor.fetchone()[0]
            print(f"📊 langchain_pg_collection: {collection_count} koleksiyon")

            # Tutarlılık kontrolü
            if count > 0 and embedding_count == 0:
                print(
                    "⚠️ Uyumsuzluk tespit edildi: document_chunks tablosunda belgeler var, ancak langchain_pg_embedding tablosunda yok!")
                return False
            elif count == 0 and embedding_count > 0:
                print(
                    "⚠️ Uyumsuzluk tespit edildi: langchain_pg_embedding tablosunda belgeler var, ancak document_chunks tablosunda yok!")
                return False
            else:
                print(
                    f"✅ Tablolar arasında tutarlılık var (document_chunks: {count}, langchain_pg_embedding: {embedding_count})")
                return True

        except psycopg2.errors.UndefinedTable:
            print("⚠️ langchain_pg_embedding veya langchain_pg_collection tablosu bulunamadı!")
            return False

        except Exception as e:
            print(f"❌ Tutarlılık kontrolü sırasında hata: {e}")
            return False

    except Exception as e:
        print(f"❌ Tutarlılık kontrolü sırasında hata: {e}")
        return False


def reindex_documents(reset=False):
    """Dokümanları yeniden indeksleyerek LangChain tablolarını oluşturur"""
    from app.db import get_vectorstore
    from langchain_core.documents import Document

    try:
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # LangChain tablolarını sıfırla
        if reset:
            try:
                cursor.execute("DROP TABLE IF EXISTS langchain_pg_embedding")
                cursor.execute("DROP TABLE IF EXISTS langchain_pg_collection")
                conn.commit()
                print("🗑️ LangChain tabloları silindi, yeniden oluşturulacak.")
            except Exception as e:
                print(f"⚠️ Tablolar silinirken hata: {e}")

        # document_chunks tablosundan belgeleri al
        cursor.execute("""
        SELECT document_id, title, content 
        FROM document_chunks 
        ORDER BY document_id, chunk_index
        """)

        documents = cursor.fetchall()
        if not documents:
            print("❌ document_chunks tablosunda belge bulunamadı!")
            return False

        print(f"📄 {len(documents)} belge parçası document_chunks tablosundan alındı.")

        # Belgeleri Document nesnelerine dönüştür
        langchain_docs = []
        for doc_id, title, content in documents:
            langchain_docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "document_id": doc_id,
                        "title": title,
                        "source": doc_id
                    }
                )
            )

        # PGVector'ü başlat ve belgeleri ekle
        embeddings = get_embeddings(EMBEDDING_MODEL)
        vector_store = get_vectorstore(embeddings)

        print(f"🔄 {len(langchain_docs)} belge LangChain vektör deposuna ekleniyor...")
        vector_store.add_documents(langchain_docs)

        # Kontrol et
        try:
            cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding")
            new_count = cursor.fetchone()[0]
            print(f"✅ langchain_pg_embedding tablosu oluşturuldu ve {new_count} belge eklendi.")

            cursor.execute("SELECT COUNT(*) FROM langchain_pg_collection")
            collection_count = cursor.fetchone()[0]
            print(f"✅ langchain_pg_collection tablosu oluşturuldu ve {collection_count} koleksiyon eklendi.")

            return True
        except Exception as e:
            print(f"❌ Yeniden indeksleme sonrası kontrol hatası: {e}")
            return False

    except Exception as e:
        print(f"❌ Yeniden indeksleme hatası: {e}")
        return False


def test_query(query="Test sorgusu"):
    """Test sorgusu yaparak sistemin çalışıp çalışmadığını kontrol eder"""
    from app.db import get_vectorstore

    try:
        print(f"\n🔍 Test sorgusu yapılıyor: '{query}'")
        embeddings = get_embeddings(EMBEDDING_MODEL)
        db = get_vectorstore(embeddings)

        # Benzerlik araması yap
        results = db.similarity_search(query, k=2)

        if results:
            print(f"✅ {len(results)} sonuç bulundu:")
            for i, doc in enumerate(results, 1):
                print(f"  {i}. {doc.metadata.get('document_id')} - {doc.page_content[:50]}...")
            return True
        else:
            print("❌ Sonuç bulunamadı!")
            return False

    except Exception as e:
        print(f"❌ Sorgu testi hatası: {e}")
        return False


def fix_database(reset=False):
    """Veritabanı sorunlarını tespit edip düzeltir"""
    # Tutarlılık kontrolü
    is_consistent = check_db_tables()

    if is_consistent and not reset:
        print("✅ Veritabanı tutarlı. Düzeltmeye gerek yok.")
        return True

    if reset:
        print("⚠️ Veritabanı sıfırlanıyor...")
    else:
        print("⚠️ Veritabanı tutarsızlığı tespit edildi. Düzeltiliyor...")

    # Belgeleri yeniden indeksle
    success = reindex_documents(reset)

    if success:
        # Test sorgusu yap
        test_query("test")
        print("\n✅ Veritabanı düzeltme işlemi tamamlandı.")
        return True
    else:
        print("\n❌ Veritabanı düzeltme işlemi başarısız oldu.")
        return False


def reset_database():
    """Veritabanını tamamen sıfırlar"""
    from app.db import setup_db

    try:
        confirm = input("⚠️ Veritabanı tamamen sıfırlanacak! Devam etmek istiyor musunuz? (e/H): ")
        if confirm.lower() != 'e':
            print("İşlem iptal edildi.")
            return False

        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # Tüm tabloları sil
        cursor.execute("DROP TABLE IF EXISTS document_chunks")
        cursor.execute("DROP TABLE IF EXISTS processed_data")
        cursor.execute("DROP TABLE IF EXISTS langchain_pg_embedding")
        cursor.execute("DROP TABLE IF EXISTS langchain_pg_collection")
        conn.commit()

        print("🗑️ Tüm tablolar silindi.")

        # Tabloları yeniden oluştur
        setup_db()
        print("✅ Veritabanı başarıyla sıfırlandı.")

        return True

    except Exception as e:
        print(f"❌ Veritabanı sıfırlama hatası: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Veritabanı tutarlılık kontrolü ve düzeltme aracı")
    parser.add_argument("--fix", action="store_true", help="Tespit edilen sorunları düzelt")
    parser.add_argument("--reset", action="store_true", help="Veritabanını tamamen sıfırla")
    parser.add_argument("--query", type=str, default="test", help="Test sorgusu")
    args = parser.parse_args()

    if args.reset:
        reset_database()
    elif args.fix:
        fix_database(reset=False)
    else:
        check_db_tables()

        # Eğer sorun varsa düzeltmeyi öner
        print("\nSorun tespit edildiyse, aşağıdaki komutu kullanarak düzeltebilirsiniz:")
        print("python check_consistency.py --fix")

    if args.query and args.query != "test":
        test_query(args.query)


if __name__ == "__main__":
    main()
