#!/usr/bin/env python3
"""
Farklı benzerlik metriklerini test eden araç.
"""
import os
import argparse
import numpy as np
import json
import time
from datetime import datetime
from sentence_transformers import SentenceTransformer

# Test metinleri
TEST_PAIRS = [
    {
        "name": "person_similar",
        "text1": "Marie Curie was a physicist and chemist who conducted pioneering research on radioactivity.",
        "text2": "Marie Skłodowska Curie was a Polish and naturalized-French physicist and chemist who conducted pioneering research on radioactivity.",
        "expected_similarity": "high"
    },
    {
        "name": "person_medium",
        "text1": "Marie Curie was a physicist and chemist who conducted pioneering research on radioactivity.",
        "text2": "Albert Einstein was a German-born theoretical physicist who developed the theory of relativity.",
        "expected_similarity": "medium"
    },
    {
        "name": "person_film",
        "text1": "Marie Curie was a physicist and chemist who conducted pioneering research on radioactivity.",
        "text2": "Inception is a 2010 science fiction action film written and directed by Christopher Nolan.",
        "expected_similarity": "low"
    },
    {
        "name": "film_similar",
        "text1": "Inception is a 2010 science fiction action film written and directed by Christopher Nolan.",
        "text2": "In the 2010 film Inception, directed by Christopher Nolan, Dom Cobb is a thief with the ability to enter people's dreams.",
        "expected_similarity": "high"
    },
    {
        "name": "film_book",
        "text1": "Inception is a 2010 science fiction action film written and directed by Christopher Nolan.",
        "text2": "The Lord of the Rings is an epic high-fantasy novel by English author J. R. R. Tolkien.",
        "expected_similarity": "low"
    }
]


