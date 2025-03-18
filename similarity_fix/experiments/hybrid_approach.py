#!/usr/bin/env python3
# similarity_fix/experiments/hybrid_approach.py

import sys
import os
import json
import time
from datetime import datetime

# Üst dizini Python yoluna ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from pgvector_utils import query_similar_documents


def hybrid_approach(query_vector, query_category="default", top_k=10):
    """
    Hibrit yaklaşım:
    - İlk olarak sorguya benzer belgeler getirilir.
    - Belge kategorisi 'query_category' ile eşleşenler filtrelenir.
    - L2 uzaklık değerleri benzerlik skorlarına dönüştürülür.
    - Sonuçlar benzerlik skorlarına göre sıralanır.
    """
    # Ham sorgu sonuçlarını al (daha fazla sonuç iste ki filtrelemeye materyal olsun)
    results = query_similar_documents(query_vector, top_k=top_k * 2)

    if not results:
        print("⚠️ Sorgu için sonuç bulunamadı")
        return []

    # Kategori filtreleme
    filtered = [r for r in results if r.get("category") == query_category]

    # Eğer filtreleme sonucunda yeterli belge kalmadıysa, tüm sonuçları kullan
    if not filtered or len(filtered) < 3:
        filtered = results
        print(f"⚠️ '{query_category}' kategorisinde yeterli belge bulunamadı, tüm sonuçlar kullanılıyor")
    else:
        print(f"✅ {len(filtered)} belge '{query_category}' kategorisine uygun")

    # L2 uzaklık değerlerini benzerlik skorlarına dönüştür
    for r in filtered:
        r["similarity"] = 1 / (1 + r.get("distance", 0))

    # Benzerlik skorlarına göre sırala (yüksekten düşüğe)
    filtered.sort(key=lambda x: x.get("similarity", 0), reverse=True)

    # Sadece top_k kadar sonuç döndür
    return filtered[:top_k]


def run_experiment(query_text, query_vector, category, output_dir=None):
    """
    Hibrit yaklaşım deneyini çalıştırır ve sonuçları kaydeder.
    """
    start_time = time.time()
    results = hybrid_approach(query_vector, category, top_k=5)
    end_time = time.time()
    elapsed = end_time - start_time

    print(f"\n🔬 Hibrit Yaklaşım Deneyi: '{query_text}'")
    print(f"⏱️ Çalışma süresi: {elapsed:.6f} saniye")
    print(f"📊 {len(results)} sonuç bulundu")

    for i, r in enumerate(results):
        title = r.get("title", "Başlıksız")
        cat = r.get("category", "bilinmiyor")
        sim = r.get("similarity", 0)
        print(f"  {i + 1}. {title} - Kategori: {cat}, Benzerlik: {sim:.4f}")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"hybrid_results_{timestamp}.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "query": query_text,
                "category": category,
                "elapsed_time": elapsed,
                "results": results
            }, f, indent=2, ensure_ascii=False)

        print(f"✅ Sonuçlar kaydedildi: {output_file}")

    return results


def detect_query_category(query_text):
    """
    Sorgu metninden kategori tespit eder.
    """
    query_lower = query_text.lower()

    # Kişi sorgusu
    person_keywords = ["kimdir", "kişi", "bilim insanı", "yazar", "politikacı", "bilim adamı", "sanatçı"]
    if any(keyword in query_lower for keyword in person_keywords):
        return "person"

    # Film sorgusu
    film_keywords = ["film", "sinema", "izle", "yönetmen", "oyuncu", "movie"]
    if any(keyword in query_lower for keyword in film_keywords):
        return "film"

    # Kitap sorgusu
    book_keywords = ["kitap", "yazar", "roman", "edebiyat", "kitabı", "eser"]
    if any(keyword in query_lower for keyword in book_keywords):
        return "book"

    # Varsayılan kategori
    return "default"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Hibrit yaklaşım deneyi")
    parser.add_argument("--query", type=str, default="Marie Curie kimdir?", help="Test sorgusu")
    parser.add_argument("--category", type=str, help="Kategori (belirtilmezse otomatik tespit edilir)")
    parser.add_argument("--output", type=str, default="../experiments/results", help="Sonuçların kaydedileceği dizin")
    args = parser.parse_args()

    query_text = args.query

    # Eğer kategori belirtilmemişse otomatik tespit et
    if not args.category:
        category = detect_query_category(query_text)
        print(f"📑 Tespit edilen kategori: {category}")
    else:
        category = args.category

    # Dummy bir embedding vektörü oluştur
    # Gerçek uygulamada bir embedding modelinden alınmalıdır