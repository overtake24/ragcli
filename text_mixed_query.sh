#!/bin/bash
# Karışık içerik sorgu testi - Tek bir sorgu ile farklı türde veriler getirilmesi

# Renk tanımlamaları
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Karışık İçerik Sorgu Testi${NC}"
echo "============================="

# Önce verilerin yüklendiğinden emin ol
if [ ! -f "test_data/films/inception.txt" ] || [ ! -f "test_data/books/lord_of_rings.txt" ] || [ ! -f "test_data/people/marie_curie.txt" ]; then
    echo -e "${RED}Eksik test verileri tespit edildi. Önce 'index_and_test.sh' betiğini çalıştırın.${NC}"
    exit 1
fi

# Test sorguları

# 1. Açık uçlu sorgu
echo -e "${BLUE}1. Açık Uçlu Sorgu (Genel Bilgi)${NC}"
echo "========================================="
python cli.py ask "Elimizdeki belgeler hakkında ne bilgiler var? Hepsinden kısaca bahseder misin?"

# 2. Spesifik olmayan film sorgusu
echo -e "\n${BLUE}2. Spesifik Olmayan Film Sorgusu${NC}"
echo "====================================="
python cli.py ask "Veritabanımızda hangi filmler var?"

# 3. İki farklı veri türünü birleştiren sorgu
echo -e "\n${BLUE}3. İki Farklı Veri Türünü Birleştiren Sorgu${NC}"
echo "================================================="
python cli.py ask "Yüzüklerin Efendisi kitabı ve Inception filmi arasındaki benzerlikler nelerdir?"

# 4. Yapılandırılmış veri - Tüm filmleri ve kitapları listele
echo -e "\n${BLUE}4. Yapılandırılmış Veri - Karışık İçerik${NC}"
echo "==========================================="
python cli.py ask "Veritabanımızdaki tüm kitapları ve filmleri listele" --template structured_data --model ContentSummary

# 5. Film hakkında teknik detay sorgusu
echo -e "\n${BLUE}5. Film Teknik Detay Sorgusu${NC}"
echo "=================================="
python cli.py ask "Inception filminin teknik başarıları nelerdir?" --template film_query --model FilmInfo

# 6. Karşılaştırmalı sorgu
echo -e "\n${BLUE}6. Karşılaştırmalı Sorgu${NC}"
echo "============================="
python cli.py ask "Inception filmindeki ve Yüzüklerin Efendisi kitabındaki ana karakterleri karşılaştır"

echo -e "\n${GREEN}Test tamamlandı!${NC}"
echo -e "\n${YELLOW}Not:${NC} Karışık veri türleri üzerindeki sorgular, sistemin verileri birlikte yorumlama yeteneğini test eder."