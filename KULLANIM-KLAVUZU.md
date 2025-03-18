# RAG CLI Kullanım Kılavuzu

RAG CLI, yerel LLM (Large Language Model) kullanarak Retrieval-Augmented Generation (RAG) sistemini kolay bir şekilde kullanmanızı sağlayan komut satırı aracıdır. Docker, PostgreSQL, pgvector ve Ollama kullanarak tamamen yerel çalışan bir sistem sunar.

## İçindekiler

- [Kurulum](#kurulum)
- [Gemma 3 Modeli Kullanımı](#gemma-3-modeli-kullanımı)
- [Temel Komutlar](#temel-komutlar)
  - [Veritabanı Başlatma](#veritabanı-başlatma)
  - [Belge İndeksleme](#belge-i̇ndeksleme)
  - [Sorgu Yanıtlama](#sorgu-yanıtlama)
  - [API Hizmeti](#api-hizmeti)
- [Gelişmiş Özellikler](#gelişmiş-özellikler)
- [Sorun Giderme](#sorun-giderme)

## Kurulum

Sistemi ilk kez kuruyorsanız:

```bash
# 1. Proje dizinine gidin
cd ragcli

# 2. Kurulum scriptini çalıştırın
bash install.sh

# 3. Her yeni oturumda Docker konteyneri başlatın
docker start postgres-ragcli

# 4. Conda ortamını etkinleştirin (kurulmuşsa)
conda activate ragcli_env
```

## Gemma 3 Modeli Kullanımı

Gemma 3:12B modelini Ollama üzerinde kullanmak için:

```bash
# 1. Gemma 3 modelini indirin
ollama pull gemma3:12b

# 2. config.py dosyasını düzenleyin
nano app/config.py
# LLM_MODEL değişkenini "gemma3:12b" olarak değiştirin
```

## Temel Komutlar

### Veritabanı Başlatma

İlk kurulum veya veritabanını sıfırlamanız gerektiğinde:

```bash
python cli.py init
```

Bu komut:
- pgvector uzantısını yükler
- Gerekli tabloları oluşturur

### Belge İndeksleme

Belgeleri vektör veritabanına eklemek için:

```bash
# Tek bir belge eklemek
python cli.py index /path/to/document.txt

# Bir klasördeki tüm belgeleri eklemek
python cli.py index /path/to/documents/folder/

# Örnekler
python cli.py index test_data/
python cli.py index ~/Belgeler/verilerim/
```

**Desteklenen Dosya Türleri:** .txt dosyaları

**Çıktı Örneği:**
```
3 belge parçası oluşturuldu
3 belge parçası işlendi ve veritabanına kaydedildi
```

### Sorgu Yanıtlama

Vektör veritabanına sorgu göndermek için:

```bash
# Temel sorgu
python cli.py ask "Sormak istediğiniz soru?"

# Şablon kullanarak sorgu
python cli.py ask "Sormak istediğiniz soru?" --template academic

# Farklı yanıt modeli kullanarak
python cli.py ask "Sormak istediğiniz soru?" --model QuestionAnswer

# Örnekler
python cli.py ask "RAG nedir?"
python cli.py ask "Gemma modeli nasıl çalışır?" --template academic
python cli.py ask "LLM güvenliği nasıl sağlanır?" --model QuestionAnswer
```

**Parametreler:**
- `--template` veya `-t`: Kullanılacak şablon adı (default, academic, summary)
- `--model` veya `-m`: Kullanılacak model adı (DocumentResponse, QuestionAnswer)

**Çıktı Örneği:**
```
=== CEVAP ===
RAG (Retrieval-Augmented Generation) sistemleri, LLM'leri harici verilerle zenginleştiren sistemlerdir.
...

=== KAYNAKLAR ===
1. /belgelerim/rag_bilgi.txt: "RAG sistemleri, özel bilgi kaynaklarını..."
...
```

### API Hizmeti

RAG sistemini FastAPI aracılığıyla sunmak için:

```bash
# Varsayılan port ile başlatma (8000)
python cli.py serve

# Belirli bir port ile başlatma
python cli.py serve --port 3000
```

**Parametreler:**
- `--port` veya `-p`: API servisinin çalışacağı port numarası (varsayılan: 8000)

API başladıktan sonra:
1. Swagger dokümantasyonu: `http://localhost:8000/docs`
2. ReDoc dokümantasyonu: `http://localhost:8000/redoc`
3. Sağlık kontrolü: `http://localhost:8000/health`

**API Endpointleri:**
- **POST** `/query`: Sorgu yapmak için
  ```json
  {
    "query": "RAG nedir?",
    "template": "default",
    "model": "DocumentResponse"
  }
  ```
- **GET** `/templates`: Mevcut şablonları listelemek için
- **GET** `/models`: Mevcut modelleri listelemek için

### Diğer Komutlar

```bash
# Şablon düzenleme
python cli.py edit-prompt
python cli.py edit-model

# Yardım görüntüleme
python cli.py --help
python cli.py ask --help
```

## Gelişmiş Özellikler

### Şablonları Özelleştirme

`templates/prompts.json` dosyasını düzenleyerek kendi prompt şablonlarınızı ekleyebilirsiniz:

```bash
python cli.py edit-prompt
```

**Örnek Şablon Yapısı:**
```json
{
  "mytheme": {
    "messages": [
      {"role": "system", "content": "Sen bir özel asistansın. Şu şekilde yanıt ver..."},
      {"role": "user", "content": "Soru: {query}\nBağlam: {context}\nCevap:"}
    ]
  }
}
```

### Yanıt Modellerini Özelleştirme

`templates/models.json` dosyasını düzenleyerek kendi yanıt modellerinizi ekleyebilirsiniz:

```bash
python cli.py edit-model
```

**Örnek Model Yapısı:**
```json
{
  "MyResponse": {
    "fields": {
      "answer": {"type": "str", "description": "Detaylı cevap"},
      "sources": {"type": "list[str]", "description": "Kullanılan kaynaklar"}
    }
  }
}
```

## Sorun Giderme

### PostgreSQL Bağlantı Sorunları

```bash
# Docker konteyneri çalışıyor mu kontrol et
docker ps | grep postgres-ragcli

# Çalışmıyorsa başlat
docker start postgres-ragcli

# Hala sorun varsa konteyner loglarını kontrol et
docker logs postgres-ragcli
```

### Ollama Sorunları

```bash
# Ollama servisini kontrol et
pgrep -x "ollama"

# Çalışmıyorsa başlat
ollama serve

# Model listesini kontrol et
ollama list
```

### İndeksleme Sorunları

```bash
# Dosya izinlerini kontrol et
ls -la /path/to/your/document.txt

# Dosya formatını kontrol et
file /path/to/your/document.txt
```

### Sorgu Yanıt Sorunları

LLM yanıt vermiyorsa:
1. Ollama'nın çalıştığından emin olun: `ollama serve`
2. Belge indekslemesinin başarılı olduğunu kontrol edin
3. LLM modelinin indirildiğini doğrulayın: `ollama list`

---

Bu kılavuz RAG CLI'ın temel ve gelişmiş özelliklerini kapsar. Daha fazla bilgi için README.md veya geliştiriciye danışabilirsiniz.