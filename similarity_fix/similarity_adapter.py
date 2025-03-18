# similarity_fix/similarity_adapter.py

from .pgvector_utils import query_similar_documents
from .analyze_similarity import analyze_results

class SimilarityAdapter:
    def __init__(self, metric="l2", strategy="reverse"):
        self.metric = metric
        self.strategy = strategy

    def query(self, query_text, top_k=5):
        """
        Sorgu metni için basit bir embedding oluşturarak benzer belgeleri döner.
        Stratejiye göre ek işlemler (normalize etme, kategori filtreleme vb.) uygulanır.
        """
        query_vector = self._embed(query_text)
        results = query_similar_documents(query_vector, top_k=top_k, metric=self.metric)

        if self.strategy == "reverse":
            # PGVector'den dönen skor, tersine çevrilmemiş ham skor (uzaklık) olarak kabul edilir.
            pass
        elif self.strategy == "scale":
            # Skorları [0,1] aralığına normalize etme
            for res in results:
                res['score'] = self._normalize_score(res['score'])
        elif self.strategy == "hybrid":
            # Kategori filtreleme: Sadece "default" kategorideki belgeleri seç
            filtered = [r for r in results if r.get("category") == "default"]
            if not filtered:
                filtered = results
            # Normalizasyon
            for res in filtered:
                res['score'] = self._normalize_score(res['score'])
            results = filtered
        return results

    def _embed(self, text):
        # Basit bir embedding örneği: 384 boyutlu dummy embedding üretir.
        vector = [float(len(text) % 10)] * 384
        return vector

    def _normalize_score(self, score):
        """
        Benzerlik skorunu normalize etmek için (örnekte skor zaten 0-1 aralığında olduğundan dönüşüme gerek yoktur).
        """
        return score
