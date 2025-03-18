#!/usr/bin/env python3
"""
PGVector veritabanı işlemleri için yardımcı fonksiyonlar.
"""
import os
import sys
import psycopg2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass


@dataclass
class Document:
    """Doküman veri yapısı."""
    id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class PGVectorClient:
    """PGVector veritabanı ile etkileşim kurmak için istemci."""

    def __init__(self, connection_string: Optional[str] = None,
                 host: str = "localhost", port: str = "5432",
                 dbname: str = "ragdb", user: str = "raguser",
                 password: str = "ragpassword"):
        """Veritabanı bağlantısını başlatır."""
        if connection_string:
            self.connection_string = connection_string
        else:
            self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

        self.conn = None
        self.is_connected = False

    def connect(self) -> bool:
        """Veritabanına bağlanır."""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Veritabanı bağlantı hatası: {e}")
            return False

    def disconnect(self) -> None:
        """Veritabanı bağlantısını kapatır."""
        if self.conn:
            self.conn.close()
            self.is_connected = False

    def check_table_exists(self, table_name: str) -> bool:
        """Belirtilen tablonun var olup olmadığını kontrol eder."""
        if not self.is_connected and not self.connect():
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT EXISTS (
               SELECT FROM information_schema.tables 
               WHERE table_name = %s
            );
            """, (table_name,))
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Tablo kontrolü hatası: {e}")
            return False

    def similarity_search(self, query_vector: List[float],
                          limit: int = 5,
                          metric: str = "l2") -> List[Tuple[Document, float]]:
        """Benzerlik araması yapar."""
        if not self.is_connected and not self.connect():
            return []

        # Metrik operatörünü belirle
        if metric == "cosine":
            operator = "<=>"
        elif metric == "l2":
            operator = "<->"
        elif metric == "inner":
            operator = "<#>"
        else:
            raise ValueError(f"Geçersiz metrik: {metric}")

        try:
            cursor = self.conn.cursor()

            # Sorgu vektörünü string literal haline getirin
            vector_str = '[' + ','.join(map(str, query_vector)) + ']'

            # Sorguda, gönderilen parametreyi explicit olarak vector tipine cast edin.
            cursor.execute(f"""
            SELECT document_id, title, content, embedding, embedding {operator} (%s)::vector AS score
            FROM document_chunks
            ORDER BY embedding {operator} (%s)::vector {"ASC" if metric == "l2" else "DESC"}
            LIMIT %s
            """, (vector_str, vector_str, limit))

            results = []
            for doc_id, title, content, embedding, score in cursor.fetchall():
                doc = Document(
                    id=doc_id,
                    title=title or "Başlıksız",
                    content=content,
                    metadata={},  # metadata sütunu yoksa boş dict atanıyor
                    embedding=embedding
                )
                results.append((doc, score))
            return results
        except Exception as e:
            print(f"Benzerlik araması hatası: {e}")
            return []

    def normalized_similarity_search(self, query_vector: List[float],
                                     limit: int = 5,
                                     metric: str = "l2") -> List[Tuple[Document, float]]:
        """Normalize edilmiş benzerlik araması yapar."""
        results = self.similarity_search(query_vector, limit, metric)
        normalized_results = []
        for doc, score in results:
            if metric == "l2":
                # L2 uzaklığını benzerlik skoruna çevir (düşük değer->yüksek benzerlik)
                normalized_score = 1 / (1 + score)
            elif metric == "cosine":
                # Kosinüs zaten [0,1] aralığında
                normalized_score = score
            elif metric == "inner":
                # Sigmoid dönüşümü
                normalized_score = 1 / (1 + np.exp(-score))
            else:
                normalized_score = score
            normalized_results.append((doc, normalized_score))
        # Benzerlik skoruna göre azalan sırada sırala (en benzer en üstte)
        return sorted(normalized_results, key=lambda x: x[1], reverse=True)


# >>> Global Fonksiyon - query_similar_documents <<<
def query_similar_documents(query_vector: List[float], top_k: int = 5, metric: str = "l2") -> List[Dict[str, Any]]:
    """
    PGVectorClient kullanarak benzerlik araması yapar.
    Dönen sonuçlar, adapter ve deney script'lerinin beklediği sözlük formatında verilir.
    """
    client = PGVectorClient()
    if not client.connect():
        print("❌ Veritabanı bağlantısı kurulamadı.")
        return []

    # Benzerlik araması (raw sonuç: (Document, score))
    results = client.similarity_search(query_vector, limit=top_k, metric=metric)
    client.disconnect()

    converted_results = []
    for doc, score in results:
        result = {
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "metadata": {},  # metadata sütunu yoksa boş dict atanıyor
            "embedding": doc.embedding,
            "score": score,  # Raw skor
            "distance": score,  # L2 metriğinde uzaklık
            "normalized_score": 1 / (1 + score) if metric == "l2" else score  # Normalize edilmiş benzerlik skoru
        }

        # Basit kategori tespiti
        content_lower = doc.content.lower() if doc.content else ""
        title_lower = doc.title.lower() if doc.title else ""

        person_keywords = ["scientist", "physicist", "chemist", "researcher", "bilim", "fizikçi", "kimyager"]
        film_keywords = ["film", "movie", "director", "actor", "cinema", "sinema", "yönetmen", "oyuncu"]
        book_keywords = ["book", "novel", "author", "kitap", "roman", "yazar"]

        if any(keyword in content_lower or keyword in title_lower for keyword in person_keywords):
            result["category"] = "person"
        elif any(keyword in content_lower or keyword in title_lower for keyword in film_keywords):
            result["category"] = "film"
        elif any(keyword in content_lower or keyword in title_lower for keyword in book_keywords):
            result["category"] = "book"
        else:
            result["category"] = "default"

        converted_results.append(result)

    # Sonuçları L2 metriğinde uzaklığa göre sırala (küçükten büyüğe)
    if metric == "l2":
        return sorted(converted_results, key=lambda x: x["score"])
    # Kosinüs ve iç çarpım metriklerinde benzerlik skoruna göre sırala (büyükten küçüğe)
    else:
        return sorted(converted_results, key=lambda x: x["score"], reverse=True)


if __name__ == "__main__":
    # Test kodu
    client = PGVectorClient()
    if client.connect():
        print("✅ Veritabanı bağlantısı başarılı!")
        client.disconnect()
    else:
        print("❌ Veritabanı bağlantısı başarısız!")