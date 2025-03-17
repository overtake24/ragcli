#!/usr/bin/env python3
"""
Düzeltilmiş vektör benzerliği kontrol scripti
"""
import psycopg2
import numpy as np
from app.config import DB_CONNECTION
from app.embedding import get_embedding_model


def cosine_similarity(a, b):
    """İki vektör arasındaki kosinüs benzerliğini hesaplar"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def check_similarity():
    """Bir sorgunun vektör veritabanındaki belgelere benzerliğini kontrol eder"""
    try:
        # Sorguları belirle
        queries = [
            "Scandinavia",
            "Nordic countries",
            "Northern Lights",
            "Best time to visit Nordic countries",
            "Denmark, Norway, Sweden"
        ]

        # Embedding modelini yükle
        model = get_embedding_model()

        # Veritabanına bağlan
        conn = psycopg2.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # Tüm dokümanları al (vektörsüz)
        cursor.execute("SELECT id, document_id, title, content FROM document_chunks")
        documents = cursor.fetchall()

        print(f"Toplam {len(documents)} belge parçası bulundu.")

        # Her sorgu için tüm belgelere benzerlik hesapla
        for query in queries:
            print(f"\nSorgu: '{query}'")
            query_vector = model.encode(query)

            # Her belge için benzerlik hesapla
            similarities = []
            for doc_id, document_id, title, content in documents:
                # Belgenin içeriğinden yeni bir vektör oluştur
                doc_vector = model.encode(content)
                similarity = cosine_similarity(query_vector, doc_vector)
                similarities.append((doc_id, document_id, title, similarity))

            # En yüksek benzerliğe sahip 3 belgeyi göster
            top_similarities = sorted(similarities, key=lambda x: x[3], reverse=True)[:3]

            print("En benzer belgeler:")
            for doc_id, document_id, title, similarity in top_similarities:
                print(f"  - ID: {doc_id} (Belge: {document_id})")
                print(f"    Başlık: {title}")
                print(f"    Benzerlik: {similarity:.4f}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Hata: {e}")


if __name__ == "__main__":
    check_similarity()