# Benzerlik fonksiyonları
def cosine_similarity(a, b):
    """Kosinüs benzerliği hesaplar"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def euclidean_distance(a, b):
    """Öklid uzaklığı hesaplar"""
    return np.sqrt(np.sum((np.array(a) - np.array(b)) ** 2))


def dot_product(a, b):
    """İç çarpım hesaplar"""
    return np.dot(a, b)


def l2_to_similarity(distance):
    """L2 uzaklığını benzerlik skoruna dönüştürür"""
    return 1 / (1 + distance)


def evaluate_metrics(model, test_pairs, output_dir=None):
    """Farklı benzerlik metriklerini değerlendirir"""
    results = []

    print("🔍 Benzerlik metriklerini değerlendirme:")
    print("=" * 80)

    # Her test çifti için değerlendirme yap
    for pair in test_pairs:
        name = pair["name"]
        text1 = pair["text1"]
        text2 = pair["text2"]
        expected = pair["expected_similarity"]

        print(f"\n📝 Test: {name}")
        print(f"Metin 1: {text1[:50]}...")
        print(f"Metin 2: {text2[:50]}...")
        print(f"Beklenen benzerlik: {expected}")

        # Vektörleri hesapla
        vector1 = model.encode(text1)
        vector2 = model.encode(text2)

        # Farklı metrikleri hesapla
        cosine = cosine_similarity(vector1, vector2)
        euclidean = euclidean_distance(vector1, vector2)
        dot = dot_product(vector1, vector2)
        l2_sim = l2_to_similarity(euclidean)

        # Normalize edilmiş benzerlik skoru (tüm metrikler için 0-1 arası, 1 = en benzer)
        normalized_cosine = (cosine + 1) / 2  # [-1, 1] -> [0, 1]
        normalized_euclidean = l2_sim         # [0, inf) -> [0, 1]
        normalized_dot = 1 / (1 + np.exp(-dot))  # [-inf, inf] -> [0, 1] (sigmoid)

        # Sonuçları yazdır
        print("📊 Sonuçlar:")
        print(f"  - Kosinüs benzerliği: {cosine:.6f} (norm: {normalized_cosine:.6f})")
        print(f"  - Öklid uzaklığı: {euclidean:.6f} (benzerlik: {normalized_euclidean:.6f})")
        print(f"  - İç çarpım: {dot:.6f} (norm: {normalized_dot:.6f})")

        # Beklenen aralıkları belirle
        expected_range = {
            "high": (0.8, 1.0),
            "medium": (0.3, 0.8),
            "low": (0.0, 0.3)
        }
        expected_min, expected_max = expected_range[expected]

        # Her metriğin doğruluğunu değerlendir
        cosine_correct = expected_min <= normalized_cosine <= expected_max
        euclidean_correct = expected_min <= normalized_euclidean <= expected_max
        dot_correct = expected_min <= normalized_dot <= expected_max

        print("🎯 Değerlendirme:")
        print(f"  - Kosinüs: {'✅' if cosine_correct else '❌'} ({normalized_cosine:.2f})")
        print(f"  - Öklid: {'✅' if euclidean_correct else '❌'} ({normalized_euclidean:.2f})")
        print(f"  - İç çarpım: {'✅' if dot_correct else '❌'} ({normalized_dot:.2f})")

        # Sonucu kaydet; boolean değerleri Python'un yerel bool() fonksiyonu ile dönüştürülüyor
        result = {
            "test_name": name,
            "expected_similarity": expected,
            "expected_range": expected_range[expected],
            "metrics": {
                "cosine": {
                    "raw": float(cosine),
                    "normalized": float(normalized_cosine),
                    "correct": bool(cosine_correct)
                },
                "euclidean": {
                    "raw": float(euclidean),
                    "normalized": float(normalized_euclidean),
                    "correct": bool(euclidean_correct)
                },
                "dot_product": {
                    "raw": float(dot),
                    "normalized": float(normalized_dot),
                    "correct": bool(dot_correct)
                }
            }
        }

        results.append(result)

    # Metrik doğruluk oranları
    metric_accuracy = {
        "cosine": sum(1 for r in results if r["metrics"]["cosine"]["correct"]) / len(results),
        "euclidean": sum(1 for r in results if r["metrics"]["euclidean"]["correct"]) / len(results),
        "dot_product": sum(1 for r in results if r["metrics"]["dot_product"]["correct"]) / len(results)
    }

    print("\n📊 Metrik doğruluk oranları:")
    for metric, accuracy in metric_accuracy.items():
        print(f"  - {metric}: {accuracy:.2%}")

    best_metric = max(metric_accuracy.items(), key=lambda x: x[1])
    print(f"\n🏆 En iyi metrik: {best_metric[0]} ({best_metric[1]:.2%})")

    # Sonuçları dosyaya kaydet
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"metric_test_results_{timestamp}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": timestamp,
                "model": model.get_sentence_embedding_dimension(),
                "results": results,
                "accuracy": metric_accuracy,
                "best_metric": {
                    "name": best_metric[0],
                    "accuracy": best_metric[1]
                }
            }, f, indent=2)
        print(f"\n✅ Sonuçlar kaydedildi: {output_file}")

    return results, metric_accuracy, best_metric[0]


def benchmark_metrics(model, test_pairs, iterations=5, output_dir=None):
    """Farklı metriklerin performansını karşılaştırır"""
    print("\n⏱️ Benzerlik metriklerinin performans karşılaştırması:")
    print("=" * 80)
    metrics = {
        "cosine": cosine_similarity,
        "euclidean": euclidean_distance,
        "dot_product": dot_product
    }
    vector_pairs = []
    for pair in test_pairs:
        vector1 = model.encode(pair["text1"])
        vector2 = model.encode(pair["text2"])
        vector_pairs.append((vector1, vector2))
    results = {}
    for name, metric_func in metrics.items():
        print(f"\n⏱️ '{name}' metriği için performans ölçümü...")
        times = []
        for _ in range(iterations):
            start_time = time.time()
            for vector1, vector2 in vector_pairs:
                if name == "euclidean":
                    similarity = l2_to_similarity(metric_func(vector1, vector2))
                elif name == "dot_product":
                    similarity = 1 / (1 + np.exp(-metric_func(vector1, vector2)))
                else:
                    similarity = metric_func(vector1, vector2)
            end_time = time.time()
            times.append(end_time - start_time)
        avg_time = sum(times) / len(times)
        std_time = np.std(times)
        print(f"  - Ortalama süre: {avg_time * 1000:.2f} ms")
        print(f"  - Standart sapma: {std_time * 1000:.2f} ms")
        results[name] = {
            "avg_time_ms": avg_time * 1000,
            "std_time_ms": std_time * 1000,
            "iterations": iterations
        }
    fastest_metric = min(results.items(), key=lambda x: x[1]["avg_time_ms"])
    print(f"\n🏁 En hızlı metrik: {fastest_metric[0]} ({fastest_metric[1]['avg_time_ms']:.2f} ms)")
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"metric_benchmark_{timestamp}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": timestamp,
                "model": model.get_sentence_embedding_dimension(),
                "results": results,
                "fastest_metric": {
                    "name": fastest_metric[0],
                    "avg_time_ms": fastest_metric[1]["avg_time_ms"]
                }
            }, f, indent=2)
        print(f"\n✅ Benchmark sonuçları kaydedildi: {output_file}")
    return results, fastest_metric[0]


def main():
    parser = argparse.ArgumentParser(description="Benzerlik metriklerini test etme aracı")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="Kullanılacak embedding modeli")
    parser.add_argument("--output", type=str, default="experiments/results", help="Sonuçların kaydedileceği dizin")
    parser.add_argument("--benchmark", action="store_true", help="Performans karşılaştırması yap")
    parser.add_argument("--iterations", type=int, default=5, help="Benchmark iterasyon sayısı")
    args = parser.parse_args()

    print(f"🔄 Embedding modeli yükleniyor: {args.model}")
    model = SentenceTransformer(args.model)

    results, accuracy, best_metric = evaluate_metrics(model, TEST_PAIRS, args.output)

    if args.benchmark:
        benchmark_results, fastest_metric = benchmark_metrics(model, TEST_PAIRS, args.iterations, args.output)


if __name__ == "__main__":
    main()
