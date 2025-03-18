# similarity_fix/benchmark.py

import json
import time
import argparse
from .similarity_adapter import SimilarityAdapter

def run_benchmark():
    adapter = SimilarityAdapter(metric="l2", strategy="hybrid")
    query = "Marie Curie kimdir?"
    start_time = time.time()
    results = adapter.query(query, top_k=5)
    end_time = time.time()
    elapsed = end_time - start_time

    benchmark_results = {
        "query": query,
        "top_k": 5,
        "elapsed_time": elapsed,
        "results": results
    }
    return benchmark_results

def main():
    parser = argparse.ArgumentParser(description="Benchmark için RAG Benzerlik Düzeltme Modülü")
    parser.add_argument("--output", type=str, default="benchmark_results.json", help="Benchmark sonuç dosya yolu")
    args = parser.parse_args()

    results = run_benchmark()
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print(f"Benchmark sonuçları {args.output} dosyasına yazıldı.")

if __name__ == "__main__":
    main()
