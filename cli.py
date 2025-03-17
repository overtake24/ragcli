#!/usr/bin/env python3
"""
RAG CLI: Yerel LLM kullanarak vektör tabanlı bilgi erişimi için CLI arayüzü.
"""
import os
import json
import click
import time
from typing import Optional, List, Dict, Any

from app.db import setup_db
from app.embedding import load_documents
from app.llm import query, load_model_schema, load_prompt_template
from app.utils import ensure_template_files_exist
from app.config import MODEL_SCHEMA_FILE, PROMPT_TEMPLATE_FILE


@click.group()
def cli():
    """RAG CLI: Basit RAG sistemi için yönetim aracı"""
    ensure_template_files_exist()
    pass


@cli.command()
def init():
    """Veritabanını kur"""
    result = setup_db()
    if result:
        click.echo("Veritabanı kurulumu tamamlandı")
    else:
        click.echo("Veritabanı kurulumunda hata oluştu")


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def index(path):
    """Belgeleri vektörleştir ve veritabanına kaydet"""
    count = load_documents(path)
    click.echo(f"{count} belge parçası işlendi ve veritabanına kaydedildi")


@cli.command()
@click.argument('question')
@click.option('--template', '-t', default="default", help="Kullanılacak şablon adı")
@click.option('--model', '-m', default="DocumentResponse", help="Kullanılacak model adı")
@click.option('--embedding', '-e', default="all-MiniLM-L6-v2", help="Kullanılacak embedding modeli")
def ask(question, template, model, embedding):
    """Sorgu yap"""
    answer, sources = query(question, template, model, embedding_model=embedding)
    click.echo("\n=== CEVAP ===")

    # Cevap bir model örneği ise yapılandırılmış şekilde yazdır
    if hasattr(answer, "__dict__"):
        for key, value in answer.__dict__.items():
            if key != "__pydantic_private__" and key != "model_fields" and key != "model_config":
                click.echo(f"\n-- {key.upper()} --")
                click.echo(value if not isinstance(value, list) else "\n".join([f"- {item}" for item in value]))
    else:
        # Ham yanıt
        click.echo(answer)

    click.echo("\n=== KAYNAKLAR ===")
    for i, source in enumerate(sources, 1):
        click.echo(f"{i}. {source}")


@cli.command()
@click.option('--model', '-m', default="DocumentResponse", help="Düzenlenecek model adı")
def edit_model(model):
    """Model şablonunu düzenle"""
    file_path = MODEL_SCHEMA_FILE

    # Dosya yoksa, varsayılan şablonları oluştur
    load_model_schema(model)

    click.echo(f"Şablon dosyası: {file_path}")
    click.echo("Dosyayı düzenledikten sonra programı tekrar çalıştırın.")

    # Dosyayı varsayılan editörle aç
    click.edit(filename=file_path)


@cli.command()
@click.option('--template', '-t', default="default", help="Düzenlenecek şablon adı")
def edit_prompt(template):
    """Prompt şablonunu düzenle"""
    file_path = PROMPT_TEMPLATE_FILE

    # Dosya yoksa, varsayılan şablonları oluştur
    load_prompt_template(template)

    click.echo(f"Şablon dosyası: {file_path}")
    click.echo("Dosyayı düzenledikten sonra programı tekrar çalıştırın.")

    # Dosyayı varsayılan editörle aç
    click.edit(filename=file_path)


