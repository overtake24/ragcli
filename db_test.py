#!/usr/bin/env python
"""
Veritabanı bağlantısını ve şemasını test eden araç.
"""
import psycopg2
import argparse
import sys
import json
from psycopg2.extras import RealDictCursor
from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS


def test_connection():
    """Veritabanı bağlantısını test eder."""
    print("🔍 Veritabanı bağlantısı test ediliyor...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        print("✅ Veritabanı bağlantısı başarılı.")
        return conn
    except Exception as e:
        print(f"❌ Veritabanı bağlantısı başarısız: {e}")
        sys.exit(1)


def check_tables(conn):
    """Veritabanındaki tabloları kontrol eder."""
    print("\n🔍 Veritabanı tabloları kontrol ediliyor...")
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"📋 Bulunan tablolar: {tables}")

    required_tables = ['document_chunks', 'langchain_pg_embedding', 'langchain_pg_collection']
    missing_tables = [table for table in required_tables if table not in tables]

    if missing_tables:
        print(f"⚠️ Eksik tablolar: {missing_tables}")
    else:
        print("✅ Gerekli tüm tablolar mevcut.")

    cursor.close()
    return tables


def check_table_schema(conn, table_name):
    """Tablonun şemasını kontrol eder."""
    print(f"\n🔍 '{table_name}' tablosunun yapısı kontrol ediliyor...")
    cursor = conn.cursor()
    cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}';")
    columns = cursor.fetchall()

    print(f"📋 '{table_name}' tablosunun sütunları:")
    for col in columns:
        print(f"  - {col[0]} ({col[1]})")

    cursor.close()
    return columns


def check_row_count(conn, table_name):
    """Tablodaki satır sayısını kontrol eder."""
    print(f"\n🔍 '{table_name}' tablosundaki satır sayısı kontrol ediliyor...")
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]

    print(f"📊 '{table_name}' tablosunda {count} satır var.")
    cursor.close()
    return count


def examine_sample_data(conn, table_name, limit=3):
    """Tablodan örnek veri inceler."""
    print(f"\n🔍 '{table_name}' tablosundan örnek veriler inceleniyor...")

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit};")
        rows = cursor.fetchall()

        if not rows:
            print(f"⚠️ '{table_name}' tablosunda veri bulunamadı.")
            return []

        for i, row in enumerate(rows):
            print(f"\n📄 Örnek {i + 1}:")
            # Embedding vektörünün boyutunu hesapla
            if 'embedding' in row and row['embedding'] is not None:
                embedding_size = len(row['embedding'])
                # Vektörün sadece ilk 5 elemanını göster
                row['embedding'] = f"[{', '.join([str(x) for x in row['embedding'][:5]])}...] (Boyut: {embedding_size})"

            # Uzun içerikleri kısalt
            for key, value in row.items():
                if isinstance(value, str) and len(value) > 100:
                    row[key] = value[:100] + "..."

            # JSON formatında göster
            print(json.dumps(row, indent=2, default=str))

        cursor.close()
        return rows
    except Exception as e:
        print(f"❌ Veri inceleme hatası: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="RAG Veritabanı Test Aracı")
    parser.add_argument("--full", action="store_true", help="Tam test yapılır (örnek veri dahil)")
    args = parser.parse_args()

    # Bağlantıyı test et
    conn = test_connection()

    # Tabloları kontrol et
    tables = check_tables(conn)

    # Her tablo için şema kontrolü
    for table in tables:
        check_table_schema(conn, table)
        count = check_row_count(conn, table)

        # Eğer tam test isteniyorsa ve tabloda veri varsa, örnek veri incele
        if args.full and count > 0:
            examine_sample_data(conn, table)

    # Bağlantıyı kapat
    conn.close()
    print("\n✅ Veritabanı testi tamamlandı.")


if __name__ == "__main__":
    main()