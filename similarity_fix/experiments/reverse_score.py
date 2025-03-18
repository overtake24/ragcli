# similarity_fix/experiments/reverse_score.py

from pgvector_utils import query_similar_documents

def reverse_score_conversion(distance):
    """
    L2 uzaklığını benzerlik skoruna dönüştürür: 1/(1+uzaklık)
    """
    return 1 / (1 + distance)

def run_experiment(query_vector):
    results = query_similar_documents(query_vector, top_k=10)
    for res in results:
        distance = res.get("distance")
        if distance is not None:
            res["reverse_score"] = reverse_score_conversion(distance)
    return results

if __name__ == "__main__":
    query_vector = [1.0, 1.0, 1.0, 1.0, 1.0]
    results = run_experiment(query_vector)
    print("Reverse Score Dönüşüm Deneyi Sonuçları:")
    for r in results:
        print(r)
