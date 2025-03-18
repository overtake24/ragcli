#!/bin/bash
# RAG CLI Kurulum ve Yapılandırma Scripti

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}RAG CLI Kurulum Başlatılıyor...${NC}"

# 1. Gerekli bağımlılıkları kontrol et ve kur
echo -e "${YELLOW}Bağımlılıklar kontrol ediliyor...${NC}"

# Python bağımlılıkları
pip install -q langchain langchain-community langchain-text-splitters click psycopg2-binary pgvector sentence-transformers fastapi uvicorn ollama

# Ollama kurulumunu kontrol et
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Ollama kuruluyor...${NC}"
    # Linux için kurulum
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    # macOS için kurulum
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo -e "${RED}Otomatik Ollama kurulumu bu işletim sistemi için desteklenmiyor.${NC}"
        echo -e "${YELLOW}Lütfen https://ollama.ai/download adresinden manuel olarak kurun.${NC}"
    fi
else
    echo -e "${GREEN}Ollama zaten kurulu.${NC}"
fi

# 2. LLM modelini kontrol et ve indir
echo -e "${YELLOW}LLM modeli kontrol ediliyor...${NC}"
LLM_MODEL=$(grep "LLM_MODEL" app/config.py | cut -d'"' -f2 | cut -d"'" -f2)
echo -e "Yapılandırılmış model: ${LLM_MODEL}"

if ollama list | grep -q "$LLM_MODEL"; then
    echo -e "${GREEN}$LLM_MODEL modeli zaten yüklü.${NC}"
else
    echo -e "${YELLOW}$LLM_MODEL modeli indiriliyor (bu işlem biraz zaman alabilir)...${NC}"
    ollama pull "$LLM_MODEL"
fi

# 3. Veritabanını başlat
echo -e "${YELLOW}Veritabanı başlatılıyor...${NC}"
python cli.py init

# 4. Docker kullanıyor mu kontrol et
if command -v docker &> /dev/null; then
    echo -e "${GREEN}Docker kurulu, veritabanı Docker container'ında çalıştırılabilir.${NC}"
    echo -e "${YELLOW}Docker ile PostgreSQL ve pgvector kurmak için:${NC}"
    echo -e "  bash scripts/docker_postgres.sh"
fi

# 5. Örnek içerik oluştur
echo -e "${YELLOW}Örnek test içeriği oluşturuluyor...${NC}"
mkdir -p test_data

# RAG hakkında
cat > test_data/rag_info.txt << EOL
# RAG Sistemleri

RAG (Retrieval-Augmented Generation) sistemleri, LLM'leri harici verilerle zenginleştiren sistemlerdir.
Kullanıcı sorguları önce vektör veritabanında aranır ve ilgili belgeler bulunur.
Ardından LLM, bulunan belgeleri kullanarak daha doğru ve bilgi içeren yanıtlar üretir.
RAG sistemlerinin en büyük avantajı, hallüsinasyon sorununu azaltmasıdır.
EOL

# Vektör veritabanları hakkında
cat > test_data/vector_db.txt << EOL
# Vektör Veritabanları

Vektör veritabanları, yüksek boyutlu vektörleri ve benzerlik aramalarını destekleyen özel veritabanlarıdır.
pgvector, PostgreSQL için bir uzantıdır ve vektör benzerlik aramalarını destekler.
Embedding vektörleri, metin veya diğer verilerin sayısal temsilini oluşturur.
Vektör uzaklıkları, kosinüs benzerliği veya öklit mesafesi ile hesaplanabilir.
EOL

# 6. Örnek içeriği indeksle
echo -e "${YELLOW}Örnek içerik indeksleniyor...${NC}"
python cli.py index test_data

# 7. Test sorgusu yap
echo -e "${YELLOW}Test sorgusu yapılıyor...${NC}"
python cli.py ask "RAG nedir?"

echo -e "${GREEN}Kurulum tamamlandı!${NC}"
echo -e "${YELLOW}RAG CLI'ı kullanmak için:${NC}"
echo -e "- Veritabanı bağlantısını düzenlemek için: app/config.py dosyasını düzenleyin"
echo -e "- Yeni belgeler eklemek için: python cli.py index /path/to/documents"
echo -e "- Sorgu yapmak için: python cli.py ask \"Sorgunuz?\""
echo -e "- API servisini başlatmak için: python cli.py serve"
echo -e "- Komutları görmek için: python cli.py --help"