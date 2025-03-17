#!/usr/bin/env python
"""
Test belgelerini veritabanına yükleyen araç.
"""
import argparse
import os
from app.embedding import get_embeddings
from app.db import get_vectorstore
from langchain_core.documents import Document


def load_test_documents(folder_path="test_data/scandinavia", force=False):
    """Test belgelerini veritabanına yükler."""
    print(f"🔍 Test belgeleri '{folder_path}' klasöründen yükleniyor...")

    if not os.path.exists(folder_path):
        print(f"❌ '{folder_path}' klasörü bulunamadı.")
        return

    # Belgeleri yükle
    documents = []
    file_count = 0

    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                file_count += 1

                # Belge başlığını içerikten çıkar (varsa)
                title = filename
                if content.startswith('#'):
                    title_line = content.split('\n')[0]
                    title = title_line.lstrip('#').strip()

                doc = Document(
                    page_content=content,
                    metadata={
                        "source": filename,
                        "title": title,
                        "document_id": f"test_{file_count}"
                    }
                )
                documents.append(doc)
                print(f"📄 Yüklenen: {filename} ({len(content)} karakter)")

    if not documents:
        print("❌ Yüklenecek belge bulunamadı.")
        return

    # Vektör deposunu hazırla
    embeddings = get_embeddings()
    db = get_vectorstore(embeddings)

    # Mevcut verileri temizle (eğer force seçeneği belirtildiyse)
    if force:
        try:
            # Veritabanı bağlantısı
            import psycopg2
            from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            cursor = conn.cursor()

            # Tabloları temizle
            cursor.execute("DELETE FROM document_chunks;")
            cursor.execute("DELETE FROM langchain_pg_embedding;")
            conn.commit()

            cursor.close()
            conn.close()
            print("✅ Veritabanı tabloları temizlendi.")
        except Exception as e:
            print(f"⚠️ Veritabanı temizleme hatası: {e}")

    # Belgeleri vektör deposuna ekle
    print(f"🔍 {len(documents)} belge veritabanına ekleniyor...")
    db.add_documents(documents)
    print(f"✅ {len(documents)} belge başarıyla eklendi.")

    # Test et
    try:
        import psycopg2
        from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()

        # Kontrol et
        cursor.execute("SELECT COUNT(*) FROM document_chunks;")
        chunk_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding;")
        embedding_count = cursor.fetchone()[0]

        print(f"📊 document_chunks tablosunda {chunk_count} satır var.")
        print(f"📊 langchain_pg_embedding tablosunda {embedding_count} satır var.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Veritabanı kontrol hatası: {e}")


def main():
    parser = argparse.ArgumentParser(description="RAG Test Belge Yükleme Aracı")
    parser.add_argument("--folder", type=str, default="test_data/scandinavia", help="Belgelerin bulunduğu klasör")
    parser.add_argument("--force", action="store_true", help="Mevcut verileri temizle")
    args = parser.parse_args()

    load_test_documents(args.folder, args.force)

    print("✅ Test belgeleri yükleme tamamlandı.")


if __name__ == "__main__":
    main()