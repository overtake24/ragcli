# app/similarity.py
"""
Vektör benzerliği ve doküman filtreleme işlemleri için yardımcı fonksiyonlar.
Bu modül similarity_fix klasöründeki hibrit yaklaşımı uygular.
"""
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union
from langchain_core.documents import Document


def normalize_similarity_score(score: float, score_type: str = "l2") -> float:
    """
    Benzerlik skorunu normalize eder (0-1 aralığına dönüştürür, 1 = en benzer).

    Args:
        score (float): Ham benzerlik skoru/uzaklık değeri
        score_type (str): Skor tipi: 'cosine', 'l2', 'dot'

    Returns:
        float: 0-1 arasında normalize edilmiş benzerlik skoru
    """
    if score_type == "cosine":
        # Kosinüs benzerliği zaten [0, 1] aralığında, 1 = en benzer
        return max(0.0, min(score, 1.0))  # Sınırlama ekledik
    elif score_type == "l2":
        # L2 uzaklığı [0, inf) aralığında, 0 = en benzer
        # Bunu [0, 1] aralığına dönüştürelim, 1 = en benzer
        return 1.0 / (1.0 + score)
    elif score_type == "dot" or score_type == "inner":
        # İç çarpım için adaptif normalizasyon
        if score > 0:
            return min(score / (1.0 + score), 1.0)  # Pozitif değerler için
        else:
            return 0.0  # Negatif değerler için 0
    else:
        # Bilinmeyen metrik, ham değerin tersi (uzaklıksa)
        if score > 1.0:  # Muhtemelen uzaklık
            return 1.0 / score
        else:  # Muhtemelen zaten benzerlik
            return score


def correct_similarity_scores(docs_with_scores: List[Tuple[Document, float]],
                              score_type: str = "l2") -> List[Tuple[Document, float]]:
    """
    LangChain tarafından döndürülen benzerlik skorlarını normalize edilmiş
    benzerlik skorlarına dönüştürür.

    Args:
        docs_with_scores: (belge, skor) tuple'larının listesi
        score_type: Benzerlik hesaplama türü ('cosine', 'l2', 'dot')

    Returns:
        (belge, normalize_edilmiş_skor) tuple'larının listesi (yüksek->düşük sıralı)
    """
    if not docs_with_scores:
        return []

    # Skorları normalize et
    normalized = []
    for doc, score in docs_with_scores:
        normalized_score = normalize_similarity_score(score, score_type)
        normalized.append((doc, normalized_score))

    # Normalize edilmiş skorlara göre sırala (yüksek->düşük)
    return sorted(normalized, key=lambda x: x[1], reverse=True)


def filter_by_threshold(docs_with_scores: List[Tuple[Document, float]],
                        threshold: float = 0.3,
                        min_docs: int = 3) -> List[Tuple[Document, float]]:
    """
    Belgeleri minimum benzerlik eşiğine göre filtreler.

    Args:
        docs_with_scores: (belge, skor) tuple'larının listesi
        threshold: Minimum benzerlik eşiği (0-1 arası)
        min_docs: Minimum döndürülecek belge sayısı

    Returns:
        Eşik üzerindeki (belge, skor) tuple'ları
    """
    if not docs_with_scores:
        return []

    # Eşik üstündeki belgeleri filtrele
    filtered = [(doc, score) for doc, score in docs_with_scores if score >= threshold]

    # Eğer yeterli belge yoksa, eşiği adapte et
    if len(filtered) < min_docs and docs_with_scores:
        # Belgeleri skorlarına göre sırala
        sorted_docs = sorted(docs_with_scores, key=lambda x: x[1], reverse=True)

        # Minimum sayıda belge döndür
        return sorted_docs[:min_docs]

    return filtered


