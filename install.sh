#!/bin/bash
# RAGCLI tam kurulum scripti (Conda uyumlu versiyon)

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}RAG CLI Kurulumu Başlatılıyor...${NC}"

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

# Dizin yapısını kontrol et
mkdir -p app templates scripts tests 2>/dev/null

# __init__.py dosyasını oluştur
cat > app/__init__.py << 'EOL'
# app/__init__.py
"""
RAG CLI modülü.
"""
__version__ = "1.0.0"
__author__ = "RAGCLI Developer"
EOL

# Tüm scripti oluştur
mkdir -p scripts

# Script dosyalarını çalıştırılabilir yap
chmod +x cli.py
[ -f "scripts/setup_env.sh" ] && chmod +x scripts/setup_env.sh
[ -f "scripts/setup_db.sh" ] && chmod +x scripts/setup_db.sh
[ -f "scripts/run_tests.sh" ] && chmod +x scripts/run_tests.sh
[ -f "scripts/docker_postgres.sh" ] && chmod +x scripts/docker_postgres.sh
chmod +x install.sh

# Ortam kurulumu
echo -e "${YELLOW}Geliştirme ortamı kuruluyor...${NC}"
bash scripts/setup_env.sh

# PostgreSQL ve pgvector kurulumu (Docker ile)
echo -e "${YELLOW}PostgreSQL ve pgvector Docker üzerinde kuruluyor...${NC}"
bash scripts/docker_postgres.sh

# Basit bir test yap
echo -e "${YELLOW}Basit bir test yapılıyor...${NC}"
python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://raguser:ragpassword@localhost:5432/ragdb')
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f'${GREEN}PostgreSQL bağlantısı başarılı: {version[0]}${NC}')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'${RED}PostgreSQL bağlantı hatası: {e}${NC}')
"

echo -e "${GREEN}Kurulum tamamlandı!${NC}"
echo -e "${YELLOW}RAG CLI kullanmak için:${NC}"
echo -e "1. Her oturumda Conda ortamını etkinleştirin: ${GREEN}conda activate ragcli_env${NC}"
echo -e "2. Docker PostgreSQL başlatın: ${GREEN}docker start postgres-ragcli${NC}"
echo -e "3. CLI komutlarını çalıştırın: ${GREEN}python cli.py [komut]${NC}"
echo -e "4. Veritabanını başlatın: ${GREEN}python cli.py init${NC}"
echo -e "5. API servisini başlatmak için: ${GREEN}python cli.py serve${NC}"
echo -e "\nDetaylı bilgi için README.md dosyasını inceleyebilirsiniz."