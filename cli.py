#!/usr/bin/env python3
"""
RAG CLI: Yerel LLM kullanarak vektör tabanlı bilgi erişimi için komut satırı arayüzü.
"""
import os
import click
import json
from app.db import setup_db
from app.embedding import load_documents
from app.llm import query
from app.utils import ensure_template_files_exist
from app.config import PROMPT_TEMPLATE_FILE, MODEL_SCHEMA_FILE


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """RAG CLI: Yerel LLM kullanarak vektör tabanlı bilgi erişimi aracı.

    Bu araç, Ollama üzerinde çalışan yerel bir LLM modelini kullanarak
    vektör veritabanı tabanlı bir RAG (Retrieval-Augmented Generation)
    sistemi kurmanızı ve yönetmenizi sağlar.
    """
    # Şablon dosyalarının varlığını kontrol et
    ensure_template_files_exist()
    pass


@cli.command(help="Veritabanını kur ve hazırla")
def init():
    """Veritabanını ve gerekli tabloları oluştur"""
    click.echo("🛠️  Veritabanı kurulumu başlatılıyor...")
    result = setup_db()
    if result:
        click.echo("✅ Veritabanı kurulumu başarıyla tamamlandı")
    else:
        click.echo("❌ Veritabanı kurulumunda hata oluştu")


@cli.command(help="Belgeleri vektörleştir ve veritabanına kaydet")
@click.argument('path', type=click.Path(exists=True))
@click.option('--model', '-m', default=None, help="Kullanılacak embedding modeli")
def index(path, model):
    """Belgeleri vektörleştir ve veritabanına kaydet"""
    if os.path.isfile(path):
        click.echo(f"📄 Dosya indeksleniyor: {path}")
    else:
        click.echo(f"📁 Klasör indeksleniyor: {path}")

    # Belgeleri indeksle
    count = load_documents(path, model)

    if count > 0:
        click.echo(f"✅ {count} belge parçası başarıyla indekslendi")
    else:
        click.echo("❌ Indekslenecek belge bulunamadı veya işlem sırasında hata oluştu")


@cli.command(help="Sorgu yap ve cevap al")
@click.argument("question", type=str)
@click.option("--template", "-t", default="default", help="Kullanılacak prompt şablonu")
@click.option("--model", "-m", default="DocumentResponse", help="Kullanılacak yanıt modeli")
@click.option("--embedding", "-e", default=None, help="Kullanılacak embedding modeli")
def ask(question, template, model, embedding):
    """Vektör veritabanına sorgu yap ve cevap al"""
    click.echo(f"🔍 Sorgulanıyor: '{question}'")
    click.echo(f"   Şablon: {template}, Model: {model}")

    # Default embedding değerini config'den al
    if embedding is None:
        from app.config import EMBEDDING_MODEL
        embedding = EMBEDDING_MODEL

    try:
        # Sorguyu yap
        answer, sources = query(question, template, model, embedding)

        # Cevabı göster
        click.echo("\n📝 CEVAP:")
        click.echo("=" * 80)

        # Cevap bir model örneği ise yapılandırılmış şekilde yazdır
        if hasattr(answer, "__dict__"):
            for key, value in answer.__dict__.items():
                if key not in ["__pydantic_private__", "model_fields", "model_config"]:
                    click.echo(f"\n📌 {key.upper()}:")
                    if isinstance(value, list):
                        for i, item in enumerate(value, 1):
                            click.echo(f"  {i}. {item}")
                    else:
                        click.echo(f"  {value}")
        else:
            # Sözlük veya başka bir yanıt tipi
            for key, value in answer.items():
                click.echo(f"\n📌 {key.upper()}:")
                if isinstance(value, list):
                    for i, item in enumerate(value, 1):
                        click.echo(f"  {i}. {item}")
                else:
                    click.echo(f"  {value}")

        # Kaynakları göster
        if sources:
            click.echo("\n📚 KAYNAKLAR:")
            click.echo("=" * 80)
            for i, source in enumerate(sources, 1):
                click.echo(f"{i}. {source}")

    except Exception as e:
        click.echo(f"❌ Sorgu işlenirken hata oluştu: {e}")


@cli.command(help="Mevcut şablonları listele")
def templates():
    """Kullanılabilir prompt şablonlarını listele"""
    try:
        with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            templates = json.load(f)

        click.echo("📋 Kullanılabilir Şablonlar:")
        click.echo("=" * 80)
        for name, template in templates.items():
            # Şablon örneğini göster
            system_message = template["messages"][0]["content"]
            click.echo(f"• {name}:")
            click.echo(f"  {system_message[:100]}...")
            click.echo()
    except Exception as e:
        click.echo(f"❌ Şablonlar yüklenirken hata oluştu: {e}")


