# RAG CLI Hızlı Başlangıç Rehberi

## PostgreSQL Sorunu Çözümü

Projeyi çalıştırırken `PostgreSQL servisi çalışmıyor` veya `Connection refused` hataları alıyorsanız, bu sorunun çözümü için Docker kullanabilirsiniz. Docker, PostgreSQL ve pgvector'ü hızlıca kurmanıza olanak tanır.

## Adım Adım Hızlı Kurulum

### 1. Eksik Script Dosyalarını Oluşturun

Aşağıdaki dosyaları `scripts` klasörünüzde oluşturun:

- `scripts/setup_env.sh` (Conda uyumlu bağımlılık kurulumu)
- `scripts/docker_postgres.sh` (Docker ile PostgreSQL kurulumu)

### 2. Docker ile PostgreSQL Kurulumu

```bash
# Docker üzerinde PostgreSQL + pgvector kurmak için
bash scripts/docker_postgres.sh
```

Bu script:
- PostgreSQL ve pgvector içeren bir Docker konteyneri oluşturur
- Veritabanı, kullanıcı ve şifre yapılandırmasını yapar
- pgvector uzantısını yükler
- Bağlantıyı test eder

### 3. CLI'ı Kullanmaya Başlayın

```bash
# Conda ortamını etkinleştirin (önceden oluşturduysanız)
conda activate ragcli_env

# Veritabanını başlatın
python cli.py init

# Test belgesi oluşturun
mkdir -p test_data
echo "RAG sistemleri, LLM'leri harici verilerle zenginleştirir." > test_data/test.txt

# Belgeleri indeksleyin
python cli.py index test_data

# Sorgu yapın
python cli.py ask "RAG nedir?"
```

## Sorun Giderme

### PostgreSQL Bağlantı Sorunları

1. Docker konteynerinin çalıştığını kontrol edin:
   ```bash
   docker ps | grep postgres-ragcli
   ```

2. Docker konteyneri çalışmıyorsa yeniden başlatın:
   ```bash
   docker start postgres-ragcli
   ```

3. Bağlantıyı test edin:
   ```bash
   psql -h localhost -U raguser -d ragdb
   # Şifre: ragpassword
   ```

### Conda Ortam Sorunları

1. Conda ortamını yeniden etkinleştirin:
   ```bash
   source ~/anaconda3/etc/profile.d/conda.sh
   conda activate ragcli_env
   ```

2. Bağımlılıkları kontrol edin:
   ```bash
   pip list | grep langchain
   ```

## Docker Konteyneri Hakkında

- **Veritabanı**: ragdb
- **Kullanıcı**: raguser
- **Şifre**: ragpassword
- **Port**: 5432
- **Konteyner adı**: postgres-ragcli

## Başka Bilgisayarda Kullanırken

Projeyi başka bir bilgisayarda kullanmak isterseniz:

1. Repo'yu indirin veya kopyalayın
2. Conda ortamı oluşturun: `conda create -n ragcli_env python=3.8`
3. Kurulum scriptini çalıştırın: `bash install.sh`
4. Docker'ın yüklü olduğundan emin olun