#!/usr/bin/env python3
"""
RAG sistemindeki benzerlik sorunlarını analiz eden araç.
"""
import os
import sys
import argparse
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

# Konfigürasyon
DEFAULT_OUTPUT_DIR = "experiments/results"
DEFAULT_QUERIES = [
    "Marie Curie kimdir?",
    "Inception filmi hakkında bilgi ver",
    "Yüzüklerin Efendisi kitabı nedir?"
]

def connect_to_database():
    """Veritabanına bağlanır"""
    try:
        # Ana projedeki bağlantı bilgilerini kullan
        sys.path.append("../..")
        from app.db import get_db_connection
        conn = get_db_connection()
        return conn
    except ImportError:
        print("⚠️ Ana projenin db modülü bulunamadı, doğrudan bağlantı kuruluyor...")
        import psycopg2
        # Varsayılan bağlantı bilgileri
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="ragdb",
            user="raguser",
            password="ragpassword"
        )
        return conn
    except Exception as e:
        print(f"❌ Veritabanı bağlantı hatası: {e}")
        return None

def get_vector_model():
    """Embedding modelini yükler"""
    try:
        sys.path.append("../..")
        from app.embedding import get_embedding_model
        model = get_embedding_model()
        return model
    except ImportError:
        print("⚠️ Ana projenin embedding modülü bulunamadı, doğrudan model yükleniyor...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model
    except Exception as e:
        print(f"❌ Model yükleme hatası: {e}")
        return None

def get_document_categories(conn):
    """Veritabanındaki belgelerin kategorilerini tespit eder"""
    try:
        sys.path.append("../..")
        from app.categorizer import detect_document_category

        cursor = conn.cursor()
        cursor.execute("SELECT document_id, content FROM document_chunks")
        documents = cursor.fetchall()

        categories = {}
        for doc_id, content in documents:
            category = detect_document_category(content)
            categories[doc_id] = category

        return categories
    except Exception as e:
        print(f"❌ Kategori tespiti hatası: {e}")
        return {}

def analyze_raw_results(query, conn, model, categories=None, top_k=5):
    """Ham PGVector benzerlik sonuçlarını analiz eder"""
    results = {}

    try:
        print(f"\n🔍 Sorgu: '{query}' için ham sonuçlar:")

        # Sorgu vektörünü hesapla
        query_vector = model.encode(query)
        vector_str = '[' + ','.join(map(str, query_vector.tolist())) + ']'

        # Veritabanında benzerlik araması yap
        cursor = conn.cursor()
        cursor.execute("""
        SELECT document_id, title, content, embedding <-> (%s)::vector AS distance
        FROM document_chunks
        ORDER BY distance
        LIMIT %s
        """, (vector_str, top_k))

        raw_results = cursor.fetchall()
        print(f"📊 Toplam {len(raw_results)} sonuç bulundu")

        # Sorgunun kategorisini tespit et
        sys.path.append("../..")
        from app.categorizer import detect_query_category
        query_category = detect_query_category(query)
        print(f"📑 Sorgu kategorisi: {query_category}")

        # Her sonucu analiz et
        analyzed_results = []
        for doc_id, title, content, distance in raw_results:
            # Belge kategorisini tespit et
            category = categories.get(doc_id, "bilinmiyor") if categories else "bilinmiyor"
            category_match = "✅" if category == query_category else "❌"
            l2_to_similarity = 1 / (1 + distance)  # Normalize edilmiş benzerlik
            analyzed_result = {
                "document_id": doc_id,
                "title": title,
                "content_preview": content[:100] + "...",
                "raw_distance": distance,
                "normalized_similarity": l2_to_similarity,
                "category": category,
                "category_match": category == query_category,
                "query_category": query_category
            }
            analyzed_results.append(analyzed_result)

            print(f"📄 {doc_id} ({title})")
            print(f"   L2 uzaklığı: {distance:.6f}")
            print(f"   Normal. benzerlik: {l2_to_similarity:.6f}")
            print(f"   Kategori: {category} {category_match}")

        # İstatistikleri hesapla
        accuracy = (sum(1 for r in analyzed_results if r["category_match"]) /
                    len(analyzed_results)) if analyzed_results else 0
        avg_distance = (sum(r["raw_distance"] for r in analyzed_results) /
                        len(analyzed_results)) if analyzed_results else 0
        avg_similarity = (sum(r["normalized_similarity"] for r in analyzed_results) /
                          len(analyzed_results)) if analyzed_results else 0

        issues = []
        if accuracy < 0.5:
            issues.append({
                "type": "category_mismatch",
                "description": "Sonuçların çoğu sorgu kategorisiyle uyuşmuyor",
                "severity": "high"
            })
        if analyzed_results and min(r["raw_distance"] for r in analyzed_results) > 1.0:
            issues.append({
                "type": "high_distance",
                "description": "Tüm sonuçlar yüksek uzaklık değerlerine sahip",
                "severity": "medium"
            })

        results = {
            "query": query,
            "query_category": query_category,
            "results": analyzed_results,
            "stats": {
                "accuracy": accuracy,
                "avg_distance": avg_distance,
                "avg_similarity": avg_similarity
            },
            "issues": issues
        }

    except Exception as e:
        print(f"❌ Analiz hatası: {e}")
        import traceback
        traceback.print_exc()

    return results


def analyze_results(results, query):
    """Sonuçları analiz eder ve rapor verir"""
    print(f"\n📊 '{query}' sorgusu için benzerlik analizi:")

    if "category_filtered" in results:
        category_results = results["category_filtered"]
        print(f"\n📑 Kategori bazlı filtreleme ({len(category_results)} sonuç):")
        for i, (doc, score) in enumerate(category_results[:5]):
            title = doc.metadata.get("title", "Başlıksız")
            print(f"  {i + 1}. {title} - Benzerlik: {score:.4f}")

    if "similarity_filtered" in results:
        similarity_results = results["similarity_filtered"]
        print(f"\n📈 Benzerlik bazlı filtreleme ({len(similarity_results)} sonuç):")
        for i, (doc, score) in enumerate(similarity_results[:5]):
            title = doc.metadata.get("title", "Başlıksız")
            print(f"  {i + 1}. {title} - Benzerlik: {score:.4f}")

    if "raw_results" in results:
        raw_results = results["raw_results"]
        print(f"\n📉 Ham sonuçlar ({len(raw_results)} sonuç):")
        for i, (doc, score) in enumerate(raw_results[:5]):
            title = doc.metadata.get("title", "Başlıksız")
            print(f"  {i + 1}. {title} - Uzaklık: {score:.4f}")

    problems = []
    if "raw_results" in results and "similarity_filtered" in results:
        raw_docs = [doc for doc, _ in results["raw_results"][:5]]
        sim_docs = [doc for doc, _ in results["similarity_filtered"][:5]]
        if all(raw_docs[i] == sim_docs[i] for i in range(min(len(raw_docs), len(sim_docs)))):
            problems.append("Filtreleme etkisiz: Ham sonuçlar ve filtrelenmiş sonuçlar aynı")

    if "category_filtered" in results and len(results["category_filtered"]) == 0:
        problems.append("Kategori filtrelemesi tüm belgeleri eledi")

    if problems:
        print("\n⚠️ Tespit edilen sorunlar:")
        for problem in problems:
            print(f"  - {problem}")

def run_analysis(queries=None, output_dir=None, top_k=5):
    """Sistem analizi çalıştırır"""
    if queries is None:
        queries = DEFAULT_QUERIES

    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"similarity_analysis_{timestamp}.json")

    conn = connect_to_database()
    model = get_vector_model()

    if not conn or not model:
        print("❌ Veritabanı veya model bağlantısı kurulamadı.")
        return

    categories = get_document_categories(conn)
    all_results = {}
    for query in queries:
        result = analyze_raw_results(query, conn, model, categories, top_k)
        all_results[query] = result

    overall_accuracy = (sum(r.get("stats", {}).get("accuracy", 0) for r in all_results.values()) /
                        len(all_results)) if all_results else 0
    all_issues = []
    for result in all_results.values():
        all_issues.extend(result.get("issues", []))

    full_results = {
        "timestamp": timestamp,
        "queries": list(all_results.keys()),
        "results": all_results,
        "overall_stats": {
            "accuracy": overall_accuracy,
            "total_issues": len(all_issues)
        },
        "issues": all_issues
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Analiz sonuçları kaydedildi: {output_file}")
    print(f"📊 Genel doğruluk: {overall_accuracy:.2%}")
    print(f"⚠️ Tespit edilen sorun sayısı: {len(all_issues)}")

    if all_issues:
        print("\n⚠️ Tespit edilen sorunlar:")
        issue_types = {}
        for issue in all_issues:
            issue_type = issue["type"]
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {issue_type}: {count} kez")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="RAG benzerlik analiz aracı")
    parser.add_argument("--query", type=str, help="Tek bir sorgu için analiz yap")
    parser.add_argument("--file", type=str, help="Sorguları içeren dosya")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_DIR, help="Çıktı dizini")
    parser.add_argument("--top-k", type=int, default=5, help="Analiz edilecek sonuç sayısı")
    args = parser.parse_args()

    queries = DEFAULT_QUERIES
    if args.query:
        queries = [args.query]
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                queries = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"❌ Dosya okuma hatası: {e}")
            return

    run_analysis(queries, args.output, args.top_k)

if __name__ == "__main__":
    main()
