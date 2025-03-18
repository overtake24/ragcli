#!/bin/bash
# full_reset_test.sh
# Bu script, veritabanını tamamen sıfırlayarak:
# 1. Veritabanını sıfırlar (reset)
# 2. Yeniden oluşturur (cli.py init)
# 3. Test verilerini indeksler (cli.py index test_data)
# 4. Fix işlemini uygular (check_consistency.py --fix)
# 5. Tutarlılık testlerini çalıştırır (test_db_consistency.py --all)
# 6. Örnek test sorgusu çalıştırır (check_consistency.py --query "test")
#
# Lütfen bu scripti çalıştırmadan önce veritabanı yedeklemenizi unutmayın!

set -e  # Hata durumunda script durur

echo "=== Full Reset Test Sequence Başlatılıyor ==="

echo "Adım 1: Veritabanı sıfırlanıyor..."
echo "e" | python check_consistency.py --reset

echo "Adım 2: Veritabanı yeniden kuruluyor (cli.py init)..."
python cli.py init

echo "Adım 3: Belgeler indeksleniyor (cli.py index test_data)..."
python cli.py index test_data

echo "Adım 4: Fix işlemi uygulanıyor (check_consistency.py --fix)..."
python check_consistency.py --fix

echo "Adım 5: Tutarlılık testi çalıştırılıyor (test_db_consistency.py --all)..."
python test_db_consistency.py --all

echo "Adım 6: Test sorgusu çalıştırılıyor (check_consistency.py --query \"test\")..."
python check_consistency.py --query "test"

echo "=== Full Reset Test Sequence Başarıyla Tamamlandı ==="
