# RAG CLI

Yerel LLM kullanarak vektör tabanlı bilgi erişimi için komut satırı arayüzü. PostgreSQL, pgvector, Ollama ve LangChain Expression Language (LCEL) kullanarak çevrimdışı çalışan bir RAG (Retrieval-Augmented Generation) sistemi.

## Özellikler

- **Tamamen Yerel**: Ollama üzerinde çalışan LLM sayesinde internet bağlantısı gerektirmez
- **Kolay Kurulum**: Tek komutla kurulum
- **Vektör Tabanlı Arama**: Semantik olarak benzer belgeleri bulur
- **CLI ve API**: Hem komut satırı hem de HTTP API üzerinden erişim
- **Özelleştirilebilir**: Prompt şablonları ve yanıt modelleri düzenlenebilir

## Hızlı Başlangıç

```bash
# 1. Proje dizininde başla
git clone <repo-url> ragcli
cd ragcli

# 2. Kurulumu çalıştır
bash setup.sh

# 3. Belge ekle
python cli.py index /path/to/documents/

# 4. Sorgu yap
python cli.py ask "Sorgunuz?"
```

## Gereksinimler

- Python 3.8+
- PostgreSQL 12+ (pgvector uzantısı ile)
- Ollama

## Kurulum

### Otomatik Kurulum

En kolay kurulum için `setup.sh` scriptini kullanın:

```bash
bash setup.sh
```

Bu script:
- Gerekli Python paketlerini kurar
- Ollama LLM'i yükler (kurulu değilse)
- Veritabanını hazırlar
- Örnek belgeler indeksler
- Test sorgusu yapar

### Manuel Kurulum

1. Bağımlılıkları yükleyin:
```bash
pip install langchain langchain-community langchain-text-splitters click psycopg2-binary pgvector sentence-transformers fastapi uvicorn ollama
```

2. Ollama'yı kurun ve başlatın:
```bash
# Linux için
curl -fsSL https://ollama.com/install.sh | sh
# Windows için https://ollama.ai/download adresinden indirin

# Ollama servisini başlatın
ollama serve
```

3. LLM modelini indirin:
```bash
ollama pull llama2
# veya başka bir model
# ollama pull gemma:2b
```

4. Veritabanını kurun:
```bash
# PostgreSQL ve pgvector kurulumu (örnek)
sudo apt install postgresql postgresql-contrib
# pgvector kurulumu için dokümantasyona bakın

# Veritabanını başlatma
python cli.py init
```

5. Yapılandırmayı düzenleyin:
```bash
# app/config.py dosyasında veritabanı bağlantı bilgilerini ayarlayın
```

## Kullanım

### Veritabanını Başlatma

```bash
python cli.py init
```

### Belgeleri İndeksleme

```bash
# Tek bir belge eklemek
python cli.py index /path/to/document.txt

# Bir klasördeki tüm belgeleri eklemek
python cli.py index /path/to/documents/
```

### Sorgu Yapma

```bash
# Temel sorgu
python cli.py ask "Sormak istediğiniz soru?"

# Şablon kullanarak sorgu
python cli.py ask "Sorgunuz?" --template academic

# Farklı yanıt modeli kullanarak sorgu
python cli.py ask "Sorgunuz?" --model QuestionAnswer
```

### API Servisi

```bash
# API servisini başlatma
python cli.py serve

# Belirli bir port ile başlatma
python cli.py serve --port 3000
```

API başladıktan sonra:
1. Swagger dokümantasyonu: `http://localhost:8000/docs`
2. Sorgu yapma: 
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG nedir?"}'
```

### Diğer Komutlar

```bash
# Şablonları listeleme
python cli.py templates

# Modelleri listeleme
python cli.py models

# Şablon düzenleme
python cli.py edit-prompt

# Model düzenleme
python cli.py edit-model

# Sistem durumunu kontrol etme
python cli.py status

# Yardım görüntüleme
python cli.py --help
```

## Yapılandırma

`app/config.py` dosyası üzerinden yapılandırma yapabilirsiniz:

- **DB_CONNECTION**: Veritabanı bağlantı dizesi
- **EMBEDDING_MODEL**: Kullanılacak embedding modeli (varsayılan: `all-MiniLM-L6-v2`)
- **LLM_MODEL**: Kullanılacak Ollama modeli (varsayılan: `llama2`)

Çevre değişkenleri ile de yapılandırabilirsiniz:

```bash
export RAGCLI_DB_HOST=localhost
export RAGCLI_DB_NAME=ragdb
export RAGCLI_LLM_MODEL=gemma:2b
```

## Mimari

RAG CLI, aşağıdaki bileşenlerden oluşur:

1. **Vektörleştirme**: SentenceTransformers ve `all-MiniLM-L6-v2` model kullanılarak belgeler vektörleştirilir
2. **Veritabanı**: pgvector uzantısı ile PostgreSQL veritabanı kullanılır
3. **LLM**: Ollama ile yerel dil modeli kullanılır
4. **CLI Arayüzü**: Click kütüphanesi ile komut satırı arayüzü sağlanır
5. **API**: FastAPI ile HTTP API servisi sağlanır

## Lisans

MIT