#!/usr/bin/env python3
"""
Vektör benzerlik hesaplama ve test etme aracı.
Bu script, LangChain ve PostgreSQL vektör benzerlik hesaplamalarını test eder.
"""
import os
import sys
import argparse
import numpy as np
import time
from tqdm import tqdm
import psycopg2
from sentence_transformers import SentenceTransformer
from app.config import DB_CONNECTION, EMBEDDING_MODEL


def cosine_similarity(a, b):
    """İki vektör arasındaki kosinüs benzerliğini hesaplar"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def load_embedding_model(model_name=None):
    """Embedding modelini yükler"""
    if model_name is None:
        model_name = EMBEDDING_MODEL

    print(f"🔄 Embedding modeli yükleniyor: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        print(f"✅ Model yüklendi: {model_name}")
        return model
    except Exception as e:
        print(f"❌ Model yükleme hatası: {e}")
        return None


def compute_text_similarity(model, text1, text2):
    """İki metin arasındaki benzerliği hesaplar"""
    embedding1 = model.encode(text1)
    embedding2 = model.encode(text2)
    similarity = cosine_similarity(embedding1, embedding2)
    return similarity, embedding1, embedding2


def get_documents_from_db(limit=10):
    """Veritabanından belgeleri getirir"""
    try:
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # document_chunks tablosundan belgeleri al
        cursor.execute("""
        SELECT document_id, title, content 
        FROM document_chunks 
        ORDER BY id 
        LIMIT %s
        """, (limit,))

        documents = cursor.fetchall()
        cursor.close()
        conn.close()

        return documents
    except Exception as e:
        print(f"❌ Veritabanı hatası: {e}")
        return []


def check_langchain_embeddings():
    """LangChain tarafından oluşturulan embedding'leri kontrol eder"""
    try:
        print("🔍 LangChain embeddings tablosunu kontrol ediliyor...")
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # Tablo var mı kontrol et
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'langchain_pg_embedding'
        )
        """)

        table_exists = cursor.fetchone()[0]
        if not table_exists:
            print("❌ langchain_pg_embedding tablosu bulunamadı!")
            cursor.close()
            conn.close()
            return False

        # Embedding sayısını kontrol et
        cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding")
        count = cursor.fetchone()[0]
        print(f"📊 langchain_pg_embedding tablosunda {count} kayıt var")

        if count == 0:
            print("⚠️ Hiç embedding kaydı yok!")
            cursor.close()
            conn.close()
            return False

        # Örnek bir embedding vektörünü al
        cursor.execute("SELECT embedding FROM langchain_pg_embedding LIMIT 1")
        embedding = cursor.fetchone()[0]

        if embedding is None:
            print("❌ Embedding değeri NULL!")
        else:
            print(f"✅ Embedding vektörü mevcut, boyutu: {len(embedding)}")
            print(f"📊 İlk 5 eleman: {embedding[:5]}")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ LangChain embedding kontrolü hatası: {e}")
        return False


def test_direct_similarity(query, model):
    """Sorgu ve veritabanındaki belgeler arasında doğrudan benzerlik hesaplar"""
    print(f"\n🔍 Doğrudan benzerlik testi yapılıyor: '{query}'")

    # Belgeleri getir
    documents = get_documents_from_db(limit=10)
    if not documents:
        print("❌ Test için belge bulunamadı!")
        return False

    print(f"📄 {len(documents)} belge getirildi")

    # Sorgu vektörünü hesapla
    query_embedding = model.encode(query)

    # Her belge için benzerliği hesapla
    similarities = []

    for doc_id, title, content in documents:
        # Belge içeriği vektörünü hesapla
        doc_embedding = model.encode(content[:1000])  # Uzun içerikleri kısalt

        # Kosinüs benzerliğini hesapla
        similarity = cosine_similarity(query_embedding, doc_embedding)
        similarities.append((doc_id, title, similarity))

    # Benzerlik değerlerine göre sırala
    similarities.sort(key=lambda x: x[2], reverse=True)

    # Sonuçları göster
    print("\n📊 Benzerlik sonuçları:")
    print("=" * 50)
    for doc_id, title, similarity in similarities:
        print(f"📄 {doc_id} - {title}: {similarity:.4f} ({similarity * 100:.2f}%)")

    return True


def test_langchain_similarity(query):
    """LangChain ile benzerlik araması yapar"""
    print(f"\n🔍 LangChain benzerlik testi yapılıyor: '{query}'")

    try:
        from app.embedding import get_embeddings
        from app.db import get_vectorstore

        # Embeddings ve vector store oluştur
        embeddings = get_embeddings()
        db = get_vectorstore(embeddings)

        # Benzerlik araması yap
        docs = db.similarity_search(query, k=5)

        # Sonuçları göster
        print(f"\n📊 LangChain benzerlik sonuçları:")
        print("=" * 50)

        if docs:
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("source", "bilinmiyor")
                doc_id = doc.metadata.get("document_id", source)
                print(f"{i}. {doc_id} - {doc.page_content[:100]}...")
            return True
        else:
            print("❌ LangChain benzerlik aramasında belge bulunamadı!")
            return False

    except Exception as e:
        print(f"❌ LangChain benzerlik testi hatası: {e}")
        return False


def test_vector_database_schema():
    """Vektör veritabanı şemasını kontrol eder"""
    print("\n🔍 Vektör veritabanı şeması kontrol ediliyor...")

    try:
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # pgvector uzantısının var olup olmadığını kontrol et
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        vector_extension_exists = cursor.fetchone()[0]

        if vector_extension_exists:
            print("✅ pgvector uzantısı yüklü")
        else:
            print("❌ pgvector uzantısı yüklü değil!")
            return False

        # document_chunks tablosunun yapısını kontrol et
        cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'document_chunks'
        """)

        columns = cursor.fetchall()
        print("\n📊 document_chunks tablosu sütunları:")

        embedding_column_exists = False
        for column_name, data_type in columns:
            print(f"- {column_name}: {data_type}")
            if column_name == 'embedding' and data_type == 'USER-DEFINED':
                embedding_column_exists = True

        if embedding_column_exists:
            print("✅ document_chunks tablosunda 'embedding' sütunu (vector türünde) var")
        else:
            print("❌ document_chunks tablosunda 'embedding' sütunu bulunamadı veya vector türünde değil!")

        # langchain_pg_embedding tablosunun yapısını kontrol et
        try:
            cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'langchain_pg_embedding'
            """)

            columns = cursor.fetchall()
            print("\n📊 langchain_pg_embedding tablosu sütunları:")

            langchain_embedding_column_exists = False
            for column_name, data_type in columns:
                print(f"- {column_name}: {data_type}")
                if column_name == 'embedding' and data_type == 'USER-DEFINED':
                    langchain_embedding_column_exists = True

            if langchain_embedding_column_exists:
                print("✅ langchain_pg_embedding tablosunda 'embedding' sütunu (vector türünde) var")
            else:
                print("❌ langchain_pg_embedding tablosunda 'embedding' sütunu bulunamadı veya vector türünde değil!")

        except Exception as e:
            print(f"❌ langchain_pg_embedding tablosu kontrolü hatası: {e}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Veritabanı şema kontrolü hatası: {e}")
        return False


def run_comprehensive_test(query):
    """Kapsamlı vektör veritabanı ve benzerlik testleri yapar"""
    print("\n" + "=" * 60)
    print("📊 KAPSAMLI VEKTÖR BENZERLİK TESTİ")
    print("=" * 60)

    # 1. Embedding modeli yükle
    model = load_embedding_model()
    if model is None:
        return False

    # 2. Veritabanı şemasını kontrol et
    test_vector_database_schema()

    # 3. LangChain embeddings tablosunu kontrol et
    check_langchain_embeddings()

    # 4. Doğrudan benzerlik testi
    test_direct_similarity(query, model)

    # 5. LangChain benzerlik testi
    test_langchain_similarity(query)

    print("\n" + "=" * 60)
    print("📊 TEST TAMAMLANDI")
    print("=" * 60)

    return True


def main():
    parser = argparse.ArgumentParser(description="Vektör Benzerlik Test Aracı")
    parser.add_argument("--query", "-q", type=str, default="Inception filmi hakkında bilgi ver",
                        help="Test sorgusu")
    parser.add_argument("--check-schema", action="store_true",
                        help="Veritabanı şemasını kontrol et")
    parser.add_argument("--check-embeddings", action="store_true",
                        help="LangChain embeddings tablosunu kontrol et")
    parser.add_argument("--direct-test", action="store_true",
                        help="Doğrudan benzerlik testi yap")
    parser.add_argument("--langchain-test", action="store_true",
                        help="LangChain benzerlik testi yap")
    parser.add_argument("--all", action="store_true",
                        help="Tüm testleri çalıştır")

    args = parser.parse_args()

    if args.all:
        run_comprehensive_test(args.query)
    else:
        # Bireysel testler
        if args.check_schema:
            test_vector_database_schema()

        if args.check_embeddings:
            check_langchain_embeddings()

        if args.direct_test:
            model = load_embedding_model()
            if model:
                test_direct_similarity(args.query, model)

        if args.langchain_test:
            test_langchain_similarity(args.query)

        # Hiçbir test seçilmediyse kapsamlı test yap
        if not any([args.check_schema, args.check_embeddings, args.direct_test, args.langchain_test]):
            run_comprehensive_test(args.query)


if __name__ == "__main__":
    main()