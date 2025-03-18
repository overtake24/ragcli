#!/usr/bin/env python3
"""
PGVector veritabanı işlemleri için yardımcı fonksiyonlar.
"""
import os
import sys
import psycopg2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass


@dataclass
class Document:
    """Doküman veri yapısı."""
    id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class PGVectorClient:
    """PGVector veritabanı ile etkileşim kurmak için istemci."""

    def __init__(self, connection_string: Optional[str] = None,
                 host: str = "localhost", port: str = "5432",
                 dbname: str = "ragdb", user: str = "raguser",
                 password: str = "ragpassword"):
        """Veritabanı bağlantısını başlatır."""
        if connection_string:
            self.connection_string = connection_string
        else:
            self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

        self.conn = None
        self.is_connected = False

    def connect(self) -> bool:
        """Veritabanına bağlanır."""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Veritabanı bağlantı hatası: {e}")
            return False

    def disconnect(self) -> None:
        """Veritabanı bağlantısını kapatır."""
        if self.conn:
            self.conn.close()
            self.is_connected = False

    def check_table_exists(self, table_name: str) -> bool:
        """Belirtilen tablonun var olup olmadığını kontrol eder."""
        if not self.is_connected and not self.connect():
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT EXISTS (
               SELECT FROM information_schema.tables 
               WHERE table_name = %s
            );
            """, (table_name,))
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Tablo kontrolü hatası: {e}")
            return False

    def check_extension_exists(self, extension_name: str = "vector") -> bool:
        """Belirtilen uzantının yüklü olup olmadığını kontrol eder."""
        if not self.is_connected and not self.connect():
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT EXISTS (
               SELECT FROM pg_extension 
               WHERE extname = %s
            );
            """, (extension_name,))
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Uzantı kontrolü hatası: {e}")
            return False

    def get_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """Belgeleri getirir."""
        if not self.is_connected and not self.connect():
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT document_id, title, content, metadata, embedding
            FROM document_chunks
            ORDER BY id
            LIMIT %s OFFSET %s
            """, (limit, offset))
            documents = []
            for doc_id, title, content, metadata, embedding in cursor.fetchall():
                documents.append(Document(
                    id=doc_id,
                    title=title or "Başlıksız",
                    content=content,
                    metadata=metadata or {},
                    embedding=embedding
                ))
            return documents
        except Exception as e:
            print(f"Belge getirme hatası: {e}")
            return []

    def similarity_search(self, query_vector: List[float],
                          limit: int = 5,
                          metric: str = "l2") -> List[Tuple[Document, float]]:
        """Benzerlik araması yapar."""
        if not self.is_connected and not self.connect():
            return []

        # Metrik operatörünü belirle
        if metric == "cosine":
            operator = "<=>"
        elif metric == "l2":
            operator = "<->"
        elif metric == "inner":
            operator = "<#>"
        else:
            raise ValueError(f"Geçersiz metrik: {metric}")

        try:
            cursor = self.conn.cursor()

            # Sorgu vektörünü string literal haline getirin
            vector_str = '[' + ','.join(map(str, query_vector)) + ']'

            # Sorguda, gönderilen parametreyi explicit olarak vector tipine cast edin.
            cursor.execute(f"""
            SELECT document_id, title, content, embedding, embedding {operator} (%s)::vector AS score
            FROM document_chunks
            ORDER BY embedding {operator} (%s)::vector {"ASC" if metric == "l2" else "DESC"}
            LIMIT %s
            """, (vector_str, vector_str, limit))

            results = []
            for doc_id, title, content, embedding, score in cursor.fetchall():
                doc = Document(
                    id=doc_id,
                    title=title or "Başlıksız",
                    content=content,
                    metadata={},  # metadata sütunu yoksa boş dict atanıyor
                    embedding=embedding
                )
                results.append((doc, score))
            return results
        except Exception as e:
            print(f"Benzerlik araması hatası: {e}")
            return []

    def normalized_similarity_search(self, query_vector: List[float],
                                     limit: int = 5,
                                     metric: str = "l2") -> List[Tuple[Document, float]]:
        """Normalize edilmiş benzerlik araması yapar."""
        results = self.similarity_search(query_vector, limit, metric)
        normalized_results = []
        for doc, score in results:
            if metric == "l2":
                normalized_score = 1 / (1 + score)
            elif metric == "cosine":
                normalized_score = score
            elif metric == "inner":
                normalized_score = 1 / (1 + np.exp(-score))
            else:
                normalized_score = score
            normalized_results.append((doc, normalized_score))
        return sorted(normalized_results, key=lambda x: x[1], reverse=True)

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Embedding vektörlerinin istatistiklerini getirir."""
        if not self.is_connected and not self.connect():
            return {}

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            total_docs = cursor.fetchone()[0]
            cursor.execute("SELECT array_length(embedding, 1) FROM document_chunks LIMIT 1")
            result = cursor.fetchone()
            vector_dim = result[0] if result else None
            cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NULL")
            null_embeddings = cursor.fetchone()[0]
            cursor.execute("SELECT embedding FROM document_chunks WHERE embedding IS NOT NULL LIMIT 1")
            sample_embedding = cursor.fetchone()
            if sample_embedding:
                sample_embedding = sample_embedding[0]
                min_val = min(sample_embedding)
                max_val = max(sample_embedding)
                avg_val = sum(sample_embedding) / len(sample_embedding)
                std_val = np.std(sample_embedding)
            else:
                min_val = max_val = avg_val = std_val = None
            return {
                "total_documents": total_docs,
                "vector_dimension": vector_dim,
                "null_embeddings": null_embeddings,
                "vector_stats": {
                    "min": min_val,
                    "max": max_val,
                    "avg": avg_val,
                    "std": std_val
                }
            }
        except Exception as e:
            print(f"Embedding istatistikleri hatası: {e}")
            return {}

    def get_database_info(self) -> Dict[str, Any]:
        """Veritabanı hakkında genel bilgi getirir."""
        if not self.is_connected and not self.connect():
            return {}

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            pgvector_version = cursor.fetchone()
            if pgvector_version:
                pgvector_version = pgvector_version[0]
            cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            langchain_tables = [table for table in tables if table.startswith('langchain_')]
            return {
                "postgresql_version": version,
                "pgvector_version": pgvector_version,
                "tables": tables,
                "langchain_tables": langchain_tables
            }
        except Exception as e:
            print(f"Veritabanı bilgisi hatası: {e}")
            return {}