@cli.command(help="Mevcut yanıt modellerini listele")
def models():
    """Kullanılabilir yanıt modellerini listele"""
    try:
        with open(MODEL_SCHEMA_FILE, 'r', encoding='utf-8') as f:
            models = json.load(f)

        click.echo("🧩 Kullanılabilir Yanıt Modelleri:")
        click.echo("=" * 80)
        for name, schema in models.items():
            fields = ", ".join(schema["fields"].keys())
            click.echo(f"• {name}:")
            click.echo(f"  Alanlar: {fields}")
            click.echo()
    except Exception as e:
        click.echo(f"❌ Modeller yüklenirken hata oluştu: {e}")


@cli.command(help="Prompt şablonlarını düzenle")
@click.option('--editor/--no-editor', default=True, help="Harici editör kullan")
def edit_prompt(editor):
    """Prompt şablonlarını düzenle"""
    if editor:
        # Harici editör ile düzenleme
        click.edit(filename=PROMPT_TEMPLATE_FILE)
        click.echo(f"✅ Prompt şablonları güncellendi: {PROMPT_TEMPLATE_FILE}")
    else:
        # Mevcut şablonları göster
        try:
            with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                templates = json.load(f)

            click.echo(json.dumps(templates, indent=2, ensure_ascii=False))
            click.echo(f"\n✏️ Şablonları düzenlemek için dosyayı açın: {PROMPT_TEMPLATE_FILE}")
        except Exception as e:
            click.echo(f"❌ Şablonlar yüklenirken hata oluştu: {e}")


@cli.command(help="Model şablonlarını düzenle")
@click.option('--editor/--no-editor', default=True, help="Harici editör kullan")
def edit_model(editor):
    """Model şablonlarını düzenle"""
    if editor:
        # Harici editör ile düzenleme
        click.edit(filename=MODEL_SCHEMA_FILE)
        click.echo(f"✅ Model şablonları güncellendi: {MODEL_SCHEMA_FILE}")
    else:
        # Mevcut modelleri göster
        try:
            with open(MODEL_SCHEMA_FILE, 'r', encoding='utf-8') as f:
                models = json.load(f)

            click.echo(json.dumps(models, indent=2, ensure_ascii=False))
            click.echo(f"\n✏️ Modelleri düzenlemek için dosyayı açın: {MODEL_SCHEMA_FILE}")
        except Exception as e:
            click.echo(f"❌ Modeller yüklenirken hata oluştu: {e}")


@cli.command(help="Sistem durumunu kontrol et")
def status():
    """Sistem bileşenlerinin durumunu kontrol et"""
    click.echo("🔍 Sistem Durumu Kontrolü")
    click.echo("=" * 80)

    # Veritabanı kontrolü
    try:
        from app.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        doc_count = cursor.fetchone()[0]

        # Belge türlerini kontrol et
        cursor.execute("SELECT COUNT(DISTINCT document_id) FROM document_chunks")
        unique_docs = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        click.echo(f"✅ Veritabanı: Bağlantı başarılı")
        click.echo(f"   - {doc_count} belge parçası ({unique_docs} benzersiz belge)")
    except Exception as e:
        click.echo(f"❌ Veritabanı: Bağlantı hatası ({str(e)})")

    # Ollama kontrolü
    import subprocess
    try:
        from app.config import LLM_MODEL
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            if LLM_MODEL in result.stdout:
                click.echo(f"✅ Ollama: '{LLM_MODEL}' modeli yüklü")
            else:
                click.echo(f"⚠️ Ollama: '{LLM_MODEL}' modeli bulunamadı, indirmeniz gerekebilir:")
                click.echo(f"   ollama pull {LLM_MODEL}")
        else:
            raise Exception("Ollama çalıştırılamadı")
    except Exception as e:
        click.echo(f"❌ Ollama: Çalışmıyor veya kurulu değil ({str(e)})")
        click.echo("   Kurulum için: https://ollama.ai/download")

    # Embedding modeli kontrolü
    try:
        from app.config import EMBEDDING_MODEL
        from sentence_transformers import SentenceTransformer

        click.echo(f"🔄 Embedding modeli yükleniyor: {EMBEDDING_MODEL}...")
        model = SentenceTransformer(EMBEDDING_MODEL)
        embedding_size = model.get_sentence_embedding_dimension()

        click.echo(f"✅ Embedding Modeli: '{EMBEDDING_MODEL}'")
        click.echo(f"   - Vektör boyutu: {embedding_size}")
    except Exception as e:
        click.echo(f"❌ Embedding Modeli: Yüklenemedi ({str(e)})")


@cli.command(help="API servisi olarak başlat")
@click.option('--port', '-p', default=8000, help="API servis portu")
@click.option('--host', '-h', default="0.0.0.0", help="API servis host adresi")
def serve(port, host):
    """FastAPI tabanlı API servisi olarak başlat"""
    try:
        from app.api import start_api
        click.echo(f"🚀 API servisi başlatılıyor: http://{host}:{port}")
        click.echo("   API belgeleri: http://localhost:{port}/docs")
        start_api(port, host)
    except Exception as e:
        click.echo(f"❌ API servisi başlatılamadı: {e}")
        click.echo("   'pip install fastapi uvicorn' komutunu çalıştırın.")


if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        click.echo(f"❌ Beklenmeyen hata: {e}")
