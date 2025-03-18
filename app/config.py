# app/config.py
"""
Konfigürasyon ayarları.
"""
import os

# Temel dizinler
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# Şablon dosyaları
MODEL_SCHEMA_FILE = os.path.join(TEMPLATE_DIR, "models.json")
PROMPT_TEMPLATE_FILE = os.path.join(TEMPLATE_DIR, "prompts.json")

# Veritabanı ayarları (Docker)
DB_HOST = os.getenv("RAGCLI_DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("RAGCLI_DB_PORT", "5432")
DB_NAME = os.getenv("RAGCLI_DB_NAME", "ragdb")
DB_USER = os.getenv("RAGCLI_DB_USER", "raguser")
DB_PASS = os.getenv("RAGCLI_DB_PASS", "ragpassword")

DB_CONNECTION = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
COLLECTION_NAME = "document_chunks"

# Model ayarları
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 boyutlu vektörler (veritabanıyla uyumlu)
LLM_MODEL = "gemma3:12b"

# Belge parçalama ayarları
DEFAULT_CHUNK_SIZE = 1000  # Varsayılan parça boyutu
DEFAULT_CHUNK_OVERLAP = 200  # Varsayılan parça örtüşme miktarı

# Sorgu ayarları
SIMILARITY_THRESHOLD = 0.7  # Benzerlik skoru eşiği (0-1 arası, 1 en benzer)
MAX_DOCUMENTS = 5  # Sorgu başına maksimum belge sayısı

# Document kategori filtreleme için anahtar kelimeler
DOCUMENT_CATEGORIES = {
    "film": ["film", "movie", "yönetmen", "director", "cast", "oyuncular", "imdb", "cinema", "sinema", "actor", "aktör"],
    "book": ["kitap", "book", "yazar", "author", "sayfa", "page", "roman", "novel", "yayın", "publication"],
    "person": ["doğum", "birth", "ölüm", "death", "meslek", "occupation", "hayat", "yaşam", "life", "biyografi", "biography"]
}