def get_client_from_env() -> PGVectorClient:
    """Çevre değişkenlerinden PGVector istemcisi oluşturur."""
    try:
        sys.path.append("../..")
        from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
        client = PGVectorClient(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
    except ImportError:
        client = PGVectorClient(
            host=os.getenv("RAGCLI_DB_HOST", "localhost"),
            port=os.getenv("RAGCLI_DB_PORT", "5432"),
            dbname=os.getenv("RAGCLI_DB_NAME", "ragdb"),
            user=os.getenv("RAGCLI_DB_USER", "raguser"),
            password=os.getenv("RAGCLI_DB_PASS", "ragpassword")
        )
    return client


def test_connection():
    """Bağlantıyı test eder."""
    client = get_client_from_env()
    if client.connect():
        print("✅ Veritabanı bağlantısı başarılı!")
        info = client.get_database_info()
        print(f"PostgreSQL sürümü: {info.get('postgresql_version', 'Bilinmiyor')}")
        print(f"pgvector sürümü: {info.get('pgvector_version', 'Bilinmiyor')}")
        print(f"Tablolar: {info.get('tables', [])}")
        embedding_stats = client.get_embedding_stats()
        print(f"Toplam belge sayısı: {embedding_stats.get('total_documents', 0)}")
        print(f"Vektör boyutu: {embedding_stats.get('vector_dimension', 'Bilinmiyor')}")
        client.disconnect()
        return True
    else:
        print("❌ Veritabanı bağlantısı başarısız!")
        return False


# >>> EK: Global Fonksiyon - query_similar_documents <<<
def query_similar_documents(query_vector: List[float], top_k: int = 5, metric: str = "l2") -> List[Dict[str, Any]]:
    """
    PGVectorClient kullanarak benzerlik araması yapar.
    Dönen sonuçlar, adapter ve deney script’lerinin beklediği sözlük formatında (score, distance, category vs.) verilir.
    """
    client = PGVectorClient()
    if not client.connect():
        print("❌ Veritabanı bağlantısı kurulamadı.")
        return []
    # Benzerlik araması (raw sonuç: (Document, score))
    # "metadata" sütunu sorgudan çıkarıldı, eğer tablo içinde mevcut değilse.
    results = client.similarity_search(query_vector, limit=top_k, metric=metric)
    client.disconnect()
    converted_results = []
    for doc, score in results:
        result = {
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "metadata": {},  # metadata sütunu olmadığından boş dict atanıyor
            "embedding": doc.embedding,
            "score": score,          # Raw skor (L2 uzaklığı, düşük ise daha iyi)
            "distance": score        # L2 metriğinde skor, tersine çevrilmek için kullanılabilir
        }
        # Kategori bilgisi yoksa "default" olarak atanıyor
        result["category"] = doc.metadata.get("category", "default") if doc.metadata else "default"
        converted_results.append(result)
    return converted_results



if __name__ == "__main__":
    test_connection()
