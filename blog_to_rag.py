#!/usr/bin/env python3
"""
Blog içeriklerini RAG sistemine aktarma scripti (Docker uyumlu - raguser)
"""
import os
import json
import psycopg2
import requests
import time
import argparse
from psycopg2 import sql

# Yapılandırma - Docker bağlantı bilgileri
BLOG_DB_CONNECTION = "postgresql://raguser:ragpassword@localhost:5432/blog_db"
RAG_API_URL = "http://localhost:8000/index_text"


def connect_to_blog_db():
    """Blog veritabanına bağlan"""
    try:
        return psycopg2.connect(BLOG_DB_CONNECTION)
    except Exception as e:
        print(f"Veritabanına bağlanırken hata: {e}")
        print("Bağlantı bilgileri kontrol ediliyor...")

        # Docker bağlantısını kontrol et
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "exec", "postgres-ragcli", "psql", "-U", "raguser", "-d", "blog_db", "-c", "SELECT 1;"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("Docker üzerinden veritabanı bağlantısı başarılı.")
                print("Ancak doğrudan bağlantı yapılamıyor.")
                print(f"Bağlantı URL'si: {BLOG_DB_CONNECTION}")
                print("Port yönlendirme kontrol ediliyor...")

                port_check = subprocess.run(
                    ["docker", "port", "postgres-ragcli"],
                    capture_output=True, text=True
                )
                print(f"Port yönlendirme: {port_check.stdout}")
            else:
                print(f"Docker üzerinden kontrol başarısız: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Docker üzerinden kontrol başarısız: {e}")

        raise e


def get_blog_posts(last_sync_id=0):
    """Blog gönderilerini getir"""
    conn = connect_to_blog_db()
    cursor = conn.cursor()

    # Blog gönderilerini al (id, title, content şeklinde)
    query = """
    SELECT id, title, content FROM blog_posts
    WHERE id > %s AND is_published = TRUE
    ORDER BY id ASC
    """

    cursor.execute(query, (last_sync_id,))
    posts = cursor.fetchall()

    cursor.close()
    conn.close()

    return posts


def index_post_to_rag(post_id, title, content):
    """Blog gönderisini RAG sistemine indeksle"""
    try:
        response = requests.post(
            RAG_API_URL,
            json={
                "text": content,
                "document_id": f"blog_{post_id}",
                "title": title
            }
        )

        return response.json()
    except requests.exceptions.ConnectionError:
        print("API bağlantı hatası. RAG API servisi çalışıyor mu?")
        print("python cli.py serve")
        return {"status": "error", "message": "API bağlantı hatası"}
    except Exception as e:
        print(f"İndeksleme hatası: {e}")
        return {"status": "error", "message": str(e)}


def update_sync_status(post_id, sync_result):
    """Blog gönderisinin senkronizasyon durumunu güncelle"""
    try:
        conn = connect_to_blog_db()
        cursor = conn.cursor()

        # RAG senkronizasyon durumunu güncelle
        if sync_result.get("status") == "success":
            chunks_count = 0
            if "message" in sync_result:
                # Mesajdan parça sayısını çıkar
                import re
                match = re.search(r"(\d+) belge parçası", sync_result["message"])
                if match:
                    chunks_count = int(match.group(1))

            # Senkronizasyon durumunu kaydet
            query = """
            INSERT INTO rag_sync_status (post_id, is_synced, last_synced_at, document_id, chunks_count)
            VALUES (%s, TRUE, CURRENT_TIMESTAMP, %s, %s)
            ON CONFLICT (post_id) DO UPDATE
            SET is_synced = TRUE,
                last_synced_at = CURRENT_TIMESTAMP,
                document_id = EXCLUDED.document_id,
                chunks_count = EXCLUDED.chunks_count
            """

            cursor.execute(query, (post_id, f"blog_{post_id}", chunks_count))
            conn.commit()

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Senkronizasyon durumu güncellenirken hata: {e}")


def get_last_sync_id():
    """Son senkronize edilen blog post ID'sini al"""
    sync_file = "blog_sync.json"
    if os.path.exists(sync_file):
        with open(sync_file, 'r') as f:
            data = json.load(f)
            return data.get("last_sync_id", 0)
    return 0


def save_last_sync_id(post_id):
    """Son senkronize edilen blog post ID'sini kaydet"""
    sync_file = "blog_sync.json"
    with open(sync_file, 'w') as f:
        json.dump({"last_sync_id": post_id, "last_sync_time": time.time()}, f)


def sync_blog_to_rag(force_sync_all=False):
    """Tüm blog gönderilerini RAG ile senkronize et"""
    # Son senkronize edilen ID'yi al
    last_sync_id = 0 if force_sync_all else get_last_sync_id()

    print(f"Son senkronize ID: {last_sync_id}")

    try:
        posts = get_blog_posts(last_sync_id)

        if not posts:
            print("Senkronize edilecek yeni içerik bulunamadı.")
            return []

        print(f"{len(posts)} yeni blog gönderisi bulundu.")
        results = []

        for post_id, title, content in posts:
            print(f"İndeksleniyor: {title} (ID: {post_id})")
            result = index_post_to_rag(post_id, title, content)

            # Senkronizasyon durumunu güncelle
            try:
                update_sync_status(post_id, result)
            except Exception as e:
                print(f"Senkronizasyon durumu güncellenirken hata: {e}")

            results.append({
                "post_id": post_id,
                "title": title,
                "result": result
            })

            # En son post ID'sini kaydet
            save_last_sync_id(post_id)

            # API'yi yormamak için kısa bir bekleme
            time.sleep(0.5)

        return results
    except Exception as e:
        print(f"Senkronizasyon sırasında hata: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Blog içeriklerini RAG\'e aktarma')
    parser.add_argument('--force', action='store_true', help='Tüm içerikleri yeniden senkronize et')
    args = parser.parse_args()

    results = sync_blog_to_rag(force_sync_all=args.force)

    if results:
        print(f"{len(results)} blog gönderisi RAG sistemine indekslendi.")

        # Hata kontrolleri
        errors = [r for r in results if r["result"].get("status") == "error"]
        if errors:
            print(f"{len(errors)} gönderide hata oluştu:")
            for error in errors:
                print(f"  - {error['title']}: {error['result'].get('message')}")


if __name__ == "__main__":
    main()