#!/bin/bash
# Test verilerini yükleme ve test etme scripti (iyileştirilmiş versiyon)

# Renk tanımlamaları
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Test Verilerini Yükleme ve Test Etme${NC}"
echo "======================================"

# Test dizinlerini kontrol et ve oluştur
for dir in "test_data/films" "test_data/books" "test_data/people"; do
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}$dir dizini oluşturuluyor...${NC}"
        mkdir -p "$dir"
    fi
done

# Test verilerini oluştur (eğer yoksa)
if [ ! -f "test_data/films/inception.txt" ]; then
    echo -e "${YELLOW}Film test verisi oluşturuluyor...${NC}"
    cat > test_data/films/inception.txt << 'EOL'
# Inception (2010)

## Özet
Dom Cobb (Leonardo DiCaprio) çok yetenekli bir hırsızdır. Uzmanlık alanı, zihnin en savunmasız olduğu rüya görme anında, bilinçaltının derinliklerindeki değerli sırları çekip çıkarmak ve onları çalmaktır. Cobb'un bu nadir mahareti, onu kurumsal casusluğun tehlikeli yeni dünyasında çok aranan bir oyuncu yapmıştır. Ancak aynı zamanda onu uluslararası bir kaçak yapmış ve sevdiği her şeye mal olmuştur. Cobb'a içinde bulunduğu durumdan kurtulmasını sağlayacak bir fırsat sunulur. Ona hayatını geri verebilecek son bir iş; inception. Kusursuz suçun tam tersine, Cobb ve ekibindeki uzmanların görevi, bir fikri çalmak değil onu yerleştirmektir. Eğer başarılı olurlarsa, mükemmel suç bu olacaktır.

## Oyuncular
- Leonardo DiCaprio (Dom Cobb)
- Joseph Gordon-Levitt (Arthur)
- Ellen Page (Ariadne)
- Tom Hardy (Eames)
- Ken Watanabe (Saito)
- Dileep Rao (Yusuf)
- Cillian Murphy (Robert Fischer)
- Tom Berenger (Peter Browning)
- Marion Cotillard (Mal Cobb)
- Michael Caine (Miles)

## Yönetmen
Christopher Nolan

## Türler
Aksiyon, Bilim Kurgu, Gerilim, Macera

## IMDb Puanı
8.8/10
EOL
fi

if [ ! -f "test_data/books/lord_of_rings.txt" ]; then
    echo -e "${YELLOW}Kitap test verisi oluşturuluyor...${NC}"
    cat > test_data/books/lord_of_rings.txt << 'EOL'
# Yüzüklerin Efendisi: Yüzük Kardeşliği (1954)

## Yazar
J.R.R. Tolkien

## Özet
Yüzüklerin Efendisi, Orta Dünya olarak adlandırılan hayali bir dünyada geçen epik bir fantastik romandır. Hikaye, Büyük Yüzük olarak da bilinen Tek Yüzük'ün yok edilmesi etrafında şekillenir. Bu güçlü yüzük, karanlık lord Sauron tarafından yaratılmıştır ve diğer tüm Güç Yüzüklerini kontrol etme yeteneğine sahiptir. Genç bir Hobbit olan Frodo Baggins, beklenmedik bir şekilde bu tehlikeli yüzüğün sahibi olur ve onu yok etmek için tehlikeli bir yolculuğa çıkar. Frodo'ya bu zorlu görevde arkadaşları Sam, Merry ve Pippin ile birlikte Gandalf, Aragorn, Legolas, Gimli ve Boromir de eşlik eder. Bu grup, "Yüzük Kardeşliği" olarak bilinir. Yolculuk sırasında, grup üyeleri çeşitli zorluklarla ve tehlikelerle karşılaşır, kendi içlerindeki zayıflıklarla mücadele eder ve Orta Dünya'nın farklı ırklarıyla etkileşime girerler.

## Sayfa Sayısı
423

## Tür
Fantastik Kurgu, Epik Fantazi, Macera

## Yayın Tarihi
29 Temmuz 1954

## Goodreads Puanı
4.36/5
EOL
fi

if [ ! -f "test_data/people/marie_curie.txt" ]; then
    echo -e "${YELLOW}Kişi test verisi oluşturuluyor...${NC}"
    cat > test_data/people/marie_curie.txt << 'EOL'
# Marie Curie

## Doğum
7 Kasım 1867, Varşova, Polonya

## Ölüm
4 Temmuz 1934, Passy, Fransa

## Uyruk
Polonya, Fransa

## Meslek
Fizikçi, Kimyager, Bilim İnsanı, Profesör

