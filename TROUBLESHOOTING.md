# RAGCLI Sorun Giderme Rehberi

## PostgreSQL Bağlantı Sorunları

### Sorun 1: PostgreSQL Servisi Çalışmıyor
**Belirtiler:** 
- `Error: connection to server at "localhost" (127.0.0.1), port 5432 failed: Bağlantı reddedildi`

**Çözümler:**
1. PostgreSQL servisinin durumunu kontrol edin:
   ```bash
   sudo systemctl status postgresql
   ```

2. PostgreSQL servisini başlatın:
   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

### Sorun 2: PostgreSQL TCP/IP Bağlantılarını Kabul Etmiyor
**Belirtiler:**
- PostgreSQL çalışıyor ancak bağlantı kurulamıyor

**Çözümler:**
1. PostgreSQL konfigürasyon dosyasını düzenleyin:
   ```bash
   sudo nano /etc/postgresql/*/main/postgresql.conf
   ```
   `listen_addresses = 'localhost'` satırını bulun ve yorum işaretini kaldırın

2. pg_hba.conf dosyasını düzenleyin:
   ```bash
   sudo nano /etc/postgresql/*/main/pg_hba.conf
   ```
   `host all all 127.0.0.1/32 md5` satırını kontrol edin

3. PostgreSQL'i yeniden başlatın:
   ```bash
   sudo systemctl restart postgresql
   ```

### Sorun 3: PostgreSQL Kullanıcı Kimlik Doğrulama Hatası
**Belirtiler:**
- `FATAL: password authentication failed for user "raguser"`

**Çözümler:**
1. Kullanıcı şifresini sıfırlayın:
   ```bash
   sudo -u postgres psql -c "ALTER USER raguser WITH PASSWORD 'ragpassword';"
   ```

## Python Paket Sorunları

### Sorun 1: Eksik LangChain Community Paketi
**Belirtiler:**
- `ModuleNotFoundError: No module named 'langchain_community'`

**Çözümler:**
1. Gerekli paketi yükleyin:
   ```bash
   pip install langchain-community
   ```

2. Tüm bağımlılıkları güncellenmiş requirements.txt ile yeniden yükleyin:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

### Sorun 2: langchain_text_splitters Modülü Bulunamadı
**Belirtiler:**
- `ModuleNotFoundError: No module named 'langchain_text_splitters'`

**Çözümler:**
1. Eksik paketi yükleyin:
   ```bash
   pip install langchain-text-splitters
   ```

### Sorun 3: Pydantic Sürüm Uyumsuzluğu
**Belirtiler:**
- `AttributeError: module 'pydantic' has no attribute 'create_model'`

**Çözümler:**
1. Pydantic'i yükseltin:
   ```bash
   pip install pydantic>=2.0.0 --upgrade
   ```

## Ollama Sorunları

### Sorun 1: Ollama Servisi Çalışmıyor
**Belirtiler:**
- `Failed to connect to Ollama service`

**Çözümler:**
1. Ollama servisini başlatın:
   ```bash
   ollama serve
   ```

### Sorun 2: Model Bulunamadı
**Belirtiler:**
- `model 'llama2' not found`

**Çözümler:**
1. Modeli indirin:
   ```bash
   ollama pull llama2
   ```

### Sorun 3: Ollama Bellek Yetersizliği
**Belirtiler:**
- `error: out of memory`

**Çözümler:**
1. Daha küçük bir model kullanın:
   ```bash
   ollama pull tinyllama
   ```
   
2. app/config.py dosyasında LLM_MODEL değişkenini değiştirin:
   ```python
   LLM_MODEL = "tinyllama"
   ```

## Veritabanı Şema Sorunları

### Sorun 1: pgvector Uzantısı Yüklü Değil
**Belirtiler:**
- `ERROR: extension "vector" does not exist`

**Çözümler:**
1. pgvector uzantısını yükleyin:
   ```bash
   sudo -u postgres psql -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

### Sorun 2: Kullanıcı Yetkileri Yetersiz
**Belirtiler:**
- `ERROR: permission denied to create extension "vector"`

**Çözümler:**
1. Kullanıcıya superuser yetkisi verin:
   ```bash
   sudo -u postgres psql -c "ALTER USER raguser WITH SUPERUSER;"
   ```

### Sorun 3: Tablo Zaten Var
**Belirtiler:**
- `ERROR: relation "processed_data" already exists`

**Çözümler:**
1. Tablonun zaten var olduğuna dair sadece bir uyarı, işlemlere devam edebilirsiniz
2. Veritabanını tamamen sıfırlamak isterseniz:
   ```bash
   sudo -u postgres psql -c "DROP DATABASE ragdb;"
   ```
   ve kurulum prosedürünü tekrarlayın

## Diğer Sorunlar

### Sorun 1: SentenceTransformer Model İndirme Hatası
**Belirtiler:**
- `OSError: [E050] Failed to read file...`

**Çözümler:**
1. Internet bağlantınızı kontrol edin
2. Manuel olarak modeli indirin:
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```

### Sorun 2: Dizin Oluşturma İzin Sorunları
**Belirtiler:**
- `PermissionError: [Errno 13] Permission denied`

**Çözümler:**
1. Kullanıcı izinlerini kontrol edin:
   ```bash
   sudo chown -R $USER:$USER .
   ```
   
2. Dosya izinlerini düzeltin:
   ```bash
   chmod -R 755 .
   ```

## Hata Ayıklama İpuçları

1. Detaylı hata ayıklama için Python'da aşağıdaki kodu ekleyin:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. PostgreSQL bağlantı sorunlarında işe yarayabilecek test komutu:
   ```bash
   PGPASSWORD=ragpassword psql -U raguser -h localhost -d ragdb -c "SELECT 1;"
   ```

3. LangChain importlarını kontrol etmek için:
   ```python
   python -c "import langchain_community; print(langchain_community.__version__)"
   ```

4. Ollama API'sini test etmek için:
   ```bash
   curl http://localhost:11434/api/tags
   ```

Yukarıdaki çözümler çalışmazsa, lütfen GitHub sorun sayfasına bir rapor açın veya aşağıdaki adımları tam olarak açıklayan bir e-posta gönderin:
1. Tam hata mesajı
2. Kullandığınız işletim sistemi ve sürümü
3. Python ve pip sürümleri
4. Paket sürümleri (`pip freeze` çıktısı)