#!/usr/bin/env python3
# similarity_fix/similarity_adapter.py

import sys
import os
import numpy as np
from pgvector_utils import query_similar_documents

try:
    from sentence_transformers import SentenceTransformer

    has_sentence_transformers = True
except ImportError:
    has_sentence_transformers = False


class SimilarityAdapter:
    def __init__(self, metric="l2", strategy="hybrid"):
        self.metric = metric
        self.strategy = strategy

        # Gerçek bir embedding modeli yükle (eğer kullanılabilirse)
        self.model = None
        if has_sentence_transformers:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                print("✅ Embedding modeli başarıyla yüklendi")
            except Exception as e:
                print(f"⚠️ Model yükleme hatası: {e}")

    def query(self, query_text, top_k=5):
        """
        Sorgu metni için benzer belgeleri döner.
        Stratejiye göre ek işlemler (normalize etme, kategori filtreleme vb.) uygulanır.
        """
        # Gerçek embedding oluştur veya fallback
        if self.model:
            query_vector = self.model.encode(query_text).tolist()
        else:
            # Dummy embedding (gerçek uygulama için uygun değil)
            query_vector = [float(len(query_text) % 10)] * 384
            print("⚠️ Dummy embedding kullanılıyor")

        # Sorgunun kategorisini belirle
        query_category = self._detect_query_category(query_text)
        print(f"📑 Sorgu kategorisi: {query_category}")

        # PGVector'den ham sonuçları al
        results = query_similar_documents(query_vector, top_k=top_k * 2, metric=self.metric)

        if not results:
            print("⚠️ Sorgu için sonuç bulunamadı")
            return []

        print(f"📊 Ham sorgu sonuçları: {len(results)}")

        if self.strategy == "reverse":
            # L2 uzaklığını benzerlik skoruna dönüştür
            for res in results:
                res['normalized_score'] = self._normalize_score(res['score'])

            # Benzerlik skoruna göre sırala (yüksekten düşüğe)
            results.sort(key=lambda x: x.get('normalized_score', 0), reverse=True)

            print("🔄 'reverse' stratejisi uygulandı")

        elif self.strategy == "scale":
            # Skorları [0,1] aralığına normalize et
            scores = [r.get('score', 0) for r in results]
            min_score, max_score = min(scores), max(scores)
            for res in results:
                if max_score - min_score == 0:
                    res['normalized_score'] = 0
                else:
                    res['normalized_score'] = (res['score'] - min_score) / (max_score - min_score)

            # Benzerlik skoruna göre sırala
            if self.metric == "l2":
                # L2'de düşük skor daha iyi (yüksek benzerlik)
                results.sort(key=lambda x: x.get('normalized_score', 0))
            else:
                # Diğer metriklerde yüksek skor daha iyi (yüksek benzerlik)
                results.sort(key=lambda x: x.get('normalized_score', 0), reverse=True)

            print("📏 'scale' stratejisi uygulandı")

        elif self.strategy == "hybrid":
            # 1. Kategori filtreleme
            filtered = [r for r in results if r.get("category") == query_category]

            if not filtered or len(filtered) < 2:  # Yeterli sonuç yoksa tüm sonuçları kullan
                filtered = results
                print(f"⚠️ '{query_category}' kategorisinde yeterli belge bulunamadı, tüm sonuçlar kullanılıyor")
            else:
                print(f"✅ {len(filtered)} belge '{query_category}' kategorisine uygun")

            # 2. L2 uzaklığını benzerlik skoruna dönüştür
            for res in filtered:
                res['normalized_score'] = self._normalize_score(res['score'])

            # 3. Skorlara göre sırala (yüksek->düşük)
            filtered.sort(key=lambda x: x.get('normalized_score', 0), reverse=True)

            # Sadece top_k kadar sonuç dön
            results = filtered[:top_k]

            print("🔄 'hybrid' stratejisi uygulandı")

        # Sonuçlardan sadece top_k kadarını döndür
        return results[:top_k]

    def _normalize_score(self, score):
        """
        L2 uzaklığını benzerlik skoruna dönüştürür: 1/(1+uzaklık)
        """
        return 1 / (1 + score)

    def _detect_query_category(self, query_text):
        """
        Basit bir kategori tespiti yapar.
        Gerçek uygulamada daha gelişmiş bir kategori belirleme algoritması kullanılabilir.
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

    def apply_to_system(self):
        """
        Bu çözümü ana sisteme uygular.
        """
        try:
            sys.path.append("../..")
            from app.retrieval import update_similarity_handler
            update_similarity_handler(self)
            print("✅ Çözüm başarıyla sisteme uygulandı!")
            return True
        except ImportError:
            print("❌ Ana sistem modülleri bulunamadı, çözüm uygulanamadı.")
            return False
        except Exception as e:
            print(f"❌ Çözüm uygulama hatası: {e}")
            return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="RAG Benzerlik Düzeltme Modülü")
    parser.add_argument("--apply", action="store_true", help="Çözümü ana sisteme uygula")
    parser.add_argument("--metric", type=str, default="l2", choices=["l2", "cosine", "inner"],
                        help="Kullanılacak benzerlik metriği")
    parser.add_argument("--strategy", type=str, default="hybrid", choices=["reverse", "scale", "hybrid"],
                        help="Kullanılacak strateji")
    parser.add_argument("--test", type=str, help="Test sorgusu çalıştır")
    args = parser.parse_args()

    adapter = SimilarityAdapter(metric=args.metric, strategy=args.strategy)

    if args.test:
        print(f"🔍 Test sorgusu çalıştırılıyor: '{args.test}'")
        results = adapter.query(args.test, top_k=5)
        print(f"📊 {len(results)} sonuç bulundu")
        for i, res in enumerate(results):
            print(f"{i + 1}. {res.get('title', 'Başlıksız')} - Benzerlik: {res.get('normalized_score', 0):.4f}")

    if args.apply:
        adapter.apply_to_system()


if __name__ == "__main__":
    main()