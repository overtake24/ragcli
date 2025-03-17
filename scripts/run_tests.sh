#!/bin/bash
# Test çalıştırma scripti (Conda uyumlu versiyon)

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}RAGCLI test senaryoları başlatılıyor...${NC}"

# Conda ortamını etkinleştir
eval "$(conda shell.bash hook 2>/dev/null || echo 'echo "Conda bulunamadı."')"
if conda info --envs 2>/dev/null | grep -q "ragcli_env"; then
    conda activate ragcli_env
else
    echo -e "${RED}ragcli_env conda ortamı bulunamadı.${NC}"
    echo -e "${YELLOW}Lütfen önce kurulum scriptini çalıştırın:${NC}"
    echo -e "${GREEN}bash scripts/setup_env.sh${NC}"
    exit 1
fi

# PostgreSQL servisini kontrol et
if ! systemctl is-active --quiet postgresql; then
    echo -e "${RED}PostgreSQL servisi çalışmıyor. Lütfen başlatın:${NC}"
    echo -e "${YELLOW}sudo systemctl start postgresql${NC}"
    exit 1
fi

# Ollama servisini kontrol et
if ! pgrep -x "ollama" > /dev/null; then
    echo -e "${YELLOW}Ollama servisi başlatılıyor...${NC}"
    ollama serve &
    sleep 2

    if ! pgrep -x "ollama" > /dev/null; then
        echo -e "${RED}Ollama servisi başlatılamadı. Lütfen manuel olarak başlatın:${NC}"
        echo -e "${YELLOW}ollama serve${NC}"
        exit 1
    fi
fi

# Veritabanı durumunu test et
echo -e "${YELLOW}Veritabanı bağlantısı test ediliyor...${NC}"
if ! psql -U raguser -h localhost -d ragdb -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}PostgreSQL bağlantısı başarısız. Lütfen veritabanının kurulu olduğundan emin olun:${NC}"
    echo -e "${YELLOW}bash scripts/setup_db.sh${NC}"
    exit 1
fi

# Test klasörü oluştur
echo -e "${YELLOW}Test verileri oluşturuluyor...${NC}"
rm -rf test_data
mkdir -p test_data

# Test dökümanları oluştur
cat > test_data/rag_info.txt << EOL
RAG (Retrieval-Augmented Generation) sistemleri, LLM'leri harici verilerle zenginleştiren sistemlerdir.
Kullanıcı sorguları önce vektör veritabanında aranır ve ilgili belgeler bulunur.
Ardından LLM, bulunan belgeleri kullanarak daha doğru ve bilgi içeren yanıtlar üretir.
RAG sistemlerinin en büyük avantajı, hallüsinasyon sorununu azaltmasıdır.
EOL

cat > test_data/vector_db.txt << EOL
Vektör veritabanları, yüksek boyutlu vektörleri ve benzerlik aramalarını destekleyen özel veritabanlarıdır.
pgvector, PostgreSQL için bir uzantıdır ve vektör benzerlik aramalarını destekler.
Embedding vektörleri, metin veya diğer verilerin sayısal temsilini oluşturur.
Vektör uzaklıkları, kosinüs benzerliği veya öklit mesafesi ile hesaplanabilir.
EOL

# Veritabanını başlat
echo -e "${YELLOW}Veritabanı başlatılıyor...${NC}"
python cli.py init

if [ $? -ne 0 ]; then
    echo -e "${RED}Veritabanı başlatılamadı. Hata mesajlarını kontrol edin.${NC}"
    exit 1
else
    echo -e "${GREEN}Veritabanı başarıyla başlatıldı.${NC}"
fi

# Test verilerini indeksle
echo -e "${YELLOW}Test verileri indeksleniyor...${NC}"
python cli.py index test_data

if [ $? -ne 0 ]; then
    echo -e "${RED}Test verileri indekslenemedi. Hata mesajlarını kontrol edin.${NC}"
    exit 1
else
    echo -e "${GREEN}Test verileri başarıyla indekslendi.${NC}"
fi

# Sorgu testi
echo -e "${YELLOW}Temel sorgu testi yapılıyor...${NC}"
python cli.py ask "RAG nedir?"

if [ $? -ne 0 ]; then
    echo -e "${RED}Sorgu testi başarısız oldu. Hata mesajlarını kontrol edin.${NC}"
    exit 1
else
    echo -e "${GREEN}Sorgu testi başarıyla tamamlandı.${NC}"
fi

# Şablon testi
echo -e "${YELLOW}Şablon kullanımı testi yapılıyor...${NC}"
python cli.py ask "Vektör veritabanları nedir?" --template summary

if [ $? -ne 0 ]; then
    echo -e "${RED}Şablon testi başarısız oldu. Hata mesajlarını kontrol edin.${NC}"
    exit 1
else
    echo -e "${GREEN}Şablon testi başarıyla tamamlandı.${NC}"
fi

# API servisi testi
echo -e "${YELLOW}API servisi testi yapılıyor (10 saniye çalışacak)...${NC}"
python cli.py serve --port 8000 &
PID=$!
sleep 5

# API sorgu testi
echo -e "${YELLOW}API sorgu testi yapılıyor...${NC}"
curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG nedir?"}'

if [ $? -ne 0 ]; then
    echo -e "${RED}API sorgu testi başarısız oldu.${NC}"
else
    echo -e "${GREEN}API sorgu testi başarıyla tamamlandı.${NC}"
fi

# API'yi sonlandır
echo -e "${YELLOW}API servisi sonlandırılıyor...${NC}"
kill $PID 2>/dev/null

# Temizlik
echo -e "${YELLOW}Test verileri temizleniyor...${NC}"
rm -rf test_data

echo -e "${GREEN}Tüm testler başarıyla tamamlandı.${NC}"