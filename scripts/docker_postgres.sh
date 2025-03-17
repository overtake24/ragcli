#!/bin/bash
# Docker üzerinde PostgreSQL ve pgvector kurulum scripti

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Docker üzerinde PostgreSQL ve pgvector kurulumu başlatılıyor...${NC}"

# Docker'ın kurulu olduğunu kontrol et
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker kurulu değil. Lütfen Docker'ı kurun:${NC}"
    echo -e "${YELLOW}https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Docker'ın çalıştığını kontrol et
if ! docker info &> /dev/null; then
    echo -e "${RED}Docker çalışmıyor. Lütfen Docker'ı başlatın:${NC}"
    echo -e "${YELLOW}sudo systemctl start docker${NC}"
    echo -e "${YELLOW}veya${NC}"
    echo -e "${YELLOW}sudo service docker start${NC}"
    exit 1
fi

# PostgreSQL konteynerini kontrol et
if docker ps -a | grep -q postgres-ragcli; then
    echo -e "${YELLOW}Mevcut postgres-ragcli konteynerini kaldırıyorum...${NC}"
    docker stop postgres-ragcli &> /dev/null
    docker rm postgres-ragcli &> /dev/null
fi

# PostgreSQL + pgvector konteyneri çalıştır
echo -e "${YELLOW}PostgreSQL + pgvector konteyneri başlatılıyor...${NC}"
docker run --name postgres-ragcli \
    -e POSTGRES_USER=raguser \
    -e POSTGRES_PASSWORD=ragpassword \
    -e POSTGRES_DB=ragdb \
    -p 5432:5432 \
    -d ankane/pgvector

# Konteyner başlatma durumunu kontrol et
if ! docker ps | grep -q postgres-ragcli; then
    echo -e "${RED}PostgreSQL konteynerı başlatılamadı.${NC}"
    exit 1
fi

# pgvector uzantısını kur
echo -e "${YELLOW}pgvector uzantısı kuruluyor...${NC}"
sleep 5  # Veritabanının başlaması için biraz bekle
docker exec postgres-ragcli psql -U raguser -c "CREATE EXTENSION IF NOT EXISTS vector;" ragdb

# Bağlantıyı test et
echo -e "${YELLOW}Bağlantı testi yapılıyor...${NC}"
if docker exec postgres-ragcli psql -U raguser -c "SELECT version();" ragdb > /dev/null 2>&1; then
    echo -e "${GREEN}PostgreSQL ve pgvector kurulumu başarıyla tamamlandı.${NC}"
else
    echo -e "${RED}Bağlantı testi başarısız. Docker konteynerine bağlanılamıyor.${NC}"
    exit 1
fi

# Bağlantı bilgilerini güncelle
cat > app/config.py << EOL
# app/config.py
"""
Konfigürasyon ayarları.
"""
import os

# Temel dizinler
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# Şablon dosyaları
MODEL_SCHEMA_FILE = os.path.join(TEMPLATE_DIR, "models.json")
PROMPT_TEMPLATE_FILE = os.path.join(TEMPLATE_DIR, "prompts.json")

# Veritabanı ayarları (Docker)
DB_HOST = os.getenv("RAGCLI_DB_HOST", "localhost")
DB_PORT = os.getenv("RAGCLI_DB_PORT", "5432")
DB_NAME = os.getenv("RAGCLI_DB_NAME", "ragdb")
DB_USER = os.getenv("RAGCLI_DB_USER", "raguser")
DB_PASS = os.getenv("RAGCLI_DB_PASS", "ragpassword")

DB_CONNECTION = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
COLLECTION_NAME = "document_chunks"

# Model ayarları
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "llama2"
EOL

echo -e "${GREEN}Veritabanı bağlantı bilgileri:${NC}"
echo "Host: localhost"
echo "Port: 5432"
echo "Database: ragdb"
echo "User: raguser"
echo "Password: ragpassword"

echo -e "${YELLOW}NOT: Sistemi yeniden başlattığınızda Docker konteynerini yeniden başlatmanız gerekebilir:${NC}"
echo -e "${GREEN}docker start postgres-ragcli${NC}"