## Biyografi
Marie Curie (7 Kasım 1867 - 4 Temmuz 1934), doğum adıyla Maria Salomea Skłodowska, Polonyalı ve naturalize Fransız fizikçi ve kimyagerdir. Radyoaktivite alanında çığır açan araştırmalar yapmış, polonyum ve radyum elementlerini keşfetmiştir. İki farklı bilim dalında (fizik ve kimya) Nobel Ödülü kazanan ilk kişi, Nobel kazanan ilk kadın ve birden fazla Nobel Ödülü alan ilk kişidir. Sorbonne Üniversitesi'nde profesörlük yapan ilk kadındır. Curie, bilim alanında cinsiyete dayalı önyargılara karşı mücadele etmiş ve dünyanın önde gelen bilim insanlarından biri olmayı başarmıştır. Radyoaktiviteyle ilgili çalışmaları sırasında maruz kaldığı radyasyon nedeniyle aplastik anemi hastalığına yakalanarak 66 yaşında hayatını kaybetmiştir.

## Önemli Çalışmalar
- Polonyum ve Radyum Elementlerinin Keşfi
- Radyoaktivite Üzerine Araştırmalar
- X-Işınları ve Tıpta Uygulama Alanları
- Piezoelektrik Kuramı Çalışmaları
- Radyum İzolasyonu Çalışmaları

## Ödüller
- 1903 Nobel Fizik Ödülü (Henri Becquerel ve Pierre Curie ile paylaşım)
- 1911 Nobel Kimya Ödülü
- Davy Madalyası (1903)
- Matteucci Madalyası (1904)
- Copley Madalyası (1903)
- Elliott Cresson Madalyası (1909)
EOL
fi

# Gerekli bağımlılıkları kontrol et
python -c "from sentence_transformers import SentenceTransformer; print('SentenceTransformer OK')" || {
    echo -e "${RED}SentenceTransformer modülü yüklenemedi. İlgili bağımlılıkları yüklemeyi deneyin:${NC}"
    echo -e "${YELLOW}pip install sentence-transformers${NC}"
    exit 1
}

# Embedding modelini kontrol et (opsiyonel ama faydalı)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); print('Model yükleme başarılı')" || {
    echo -e "${RED}Embedding modeli yüklenirken hata oluştu.${NC}"
    echo -e "${YELLOW}pip install --upgrade sentence-transformers${NC}"
    echo -e "${YELLOW}pip install --upgrade torch${NC}"
    exit 1
}

# 1. Veritabanı durumunu kontrol et
echo -e "\n${BLUE}Veritabanı durumu kontrol ediliyor...${NC}"
python cli.py status

# 2. Veritabanını başlat (eğer gerekiyorsa)
echo -e "\n${BLUE}Veritabanı başlatılıyor...${NC}"
python cli.py init

# 3. Test verilerini yükle
echo -e "\n${BLUE}Test verileri yükleniyor...${NC}"

echo -e "${YELLOW}1. Film verilerini yükleme${NC}"
python cli.py index test_data/films

echo -e "\n${YELLOW}2. Kitap verilerini yükleme${NC}"
python cli.py index test_data/books

echo -e "\n${YELLOW}3. Kişi verilerini yükleme${NC}"
python cli.py index test_data/people

# 4. Veritabanı durumunu tekrar kontrol et
echo -e "\n${BLUE}Yükleme sonrası veritabanı durumu kontrol ediliyor...${NC}"
python cli.py status

# 5. Veritabanındaki belgeleri daha detaylı kontrol et
echo -e "\n${BLUE}Veritabanındaki belgeler kontrol ediliyor...${NC}"
PGPASSWORD=ragpassword psql -h localhost -U raguser -d ragdb -c "SELECT document_id, title, LEFT(content, 50) AS preview FROM document_chunks ORDER BY id DESC LIMIT 10;"

# 6. Test sorguları
echo -e "\n${GREEN}Test sorguları yapılıyor...${NC}"

# Basit sorgu - bu sorgu var olan İskandinav verilerini kullanır
echo -e "\n${BLUE}0. Basit Sorgu (İskandinav Ülkeleri)${NC}"
echo "============================================"
python cli.py ask "İskandinav ülkeleri hangileridir?"

# Film sorgusu
echo -e "\n${BLUE}1. Film Sorgusu (Inception)${NC}"
echo "============================================"
python cli.py ask "Inception filmi hakkında bilgi ver" --template film_query --model FilmInfo

# Kitap sorgusu
echo -e "\n${BLUE}2. Kitap Sorgusu (Yüzüklerin Efendisi)${NC}"
echo "=============================================="
python cli.py ask "Yüzüklerin Efendisi kitabı hakkında bilgi ver" --template book_query --model BookInfo

# Kişi sorgusu
echo -e "\n${BLUE}3. Kişi Sorgusu (Marie Curie)${NC}"
echo "========================================="
python cli.py ask "Marie Curie kimdir?" --template person_query --model PersonInfo

echo -e "\n${GREEN}Test tamamlandı!${NC}"