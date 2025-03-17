#!/usr/bin/env python3
"""
Blog Yazısı Ekleme Scripti - RAG CLI entegrasyonu ile blog veritabanına içerik ekler
"""
import os
import sys
import time
import re
import psycopg2
import argparse
from datetime import datetime
import subprocess

# Veritabanı bağlantı bilgileri - Docker bağlantısı (değiştirebilirsiniz)
DB_CONNECTION = "postgresql://raguser:ragpassword@localhost:5432/blog_db"


def slugify(text):
    """
    Metni URL-dostu (slug) hale getirir.
    Türkçe karakterleri destekler.
    """
    # Türkçe karakterleri değiştir
    text = text.lower()
    text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u')
    text = text.replace('ş', 's').replace('ö', 'o').replace('ç', 'c')

    # Alfanumerik olmayan karakterleri tire ile değiştir
    text = re.sub(r'[^a-z0-9]+', '-', text)

    # Baştaki ve sondaki tireleri kaldır
    text = text.strip('-')

    return text


def connect_to_db():
    """
    Veritabanına bağlantı kurar.
    """
    try:
        return psycopg2.connect(DB_CONNECTION)
    except Exception as e:
        print(f"Veritabanı bağlantı hatası: {e}")

        # Docker kontrolü yapılabilir
        try:
            print("Docker PostgreSQL konteynerini kontrol ediyorum...")
            subprocess.run(["docker", "ps", "-a"], check=True)
            print("\nEğer postgres-ragcli konteyneri çalışmıyorsa:")
            print("docker start postgres-ragcli")
        except:
            pass

        sys.exit(1)


def check_slug_exists(cursor, slug):
    """
    Belirtilen slug'ın veritabanında var olup olmadığını kontrol eder.
    """
    cursor.execute("SELECT id FROM blog_posts WHERE slug = %s", (slug,))
    return cursor.fetchone() is not None