def filter_by_category(docs_with_scores: List[Tuple[Document, float]],
                       query_category: str,
                       min_category_docs: int = 2) -> List[Tuple[Document, float]]:
    """
    Belgeleri kategoriye göre filtreler.

    Args:
        docs_with_scores: (belge, skor) tuple'larının listesi
        query_category: Sorgu kategorisi (film, book, person, vb.)
        min_category_docs: Minimum döndürülecek kategoriye uygun belge sayısı

    Returns:
        Filtrelenmiş (belge, skor) tuple'ları
    """
    if not docs_with_scores or query_category == "general":
        return docs_with_scores

    from app.categorizer import detect_document_category

    # Kategori eşleşmelerine göre ayır
    matching_category = []
    other_categories = []

    print(f"🔍 Belge kategori analizi (aranan kategori: {query_category}):")
    for doc, score in docs_with_scores:
        try:
            doc_category = detect_document_category(doc.page_content)
            doc_source = doc.metadata.get('source', 'bilinmiyor')

            print(f"  - {doc_source}: {doc_category} (skor: {score:.4f})")

            if doc_category == query_category:
                matching_category.append((doc, score))
            else:
                other_categories.append((doc, score))
        except Exception as e:
            print(f"⚠️ Kategori tespitinde hata: {e}")
            other_categories.append((doc, score))

    # Kategori eşleşmelerini kontrol et
    if len(matching_category) >= min_category_docs:
        print(f"✅ Kategori filtrelemesi sonrası {len(matching_category)} belge kaldı")
        return matching_category

    # Yetersiz kategori eşleşmesi varsa, diğer belgelerden de ekle
    if matching_category and other_categories:
        print(
            f"⚠️ '{query_category}' kategorisinde sadece {len(matching_category)} belge var, diğerlerinden de eklenecek")
        # Kategoriye uyan belgeleri önce koy, sonra diğerlerinden ekle
        combined = matching_category + other_categories
        # Benzerlik skoruna göre sırala
        return sorted(combined, key=lambda x: x[1], reverse=True)

    # Hiç eşleşme yoksa tüm belgeleri döndür
    print(f"⚠️ '{query_category}' kategorisinde hiç belge bulunamadı, tüm belgeler kullanılacak")
    return docs_with_scores


def filter_irrelevant_documents(docs_with_scores: List[Tuple[Document, float]],
                                category: str = None,
                                threshold: float = 0.3,
                                max_docs: int = 5) -> List[Tuple[Document, float]]:
    """
    Hibrit filtreleme uygular: Önce benzerlik eşiği, sonra kategori filtresi.

    Args:
        docs_with_scores: (belge, skor) tuple'larının listesi
        category: Aranan kategori
        threshold: Minimum benzerlik eşiği
        max_docs: Maksimum döndürülecek belge sayısı

    Returns:
        Filtrelenmiş (belge, skor) tuple'ları
    """
    if not docs_with_scores:
        return []

    # 1. Benzerlik eşiğine göre filtrele
    threshold_filtered = filter_by_threshold(
        docs_with_scores,
        threshold=threshold,
        min_docs=3
    )

    if not threshold_filtered:
        print("⚠️ Benzerlik eşiğine göre hiç belge kalmadı")
        # En yüksek benzerliği olan belgeleri döndür
        return sorted(docs_with_scores, key=lambda x: x[1], reverse=True)[:max_docs]

    # 2. Kategori filtrelemesi uygula
    if category is not None and category != "general":
        category_filtered = filter_by_category(
            threshold_filtered,
            query_category=category,
            min_category_docs=2
        )

        # Kategori filtresi sonrası sırala
        category_filtered.sort(key=lambda x: x[1], reverse=True)
        return category_filtered[:max_docs]

    # Sadece benzerlik eşiği ile filtrelenmiş sonuçları döndür
    return threshold_filtered[:max_docs]


def analyze_similarity_results(query: str, docs_with_scores: List[Tuple[Document, float]],
                               original_docs_with_scores: List[Tuple[Document, float]] = None):
    """
    Benzerlik sonuçlarını analiz eder ve sorunları tespit eder.

    Args:
        query: Kullanıcı sorgusu
        docs_with_scores: Düzeltilmiş (belge, skor) tuple'larının listesi
        original_docs_with_scores: Orijinal (belge, skor) tuple'larının listesi
    """
    from app.categorizer import detect_query_category, detect_document_category

    print("\n" + "=" * 80)
    print(f"📊 BENZERLİK ANALİZİ: '{query}'")
    print("=" * 80)

    # Sorgu kategorisini tespit et
    query_category = detect_query_category(query)
    print(f"📑 Sorgu kategorisi: {query_category}")

    if not docs_with_scores:
        print("⚠️ Hiç belge bulunamadı!")
        return

    # Belge kategori analizi
    doc_categories = {}
    for doc, score in docs_with_scores:
        doc_categories[doc] = detect_document_category(doc.page_content)

    # Kategori bazlı doğruluk
    matching_categories = sum(1 for doc, _ in docs_with_scores if doc_categories[doc] == query_category)
    if docs_with_scores:
        accuracy = matching_categories / len(docs_with_scores)
        print(f"📊 Kategori doğruluğu: {accuracy:.2%} ({matching_categories}/{len(docs_with_scores)})")

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

        # İçerik önizlemesi (ilk 100 karakter)
        content_preview = doc.page_content[:100].replace('\n', ' ')
        print(f"   İçerik: {content_preview}...")

        # Orijinal skorlar varsa onları da göster
        if original_docs_with_scores:
            for orig_doc, orig_score in original_docs_with_scores:
                if orig_doc == doc:
                    print(f"   Orijinal skor: {orig_score:.4f}")
                    break

        print()

    print("=" * 80)