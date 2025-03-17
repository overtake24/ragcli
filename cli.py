#!/usr/bin/env python3
"""
RAG CLI: Yerel LLM kullanarak vektör tabanlı bilgi erişimi için CLI arayüzü.
"""
import os
import json
import click
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
def ask(question, template, model):
    """Sorgu yap"""
    answer, sources = query(question, template, model)
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
    from fastapi import FastAPI
    from pydantic import BaseModel as FastAPIModel
    from typing import Optional

    app = FastAPI(title="RAG API")

    class QueryRequest(FastAPIModel):
        query: str
        template: Optional[str] = "default"
        model: Optional[str] = "DocumentResponse"

    @app.post("/query")
    async def query_endpoint(request: QueryRequest):
        answer, sources = query(request.query, request.template, request.model)

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