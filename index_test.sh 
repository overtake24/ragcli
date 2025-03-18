#!/bin/bash
# Test içeriği oluşturup indeksleyen script

# Renk tanımlamaları
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Test içeriği oluşturuluyor...${NC}"

# Dizin kontrolü
mkdir -p test_data

# Basit test dosyası oluştur
cat > test_data/nordic_test.txt << 'EOL'
# Nordic Countries Travel Guide

The Nordic countries consist of Denmark, Norway, Sweden, Finland, and Iceland. These Scandinavian destinations are known for their stunning landscapes, rich history, and high quality of life.

Denmark is known for its design, cycling culture, and the colorful buildings of Copenhagen.

Norway offers dramatic fjords, mountains, and the Northern Lights (Aurora Borealis).

Sweden has beautiful archipelagos, medieval towns, and Stockholm's elegant architecture.

Finland is famous for its thousands of lakes, saunas, and the Northern Lights.

Iceland features volcanoes, geysers, hot springs, and dramatic landscapes.

The best time to visit is summer (June-August) for long days and mild weather, or winter (December-February) to see the Northern Lights.
EOL

echo -e "${GREEN}İçerik dosyası oluşturuldu: test_data/nordic_test.txt${NC}"

echo -e "${YELLOW}İçerik indeksleniyor...${NC}"
python cli.py index test_data/nordic_test.txt

echo -e "${GREEN}İndeksleme tamamlandı!${NC}"
echo ""
echo -e "${YELLOW}Test sorgusunu deneyin:${NC}"
echo "python cli.py ask \"What are the Nordic countries?\""
echo "python cli.py ask \"When is the best time to see the Northern Lights?\""