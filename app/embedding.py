# app/embedding.py
"""
Doküman yükleme, parçalama ve vektörleştirme işlemleri
"""
import os
import sys
import json
import time
from typing import List, Dict, Any, Optional

from app.db import get_db_connection
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings

from app.config import EMBEDDING_MODEL, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP

# Default embedding model
DEFAULT_EMBEDDING_MODEL = EMBEDDING_MODEL
_embedding_model = None


def get_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> SentenceTransformer:
    """Yüklü embedding modelini döndür veya yükle"""
    global _embedding_model

    # Model adı None ise varsayılan değeri kullan
    if model_name is None:
        model_name = DEFAULT_EMBEDDING_MODEL
        print(f"UYARI - Model adı None, varsayılan model kullanılıyor: {DEFAULT_EMBEDDING_MODEL}")

    # Eğer model yüklüyse ve istenen model aynıysa, mevcut modeli kullan
    if _embedding_model is not None and _embedding_model.get("name") == model_name:
        return _embedding_model.get("model")

    # Modeli yükle
    try:
        print(f"INFO - Embedding modeli yükleniyor: {model_name}")
        model = SentenceTransformer(model_name)
        _embedding_model = {
            "name": model_name,
            "model": model
        }
        return model
    except Exception as e:
        print(f"ERROR - Embedding modeli yüklenirken hata: {e}")
        print(f"Model: {model_name}")
        raise


def get_embeddings(model_name=None):
    """Embedding modelini döndürür"""
    from app.config import EMBEDDING_MODEL
    if model_name is None:
        model_name = EMBEDDING_MODEL
    print(f"INFO - Embedding modeli kullanılıyor: {model_name}")
    return SentenceTransformerEmbeddings(model_name=model_name)


def generate_embeddings(texts: List[str], model_name: str = DEFAULT_EMBEDDING_MODEL) -> List[List[float]]:
    """Metinler için embedding vektörleri oluştur"""
    # Model adı None ise varsayılan değeri kullan
    if model_name is None:
        model_name = DEFAULT_EMBEDDING_MODEL
        print(f"UYARI - Model adı None, varsayılan model kullanılıyor: {DEFAULT_EMBEDDING_MODEL}")

    model = get_embedding_model(model_name)
    return model.encode(texts).tolist()


def chunk_document(content: str, title: str = "Untitled",
                   chunk_size: int = DEFAULT_CHUNK_SIZE,
                   chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """Dokümanı parçalara böl"""
    # Markdown başlıklarını ve listelerini koruyarak böl
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )

    chunks = text_splitter.split_text(content)
    print(f"INFO - Belge {len(chunks)} parçaya bölündü. Belge boyutu: {len(content)} karakter")

    # Her bir parçayı hazırla
    document_chunks = []
    for i, chunk in enumerate(chunks):
        document_chunks.append({
            "title": title,
            "content": chunk,
            "chunk_index": i,
            "total_chunks": len(chunks)
        })

    return document_chunks


def save_chunks_to_db(document_id: str, chunks: List[Dict[str, Any]],
                      model_name: str = DEFAULT_EMBEDDING_MODEL) -> int:
    """Belge parçalarını veritabanına kaydet"""
    if not chunks:
        print("UYARI - Kaydedilecek belge parçası bulunamadı")
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Tüm parçaların içerik metinlerini al
        texts = [chunk["content"] for chunk in chunks]

        # Vektörler oluştur
        print(f"INFO - {len(texts)} parça için embedding vektörleri oluşturuluyor...")
        # Model adı None ise varsayılan değeri kullan - önemli düzeltme
        if model_name is None:
            model_name = DEFAULT_EMBEDDING_MODEL
            print(f"UYARI - Model adı None, varsayılan model kullanılıyor: {DEFAULT_EMBEDDING_MODEL}")

        embeddings = generate_embeddings(texts, model_name)

        # Her bir parçayı veritabanına kaydet
        for i, chunk in enumerate(chunks):
            cursor.execute("""
            INSERT INTO document_chunks 
                (document_id, title, content, chunk_index, total_chunks, embedding, embedding_model)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                document_id,
                chunk["title"],
                chunk["content"],
                chunk["chunk_index"],
                chunk["total_chunks"],
                embeddings[i],
                model_name  # Burada model_name kullanılıyor
            ))

        conn.commit()
        print(f"INFO - {len(chunks)} belge parçası veritabanına kaydedildi")
        return len(chunks)
    except Exception as e:
        conn.rollback()
        print(f"HATA - Veri kaydedilirken hata: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def extract_title_from_content(content: str) -> str:
    """İçerikten başlık çıkar (markdown başlıklarına bakarak)"""
    lines = content.strip().split('\n')

    for line in lines:
        line = line.strip()
        # H1 başlık kontrolü (# ile başlayan)
        if line.startswith('# '):
            return line[2:].strip()

    # Başlık bulunamadıysa dosya adını kullan
    return "Untitled Document"


def load_document(file_path: str, model_name: str = DEFAULT_EMBEDDING_MODEL) -> int:
    """Tek bir dokümanı yükle ve işle"""
    try:
        # Dosya adından document_id oluştur
        base_name = os.path.basename(file_path)
        document_id = os.path.splitext(base_name)[0]

        print(f"INFO - Dosya yükleniyor: {file_path}")

        # Dosyayı oku
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Başlık çıkar
        title = extract_title_from_content(content)
        print(f"INFO - Başlık: {title}")

        # Dokümanı parçala
        chunks = chunk_document(content, title)

        # Veritabanına kaydet - model adını düzgün bir şekilde geçir
        return save_chunks_to_db(document_id, chunks, model_name)
    except Exception as e:
        print(f"HATA - Dosya yüklenirken hata: {e}")
        print(f"Dosya: {file_path}")
        return 0


def load_documents(path: str, model_name: str = DEFAULT_EMBEDDING_MODEL) -> int:
    """Dokümanları yükle ve işle"""
    total_chunks = 0

    if os.path.isfile(path):
        # Tek dosya
        print(f"📄 Dosya indeksleniyor: {path}")
        total_chunks = load_document(path, model_name)
    elif os.path.isdir(path):
        # Klasördeki tüm .txt ve .md dosyalarını işle
        print(f"📁 Klasör indeksleniyor: {path}")
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(('.txt', '.md')):
                    file_path = os.path.join(root, file)
                    chunks_count = load_document(file_path, model_name)
                    total_chunks += chunks_count
                    print(f"Yüklenen: {file} ({chunks_count} parça)")
    else:
        raise ValueError(f"Geçersiz dosya yolu: {path}")

    if total_chunks > 0:
        print(f"✅ {total_chunks} belge parçası başarıyla indekslendi")
    else:
        print("❌ Indekslenecek belge bulunamadı veya işlem sırasında hata oluştu")

    return total_chunks
