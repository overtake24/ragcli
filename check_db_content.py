#!/usr/bin/env python3
"""
Veritabanında indekslenen içerikleri kontrol etmek için script
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import argparse

# Veritabanı bağlantı bilgileri
from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS


def check_document_chunks():
    """Document_chunks tablosunu kontrol eder ve istatistikler verir"""
    try:
        # Veritabanına bağlan
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Toplam belge sayısını kontrol et
        cursor.execute("SELECT COUNT(*) AS total FROM document_chunks")
        total_count = cursor.fetchone()['total']
        print(f"Veritabanında toplam {total_count} belge parçası bulunuyor")

        # Benzersiz belge sayısını kontrol et
        cursor.execute("SELECT COUNT(DISTINCT document_id) AS unique_docs FROM document_chunks")
        unique_docs = cursor.fetchone()['unique_docs']
        print(f"Veritabanında {unique_docs} benzersiz belge bulunuyor")

        # Belge ID'lerine göre grupla
        cursor.execute("""
        SELECT document_id, COUNT(*) as chunk_count, MIN(title) as title
        FROM document_chunks
        GROUP BY document_id
        ORDER BY chunk_count DESC
        """)
        doc_stats = cursor.fetchall()

        print("\nBelge istatistikleri:")
        print("-" * 60)
        print(f"{'Belge ID':<30} | {'Parça Sayısı':<12} | {'Başlık':<30}")
        print("-" * 60)

        for doc in doc_stats:
            print(f"{doc['document_id'][:30]:<30} | {doc['chunk_count']:<12} | {(doc['title'] or 'Başlık yok')[:30]}")

        # İçerik türlerine göre analiz
        print("\nİçerik türleri:")
        content_types = {
            "film": 0,
            "book": 0,
            "person": 0,
            "other": 0
        }

        for doc in doc_stats:
            doc_id = doc['document_id']
            if "inception" in doc_id.lower() or "matrix" in doc_id.lower():
                content_types["film"] += 1
            elif "lord_of_rings" in doc_id.lower() or "yuzuk" in doc_id.lower():
                content_types["book"] += 1
            elif "marie_curie" in doc_id.lower() or "curie" in doc_id.lower():
                content_types["person"] += 1
            else:
                content_types["other"] += 1

        for content_type, count in content_types.items():
            print(f"- {content_type.capitalize()}: {count} belge")

        # En son eklenen belgeleri kontrol et
        cursor.execute("""
        SELECT document_id, title, LEFT(content, 100) as preview, created_at
        FROM document_chunks
        ORDER BY created_at DESC
        LIMIT 5
        """)
        recent_docs = cursor.fetchall()

        print("\nEn son eklenen 5 belge parçası:")
        for doc in recent_docs:
            print(f"ID: {doc['document_id']}")
            print(f"Başlık: {doc['title']}")
            print(f"Oluşturulma: {doc['created_at']}")
            print(f"Önizleme: {doc['preview']}...")
            print("-" * 40)

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Hata: {e}")
        return False


def check_embeddings():
    """Embedding vektörlerini kontrol eder"""
    try:
        # Veritabanına bağlan
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Toplam embedding sayısını kontrol et
        cursor.execute("SELECT COUNT(*) AS total FROM langchain_pg_embedding")
        total_count = cursor.fetchone()['total']
        print(f"\nVeritabanında toplam {total_count} embedding vektörü bulunuyor")

        # Embedding vektörlerinin boyutunu kontrol et
        cursor.execute("""
        SELECT array_length(embedding, 1) as vector_size
        FROM langchain_pg_embedding
        LIMIT 1
        """)
        result = cursor.fetchone()

        if result and 'vector_size' in result:
            print(f"Embedding vektör boyutu: {result['vector_size']}")
        else:
            print("Embedding vektör boyutu belirlenemedi")

        # Koleksiyonları kontrol et
        cursor.execute("SELECT * FROM langchain_pg_collection")
        collections = cursor.fetchall()

        print(f"\nToplam {len(collections)} koleksiyon bulunuyor:")
        for coll in collections:
            coll_name = coll.get('name', 'İsimsiz')
            coll_id = coll.get('uuid', 'ID yok')

            # Koleksiyondaki belge sayısını kontrol et
            cursor.execute("SELECT COUNT(*) as doc_count FROM langchain_pg_embedding WHERE collection_id = %s",
                           (coll_id,))
            doc_count = cursor.fetchone()['doc_count']

            print(f"- {coll_name}: {doc_count} belge (ID: {coll_id})")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Hata: {e}")
        return False


def run_custom_query(query):
    """Özel bir sorgu çalıştırır"""
    try:
        # Veritabanına bağlan
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Sorguyu çalıştır
        cursor.execute(query)
        results = cursor.fetchall()

        print(f"\nÖzel sorgu sonuçları ({len(results)} satır):")
        print("-" * 60)

        # Sonuçları göster
        if results:
            # Sütun başlıklarını göster
            columns = list(results[0].keys())
            header = " | ".join(f"{col[:15]:<15}" for col in columns)
            print(header)
            print("-" * 60)

            # Satırları göster (en fazla 20 satır)
            for row in results[:20]:
                row_str = " | ".join(f"{str(val)[:15]:<15}" for val in row.values())
                print(row_str)

            if len(results) > 20:
                print(f"...ve {len(results) - 20} satır daha")
        else:
            print("Sorgu sonuç döndürmedi")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Hata: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Veritabanı içerik kontrolü")
    parser.add_argument("--query", type=str, help="Özel bir SQL sorgusu çalıştır")
    args = parser.parse_args()

    print("RAG CLI Veritabanı İçerik Kontrolü")
    print("=" * 60)

    if args.query:
        run_custom_query(args.query)
    else:
        # Standart kontroller
        check_document_chunks()
        check_embeddings()