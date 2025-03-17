#!/usr/bin/env python3
"""
Veritabanındaki belgeleri kontrol eden basit script
"""
import psycopg2
from app.config import DB_CONNECTION


def check_database():
    """Veritabanındaki document_chunks tablosunun içeriğini kontrol eder"""
    try:
        # Veritabanına bağlan
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # Tablo yapısını kontrol et
        print("Tablo yapısı kontrol ediliyor...")
        cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'document_chunks'
        """)
        columns = cursor.fetchall()

        print("Tablo yapısı:")
        for column_name, data_type in columns:
            print(f"  - {column_name}: {data_type}")

        # Belge sayısını kontrol et
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        count = cursor.fetchone()[0]
        print(f"\nToplam belge parçası sayısı: {count}")

        # İskandinav içeriği var mı kontrol et
        print("\nİçerik arama:")
        search_terms = ['Scandinavia', 'Nordic', 'Denmark', 'Norway', 'Sweden', 'Finland', 'Iceland']

        for term in search_terms:
            cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE content ILIKE %s", (f'%{term}%',))
            term_count = cursor.fetchone()[0]
            print(f"  - '{term}' içeren belge sayısı: {term_count}")

        # En son eklenen 5 belgeyi göster
        print("\nEn son eklenen 5 belge:")
        cursor.execute("""
        SELECT document_id, title, LEFT(content, 100) 
        FROM document_chunks 
        ORDER BY id DESC 
        LIMIT 5
        """)
        recent_docs = cursor.fetchall()

        for doc_id, title, content_preview in recent_docs:
            print(f"  - Belge: {doc_id}")
            print(f"    Başlık: {title}")
            print(f"    İçerik önizleme: {content_preview.replace(chr(10), ' ')}...")
            print()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Hata: {e}")


if __name__ == "__main__":
    check_database()