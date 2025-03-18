#!/usr/bin/env python3
"""
RAG Sistemi Entegrasyon Testi

Bu script, RAG sisteminin tüm bileşenlerini test eder:
1. Veritabanı tutarlılığı
2. Vektör benzerliği
3. LLM yanıtları
4. JSON ayrıştırma

Kullanım:
  python run_integration_test.py --query "Test sorgusu"
"""
import os
import sys
import argparse
import time
import json
import warnings
from colorama import Fore, Style, init

# Colorama başlat
init(autoreset=True)

# Uyarıları gizle
warnings.filterwarnings("ignore")

# Kullanılacak test sorguları
TEST_QUERIES = {
    "film": "Inception filmi hakkında bilgi ver",
    "kitap": "Yüzüklerin Efendisi kitabı hakkında bilgi ver",
    "kişi": "Marie Curie kimdir ve ne yapmıştır",
    "genel": "İskandinav ülkeleri hangileridir"
}

# Test şablonları
TEST_TEMPLATES = ["default", "academic", "film_query", "book_query", "person_query"]

# Test modelleri
TEST_MODELS = ["DocumentResponse", "QuestionAnswer", "FilmInfo", "BookInfo", "PersonInfo"]


def print_header(title):
    """Renkli başlık yazdırır"""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}" + "=" * 80)
    print(f"{Fore.BLUE}{Style.BRIGHT} {title}")
    print(f"{Fore.BLUE}{Style.BRIGHT}" + "=" * 80)


