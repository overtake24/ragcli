#!/bin/bash
# Test script to verify the categorizer fix

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Kategorileme sistemi düzeltme testi başlatılıyor...${NC}"

# Import düzeltmesini uygula
echo -e "${YELLOW}1. app/llm.py dosyasında eksik import kontrol ediliyor...${NC}"
if ! grep -q "from app.categorizer import detect_query_category, detect_document_category" app/llm.py; then
    echo -e "${RED}Eksik import tespit edildi, ekleniyor...${NC}"
    # En üstteki import bloğunun sonuna ekle
    sed -i '/^import/,/^[^import]/ {
    /^[^import]/i from app.categorizer import detect_query_category, detect_document_category, filter_documents_by_category
    }' app/llm.py
    echo -e "${GREEN}Import eklendi!${NC}"
else
    echo -e "${GREEN}Import zaten mevcut.${NC}"
fi

# detect_document_category fonksiyonunu kontrol et ve ekle
echo -e "${YELLOW}2. app/categorizer.py dosyasında detect_document_category fonksiyonu kontrol ediliyor...${NC}"
if ! grep -q "def detect_document_category" app/categorizer.py; then
    echo -e "${RED}detect_document_category fonksiyonu bulunamadı, ekleniyor...${NC}"
    cat >> app/categorizer.py << 'EOL'

def detect_document_category(content):
    """
    İçerik metnine göre belgenin kategorisini tespit eder
    """
    content_lower = content.lower()

    # Film/dizi kategorisi
    film_keywords = ["film", "movie", "sinema", "cinema", "yönetmen", "director",
                     "oyuncu", "actor", "imdb", "cast", "inception"]

    # Kitap kategorisi
    book_keywords = ["kitap", "book", "yazar", "author", "sayfa", "page",
                     "roman", "novel", "yüzük", "lord of rings", "tolkien"]

    # Kişi/biyografi kategorisi
    person_keywords = ["doğum", "birth", "ölüm", "death", "hayat", "life",
                       "biyografi", "biography", "marie curie", "meslek", "occupation"]

    # Kategori belirle
    film_score = sum(1 for word in film_keywords if word in content_lower)
    book_score = sum(1 for word in book_keywords if word in content_lower)
    person_score = sum(1 for word in person_keywords if word in content_lower)

    # En yüksek skora sahip kategoriyi döndür
    if film_score > book_score and film_score > person_score:
        return "film"
    elif book_score > film_score and book_score > person_score:
        return "book"
    elif person_score > film_score and person_score > book_score:
        return "person"

    # Belirsizse "other" döndür
    return "other"
EOL
    echo -e "${GREEN}Fonksiyon eklendi!${NC}"
else
    echo -e "${GREEN}Fonksiyon zaten mevcut.${NC}"
fi

# Test sorgusu çalıştır
echo -e "\n${YELLOW}3. Test sorgusu yapılıyor (Marie Curie)...${NC}"
python cli.py ask "Marie Curie kimdir" --template person_query --model PersonInfo > test_output.log 2>&1

# Hata kontrolü
if grep -q "name 'detect_document_category' is not defined" test_output.log; then
    echo -e "${RED}Hata devam ediyor. Lütfen test_output.log dosyasını kontrol edin.${NC}"
else
    echo -e "${GREEN}Sorgu başarıyla çalıştı! Hata giderildi.${NC}"
    # Sonucu göster
    grep -A 20 "📝 CEVAP" test_output.log
fi

echo -e "\n${GREEN}Test tamamlandı! Daha fazla ayrıntı için test_output.log dosyasını kontrol edin.${NC}"