#!/usr/bin/env python
"""
Embedding işlemlerini test eden araç.
"""
import argparse
import numpy as np
from app.embedding import get_embeddings
from app.config import EMBEDDING_MODEL


def test_embedding_model():
    """Embedding modelini test eder."""
    print(f"🔍 Embedding modeli '{EMBEDDING_MODEL}' test ediliyor...")
    try:
        embeddings = get_embeddings()
        print(f"✅ Embedding modeli başarıyla yüklendi: {EMBEDDING_MODEL}")
        return embeddings
    except Exception as e:
        print(f"❌ Embedding modeli yüklenirken hata: {e}")
        return None


def test_embedding_generation(embeddings, text):
    """Verilen metinden embedding oluşturmayı test eder."""
    print(f"\n🔍 Metin için embedding oluşturuluyor: '{text[:50]}...'")
    try:
        vector = embeddings.embed_query(text)
        print(f"✅ Embedding başarıyla oluşturuldu. Boyut: {len(vector)}")
        print(f"📊 Embedding vektörü (ilk 5 eleman): {vector[:5]}")

        # Vektör istatistikleri
        print(f"📈 Vektör istatistikleri:")
        print(f"  - Ortalama: {np.mean(vector):.6f}")
        print(f"  - Min: {np.min(vector):.6f}")
        print(f"  - Max: {np.max(vector):.6f}")
        print(f"  - Standart sapma: {np.std(vector):.6f}")

        return vector
    except Exception as e:
        print(f"❌ Embedding oluşturulurken hata: {e}")
        return None


def test_embedding_similarity(embeddings, text1, text2):
    """İki metin arasındaki benzerliği test eder."""
    print(f"\n🔍 Metin benzerliği test ediliyor:")
    print(f"  - Metin 1: '{text1[:50]}...'")
    print(f"  - Metin 2: '{text2[:50]}...'")

    try:
        vector1 = embeddings.embed_query(text1)
        vector2 = embeddings.embed_query(text2)

        # Kosinüs benzerliği hesapla
        similarity = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))

        print(f"✅ Benzerlik skoru: {similarity:.4f} (0-1 arası, 1 en benzer)")
        return similarity
    except Exception as e:
        print(f"❌ Benzerlik hesaplanırken hata: {e}")
        return None


def test_multilingual(embeddings):
    """Çok dilli benzerlik testi yapar."""
    print("\n🔍 Çok dilli benzerlik testi yapılıyor...")

    texts = {
        "en": "The Scandinavian countries include Denmark, Norway, and Sweden.",
        "tr": "İskandinav ülkeleri Danimarka, Norveç ve İsveç'i içerir.",
        "de": "Zu den skandinavischen Ländern gehören Dänemark, Norwegen und Schweden.",
        "fr": "Les pays scandinaves comprennent le Danemark, la Norvège et la Suède."
    }

    # Her dil çiftini karşılaştır
    results = {}
    for lang1, text1 in texts.items():
        for lang2, text2 in texts.items():
            if lang1 != lang2:
                key = f"{lang1}-{lang2}"
                similarity = test_embedding_similarity(embeddings, text1, text2)
                results[key] = similarity

    # En yüksek ve en düşük benzerliği göster
    if results:
        max_pair = max(results.items(), key=lambda x: x[1])
        min_pair = min(results.items(), key=lambda x: x[1])

        print(f"\n📊 En yüksek benzerlik: {max_pair[0]} ({max_pair[1]:.4f})")
        print(f"📊 En düşük benzerlik: {min_pair[0]} ({min_pair[1]:.4f})")

    return results


def main():
    parser = argparse.ArgumentParser(description="RAG Embedding Test Aracı")
    parser.add_argument("--text", type=str, help="Test edilecek metin")
    parser.add_argument("--multilingual", action="store_true", help="Çok dilli test yap")
    args = parser.parse_args()

    # Embedding modelini test et
    embeddings = test_embedding_model()
    if not embeddings:
        return

    # Test metni
    test_text = args.text or "İskandinav ülkeleri Danimarka, Norveç ve İsveç'i içerir."

    # Embedding oluşturmayı test et
    vector = test_embedding_generation(embeddings, test_text)

    # Benzerlik testleri
    similar_text = "Nordic countries include Denmark, Norway, and Sweden."
    different_text = "Machine learning is a subset of artificial intelligence."

    test_embedding_similarity(embeddings, test_text, similar_text)
    test_embedding_similarity(embeddings, test_text, different_text)

    # Çok dilli test
    if args.multilingual:
        test_multilingual(embeddings)

    print("\n✅ Embedding testi tamamlandı.")


if __name__ == "__main__":
    main()