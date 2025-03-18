# app/db.py
"""
Veritabanı işlemleri.
"""
import psycopg2
from psycopg2 import sql
from langchain_community.vectorstores import PGVector

from app.config import DB_CONNECTION, COLLECTION_NAME


def get_db_connection():
    """
    PostgreSQL veritabanı bağlantısı oluştur.
    """
    return psycopg2.connect(DB_CONNECTION)


def setup_db():
    """
    PostgreSQL veritabanını RAG için hazırla.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # pgvector uzantısını yükle
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Document chunks tablosunu oluştur
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id SERIAL PRIMARY KEY,
        document_id TEXT,
        title TEXT,
        content TEXT,
        chunk_index INTEGER,
        total_chunks INTEGER,
        embedding vector(384),
        embedding_model TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # İşlenmiş veri tablosunu oluştur
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_data (
        id SERIAL PRIMARY KEY,
        title TEXT,
        summary TEXT,
        key_points TEXT[],
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    return True


def get_vectorstore(embeddings=None):
    """Vektör deposunu oluşturur ve döndürür"""
    from app.config import DB_CONNECTION, COLLECTION_NAME, EMBEDDING_MODEL
    if embeddings is None:
        embeddings = get_embeddings(EMBEDDING_MODEL)

    # Config.py'den gelen bağlantı dizesini kullan
    print(f"DEBUG - Veritabanı bağlantısı: {DB_CONNECTION}")

    return PGVector(
        connection_string=DB_CONNECTION,  # <-- BU SATIR ÇÖZÜM
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )


def add_documents(documents):
    """Belgeleri vektör deposuna ekle."""
    transaction_id = f"tx_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    logger.info(f"Belge ekleme başladı (TX: {transaction_id}): {len(documents)} belge")

    try:
        # Embedding modelini hazırla
        embeddings = get_embeddings()
        vectorstore = get_vectorstore(embeddings)

        # Her belgeye transaction_id ekle
        for doc in documents:
            if isinstance(doc.metadata, dict):
                doc.metadata["transaction_id"] = transaction_id

        # Belgeleri ekle
        vectorstore.add_documents(documents)

        # Doğrulama yap
        import psycopg2

        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()

        # document_chunks tablosunda bu transaction ile eklenen belge sayısı
        cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE metadata->>'transaction_id' = %s;",
                       (transaction_id,))
        chunk_count = cursor.fetchone()[0]

        # langchain_pg_embedding tablosunda bu transaction ile eklenen belge sayısı
        cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding WHERE cmetadata->>'transaction_id' = %s;",
                       (transaction_id,))
        embedding_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        # Tutarlılık kontrolü
        logger.info(f"Belge ekleme tamamlandı (TX: {transaction_id}): {chunk_count} chunk, {embedding_count} embedding")

        if chunk_count != embedding_count:
            logger.warning(
                f"⚠️ Tutarsızlık tespit edildi (TX: {transaction_id}): chunks={chunk_count}, embeddings={embedding_count}")

            # Hook'u çağır (varsa)
            try:
                from app.hooks import after_document_load
                after_document_load(len(documents), source="add_documents")
            except ImportError:
                logger.warning("Hook modülü bulunamadı, otomatik kontrol yapılmıyor.")

        return len(documents)
    except Exception as e:
        logger.error(f"Belge ekleme hatası (TX: {transaction_id}): {e}")

        # Zamanı gelince silmek üzere işaretlenmiş transaction'ları temizle
        try:
            # Burada başarısız olan transaction temizliği yapılabilir
            pass
        except:
            pass

        return 0
# Hook'ları kaydet
try:
    from app.hooks import register_hooks
    register_hooks()
except ImportError:
    pass