@cli.command()
@click.option('--port', '-p', default=8000, help="Servis portu")
def serve(port):
    """API servisi olarak başlat"""
    import uvicorn
    from fastapi import FastAPI, HTTPException, Depends, Query
    from pydantic import BaseModel as FastAPIModel, Field
    from typing import Optional, List

    app = FastAPI(title="RAG API")

    class QueryRequest(FastAPIModel):
        query: str
        template: Optional[str] = "default"
        model: Optional[str] = "DocumentResponse"
        embedding_model: Optional[str] = "all-MiniLM-L6-v2"

    class IndexTextRequest(FastAPIModel):
        text: str
        document_id: Optional[str] = None
        title: Optional[str] = None

    class BlogToRagRequest(FastAPIModel):
        force_sync_all: Optional[bool] = False
        blog_db_connection: Optional[str] = None

    class SyncResult(FastAPIModel):
        post_id: int
        title: str
        status: str
        message: Optional[str] = None

    class DeleteDocumentRequest(FastAPIModel):
        document_id: str

    class UpdateDocumentRequest(FastAPIModel):
        document_id: str
        text: str
        title: Optional[str] = None

    class DocumentInfo(FastAPIModel):
        document_id: str
        title: str
        chunk_count: int
        last_updated: str

    async def import_blog_to_rag_module():
        """Blog to RAG modülünü dinamik olarak içe aktar"""
        try:
            import sys
            import importlib.util

            # blog_to_rag.py dosyasının tam yolunu bul
            script_dir = os.path.dirname(os.path.realpath(__file__))
            module_path = os.path.join(script_dir, "blog_to_rag.py")

            if not os.path.exists(module_path):
                module_path = "blog_to_rag.py"  # Mevcut dizinde ara

            if not os.path.exists(module_path):
                raise ImportError("blog_to_rag.py dosyası bulunamadı")

            # Modülü dinamik olarak yükle
            spec = importlib.util.spec_from_file_location("blog_to_rag", module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["blog_to_rag"] = module
            spec.loader.exec_module(module)

            return module
        except Exception as e:
            raise ImportError(f"Blog to RAG modülü yüklenirken hata: {str(e)}")

    @app.post("/query")
    async def query_endpoint(request: QueryRequest):
        answer, sources = query(request.query, request.template, request.model, request.embedding_model)

        # Yanıt bir model örneği ise
        if hasattr(answer, "__dict__"):
            result = {}
            for key, value in answer.__dict__.items():
                if key != "__pydantic_private__" and key != "model_fields" and key != "model_config":
                    result[key] = value
        else:
            # Ham yanıt
            result = {"answer": answer}

        return {
            "result": result,
            "sources": sources
        }

    @app.post("/index_text")
    async def index_text_endpoint(request: IndexTextRequest):
        """API üzerinden metin indeksle"""
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
                # Başlık varsa ekle
                if title:
                    f.write(f"# {title}\n\n")
                f.write(text)

            # Dosyayı indeksle
            count = load_documents(file_path)

            return {
                "status": "success",
                "message": f"{count} belge parçası işlendi ve veritabanına kaydedildi",
                "document_id": document_id
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    @app.post("/blog_to_rag", response_model=List[SyncResult])
    async def blog_to_rag_endpoint(request: BlogToRagRequest):
        """Blog verilerini RAG veritabanına aktarır"""
        try:
            # blog_to_rag modülünü dinamik olarak içe aktar
            blog_to_rag = await import_blog_to_rag_module()

            # Bağlantı bilgisini güncelle (isteğe bağlı)
            if request.blog_db_connection:
                blog_to_rag.BLOG_DB_CONNECTION = request.blog_db_connection

            # Blog içeriklerini senkronize et
            results = blog_to_rag.sync_blog_to_rag(force_sync_all=request.force_sync_all)

            # Sonuçları dönüştür
            sync_results = []
            for result in results:
                sync_results.append(SyncResult(
                    post_id=result["post_id"],
                    title=result["title"],
                    status=result["result"].get("status", "unknown"),
                    message=result["result"].get("message", "")
                ))

            return sync_results

        except ImportError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Blog senkronizasyonu sırasında hata: {str(e)}")

    @app.get("/sync_status")
    async def sync_status_endpoint():
        """Senkronizasyon durumunu kontrol et"""
        try:
            sync_file = "blog_sync.json"

            if not os.path.exists(sync_file):
                return {
                    "synchronized": False,
                    "last_sync_id": 0,
                    "last_sync_time": None
                }

            with open(sync_file, 'r') as f:
                data = json.load(f)

            return {
                "synchronized": True,
                "last_sync_id": data.get("last_sync_id", 0),
                "last_sync_time": data.get("last_sync_time"),
                "last_sync_time_formatted": time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(data.get("last_sync_time", 0))
                ) if data.get("last_sync_time") else None
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Senkronizasyon durumu kontrolü sırasında hata: {str(e)}")

    @app.delete("/documents/{document_id}")
    async def delete_document_endpoint(document_id: str):
        """Belirli bir belgeyi sil"""
        try:
            from app.db import get_db_connection

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
            raise HTTPException(status_code=500, detail=f"Belge silinirken hata: {str(e)}")

    @app.put("/documents/{document_id}")
    async def update_document_endpoint(document_id: str, request: UpdateDocumentRequest):
        """Belirli bir belgeyi güncelle"""
        try:
            # Önce eski belgeyi sil
            delete_response = await delete_document_endpoint(document_id)

            # Yeni içeriği ekle
            index_request = IndexTextRequest(
                text=request.text,
                document_id=document_id,
                title=request.title or document_id
            )

            index_response = await index_text_endpoint(index_request)

            return {
                "status": "success",
                "document_id": document_id,
                "delete_info": delete_response,
                "index_info": index_response
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Belge güncellenirken hata: {str(e)}")

    @app.get("/documents")
    async def list_documents_endpoint(limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
        """İndekslenmiş belgeleri listele"""
        try:
            from app.db import get_db_connection

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
            raise HTTPException(status_code=500, detail=f"Belge listesi alınırken hata: {str(e)}")

    @app.get("/health")
    async def health_check():
        """Sistem sağlık kontrolü"""
        try:
            from app.db import get_db_connection

            # Veritabanı bağlantısını kontrol et
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()

            # Embedding modelini kontrol et
            import sentence_transformers
            model_info = {
                "name": "all-MiniLM-L6-v2",
                "library": sentence_transformers.__version__
            }

            return {
                "status": "healthy",
                "database": "connected",
                "embedding_model": model_info,
                "api_version": "1.0.0"
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    @app.get("/templates")
    async def list_templates():
        with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    @app.get("/models")
    async def list_models():
        with open(MODEL_SCHEMA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    # API servisini başlat
    click.echo(f"API servisi başlatılıyor: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    cli()