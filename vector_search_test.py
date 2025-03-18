#!/usr/bin/env python
"""
Vektör aramaları test eden araç.
"""
import argparse
import os
import psycopg2
import numpy as np
from app.embedding import get_embeddings
from app.db import get_vectorstore
from langchain_core.documents import Document


def test_vectorstore_connection():
    """Vektör deposu bağlantısını test eder."""
    print("🔍 Vektör deposu bağlantısı test ediliyor...")
    try:
        embeddings = get_embeddings()
        db = get_vectorstore(embeddings)
        print("✅ Vektör deposu bağlantısı başarılı.")
        return db
    except Exception as e:
        print(f"❌ Vektör deposu bağlantısı başarısız: {e}")
        return None


def add_test_documents(db, folder_path="test_data/scandinavia"):
    """Test belgelerini vektör deposuna ekler."""
    print(f"\n🔍 Test belgeleri '{folder_path}' klasöründen yükleniyor...")
    documents = []

    if not os.path.exists(folder_path):
        print(f"❌ '{folder_path}' klasörü bulunamadı.")
        return []

    try:
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                doc = Document(
                    page_content=content,
                    metadata={"source": filename, "filename": filename}
                )
                documents.append(doc)
                print(f"📄 Yüklenen: {filename} ({len(content)} karakter)")

        if documents:
            print(f"\n🔍 {len(documents)} belge vektör deposuna ekleniyor...")
            db.add_documents(documents)
            print(f"✅ {len(documents)} belge başarıyla eklendi.")
        else:
            print("⚠️ Yüklenecek belge bulunamadı.")

        return documents
    except Exception as e:
        print(f"❌ Belge yükleme hatası: {e}")
        return []


def test_search(db, query, k=3):
    """Vektör araması yapar."""
    print(f"\n🔍 Sorgu test ediliyor: '{query}'")

    try:
        results = db.similarity_search(query, k=k)

        print(f"✅ {len(results)} sonuç bulundu.")
        for i, doc in enumerate(results):
            print(f"\n📄 Sonuç {i + 1}:")
            print(f"  - Kaynak: {doc.metadata.get('source', 'bilinmiyor')}")
            print(f"  - İçerik: {doc.page_content[:100]}...")

        return results
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        return []


def test_embeddings_in_db(db_config, model_name):
    """Veritabanındaki embedding vektörlerini kontrol eder."""
    print("\n🔍 Veritabanındaki embedding vektörleri kontrol ediliyor...")

    try:
        # Veritabanına bağlan
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()

        # Embedding vektörlerini kontrol et
        cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding WHERE embedding IS NOT NULL;")
        count_with_embeddings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding;")
        total_count = cursor.fetchone()[0]

        print(f"📊 Toplam {total_count} belgeden {count_with_embeddings} tanesinde embedding vektörü var.")

        if count_with_embeddings > 0:
            # Bir vektörü incele
            cursor.execute("SELECT embedding FROM langchain_pg_embedding WHERE embedding IS NOT NULL LIMIT 1;")
            embedding = cursor.fetchone()[0]

            print(f"📈 Örnek embedding vektörü:")
            print(f"  - Boyut: {len(embedding)}")
            print(f"  - İlk 5 eleman: {embedding[:5]}")

            # Vektör istatistikleri
            embedding_array = np.array(embedding)
            print(f"  - Ortalama: {np.mean(embedding_array):.6f}")
            print(f"  - Min: {np.min(embedding_array):.6f}")
            print(f"  - Max: {np.max(embedding_array):.6f}")
            print(f"  - Standart sapma: {np.std(embedding_array):.6f}")

            # Model adını kontrol et
            cursor.execute("SELECT cmetadata FROM langchain_pg_embedding WHERE embedding IS NOT NULL LIMIT 1;")
            metadata = cursor.fetchone()[0]

            if metadata and 'model' in metadata:
                db_model = metadata['model']
                print(f"  - Kullanılan embedding modeli: {db_model}")

                if db_model != model_name:
                    print(f"⚠️ Uyarı: Veritabanındaki model ({db_model}) şu anki modelden ({model_name}) farklı!")
            else:
                print("⚠️ Uyarı: Embedding metadata'sında model bilgisi bulunamadı.")

        cursor.close()
        conn.close()

        return count_with_embeddings, total_count
    except Exception as e:
        print(f"❌ Veritabanı kontrol hatası: {e}")
        return 0, 0


def main():
    parser = argparse.ArgumentParser(description="RAG Vektör Arama Test Aracı")
    parser.add_argument("--query", type=str, default="İskandinav ülkeleri", help="Test sorgusu")
    parser.add_argument("--k", type=int, default=3, help="Döndürülecek sonuç sayısı")
    parser.add_argument("--load", action="store_true", help="Test belgelerini yükle")
    args = parser.parse_args()

    # Vektör deposuna bağlan
    db = test_vectorstore_connection()
    if not db:
        return

    # Veritabanı konfigürasyonu
    from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
    db_config = {
        'host': DB_HOST,
        'port': DB_PORT,
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASS
    }

    # Veritabanındaki embeddinglari kontrol et
    from app.config import EMBEDDING_MODEL
    test_embeddings_in_db(db_config, EMBEDDING_MODEL)

    # Belge yükleme
    if args.load:
        add_test_documents(db)

    # Arama testi
    test_search(db, args.query, args.k)

    print("\n✅ Vektör arama testi tamamlandı.")


if __name__ == "__main__":
    main()