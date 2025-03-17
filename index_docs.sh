#!/bin/bash
# index_docs.sh - Belgeleri kolayca RAG sistemine ekleyin

# Renk tanımlamaları
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Örnek belge oluştur
mkdir -p test_data

echo -e "${YELLOW}Örnek belgeler oluşturuluyor...${NC}"

# RAG hakkında belge
cat > test_data/rag_info.txt << EOL
# RAG Sistemleri

RAG (Retrieval-Augmented Generation) sistemleri, LLM'leri harici verilerle zenginleştiren sistemlerdir.
Kullanıcı sorguları önce vektör veritabanında aranır ve ilgili belgeler bulunur.
Ardından LLM, bulunan belgeleri kullanarak daha doğru ve bilgi içeren yanıtlar üretir.
RAG sistemlerinin en büyük avantajı, hallüsinasyon sorununu azaltmasıdır.
EOL

# Vektör veritabanları hakkında belge
cat > test_data/vector_db.txt << EOL
# Vektör Veritabanları

Vektör veritabanları, yüksek boyutlu vektörleri ve benzerlik aramalarını destekleyen özel veritabanlarıdır.
pgvector, PostgreSQL için bir uzantıdır ve vektör benzerlik aramalarını destekler.
Embedding vektörleri, metin veya diğer verilerin sayısal temsilini oluşturur.
Vektör uzaklıkları, kosinüs benzerliği veya öklit mesafesi ile hesaplanabilir.
EOL

# LLM modelleri hakkında belge
cat > test_data/llm_models.txt << EOL
# LLM Modelleri

Büyük dil modelleri (LLM), milyarlarca parametreye sahip derin öğrenme modelleridir.
Transformer mimarisi üzerine kurulu olan bu modeller, doğal dil işleme görevlerinde üstün başarı gösterirler.
Gemma, Llama, GPT gibi farklı model aileleri bulunmaktadır.
Her bir model farklı boyutlarda ve farklı güçte gelmektedir.
EOL

echo -e "${GREEN}Belgeler oluşturuldu. Şimdi indeksleniyor...${NC}"

# Belgeleri indeksle
python cli.py index test_data

echo -e "${GREEN}Belgeler başarıyla indekslendi!${NC}"
echo -e "${YELLOW}Test sorgusu yapabilirsiniz:${NC}"
echo -e "python cli.py ask \"RAG nedir?\""
echo -e "python cli.py ask \"Vektör veritabanları ne işe yarar?\" --template academic"