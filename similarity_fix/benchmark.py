#!/usr/bin/env python3
# similarity_fix/benchmark.py

import json
import time
import argparse
import os
import sys
from datetime import datetime
from similarity_adapter import SimilarityAdapter


def run_benchmark(queries=None, metric="l2", strategy="hybrid", top_k=5):
    """
    Benzerlik adaptörünü test etmek için benchmark çalıştırır.
    """
    if queries is None:
        queries = [
            "Marie Curie kimdir?",
            "Inception filmi hakkında bilgi ver",
            "Yüzüklerin Efendisi kitabı nedir?"
        ]

    adapter = SimilarityAdapter(metric=metric, strategy=strategy)

    all_results = {}
    total_time = 0

    for query in queries:
        print(f"🔍 Sorgu: '{query}'")
        start_time = time.time()
        results = adapter.query(query, top_k=top_k)
        end_time = time.time()
        elapsed = end_time - start_time
        total_time += elapsed

        if not results:
            print(f"⚠️ Sorgu için sonuç bulunamadı: {query}")
            continue

        print(f"⏱️ Çalışma süresi: {elapsed:.6f} saniye")
        print(f"📊 {len(results)} sonuç bulundu")

        for i, res in enumerate(results):
            title = res.get('title', 'Başlıksız')
            category = res.get('category', 'bilinmiyor')
            score = res.get('normalized_score', res.get('score', 0))
            print(f"  {i + 1}. {title} - Kategori: {category}, Benzerlik: {score:.4f}")

        query_results = {
            "query": query,
            "top_k": top_k,
            "elapsed_time": elapsed,
            "results": results
        }
        all_results[query] = query_results

    avg_time = total_time / len(queries) if queries else 0
    benchmark_results = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "metric": metric,
        "strategy": strategy,
        "top_k": top_k,
        "queries": queries,
        "avg_time": avg_time,
        "results": all_results
    }

    return benchmark_results


def main():
    parser = argparse.ArgumentParser(description="Benchmark için RAG Benzerlik Düzeltme Modülü")
    parser.add_argument("--output", type=str, default="benchmark_results.json", help="Benchmark sonuç dosya yolu")
    parser.add_argument("--queries", type=str, help="Sorguları içeren dosya yolu")
    parser.add_argument("--metric", type=str, default="l2", choices=["l2", "cosine", "inner"],
                        help="Kullanılacak benzerlik metriği")
    parser.add_argument("--strategy", type=str, default="hybrid", choices=["reverse", "scale", "hybrid"],
                        help="Kullanılacak strateji")
    parser.add_argument("--top-k", type=int, default=5, help="Her sorgu için dönecek sonuç sayısı")
    args = parser.parse_args()

    queries = None
    if args.queries:
        try:
            with open(args.queries, "r", encoding="utf-8") as f:
                queries = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"❌ Sorgu dosyası okuma hatası: {e}")
            return

    print(f"⚙️ Benchmark çalıştırılıyor...")
    print(f"  Metrik: {args.metric}")
    print(f"  Strateji: {args.strategy}")
    print(f"  Top-K: {args.top_k}")

    results = run_benchmark(queries, args.metric, args.strategy, args.top_k)

    # Sonuçları dosyaya kaydet
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"✅ Benchmark sonuçları {args.output} dosyasına yazıldı.")
    print(f"⏱️ Ortalama çalışma süresi: {results['avg_time']:.6f} saniye")


if __name__ == "__main__":
    main()