# similarity_fix/experiments/hybrid_approach.py

from pgvector_utils import query_similar_documents

def hybrid_approach(query_vector, desired_category="default", top_k=10):
    """
    Hibrit yaklaşım:
    - İlk olarak sorguya benzer belgeler getirilir.
    - Belge kategorisi 'desired_category' ile eşleşenler filtrelenir.
    - (Gerekirse) Skor dönüşümü uygulanır.
    """
    results = query_similar_documents(query_vector, top_k=top_k)
    filtered = [r for r in results if r.get("category") == desired_category]
    if not filtered:
        filtered = results
    return filtered

if __name__ == "__main__":
    query_vector = [1.0, 1.0, 1.0, 1.0, 1.0]
    results = hybrid_approach(query_vector)
    print("Hibrit Yaklaşım Deneyi Sonuçları:")
    for r in results:
        print(r)