def add_blog_post(title, content, excerpt=None, publish=False):
    """
    Veritabanına yeni bir blog yazısı ekler.
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    # Slug oluştur
    slug = slugify(title)

    # Slug'ın benzersiz olup olmadığını kontrol et
    if check_slug_exists(cursor, slug):
        # Slug zaten var, unique yapmak için zaman damgası ekle
        timestamp = int(time.time())
        slug = f"{slug}-{timestamp}"

    try:
        # Blog yazısını ekle
        cursor.execute("""
        INSERT INTO blog_posts (title, slug, content, excerpt, is_published)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """, (title, slug, content, excerpt, publish))

        post_id = cursor.fetchone()[0]
        conn.commit()

        print(f"\n✅ Blog yazısı başarıyla eklendi (ID: {post_id})")
        print(f"Başlık: {title}")
        print(f"Slug: {slug}")
        if publish:
            print("Durum: Yayınlandı")
        else:
            print("Durum: Taslak")

        return post_id
    except Exception as e:
        conn.rollback()
        print(f"Blog yazısı eklenirken hata: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def sync_to_rag(post_id):
    """
    Eklenen blog yazısını RAG sistemine senkronize eder.
    """
    try:
        # blog_to_rag.py script'ini çağır
        result = subprocess.run(
            ["python", "blog_to_rag.py"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("\n✅ Blog yazısı RAG sistemine başarıyla senkronize edildi")
        else:
            print(f"\n❌ RAG senkronizasyonu sırasında hata oluştu: {result.stderr}")

    except Exception as e:
        print(f"\n❌ RAG senkronizasyonu sırasında hata oluştu: {e}")


def list_blog_posts(limit=10):
    """
    Mevcut blog yazılarını listeler.
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT id, title, slug, excerpt, is_published, created_at
        FROM blog_posts
        ORDER BY created_at DESC
        LIMIT %s
        """, (limit,))

        posts = cursor.fetchall()

        if not posts:
            print("Henüz blog yazısı bulunmuyor.")
            return

        print("\n📋 Blog Yazıları")
        print("=" * 80)
        for post in posts:
            post_id, title, slug, excerpt, is_published, created_at = post
            status = "✅ Yayında" if is_published else "📝 Taslak"
            date_str = created_at.strftime("%d-%m-%Y %H:%M")

            print(f"{post_id}. {title} [{status}] - {date_str}")
            if excerpt:
                print(f"   {excerpt[:100]}...")
            print("-" * 80)

    except Exception as e:
        print(f"Blog yazıları listelenirken hata: {e}")
    finally:
        cursor.close()
        conn.close()


def edit_post_content():
    """
    Editör açarak içerik düzenlemeyi sağlar.
    """
    # Geçici dosya oluştur
    temp_file = f"/tmp/blog_content_{int(time.time())}.md"

    # Kullanıcı bilgilendirme metni
    with open(temp_file, "w") as f:
        f.write("# Blog İçeriği\n\n")
        f.write("Blog içeriğinizi Markdown formatında yazabilirsiniz.\n")
        f.write("Bu satırları silin ve içeriğinizi buraya yazın.\n\n")
        f.write("## Örnek Başlık\n\n")
        f.write("Örnek paragraf içeriği...\n\n")
        f.write("- Madde 1\n")
        f.write("- Madde 2\n\n")
        f.write("```python\n# Kod örneği\nprint('Merhaba Dünya')\n```\n")

    # Editör komutunu belirle
    editor = os.environ.get("EDITOR", "nano")

    # Editörü aç
    try:
        subprocess.run([editor, temp_file])
    except Exception as e:
        print(f"Editör açılırken hata: {e}")
        return None

    # Dosyadan içeriği oku
    try:
        with open(temp_file, "r") as f:
            content = f.read()

        # Eğer içerik, örnek metni içeriyorsa ve başka bir şey yazılmadıysa
        if "Blog içeriğinizi Markdown formatında yazabilirsiniz." in content and len(content.split("\n")) < 10:
            print("İçerik değiştirilmemiş gibi görünüyor. İşlem iptal edildi.")
            return None

        # Dosyayı temizle
        os.unlink(temp_file)

        return content
    except Exception as e:
        print(f"İçerik okunurken hata: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Blog Veritabanı İçerik Yönetimi")
    subparsers = parser.add_subparsers(dest="command", help="Komutlar")

    # Ekleme komutu
    add_parser = subparsers.add_parser("add", help="Yeni blog yazısı ekle")
    add_parser.add_argument("--title", "-t", help="Blog başlığı")
    add_parser.add_argument("--content", "-c", help="Blog içeriği (dosya yolu veya metin)")
    add_parser.add_argument("--excerpt", "-e", help="Blog özeti")
    add_parser.add_argument("--publish", "-p", action="store_true", help="Yayınla (varsayılan: taslak)")
    add_parser.add_argument("--sync", "-s", action="store_true", help="RAG sistemine senkronize et")

    # Listeleme komutu
    list_parser = subparsers.add_parser("list", help="Blog yazılarını listele")
    list_parser.add_argument("--limit", "-l", type=int, default=10, help="Listelenecek maksimum yazı sayısı")

    args = parser.parse_args()

    # Komut belirlenmemişse interaktif mod
    if args.command is None or args.command == "add" and args.title is None:
        print("📝 Blog Yazısı Ekleme - İnteraktif Mod")
        print("=" * 50)

        title = input("Blog başlığı: ")

        print("\nBlog içeriğini girmek için bir editör açılacak...")
        input("Devam etmek için ENTER tuşuna basın...")

        content = edit_post_content()
        if not content:
            print("İçerik boş. İşlem iptal edildi.")
            return

        excerpt = input("\nBlog özeti (opsiyonel): ")
        if not excerpt:
            excerpt = content.split("\n\n")[0][:100] + "..."

        publish = input("\nYayınlamak istiyor musunuz? (e/H): ").lower() == "e"
        sync_rag = input("RAG sistemine senkronize edilsin mi? (e/H): ").lower() == "e"

        post_id = add_blog_post(title, content, excerpt, publish)

        if post_id and sync_rag:
            sync_to_rag(post_id)

    # Komutlara göre işlem yap
    elif args.command == "add":
        content = args.content

        # İçerik bir dosya yoluysa, dosyadan oku
        if content and os.path.isfile(content):
            with open(content, "r") as f:
                content = f.read()

        # İçerik belirtilmemişse, editör aç
        if not content:
            content = edit_post_content()
            if not content:
                print("İçerik boş. İşlem iptal edildi.")
                return

        post_id = add_blog_post(args.title, content, args.excerpt, args.publish)

        if post_id and args.sync:
            sync_to_rag(post_id)

    elif args.command == "list":
        list_blog_posts(args.limit)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()