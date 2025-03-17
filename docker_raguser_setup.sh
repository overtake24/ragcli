#!/bin/bash
# RAG CLI Blog Entegrasyonu Kurulum ve Test Scripti (raguser kullanıcılı Docker)
set -e

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}RAG CLI ve Blog Entegrasyonu Kurulumu (Docker - raguser)${NC}"

# 1. Docker PostgreSQL konteynerini kontrol et
echo -e "${YELLOW}Docker PostgreSQL kontrol ediliyor...${NC}"
if ! docker ps | grep -q postgres-ragcli; then
    echo -e "${YELLOW}PostgreSQL konteyneri başlatılıyor...${NC}"
    if ! docker start postgres-ragcli; then
        echo -e "${RED}PostgreSQL konteyneri başlatılamadı.${NC}"
        exit 1
    fi
fi

# 2. Blog veritabanını oluştur (raguser kullanıcısı ile)
echo -e "${YELLOW}Blog veritabanı oluşturuluyor...${NC}"

# SQL dosyasını Docker konteynerine kopyala
echo -e "${YELLOW}SQL dosyası konteynere kopyalanıyor...${NC}"
docker cp blog_schema.sql postgres-ragcli:/tmp/blog_schema.sql

# Veritabanını oluştur (doğrudan raguser olarak)
echo -e "${YELLOW}Veritabanı oluşturuluyor...${NC}"
# Önce veritabanını düşür (varsa)
docker exec postgres-ragcli psql -U raguser -d ragdb -c "DROP DATABASE IF EXISTS blog_db;"
# Veritabanını oluştur
docker exec postgres-ragcli psql -U raguser -d ragdb -c "CREATE DATABASE blog_db;"
# Şemayı uygula
docker exec postgres-ragcli psql -U raguser -d blog_db -f /tmp/blog_schema.sql

# 3. blog_to_rag.py dosyasını güncelle
echo -e "${YELLOW}blog_to_rag.py dosyasını güncelleniyor...${NC}"
if [ -f blog_to_rag.py ]; then
    # Dosyada bağlantı bilgisini değiştir
    sed -i 's|BLOG_DB_CONNECTION = ".*"|BLOG_DB_CONNECTION = "postgresql://raguser:ragpassword@localhost:5432/blog_db"|g' blog_to_rag.py
    echo -e "${GREEN}blog_to_rag.py dosyası güncellendi.${NC}"
else
    echo -e "${RED}blog_to_rag.py dosyası bulunamadı. Lütfen dosyayı oluşturun ve bağlantı bilgisini güncelleyin.${NC}"
    echo -e "BLOG_DB_CONNECTION = \"postgresql://raguser:ragpassword@localhost:5432/blog_db\""
    exit 1
fi

# 4. RAG CLI API servisini başlat (arka planda)
echo -e "${YELLOW}RAG CLI API servisi başlatılıyor...${NC}"
python cli.py serve --port 8000 > api_logs.txt 2>&1 &
API_PID=$!
sleep 3

# API servisinin çalıştığını kontrol et
if curl -s http://localhost:8000/docs > /dev/null; then
    echo -e "${GREEN}API servisi başarıyla çalışıyor${NC}"
else
    echo -e "${RED}API servisi başlatılamadı. Lütfen api_logs.txt dosyasını kontrol edin.${NC}"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# 5. Blog veritabanını RAG'e aktar
echo -e "${YELLOW}Blog gönderileri RAG'e aktarılıyor...${NC}"
python blog_to_rag.py --force

# 6. Test sorgusu yap
echo -e "${YELLOW}Test sorgusu yapılıyor...${NC}"
echo -e "RAG sistemleri nedir? sorgusu yapılıyor:"
curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "RAG sistemleri nedir?",
    "template": "default"
  }' | python -m json.tool 2>/dev/null || echo "JSON yanıtı işlenemedi"

echo -e "\n${YELLOW}İkinci test sorgusu yapılıyor...${NC}"
echo -e "Vektör veritabanları sorgusu yapılıyor:"
curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Vektör veritabanları ne işe yarar?",
    "template": "academic"
  }' | python -m json.tool 2>/dev/null || echo "JSON yanıtı işlenemedi"

# 7. Manuel metin indeksleme testi
echo -e "\n${YELLOW}Manuel metin indeksleme testi yapılıyor...${NC}"
curl -s -X POST "http://localhost:8000/index_text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "LLM modelleri, büyük dil modelleri olarak da bilinen yapay zeka sistemleridir. Doğal dil işleme ve üretme yetenekleri sunarlar.",
    "document_id": "test_manual_doc",
    "title": "LLM Modelleri Hakkında"
  }' | python -m json.tool 2>/dev/null || echo "JSON yanıtı işlenemedi"

# 8. API servisini durdur
echo -e "\n${YELLOW}API servisi durduruluyor...${NC}"
kill $API_PID 2>/dev/null || true

echo -e "${GREEN}Kurulum ve test işlemleri başarıyla tamamlandı.${NC}"
echo -e "${YELLOW}API'yi manuel olarak başlatmak için:${NC} python cli.py serve"
echo -e "${YELLOW}Blog içeriklerini güncellemek için:${NC} python blog_to_rag.py"