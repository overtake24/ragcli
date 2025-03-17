#!/bin/bash
# PostgreSQL ve pgvector kurulum ve yapılandırma scripti

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}PostgreSQL ve pgvector kurulumu başlatılıyor...${NC}"

# PostgreSQL kurulumu
if command -v psql >/dev/null 2>&1; then
    echo -e "${GREEN}PostgreSQL zaten kurulu.${NC}"
else
    echo -e "${YELLOW}PostgreSQL kuruluyor...${NC}"
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
    if [ $? -ne 0 ]; then
        echo -e "${RED}PostgreSQL kurulumu başarısız oldu.${NC}"
        exit 1
    fi
fi

# PostgreSQL'i başlat
echo -e "${YELLOW}PostgreSQL servisi başlatılıyor...${NC}"
sudo systemctl start postgresql
sudo systemctl enable postgresql

# PostgreSQL hizmet durumunu kontrol et
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}PostgreSQL servisi çalışıyor.${NC}"
else
    echo -e "${RED}PostgreSQL servisi başlatılamadı. Lütfen kontrol edin.${NC}"
    exit 1
fi

# PostgreSQL'in TCP/IP bağlantılarını kabul etmesini sağla
echo -e "${YELLOW}PostgreSQL konfigürasyonu yapılandırılıyor...${NC}"
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf
sudo sed -i "s/host    all             all             127.0.0.1\/32            md5/host    all             all             0.0.0.0\/0               md5/" /etc/postgresql/*/main/pg_hba.conf

# PostgreSQL'i yeniden başlat
sudo systemctl restart postgresql

# pgvector kurulumu
echo -e "${YELLOW}pgvector kurulumu başlatılıyor...${NC}"
if [ -d "pgvector" ]; then
    rm -rf pgvector
fi
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
cd ..
rm -rf pgvector

# ragdb veritabanını oluştur
echo -e "${YELLOW}Veritabanı oluşturuluyor...${NC}"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ragdb;"
sudo -u postgres psql -c "DROP USER IF EXISTS raguser;"
sudo -u postgres psql -c "CREATE DATABASE ragdb;"
sudo -u postgres psql -c "CREATE USER raguser WITH PASSWORD 'ragpassword';"
sudo -u postgres psql -c "ALTER USER raguser WITH SUPERUSER;"  # pgvector için gerekli
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;"

# pgvector uzantısını etkinleştir
echo -e "${YELLOW}pgvector uzantısı etkinleştiriliyor...${NC}"
sudo -u postgres psql -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Bağlantıyı test et
echo -e "${YELLOW}Bağlantı testi yapılıyor...${NC}"
if sudo -u postgres psql -d ragdb -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}PostgreSQL ve pgvector kurulumu başarıyla tamamlandı.${NC}"
else
    echo -e "${RED}Bağlantı testi başarısız. Lütfen PostgreSQL yapılandırmanızı kontrol edin.${NC}"
    exit 1
fi

echo -e "${GREEN}Veritabanı bağlantı bilgileri:${NC}"
echo "Host: localhost"
echo "Port: 5432"
echo "Database: ragdb"
echo "User: raguser"
echo "Password: ragpassword"