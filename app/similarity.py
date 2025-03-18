# app/similarity.py
"""
Vektör benzerliği ve doküman filtreleme işlemleri için yardımcı fonksiyonlar.
"""
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.documents import Document


def normalize_similarity_score(score: float, score_type: str = "cosine") -> float:
    """
    Benzerlik skorunu normalize eder.

    Args:
        score (float): Ham benzerlik skoru
        score_type (str): Skor tipi: 'cosine', 'l2', 'dot'

    Returns:
        float: 0-1 arasında normalize edilmiş benzerlik skoru (1 = en benzer)
    """
    if score_type == "cosine":
        # Kosinüs benzerliği zaten [0, 1] aralığında, 1 = en benzer
        return score
    elif score_type == "l2":
        # L2 uzaklığı [0, inf) aralığında, 0 = en benzer
        # Bunu [0, 1] aralığına dönüştürelim, 1 = en benzer
        # Basit bir dönüşüm: 1/(1+x)
        return 1 / (1 + score)
    elif score_type == "dot":
        # Dot product'ı [-inf, inf] aralığından [0, 1] aralığına dönüştür
        # Sigmoid fonksiyonu: 1/(1+e^-x)
        return 1 / (1 + np.exp(-score))
    else:
        # Bilinmeyen metrik, ham değeri döndür
        return score


def correct_similarity_scores(docs_with_scores: List[Tuple[Document, float]],
                              score_type: str = "l2") -> List[Tuple[Document, float]]:
    """
    LangChain tarafından döndürülen benzerlik skorlarını düzeltir.
    PGVector varsayılan olarak L2 mesafesini kullanır, burada düşük değerler daha iyidir.

    Args:
        docs_with_scores: (belge, skor) tuple'larının listesi
        score_type: Benzerlik hesaplama türü ('cosine', 'l2', 'dot')

    Returns:
        (belge, normalize_edilmiş_skor) tuple'larının listesi
    """
    # Skorları normalize et
    normalized_docs_with_scores = []

    for doc, score in docs_with_scores:
        # L2 uzaklığı için ters çevir, kosinüs içinse aynı bırak
        normalized_score = normalize_similarity_score(score, score_type)
        normalized_docs_with_scores.append((doc, normalized_score))

    # Düzeltilmiş skorlara göre sırala (en yüksek ilk)
    return sorted(normalized_docs_with_scores, key=lambda x: x[1], reverse=True)


def filter_irrelevant_documents(docs_with_scores: List[Tuple[Document, float]],
                                category: str = None,
                                threshold: float = 0.5) -> List[Tuple[Document, float]]:
    """
    İlgisiz belgeleri filtreler.

    Args:
        docs_with_scores: (belge, skor) tuple'larının listesi
        category: Filtrelenecek kategori (film, book, person, vb.)
        threshold: Minimum benzerlik eşiği

    Returns:
        Filtrelenmiş (belge, skor) tuple'larının listesi
    """
    from app.categorizer import detect_document_category

    # 1. Benzerlik eşiğine göre filtrele
    filtered_by_score = [(doc, score) for doc, score in docs_with_scores if score >= threshold]

    # Eğer kategori belirtilmediyse, skorla filtrelenmiş belgeleri döndür
    if category is None or category == "general" or len(filtered_by_score) == 0:
        return filtered_by_score

    # 2. Kategoriye göre filtrele
    filtered_by_category = []

    for doc, score in filtered_by_score:
        doc_category = detect_document_category(doc.page_content)

        # Belge kategorisi, sorgu kategorisiyle uyuşuyorsa ekle
        if doc_category == category:
            filtered_by_category.append((doc, score))

    # Eğer kategori filtrelemesinden sonra belge kalmadıysa,
    # benzerlik skoruna göre filtrelenmiş belgeleri döndür
    if len(filtered_by_category) == 0:
        return filtered_by_score[:3]  # En çok benzeyen 3 belge

    return filtered_by_category


def analyze_similarity_results(query: str, docs_with_scores: List[Tuple[Document, float]],
                               original_scores: List[Tuple[Document, float]] = None):
    """
    Benzerlik sonuçlarını analiz eder ve sorunları tespit eder.

    Args:
        query: Kullanıcı sorgusu
        docs_with_scores: Düzeltilmiş (belge, skor) tuple'larının listesi
        original_scores: Orijinal (belge, skor) tuple'larının listesi
    """
    print("\n" + "=" * 80)
    print(f"📊 BENZERLİK ANALİZİ: '{query}'")
    print("=" * 80)

    # Kategori analizi
    from app.categorizer import detect_query_category
    query_category = detect_query_category(query)
    print(f"📑 Sorgu kategorisi: {query_category}")

    # Belge kategori analizi
    doc_categories = {}
    for doc, score in docs_with_scores:
        from app.categorizer import detect_document_category
        category = detect_document_category(doc.page_content)
        doc_categories[doc] = category

    # Sonuçları göster
    print("\n📋 Benzerlik sonuçları:")
    for i, (doc, score) in enumerate(docs_with_scores):
        title = doc.metadata.get('title', 'Başlıksız')
        doc_id = doc.metadata.get('source', f'belge_{i}')
        category = doc_categories.get(doc, 'bilinmiyor')

        # Kategori eşleşiyor mu?
        category_match = "✅" if category == query_category else "❌"

        print(f"{i + 1}. {title} (ID: {doc_id})")
        print(f"   Benzerlik: {score:.4f} ({score * 100:.1f}%)")
        print(f"   Kategori: {category} {category_match}")
        print(f"   İçerik: {doc.page_content[:100]}...")

        # Orijinal skorlar verildiyse karşılaştır
        if original_scores:
            for orig_doc, orig_score in original_scores:
                if orig_doc == doc:
                    print(f"   Orijinal skor: {orig_score:.4f}")
                    break

        print()

    # Öneriler
    print("\n🔍 ANALİZ SONUCU:")

    # Kategori uyumsuzluğu kontrolü
    category_mismatch = sum(1 for doc in docs_with_scores if doc_categories.get(doc[0]) != query_category)
    if category_mismatch > len(docs_with_scores) / 2:
        print("⚠️  Kategori uyumsuzluğu: Sonuçların çoğu sorgu kategorisine uymuyor.")
        print("    Öneri: Kategoriye göre filtrelemeyi güçlendirin.")

    # Düşük benzerlik skoru kontrolü
    low_scores = sum(1 for _, score in docs_with_scores if score < 0.5)
    if low_scores > len(docs_with_scores) / 2:
        print("⚠️  Düşük benzerlik skorları: Sonuçların çoğu düşük benzerlik gösteriyor.")
        print("    Öneri: Embedding modelini veya benzerlik hesaplama yöntemini değiştirin.")

    # Yüksek kategorili sonuçların benzerliği
    matching_category_docs = [(doc, score) for doc, score in docs_with_scores
                              if doc_categories.get(doc) == query_category]

    if matching_category_docs:
        avg_matching_score = sum(score for _, score in matching_category_docs) / len(matching_category_docs)
        print(f"📊 Sorgu kategorisine uyan belgelerin ortalama benzerliği: {avg_matching_score:.4f}")
    else:
        print("⚠️  Sorgu kategorisine uyan hiç belge bulunamadı!")

    print("=" * 80)