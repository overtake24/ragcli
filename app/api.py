# app/api.py
"""
FastAPI API servisi için modül
"""
import os
import json
import time
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from app.db import get_db_connection, get_vectorstore
from app.embedding import get_embeddings, load_documents
from app.llm import query
from app.config import MODEL_SCHEMA_FILE, PROMPT_TEMPLATE_FILE


def start_api(port=8000):
    """
    API servisini başlat
    """
    app = FastAPI(title="RAG API",
                  description="Vektör tabanlı bilgi erişimi için API",
                  version="1.0.0")

    class QueryRequest(BaseModel):
        query: str = Field(..., description="Sorgunuz")
        template: Optional[str] = Field("default", description="Kullanılacak şablon")
        model: Optional[str] = Field("DocumentResponse", description="Kullanılacak yanıt modeli")
        embedding_model: Optional[str] = Field("all-MiniLM-L6-v2", description="Kullanılacak embedding modeli")

    class IndexTextRequest(BaseModel):
        text: str = Field(..., description="İndekslenecek metin içeriği")
        document_id: Optional[str] = Field(None, description="Belge ID (otomatik oluşturulur)")
        title: Optional[str] = Field(None, description="Belge başlığı")

    class DeleteDocumentRequest(BaseModel):
        document_id: str = Field(..., description="Silinecek belge ID")

    @app.post("/query", summary="Sorgu yap")
    async def query_endpoint(request: QueryRequest):
        try:
            answer, sources = query(
                request.query,
                request.template,
                request.model,
                request.embedding_model
            )

            # Yanıt bir model örneği ise
            if hasattr(answer, "__dict__"):
                result = {}
                for key, value in answer.__dict__.items():
                    if key not in ["__pydantic_private__", "model_fields", "model_config"]:
                        result[key] = value
            else:
                # Ham yanıt
                result = {"answer": answer}

            return {
                "result": result,
                "sources": sources
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/index_text", summary="Metin indeksle")
    async def index_text_endpoint(request: IndexTextRequest):
        try:
            text = request.text
            document_id = request.document_id or f"api_doc_{int(time.time())}"
            title = request.title or document_id

            if not text:
                return {"status": "error", "message": "Metin içeriği boş olamaz"}

            # Geçici bir dosya oluştur
            temp_dir = os.path.join(os.getcwd(), "temp_docs")
            os.makedirs(temp_dir, exist_ok=True)

            file_path = os.path.join(temp_dir, f"{document_id}.txt")

            # Metni dosyaya yaz
            with open(file_path, "w", encoding="utf-8") as f:
                if title:
                    f.write(f"# {title}\n\n")
                f.write(text)

            # Dosyayı indeksle
            count = load_documents(file_path)

            return {
                "status": "success",
                "message": f"{count} belge parçası oluşturuldu",
                "document_id": document_id
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @app.get("/templates", summary="Şablonları listele")
    async def list_templates():
        try:
            with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/models", summary="Modelleri listele")
    async def list_models():
        try:
            with open(MODEL_SCHEMA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/documents/{document_id}", summary="Belge sil")
    async def delete_document_endpoint(document_id: str):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Belgenin chunk'larını sil
            delete_query = """
            DELETE FROM document_chunks 
            WHERE document_id = %s
            RETURNING COUNT(*)
            """

            cursor.execute(delete_query, (document_id,))
            result = cursor.fetchone()
            deleted_count = result[0] if result else 0

            conn.commit()
            cursor.close()
            conn.close()

            return {
                "status": "success",
                "message": f"{deleted_count} belge parçası silindi",
                "document_id": document_id
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/documents", summary="Belgeleri listele")
    async def list_documents_endpoint(limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Belgeleri gruplandırarak listele
            query = """
            SELECT 
                document_id, 
                FIRST_VALUE(title) OVER (PARTITION BY document_id ORDER BY id) as title,
                COUNT(*) as chunk_count,
                MAX(created_at) as last_updated
            FROM document_chunks
            GROUP BY document_id
            ORDER BY last_updated DESC
            LIMIT %s OFFSET %s
            """

            cursor.execute(query, (limit, offset))
            results = cursor.fetchall()

            # Toplam belge sayısını al
            cursor.execute("SELECT COUNT(DISTINCT document_id) FROM document_chunks")
            total_count = cursor.fetchone()[0]

            documents = []
            for doc_id, title, chunk_count, last_updated in results:
                documents.append({
                    "document_id": doc_id,
                    "title": title,
                    "chunk_count": chunk_count,
                    "last_updated": last_updated.isoformat() if last_updated else None
                })

            cursor.close()
            conn.close()

            return {
                "documents": documents,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health", summary="Sağlık kontrolü")
    async def health_check():
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()

            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }

    # API servisini başlat
    uvicorn.run(app, host="0.0.0.0", port=port)