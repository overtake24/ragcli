#!/usr/bin/env python
"""
Tüm RAG testlerini çalıştıran ana script.
"""
import argparse
import importlib
import os
import sys
import time

# Test modülleri
TEST_MODULES = [
    "db_test",
    "embedding_test",
    "vector_search_test"
]


def run_test(module_name, args):
    """Belirtilen test modülünü çalıştırır."""
    print(f"\n{'=' * 80}")
    print(f"🔍 {module_name} testi çalıştırılıyor...")
    print(f"{'=' * 80}\n")

    # Ortak argümanları komut satırı parametrelerine dönüştür
    argv = []

    if module_name == "db_test" and args.full_db:
        argv.extend(["--full"])
    elif module_name == "embedding_test":
        if args.multilingual:
            argv.extend(["--multilingual"])
        if args.query:
            argv.extend(["--text", args.query])
    elif module_name == "vector_search_test":
        if args.query:
            argv.extend(["--query", args.query])
        if args.k:
            argv.extend(["--k", str(args.k)])
        if args.load:
            argv.extend(["--load"])

    try:
        # Orijinal sys.argv'yi yedekle
        old_argv = sys.argv
        # Modül için argümanları ayarla
        sys.argv = [module_name + '.py'] + argv

        # Modülü dinamik olarak içe aktar
        module = importlib.import_module(module_name)

        # main fonksiyonunu çağır
        if hasattr(module, "main"):
            module.main()  # Parametresiz çağrı
            print(f"\n✅ {module_name} testi tamamlandı.")
            # sys.argv'yi geri yükle
            sys.argv = old_argv
            return True
        else:
            print(f"❌ {module_name} modülünde main fonksiyonu bulunamadı.")
            # sys.argv'yi geri yükle
            sys.argv = old_argv
            return False
    except Exception as e:
        print(f"❌ {module_name} testi çalıştırılırken hata: {e}")
        # sys.argv'yi geri yükle
        sys.argv = old_argv
        return False


def main():
    parser = argparse.ArgumentParser(description="RAG Test Sistemi")
    parser.add_argument("--full", action="store_true", help="Tüm testleri çalıştır")
    parser.add_argument("--db", action="store_true", help="Veritabanı testlerini çalıştır")
    parser.add_argument("--embedding", action="store_true", help="Embedding testlerini çalıştır")
    parser.add_argument("--search", action="store_true", help="Vektör arama testlerini çalıştır")
    parser.add_argument("--full-db", action="store_true", help="Veritabanı için ayrıntılı test yap")
    parser.add_argument("--multilingual", action="store_true", help="Çok dilli embedding testi yap")
    parser.add_argument("--query", type=str, default="İskandinav ülkeleri", help="Test sorgusu")
    parser.add_argument("--k", type=int, default=3, help="Döndürülecek sonuç sayısı")
    parser.add_argument("--load", action="store_true", help="Test belgelerini yükle")
    args = parser.parse_args()

    start_time = time.time()

    # Hangi testlerin çalıştırılacağını belirle
    tests_to_run = []
    if args.full:
        tests_to_run = TEST_MODULES
    else:
        if args.db:
            tests_to_run.append("db_test")
        if args.embedding:
            tests_to_run.append("embedding_test")
        if args.search:
            tests_to_run.append("vector_search_test")

        # Hiçbir test seçilmediyse tümünü çalıştır
        if not tests_to_run:
            tests_to_run = TEST_MODULES

    # Test scriptlerini doğrula
    for module_name in tests_to_run:
        script_path = f"{module_name}.py"
        if not os.path.exists(script_path):
            print(f"⚠️ Uyarı: {script_path} dosyası bulunamadı!")

    # Testleri çalıştır
    results = {}
    for module_name in tests_to_run:
        results[module_name] = run_test(module_name, args)

    # Sonuçları özetle
    print("\n" + "=" * 80)
    print("📋 TEST SONUÇLARI")
    print("=" * 80)

    all_passed = True
    for module_name, passed in results.items():
        status = "✅ BAŞARILI" if passed else "❌ BAŞARISIZ"
        print(f"{status} - {module_name}")
        if not passed:
            all_passed = False

    elapsed_time = time.time() - start_time
    print("\n" + "-" * 80)
    print(f"⏱️ Toplam süre: {elapsed_time:.2f} saniye")
    print(f"📌 Durum: {'✅ Tüm testler başarılı' if all_passed else '❌ Bazı testler başarısız'}")
    print("=" * 80)

    # Başarısız testler varsa hata kodu döndür
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()