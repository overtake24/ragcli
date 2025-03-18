# similarity_fix/experiments/scale_transform.py

def normalize_scores(results):
    """
    Sonuçlardaki skorları min-max normalizasyonu ile [0,1] aralığına çeker.
    """
    scores = [r.get("score", 0) for r in results]
    if not scores:
        return results
    min_score = min(scores)
    max_score = max(scores)
    for r in results:
        score = r.get("score", 0)
        if max_score - min_score == 0:
            r["normalized_score"] = 0
        else:
            r["normalized_score"] = (score - min_score) / (max_score - min_score)
    return results

def run_experiment(results):
    normalized_results = normalize_scores(results)
    return normalized_results

if __name__ == "__main__":
    results = [
        {"document": "Doc 1", "score": 0.2},
        {"document": "Doc 2", "score": 0.8},
        {"document": "Doc 3", "score": 0.5},
    ]
    normalized = run_experiment(results)
    print("Scale Transform Deneyi Sonuçları:")
    for r in normalized:
        print(r)
