# RAG CLI

Yerel LLM kullanarak vektör tabanlı bilgi erişimi için komut satırı arayüzü. PostgreSQL, pgvector, Ollama ve LangChain Expression Language (LCEL) kullanarak çevrimdışı çalışan bir RAG (Retrieval-Augmented Generation) sistemi.

## Hızlı Başlangıç

```bash
# 1. Proje dizininde başla
git clone <repo-url> ragcli
cd ragcli

# 2. Kurulum ve ortam hazırlık
bash scripts/setup_env.sh

# 3. Veritabanı kurulumu
bash scripts/setup_db.sh

# 4. Temel testleri çalıştır
bash scripts/run_tests.sh
```

## Detaylı Kurulum

### 1. PostgreSQL ve pgvector Kurulumu

```bash
bash scripts/setup_db.sh
```

Manuel kurulum için:

1. PostgreSQL kurulumu:
   ```bash
   sudo apt-get update
   sudo apt-get install -y postgresql postgresql-contrib
   ```

2. TCP/IP bağlantılarını etkinleştir:
   ```bash
   sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf
   sudo sed -i "s/host    all             all             127.0.0.1\/32            md5/host    all             all             0.0.0.0\/0               md5/" /etc/postgresql/*/main/pg_hba.conf
   ```

3. PostgreSQL'i yeniden başlat:
   ```bash
   sudo systemctl restart postgresql
   ```

4. Veritabanı oluşturma:
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE ragdb;"
   sudo -u postgres psql -c "CREATE USER raguser WITH PASSWORD 'ragpassword';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;"
   sudo -u postgres psql -c "ALTER USER raguser WITH SUPERUSER;"  # pgvector için gerekli
   ```

5. pgvector uzantısını etkinleştirme:
   ```bash
   sudo -u postgres psql -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

### 2. Python Ortamı ve Bağımlılıklar

```bash
# Python sanal ortam oluştur
python -m venv ragcli_env
source ragcli_env/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 3. Ollama Kurulumu

1. Ollama'yı yükleyin:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. LLaMA 2 veya başka bir model yükleyin:
   ```bash
   ollama pull llama2
   ```

3. Ollama servisini başlatın:
   ```bash
   ollama serve
   ```

## Kullanım

### Veritabanını Başlatma

```bash
python cli.py init
```

### Belgeleri İndeksleme

```bash
python cli.py index ./belgeler
```

### Sorgu Yapma

```bash
python cli.py ask "Bu belgelerde neler anlatılıyor?"
```

### Farklı Şablonlarla Sorgu

```bash
# Akademik şablon ile sorgu
python cli.py ask "Veri tabanı nedir?" --template academic

# Farklı model kullanarak sorgu
python cli.py ask "Özetler misin?" --model QuestionAnswer
```

### Şablonları Düzenleme

```bash
# Prompt şablonlarını düzenle
python cli.py edit-prompt

# Model şablonlarını düzenle
python cli.py edit-model
```

### API Servisini Başlatma

```bash
python cli.py serve --port 8000
```

## API Kullanımı

### Sorgu Yapma

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Bu belgelerde neler anlatılıyor?", "template": "summary"}'
```

### Şablonları Listeleme

```bash
curl "http://localhost:8000/templates"
```

### Modelleri Listeleme

```bash
curl "http://localhost:8000/models"
```

## Yapılandırma

Temel yapılandırma ayarları `app/config.py` dosyasında bulunur. Veritabanı bağlantı bilgileri, model adları ve diğer ayarları buradan düzenleyebilirsiniz.

Alternatif olarak, çevre değişkenleri kullanarak yapılandırma yapabilirsiniz:

```bash
export RAGCLI_DB_HOST=localhost
export RAGCLI_DB_PORT=5432
export RAGCLI_DB_NAME=ragdb
export RAGCLI_DB_USER=raguser
export RAGCLI_DB_PASS=ragpassword
```

## Sorun Giderme

Yaygın sorunlar ve çözümleri için [TROUBLESHOOTING.md](TROUBLESHOOTING.md) dosyasına bakabilirsiniz.

## Proje Klasör Yapısı

```
ragcli/
  ├── app/
  │    ├── __init__.py           # Modül bilgileri
  │    ├── config.py             # Konfigürasyon ayarları
  │    ├── db.py                 # Veritabanı işlemleri
  │    ├── embedding.py          # Embedding işlemleri
  │    ├── llm.py                # LLM işlemleri
  │    └── utils.py              # Yardımcı fonksiyonlar
  ├── templates/
  │    ├── models.json           # Model şablonları
  │    └── prompts.json          # Prompt şablonları
  ├── scripts/
  │    ├── setup_db.sh           # PostgreSQL ve pgvector kurulum scripti
  │    ├── setup_env.sh          # Geliştirme ortamı kurulum scripti
  │    └── run_tests.sh          # Test çalıştırma scripti
  ├── tests/
  │    ├── __init__.py
  │    └── test_basic.py         # Temel testler
  ├── cli.py                     # Ana CLI programı
  ├── requirements.txt           # Bağımlılıklar
  └── README.md                  # Dokümantasyon
```

## Özellikler

- **LCEL Optimizasyonu**: Modern LCEL pipe operatörleri ile akıcı ve verimli iş akışları
- **Dinamik Şablonlar**: JSON dosyalarından okunan özelleştirilebilir prompt ve model şablonları
- **API Desteği**: FastAPI entegrasyonu ile kolay kullanım
- **Minimal Tasarım**: Az ve öz kod ile maksimum işlevsellik
- **Offline Kullanım**: Ollama ile tamamen yerel çalışma
- **all-MiniLM-L6-v2**: Hafif ve hızlı embedding modeli