def print_subheader(title):
    """Renkli alt başlık yazdırır"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT} {title}")
    print(f"{Fore.CYAN}{Style.BRIGHT}" + "-" * 60)


def print_success(message):
    """Başarı mesajı yazdırır"""
    print(f"{Fore.GREEN}✅ {message}")


def print_warning(message):
    """Uyarı mesajı yazdırır"""
    print(f"{Fore.YELLOW}⚠️ {message}")


def print_error(message):
    """Hata mesajı yazdırır"""
    print(f"{Fore.RED}❌ {message}")


def print_info(message):
    """Bilgi mesajı yazdırır"""
    print(f"{Fore.WHITE}ℹ️ {message}")


def test_database_consistency():
    """Veritabanı tutarlılığını test eder"""
    print_subheader("Veritabanı Tutarlılık Testi")

    try:
        # test_db_consistency.py script'ini çağır
        result = os.system("python test_db_consistency.py --all")

        if result == 0:
            print_success("Veritabanı tutarlılık testi başarılı")
            return True
        else:
            print_error("Veritabanı tutarlılık testi başarısız")
            print_warning("Düzeltme denemesi yapılıyor...")

            # Düzeltmeyi dene
            fix_result = os.system("python check_consistency.py --fix")

            if fix_result == 0:
                print_success("Veritabanı tutarlılığı düzeltildi")
                return True
            else:
                print_error("Veritabanı tutarlılığı düzeltilemedi")
                return False
    except Exception as e:
        print_error(f"Veritabanı tutarlılık testi sırasında hata: {e}")
        return False


def test_vector_similarity(query):
    """Vektör benzerliği hesaplamalarını test eder"""
    print_subheader("Vektör Benzerlik Testi")

    try:
        # test_vector_similarity.py script'ini çağır
        result = os.system(f"python test_vector_similarity.py --query \"{query}\" --all")

        if result == 0:
            print_success("Vektör benzerlik testi başarılı")
            return True
        else:
            print_error("Vektör benzerlik testi başarısız")
            return False
    except Exception as e:
        print_error(f"Vektör benzerlik testi sırasında hata: {e}")
        return False


def test_json_parser():
    """JSON ayrıştırma işlemlerini test eder"""
    print_subheader("JSON Ayrıştırma Testi")

    try:
        # test_json_parser.py script'ini çağır
        result = os.system("python test_json_parser.py")

        if result == 0:
            print_success("JSON ayrıştırma testi başarılı")
            return True
        else:
            print_error("JSON ayrıştırma testi başarısız")
            return False
    except Exception as e:
        print_error(f"JSON ayrıştırma testi sırasında hata: {e}")
        return False


def test_rag_query(query, template="default", model="DocumentResponse"):
    """RAG sorgusu test eder"""
    print_subheader(f"RAG Sorgu Testi: '{query}'")
    print_info(f"Şablon: {template}, Model: {model}")

    try:
        start_time = time.time()

        # cli.py script'ini çağır
        command = f"python cli.py ask \"{query}\" --template {template} --model {model}"
        result = os.system(command)

        elapsed_time = time.time() - start_time

        if result == 0:
            print_success(f"RAG sorgu testi başarılı (süre: {elapsed_time:.2f} saniye)")
            return True
        else:
            print_error("RAG sorgu testi başarısız")
            return False
    except Exception as e:
        print_error(f"RAG sorgu testi sırasında hata: {e}")
        return False


def test_all_categories():
    """Tüm kategori ve şablon kombinasyonlarını test eder"""
    print_subheader("Kategori ve Şablon Testleri")

    results = {}

    # Her kategori için
    for category, query in TEST_QUERIES.items():
        print_info(f"\nKategori: {category.upper()}")

        category_results = {}

        # Uygun şablon ve model seç
        if category == "film":
            template = "film_query"
            model = "FilmInfo"
        elif category == "kitap":
            template = "book_query"
            model = "BookInfo"
        elif category == "kişi":
            template = "person_query"
            model = "PersonInfo"
        else:
            template = "default"
            model = "DocumentResponse"

        # Sorguyu test et
        success = test_rag_query(query, template, model)
        category_results[f"{template}_{model}"] = "✅ Başarılı" if success else "❌ Başarısız"

        # Varsayılan şablonu da test et
        if template != "default":
            success = test_rag_query(query, "default", model)
            category_results["default_" + model] = "✅ Başarılı" if success else "❌ Başarısız"

        # Sonuçları kaydet
        results[category] = category_results

    # Özet tablosu yazdır
    print_subheader("Kategori Testleri Özeti")

    print(f"\n{'Kategori':<10} | {'Şablon+Model':<25} | {'Sonuç':<10}")
    print("-" * 50)

    for category, tests in results.items():
        for test_key, result in tests.items():
            print(f"{category:<10} | {test_key:<25} | {result:<10}")

    # Başarı oranını hesapla
    total_tests = sum(len(tests) for tests in results.values())
    success_tests = sum(sum(1 for result in tests.values() if "✅" in result) for tests in results.values())
    success_rate = (success_tests / total_tests) * 100

    print(f"\nBaşarı Oranı: {success_rate:.2f}% ({success_tests}/{total_tests})")

    return success_rate >= 80  # %80 ve üzeri başarı kabul edilebilir


def run_all_tests(query=None):
    """Tüm testleri sırayla çalıştırır"""
    print_header("RAG SİSTEMİ ENTEGRASYON TESTİ")

    if query is None:
        query = TEST_QUERIES["genel"]

    # Test sonuçlarını kaydet
    results = {}

    # 1. Veritabanı tutarlılığını test et
    results["database"] = test_database_consistency()

    # 2. Vektör benzerliğini test et
    results["vector"] = test_vector_similarity(query)

    # 3. JSON ayrıştırmayı test et
    results["json"] = test_json_parser()

    # 4. Temel RAG sorgusunu test et
    results["basic_query"] = test_rag_query(query)

    # 5. Tüm kategorileri test et
    results["all_categories"] = test_all_categories()

    # Test sonuçlarını özet tablo halinde göster
    print_header("ENTEGRASYON TESTİ SONUÇLARI")

    print(f"\n{'Test':<20} | {'Sonuç':<10}")
    print("-" * 40)

    for test_name, result in results.items():
        result_text = f"{Fore.GREEN}✅ Başarılı" if result else f"{Fore.RED}❌ Başarısız"
        print(f"{test_name:<20} | {result_text:<10}")

    # Genel başarı durumu
    success_rate = (sum(1 for result in results.values() if result) / len(results)) * 100

    print(f"\n{Fore.BLUE}{Style.BRIGHT}Genel Başarı Oranı: {success_rate:.2f}%")

    if success_rate == 100:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 TÜM TESTLER BAŞARILI! Sistem çalışır durumda.")
    elif success_rate >= 80:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️ SİSTEM KISMİ OLARAK ÇALIŞIYOR. Bazı testler başarısız oldu.")
    else:
        print(f"\n{Fore.RED}{Style.BRIGHT}❌ SİSTEM YETERLİ DÜZEYDE ÇALIŞMIYOR. Önemli testler başarısız oldu.")

    return success_rate


def main():
    parser = argparse.ArgumentParser(description="RAG Sistemi Entegrasyon Testi")
    parser.add_argument("--query", "-q", type=str, default=None,
                        help="Test sorgusu")
    parser.add_argument("--database", "-d", action="store_true",
                        help="Yalnızca veritabanı testini çalıştır")
    parser.add_argument("--vector", "-v", action="store_true",
                        help="Yalnızca vektör benzerlik testini çalıştır")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Yalnızca JSON ayrıştırma testini çalıştır")
    parser.add_argument("--basic-query", "-b", action="store_true",
                        help="Yalnızca temel sorgu testini çalıştır")
    parser.add_argument("--categories", "-c", action="store_true",
                        help="Yalnızca kategori testlerini çalıştır")

    args = parser.parse_args()

    if args.database:
        test_database_consistency()
    elif args.vector:
        test_vector_similarity(args.query or TEST_QUERIES["genel"])
    elif args.json:
        test_json_parser()
    elif args.basic_query:
        test_rag_query(args.query or TEST_QUERIES["genel"])
    elif args.categories:
        test_all_categories()
    else:
        run_all_tests(args.query)


if __name__ == "__main__":
    main()