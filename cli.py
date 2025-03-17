#!/usr/bin/env python3
"""
RAG CLI: Yerel LLM kullanarak vektör tabanlı bilgi erişimi için basit CLI arayüzü.
"""
import os
import click
from app.db import setup_db
from app.embedding import load_documents
from app.llm import query
from app.utils import ensure_template_files_exist
from app.config import PROMPT_TEMPLATE_FILE, MODEL_SCHEMA_FILE
import json


@click.group()
def cli():
    """RAG CLI: Basit RAG sistemi için yönetim aracı"""
    ensure_template_files_exist()
    pass


@cli.command()
def init():
    """Veritabanını kur ve hazırla"""
    result = setup_db()
    if result:
        click.echo("✅ Veritabanı kurulumu tamamlandı")
    else:
        click.echo("❌ Veritabanı kurulumunda hata oluştu")


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def index(path):
    """Belgeleri vektörleştir ve veritabanına kaydet"""
    count = load_documents(path)
    click.echo(f"✅ {count} belge parçası işlendi ve veritabanına kaydedildi")


@cli.command()
@click.argument("question", type=str)
@click.option("--template", "-t", default="default", help="Kullanılacak prompt şablonu")
@click.option("--model", "-m", default="DocumentResponse", help="Kullanılacak yanıt modeli")
@click.option("--embedding", "-e", default=None, help="Kullanılacak embedding modeli")
def ask(question, template, model, embedding):
    """Sorgu yap ve cevap al"""
    print(f"🔍 Sorgulanıyor: '{question}' (şablon: {template}, model: {model})")

    # Default embedding değerini config'den al
    if embedding is None:
        from app.config import EMBEDDING_MODEL
        embedding = EMBEDDING_MODEL

    answer, sources = query(question, template, model, embedding)

    click.echo("\n📝 CEVAP:")
    click.echo("=" * 50)

    # Cevap bir model örneği ise yapılandırılmış şekilde yazdır
    if hasattr(answer, "__dict__"):
        for key, value in answer.__dict__.items():
            if key != "__pydantic_private__" and key != "model_fields" and key != "model_config":
                click.echo(f"\n📌 {key.upper()}:")
                if isinstance(value, list):
                    for i, item in enumerate(value, 1):
                        click.echo(f"  {i}. {item}")
                else:
                    click.echo(f"  {value}")
    else:
        # Ham yanıt
        click.echo(answer)

    click.echo("\n📚 KAYNAKLAR:")
    click.echo("=" * 50)
    for i, source in enumerate(sources, 1):
        click.echo(f"{i}. {source}")


@cli.command()
def templates():
    """Mevcut şablonları listele"""
    with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        templates = json.load(f)

    click.echo("📋 Kullanılabilir Şablonlar:")
    click.echo("=" * 50)
    for name in templates.keys():
        click.echo(f"• {name}")


@cli.command()
def models():
    """Mevcut yanıt modellerini listele"""
    with open(MODEL_SCHEMA_FILE, 'r', encoding='utf-8') as f:
        models = json.load(f)

    click.echo("🧩 Kullanılabilir Yanıt Modelleri:")
    click.echo("=" * 50)
    for name, schema in models.items():
        fields = ", ".join(schema["fields"].keys())
        click.echo(f"• {name} (alanlar: {fields})")


@cli.command()
def status():
    """Sistem durumunu kontrol et"""
    from app.db import get_db_connection
    import psycopg2
    from app.config import LLM_MODEL

    click.echo("🔍 Sistem Durumu Kontrolü")
    click.echo("=" * 50)

    # Veritabanı kontrolü
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        doc_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        click.echo(f"✅ Veritabanı: Bağlantı başarılı ({doc_count} belge parçası)")
    except Exception as e:
        click.echo(f"❌ Veritabanı: Bağlantı hatası ({str(e)})")

    # Ollama kontrolü
    import subprocess
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if LLM_MODEL in result.stdout:
            click.echo(f"✅ Ollama: '{LLM_MODEL}' modeli mevcut")
        else:
            click.echo(f"⚠️ Ollama: '{LLM_MODEL}' modeli bulunamadı, indirmeniz gerekebilir")
    except Exception as e:
        click.echo(f"❌ Ollama: Çalışmıyor veya kurulu değil ({str(e)})")


@cli.command()
@click.option('--port', '-p', default=8000, help="API servis portu")
def serve(port):
    """API servisi olarak başlat"""
    from app.api import start_api
    click.echo(f"🚀 API servisi başlatılıyor: http://localhost:{port}")
    start_api(port)


if __name__ == "__main__":
    cli()