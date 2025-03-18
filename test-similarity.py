#!/usr/bin/env python3
"""
Benzerlik hesaplama test aracı.
PGVector ve diğer vektör veritabanlarının benzerlik hesaplamalarını test eder.
"""
import argparse
import numpy as np
from sentence_transformers import SentenceTransformer
from app.similarity import normalize_similarity_score, correct_similarity_scores, analyze_similarity_results
from app.config import EMBEDDING_MODEL


def cosine_similarity(a, b):
    """İki vektör arasındaki kosinüs benzerliğini hesaplar"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def euclidean_distance(a, b):
    """İki vektör arasındaki Öklid uzaklığını hesaplar"""
    return np.sqrt(np.sum((np.array(a) - np.array(b)) ** 2))


def dot_product(a, b):
    """İki vektör arasındaki iç çarpımı hesaplar"""
    return np.dot(a, b)


def test_similarity_metrics():
    """Farklı benzerlik metriklerini test eder"""
    print("🔍 Benzerlik Metrikleri Testi")
    print("=" * 60)

    # Test vektörleri
    # Not: a ve c benzer içeriği temsil ederken, b farklı bir içeriği temsil eder
    sentences = {
        "a": "Marie Curie was a pioneering physicist and chemist who conducted groundbreaking research on radioactivity.",
        "b": "Inception is a 2010 science fiction film directed by Christopher Nolan.",
        "c": "The Nobel Prize winning scientist Marie Curie discovered radium and polonium."
    }

    print("📝 Test cümleleri:")
    for key, sentence in sentences.items():
        print(f"  {key}: {sentence}")

    print("\n🧮 Embedding vektörleri oluşturuluyor...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    embeddings = {}
    for key, sentence in sentences.items():
        embeddings[key] = model.encode(sentence)
        print(f"  {key} vektör boyutu: {len(embeddings[key])}")

    print("\n📊 Ham benzerlik değerleri:")
    print(f"  a-c Kosinüs Benzerliği: {cosine_similarity(embeddings['a'], embeddings['c']):.6f}")
    print(f"  a-b Kosinüs Benzerliği: {cosine_similarity(embeddings['a'], embeddings['b']):.6f}")

    print(f"  a-c Öklid Uzaklığı: {euclidean_distance(embeddings['a'], embeddings['c']):.6f}")
    print(f"  a-b Öklid Uzaklığı: {euclidean_distance(embeddings['a'], embeddings['b']):.6f}")

    print(f"  a-c İç Çarpım: {dot_product(embeddings['a'], embeddings['c']):.6f}")
    print(f"  a-b İç Çarpım: {dot_product(embeddings['a'], embeddings['b']):.6f}")

    print("\n📊 Normalize edilmiş benzerlik değerleri:")

    # Kosinüs benzerliği (yüksek = daha benzer)
    cos_ac = cosine_similarity(embeddings['a'], embeddings['c'])
    cos_ab = cosine_similarity(embeddings['a'], embeddings['b'])
    print(f"  a-c Kosinüs (normalize): {normalize_similarity_score(cos_ac, 'cosine'):.6f}")
    print(f"  a-b Kosinüs (normalize): {normalize_similarity_score(cos_ab, 'cosine'):.6f}")

    # Öklid uzaklığı (düşük = daha benzer)
    l2_ac = euclidean_distance(embeddings['a'], embeddings['c'])
    l2_ab = euclidean_distance(embeddings['a'], embeddings['b'])
    print(f"  a-c L2 (normalize): {normalize_similarity_score(l2_ac, 'l2'):.6f}")
    print(f"  a-b L2 (normalize): {normalize_similarity_score(l2_ab, 'l2'):.6f}")

    # İç çarpım
    dot_ac = dot_product(embeddings['a'], embeddings['c'])
    dot_ab = dot_product(embeddings['a'], embeddings['b'])
    print(f"  a-c Dot (normalize): {normalize_similarity_score(dot_ac, 'dot'):.6f}")
    print(f"  a-b Dot (normalize): {normalize_similarity_score(dot_ab, 'dot'):.6f}")

    print("\n🔍 Analiz sonucu:")
    if normalize_similarity_score(l2_ac, 'l2') > normalize_similarity_score(l2_ab, 'l2'):
        print("✅ L2 metriği doğru normalize edildi: Benzer içerik daha yüksek skor aldı")
    else:
        print("❌ L2 metriği yanlış normalize edildi: Farklı içerik daha yüksek skor aldı")

    print("\n💡 Sonuç:")
    print("- Kosinüs benzerliği: [0,1] aralığında, 1 = en benzer")
    print("- L2 uzaklığı: [0,∞) aralığında, 0 = en benzer")
    print("- PGVector varsayılan olarak L2 uzaklığını kullanır")
    print("- Uzaklık değerini benzerlik değerine dönüştürmek için: 1/(1+uzaklık)")
    print("- Tüm skorlar [0,1] aralığına normalize edilmeli, 1 = en benzer")


def test_with_pgvector():
    """PGVector ile benzerlik hesaplamalarını test eder"""
    from app.db import get_vectorstore
    from app.embedding import get_embeddings
    from langchain_core.documents import Document

    print("\n🔍 PGVector Benzerlik Testi")
    print("=" * 60)

    # Test sorguları
    queries = [
        "Marie Curie kimdir ve ne yapmıştır?",
        "Inception filminin konusu nedir?",
        "Yüzüklerin Efendisi kitabı hakkında bilgi ver"
    ]

    try:
        embeddings = get_embeddings()
        db = get_vectorstore(embeddings)

        for query in queries:
            print(f"\n📝 Sorgu: '{query}'")

            # Orijinal sonuçları al
            original_results = db.similarity_search_with_score(query, k=3)

            print("  Ham sonuçlar:")
            for i, (doc, score) in enumerate(original_results):
                source = doc.metadata.get('source', 'bilinmiyor')
                print(f"    {i + 1}. {source[:30]}: {score:.6f}")

            # Düzeltilmiş sonuçlar
            corrected_results = correct_similarity_scores(original_results, score_type="l2")

            print("  Düzeltilmiş sonuçlar:")
            for i, (doc, score) in enumerate(corrected_results):
                source = doc.metadata.get('source', 'bilinmiyor')
                print(f"    {i + 1}. {source[:30]}: {score:.6f}")

            # Belge kategorileriyle analiz et
            print("\n  Belge kategorileri:")
            from app.categorizer import detect_query_category, detect_document_category
            query_category = detect_query_category(query)
            print(f"    Sorgu kategorisi: {query_category}")

            for doc, _ in corrected_results:
                doc_category = detect_document_category(doc.page_content)
                match = "✅" if doc_category == query_category else "❌"
                print(f"    - {doc.metadata.get('source', 'bilinmiyor')[:30]}: {doc_category} {match}")

    except Exception as e:
        print(f"❌ PGVector testi sırasında hata: {e}")


def main():
    parser = argparse.ArgumentParser(description="Benzerlik Hesaplama Test Aracı")
    parser.add_argument("--pgvector", action="store_true", help="PGVector ile test et")
    parser.add_argument("--query", type=str, default=None, help="Test sorgusu")
    args = parser.parse_args()

    # Temel benzerlik metriklerini test et
    test_similarity_metrics()

    # PGVector testi (isteğe bağlı)
    if args.pgvector:
        test_with_pgvector()

    # Test sorgusu varsa analiz et
    if args.query:
        print(f"\n🔍 Sorgu analizi: '{args.query}'")
        from app.categorizer import detect_query_category
        query_category = detect_query_category(args.query)
        print(f"  Sorgu kategorisi: {query_category}")


if __name__ == "__main__":
    main()