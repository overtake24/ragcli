#!/usr/bin/env python3
"""
Embedding sütununun veri tipini kontrol eder
"""
import psycopg2
from app.config import DB_CONNECTION


def check_embedding_type():
    """Embedding sütununun veri tipini kontrol eder"""
    try:
        # Veritabanına bağlan
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # Embedding sütununun veri tipini sorgula
        cursor.execute("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name = 'document_chunks' 
        AND column_name = 'embedding'
        """)

        result = cursor.fetchone()
        if result:
            print(f"'embedding' sütununun veri tipi: {result[0]}")

            # Veri tipine göre öneriler
            if result[0] == 'USER-DEFINED' or result[0] == 'vector':
                print("✅ Doğru veri tipi! (pgvector'ün 'vector' tipi)")
            else:
                print("❌ Beklenmeyen veri tipi! pgvector kurulumu doğru yapılmamış olabilir.")
        else:
            print("'embedding' sütunu bulunamadı!")

        # İlk kaydın embedding sütununu örnek olarak göster
        cursor.execute("SELECT id, embedding FROM document_chunks LIMIT 1")
        record = cursor.fetchone()
        if record:
            embedding_sample = str(record[1])
            print(f"\nİlk kaydın embedding örneği (ilk 100 karakter):")
            print(embedding_sample[:100], "...")
            print(f"Embedding veri tipi: {type(record[1])}")

            # Uzunluk kontrol et
            try:
                if hasattr(record[1], '__len__'):
                    print(f"Embedding uzunluğu: {len(record[1])}")
            except:
                print("Embedding uzunluğu hesaplanamadı")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Hata: {e}")


if __name__ == "__main__":
    check_embedding_type()