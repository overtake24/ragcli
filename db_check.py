#!/usr/bin/env python3
"""
Veritabanındaki belgeleri kontrol eden script
"""
import psycopg2
from app.config import DB_CONNECTION


def check_database():
    """Veritabanındaki document_chunks tablosunun içeriğini kontrol eder"""
    try:
        # Veritabanına bağlan
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # Belge sayısını kontrol et
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        count = cursor.fetchone()[0]
        print(f"Toplam belge parçası sayısı: {count}")

        # Belge ID'lerini kontrol et
        cursor.execute("SELECT DISTINCT document_id FROM document_chunks")
        document_ids = cursor.fetchall()
        print("\nBelge ID'leri:")
        for doc_id in document_ids:
            cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE document_id = %s", (doc_id[0],))
            doc_count = cursor.fetchone()[0]
            print(f"  - {doc_id[0]}: {doc_count} parça")

        # İçerik örneklerini kontrol et
        print("\nİçerik örnekleri (ilk 200 karakter):")
        cursor.execute("SELECT document_id, content FROM document_chunks LIMIT 5")
        contents = cursor.fetchall()
        for doc_id, content in contents:
            print(f"  - {doc_id}: {content[:200].replace(chr(10), ' ')}...")

        # "Scandinavia" içeren belgeler var mı?
        cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE content ILIKE %s", ('%Scandinavia%',))
        scandinavia_count = cursor.fetchone()[0]
        print(f"\n'Scandinavia' içeren belge sayısı: {scandinavia_count}")

        if scandinavia_count > 0:
            cursor.execute("SELECT document_id FROM document_chunks WHERE content ILIKE %s LIMIT 3", ('%Scandinavia%',))
            scan_docs = cursor.fetchall()
            print("'Scandinavia' içeren belge ID'leri (ilk 3):")
            for doc_id in scan_docs:
                print(f"  - {doc_id[0]}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Hata: {e}")


if __name__ == "__main__":
    check_database()