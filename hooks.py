# app/hooks.py
"""
RAG sistemi için basit hook'lar.
"""
import logging

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename="rag_hooks.log"
)

logger = logging.getLogger("rag_hooks")


def after_document_load(document_count, source=None):
    """Belge yükleme işleminden sonra çağrılır."""
    logger.info(f"Belge yükleme tamamlandı: {document_count} belge, kaynak: {source}")

    # Tutarlılık kontrolü yap
    try:
        # Temel kontrol kodunu doğrudan buraya ekleyelim
        # (Bağımlılıkları azaltmak için)
        import psycopg2
        from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM document_chunks;")
        chunk_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding;")
        embedding_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        if chunk_count == embedding_count:
            logger.info("✅ Tutarlılık kontrolü başarılı: Belgeler ve embeddingler eşit.")
        else:
            logger.warning(f"⚠️ Tutarsızlık tespit edildi: chunks={chunk_count}, embeddings={embedding_count}")
    except Exception as e:
        logger.error(f"Tutarlılık kontrolü sırasında hata: {e}")