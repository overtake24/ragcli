# RAG CLI Kurulum Rehberi

Bu rehber, RAG CLI'ı adım adım kurmanız için gereken tüm adımları içermektedir.

## Tek Komut Kurulumu

Tüm kurulum adımlarını tek bir komutla gerçekleştirmek için:

```bash
bash install.sh
```

Bu komut şunları yapacaktır:
1. Geliştirme ortamını hazırlar
2. PostgreSQL ve pgvector kurar
3. Test senaryolarını çalıştırır

## Adım Adım Kurulum

### 1. Gerekli Dizin Yapısını Oluşturma

```bash
mkdir -p ragcli
cd ragcli
mkdir -p app templates scripts tests
```

### 2. Dosyaları İndirme ve Yerleştirme

Tüm Python (.py), JSON (.json) ve Bash (.sh) dosyalarını ilgili dizinlere yerleştirin:

```bash
# Bash script dosyalarına çalıştırma izni ver
chmod +x cli.py
chmod +x scripts/setup_db.sh
chmod +x scripts/setup_env.sh
chmod +x scripts/run_tests.sh
```

### 3. Python Sanal Ortamını Oluşturma

```bash
python -m venv ragcli_env
source ragcli_env/bin/activate
```

### 4. Bağımlılıkları Yükleme

```bash
pip install -r requirements.txt
```

### 5. PostgreSQL ve pgvector Kurulumu

```bash
bash scripts/setup_db.sh
```

### 6. Ollama Yükleme ve Model İndirme

```bash
# Ollama'yı yükle
curl -fsSL https://ollama.com/install.sh | sh

# llama2 modelini indir
ollama pull llama2

# Ollama servisini başlat
ollama serve
```

### 7. RAG CLI'ı Test Etme

```bash
bash scripts/run_tests.sh
```

## Olası Sorunlar ve Çözümleri

### PostgreSQL Kurulumu Sorunları

```bash
# PostgreSQL servisini yeniden başlat
sudo systemctl restart postgresql

# PostgreSQL durumunu kontrol et
sudo systemctl status postgresql
```

### Python Bağımlılık Sorunları

```bash
# Bağımlılıkları zorla güncelle
pip install --upgrade --force-reinstall -r requirements.txt

# Temel paketleri manuel olarak kur
pip install langchain==0.1.0 langchain-community==0.0.16 langchain-core==0.1.14 langchain-text-splitters==0.0.1
pip install ollama==0.1.0 sentence-transformers==2.2.2 psycopg2-binary==2.9.5
```

### Ollama Sorunları

```bash
# Ollama'yı manuel olarak başlat
ollama serve

# Model indirme durumunu kontrol et
ollama list
```

## Başlatma ve Kullanım

### RAG CLI'ı Kullanma

```bash
# Her yeni oturumda sanal ortamı etkinleştir
source ragcli_env/bin/activate

# Veritabanını başlat
python cli.py init

# Bir belge klasörünü indeksle
python cli.py index ./belgeler

# Sorgu yap
python cli.py ask "RAG nedir?"

# API servisini başlat
python cli.py serve
```

### API Kullanımı

```bash
# Sorgu yap
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG nedir?"}'
```

## Sistem Gereksinimleri

- **İşletim Sistemi**: Linux (Ubuntu 20.04 veya üzeri önerilir)
- **Python**: 3.8 veya üzeri
- **RAM**: En az 4GB (8GB önerilir)
- **Disk**: En az 2GB boş alan
- **CPU**: 2 çekirdek veya üzeri
- **Internet**: İlk kurulum için gerekli (model ve paket indirme)

## Konfigürasyon Ayarları

RAG CLI'ın davranışını değiştirmek için `app/config.py` dosyasını düzenleyebilirsiniz:

- **Veritabanı Bağlantısı**: `DB_CONNECTION` değişkeni
- **Embedding Modeli**: `EMBEDDING_MODEL` değişkeni (varsayılan: all-MiniLM-L6-v2)
- **LLM Modeli**: `LLM_MODEL` değişkeni (varsayılan: llama2)

## Görsel Kurulum Akışı

1. Dosyaları yerleştir
2. Sanal ortamı oluştur
3. Bağımlılıkları yükle
4. PostgreSQL ve pgvector kur
5. Ollama'yı yükle ve modeli indir
6. RAG CLI'ı başlat ve test et