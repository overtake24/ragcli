#!/bin/bash
# Conda ile geliştirme ortamı kurulum scripti

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}RAGCLI geliştirme ortamı kurulumu başlatılıyor...${NC}"

# Conda komutunu aktif hale getir
if [ -f ~/anaconda3/etc/profile.d/conda.sh ]; then
    source ~/anaconda3/etc/profile.d/conda.sh
elif [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
    source ~/miniconda3/etc/profile.d/conda.sh
else
    echo -e "${YELLOW}conda.sh bulunamadı. Conda zaten aktif olduğunu varsayıyorum.${NC}"
fi

# Conda ortamının varlığını kontrol et
if conda info --envs 2>/dev/null | grep -q "ragcli_env"; then
    echo -e "${GREEN}ragcli_env conda ortamı mevcut, etkinleştiriliyor...${NC}"
    conda activate ragcli_env
else
    echo -e "${YELLOW}ragcli_env conda ortamı zaten aktif olduğunu varsayıyorum.${NC}"
fi

# Python versiyonunu kontrol et
PY_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${YELLOW}Python versiyonu: $PY_VERSION${NC}"

# pip'i güncelleyelim
echo -e "${YELLOW}pip güncelleniyor...${NC}"
pip install --upgrade pip setuptools wheel

# Bağımlılıkları kur
echo -e "${YELLOW}Bağımlılıklar yükleniyor...${NC}"
pip install langchain>=0.1.0 langchain-community>=0.0.16 langchain-core>=0.1.14 langchain-text-splitters
pip install ollama>=0.1.0 sentence-transformers>=2.2.2 psycopg2-binary>=2.9.5 pgvector>=0.2.0
pip install click>=8.1.3 fastapi>=0.95.0 uvicorn>=0.21.1 pydantic>=2.0.0

# Dizin yapısını oluştur
echo -e "${YELLOW}Proje dizin yapısı oluşturuluyor...${NC}"
mkdir -p app templates scripts tests 2>/dev/null

# __init__.py dosyalarını oluştur
touch app/__init__.py
touch tests/__init__.py

# Betik dosyalarını çalıştırılabilir yap
chmod +x cli.py
[ -f "scripts/setup_db.sh" ] && chmod +x scripts/setup_db.sh
[ -f "scripts/run_tests.sh" ] && chmod +x scripts/run_tests.sh
[ -f "scripts/docker_postgres.sh" ] && chmod +x scripts/docker_postgres.sh

# Ollama kurulumunu kontrol et ve gerekirse kur
echo -e "${YELLOW}Ollama kurulumu kontrol ediliyor...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Ollama kuruluyor...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh

    if [ $? -ne 0 ]; then
        echo -e "${RED}Ollama kurulumu başarısız oldu.${NC}"
        echo -e "${YELLOW}Lütfen Ollama'yı manuel olarak kurun: https://ollama.ai/download${NC}"
    else
        echo -e "${GREEN}Ollama başarıyla kuruldu.${NC}"
    fi
else
    echo -e "${GREEN}Ollama zaten kurulu.${NC}"
fi

# LLM modelinin varlığını kontrol et
if command -v ollama &> /dev/null; then
    echo -e "${YELLOW}LLM modeli kontrol ediliyor...${NC}"
    if ! ollama list 2>/dev/null | grep -q "llama2"; then
        echo -e "${YELLOW}llama2 modeli indiriliyor (bu işlem 5-10 dakika sürebilir)...${NC}"
        ollama pull llama2

        if [ $? -ne 0 ]; then
            echo -e "${RED}llama2 modeli indirilemedi.${NC}"
        else
            echo -e "${GREEN}llama2 modeli başarıyla indirildi.${NC}"
        fi
    else
        echo -e "${GREEN}llama2 modeli zaten kurulu.${NC}"
    fi

    # Ollama servisini başlat
    echo -e "${YELLOW}Ollama servisi başlatılıyor...${NC}"
    ollama serve &
    sleep 2

    if pgrep -x "ollama" > /dev/null; then
        echo -e "${GREEN}Ollama servisi çalışıyor.${NC}"
    else
        echo -e "${RED}Ollama servisi başlatılamadı. Lütfen manuel olarak başlatın: ollama serve${NC}"
    fi
fi

echo -e "${GREEN}Geliştirme ortamı kurulumu tamamlandı.${NC}"
echo -e "${YELLOW}Notlar:${NC}"
echo -e "1. Conda ortamını aktifleştirmek için: ${GREEN}conda activate ragcli_env${NC}"
echo -e "2. PostgreSQL için Docker kurulumu: ${GREEN}bash scripts/docker_postgres.sh${NC}"
echo -e "3. Test senaryolarını çalıştırmak için: ${GREEN}bash scripts/run_tests.sh${NC}"
echo -e "4. CLI kullanımı: ${GREEN}python cli.py [komut]${NC}"