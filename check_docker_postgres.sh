#!/bin/bash
# Docker PostgreSQL Konteynerini Kontrol Et

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Docker PostgreSQL konteyner bilgileri kontrol ediliyor...${NC}"

# Docker çalışıyor mu kontrol et
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker bulunamadı. Lütfen Docker'ı yükleyin.${NC}"
    exit 1
fi

# Docker servisinin çalışıp çalışmadığını kontrol et
if ! docker info &> /dev/null; then
    echo -e "${RED}Docker servisi çalışmıyor. Docker servisini başlatın:${NC}"
    echo -e "sudo systemctl start docker"
    exit 1
fi

# Konteyner var mı kontrol et
if ! docker ps -a | grep -q postgres-ragcli; then
    echo -e "${RED}postgres-ragcli konteyneri bulunamadı.${NC}"
    echo -e "Mevcut PostgreSQL konteynerleri:"
    docker ps -a | grep postgres
    exit 1
fi

# Konteyner çalışıyor mu kontrol et
if ! docker ps | grep -q postgres-ragcli; then
    echo -e "${YELLOW}postgres-ragcli konteyneri çalışmıyor, başlatılıyor...${NC}"
    docker start postgres-ragcli
    sleep 2

    if ! docker ps | grep -q postgres-ragcli; then
        echo -e "${RED}postgres-ragcli konteyneri başlatılamadı.${NC}"
        exit 1
    fi
fi

# Konteyner bilgilerini al
echo -e "${GREEN}postgres-ragcli konteyneri çalışıyor.${NC}"

# Konteyner ortam değişkenlerini al
echo -e "\n${YELLOW}Konteyner ortam değişkenleri:${NC}"
docker exec postgres-ragcli env | grep POSTGRES

# Konteyner içindeki veritabanlarını listele
echo -e "\n${YELLOW}Veritabanları:${NC}"
docker exec postgres-ragcli psql -U postgres -c "\l"

# PostgreSQL kullanıcılarını listele
echo -e "\n${YELLOW}PostgreSQL kullanıcıları:${NC}"
docker exec postgres-ragcli psql -U postgres -c "\du"

# Bağlantı bilgilerini göster
echo -e "\n${YELLOW}Bağlantı bilgileri:${NC}"
echo -e "Host: localhost"
echo -e "Port: 5432"
echo -e "PostgreSQL Docker Konteyner ID: $(docker ps -q -f name=postgres-ragcli)"

# Docker port yönlendirmeyi kontrol et
echo -e "\n${YELLOW}Port yönlendirme:${NC}"
docker port postgres-ragcli

echo -e "\n${GREEN}PostgreSQL veritabanı bağlantı bilgileri:${NC}"
echo -e "postgresql://postgres:şifre@localhost:5432/postgres"
echo -e "postgresql://raguser:şifre@localhost:5432/ragdb"

echo -e "\nBu bilgileri blog_to_rag.py dosyasındaki BLOG_DB_CONNECTION değişkeninde kullanın."