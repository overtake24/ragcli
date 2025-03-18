# app/llm.py
"""
LLM işlemleri.
"""
import json
import os
import re
from pydantic import create_model, Field
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_core.documents import Document

from app.config import LLM_MODEL, MODEL_SCHEMA_FILE, PROMPT_TEMPLATE_FILE
from app.embedding import get_embeddings
from app.db import get_vectorstore


def get_llm():
    """
    LLM modelini döndür.
    """
    return Ollama(model=LLM_MODEL)


def load_model_schema(schema_name="DocumentResponse", schema_file=MODEL_SCHEMA_FILE):
    """
    Dinamik model şablonunu yükle.
    """
    if not os.path.exists(schema_file):
        os.makedirs(os.path.dirname(schema_file), exist_ok=True)
        default_schema = {
            "DocumentResponse": {
                "fields": {
                    "title": {"type": "str", "description": "Belgenin başlığı"},
                    "summary": {"type": "str", "description": "İçerik özeti"},
                    "key_points": {"type": "list[str]", "description": "Anahtar noktalar"}
                }
            }
        }
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(default_schema, f, indent=2, ensure_ascii=False)

    with open(schema_file, 'r', encoding='utf-8') as f:
        schemas = json.load(f)

    if schema_name not in schemas:
        raise ValueError(f"Şema '{schema_name}' bulunamadı")

    schema_def = schemas[schema_name]
    fields = {}

    for field_name, field_props in schema_def["fields"].items():
        field_type = eval(field_props["type"])
        fields[field_name] = (field_type, Field(description=field_props["description"]))

    return create_model(schema_name, **fields)


def load_prompt_template(template_name="default", template_file=PROMPT_TEMPLATE_FILE):
    """
    Dinamik prompt şablonunu yükle.
    """
    if not os.path.exists(template_file):
        os.makedirs(os.path.dirname(template_file), exist_ok=True)
        default_templates = {
            "default": {
                "messages": [
                    {"role": "system",
                     "content": "Sen bir uzman asistansın. Kullanıcının sorgusunu, verilen bağlamı kullanarak yanıtla."},
                    {"role": "user", "content": "Soru: {query}\nBağlam: {context}\nCevap:"}
                ]
            }
        }
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(default_templates, f, indent=2, ensure_ascii=False)

    with open(template_file, 'r', encoding='utf-8') as f:
        templates = json.load(f)

    if template_name not in templates:
        raise ValueError(f"Şablon '{template_name}' bulunamadı")

    template_def = templates[template_name]
    messages = [(msg["role"], msg["content"]) for msg in template_def["messages"]]

    return ChatPromptTemplate.from_messages(messages)


def create_rag_chain(template_name="default"):
    """
    LCEL kullanarak RAG zinciri oluştur.
    """
    llm = get_llm()
    db = get_vectorstore(get_embeddings())
    retriever = db.as_retriever(search_kwargs={"k": 3})
    prompt_template = load_prompt_template(template_name)

    # LCEL ile zincir oluştur
    return (
            {"query": RunnablePassthrough(), "context": retriever}
            | prompt_template
            | llm
            | StrOutputParser()
    )


# app/llm.py dosyasında parse_structured_data fonksiyonu bu şekilde değiştirilmeli:

def parse_structured_data(question, context, model_name, template_name, sources):
    """
    Yapılandırılmış veri modelleri için metinsel verileri analiz eder.

    Args:
        question: Kullanıcı sorusu
        context: Bağlam metni
        model_name: Kullanılacak model adı (FilmInfo, BookInfo, PersonInfo vb.)
        template_name: Kullanılacak şablon adı (film_query, book_query, person_query vb.)
        sources: Kaynak belgeler

    Returns:
        Yapılandırılmış veri nesnesi ve kullanılan kaynaklar
    """
    print(f"INFO - Yapılandırılmış veri sorgusu algılandı: {model_name} modeli ile işleniyor...")

    # Prompt hazırlama
    prompt = f"""Sen bir veri ayrıştırma uzmanısın. Verilen metni analiz ederek ilgili tüm bilgileri çıkar ve JSON formatında yapılandır.

Soru: {question}

İlgili belgeler:
{context}

Metinden tüm önemli bilgileri çıkar ve aşağıdaki JSON formatında döndür:

"""

    # Model tipine göre şablon ekleme
    if model_name == "FilmInfo":
        prompt += """{
  "title": "Filmin başlığı",
  "plot_summary": "Film özeti",
  "cast": [
    {
      "name": "Oyuncu adı",
      "role": "Oynadığı karakter"
    }
  ],
  "director": "Yönetmen adı",
  "genre": ["Tür1", "Tür2"],
  "release_year": "Çıkış yılı",
  "imdb_rating": "IMDb puanı"
}"""
    elif model_name == "BookInfo":
        prompt += """{
  "title": "Kitap başlığı",
  "author": "Yazar adı",
  "summary": "Kitap özeti",
  "genre": ["Tür1", "Tür2"],
  "publish_year": "Yayın yılı",
  "page_count": "Sayfa sayısı",
  "rating": "Puanlama"
}"""
    elif model_name == "PersonInfo":
        prompt += """{
  "name": "Kişinin adı",
  "birth_date": "Doğum tarihi",
  "death_date": "Ölüm tarihi (varsa)",
  "nationality": "Uyruk",
  "occupation": ["Meslek1", "Meslek2"],
  "biography": "Kısa biyografi",
  "notable_works": ["Eser1", "Eser2"]
}"""
    else:
        # Genel yapılandırılmış veri formatı
        prompt += f"Model için uygun JSON formatını kullan ({model_name})"

    prompt += "\n\nSadece JSON döndür, başka açıklama ekleme. Eğer belirli bir bilgiyi bulamazsan, ilgili alanı boş bırak veya \"\" kullan, null kullanma."

    # LLM çağrısı
    llm = get_llm()
    raw_answer = llm(prompt)

    print(f"DEBUG - Yapılandırılmış veri LLM yanıtı: {raw_answer[:200]}...")

    # JSON formatını çıkar
    try:
        # Kod bloğu işaretlerini kaldır (```json ve ```)
        cleaned_json = raw_answer
        if "```" in cleaned_json:
            # Sadece içeriği al
            code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
            matches = re.findall(code_block_pattern, cleaned_json)
            if matches:
                cleaned_json = matches[0].strip()

        # JSON'ı parse et
        structured_data = json.loads(cleaned_json)

        # Null değerleri varsayılan değerlerle değiştir
        for key in structured_data:
            if structured_data[key] is None:
                # Liste tipleri için boş liste
                if key in ["occupation", "notable_works", "genre", "cast", "key_points"]:
                    structured_data[key] = []
                # String türleri için boş string
                else:
                    structured_data[key] = ""

        # Model şablonunu yükle
        model_schema = load_model_schema(model_name)

        # Modele göre dönüşüm yap
        try:
            result = model_schema(**structured_data)
            return result, sources
        except Exception as e:
            print(f"HATA: Yapılandırılmış veri modele dönüştürülürken hata: {e}")
            # Varsayılan değerlerle nesne oluştur
            default_values = {}
            for field_name in model_schema.__annotations__:
                if field_name in ["occupation", "notable_works", "genre", "cast", "key_points"]:
                    default_values[field_name] = []
                else:
                    default_values[field_name] = "Bilgi bulunamadı"

            # Bulunan değerleri ekle
            for key, value in structured_data.items():
                if key in default_values and value not in [None, ""]:
                    default_values[key] = value

            return model_schema(**default_values), sources

    except Exception as e:
        print(f"HATA: Yapılandırılmış veri ayrıştırılamadı: {e}")

        # Boş bir şablon nesne döndür - varsayılan değerlerle
        empty_schema = load_model_schema(model_name)
        default_values = {}
        for field_name in empty_schema.__annotations__:
            if field_name in ["occupation", "notable_works", "genre", "cast", "key_points"]:
                default_values[field_name] = []
            else:
                default_values[field_name] = "Bilgi bulunamadı"

        return empty_schema(**default_values), sources


# İlgili llm.py bölümü güncellendi - veritabanı sorgulama ve sorgu filtreleme

def query(question, template_name="default", model_name="DocumentResponse", embedding_model=None):
    """
    Sorgu yap ve yanıtı döndür.
    """
    from app.config import EMBEDDING_MODEL, SIMILARITY_THRESHOLD, MAX_DOCUMENTS, DOCUMENT_CATEGORIES
    if embedding_model is None:
        embedding_model = EMBEDDING_MODEL

    print(f"INFO - Sorgu embedding modeli: {embedding_model}")
    embeddings = get_embeddings(embedding_model)
    db = get_vectorstore(embeddings)

    # Veritabanı bağlantısını ve tabloları kontrol et
    print("DEBUG - Veritabanı kontrol ediliyor")
    docs = []
    docs_with_scores = []  # Skorlarla birlikte belgeleri sakla

    try:
        # Kategori bazlı filtreleme için sorgu analizi
        query_category = detect_query_category(question)
        print(f"INFO - Algılanan sorgu kategorisi: {query_category}")

        # Benzerlik skorları ile birlikte belgeleri getir
        try:
            # similarity_search_with_score kullanarak benzerlik skorlarını al
            docs_with_scores = db.similarity_search_with_score(question,
                                                               k=MAX_DOCUMENTS * 2)  # Daha fazla belge getir, sonra filtreleyeceğiz

            # Belgelerin benzerlik skorlarını göster
            print(f"\n🔍 '{question}' sorgusu için benzerlik skorları:")
            print("=" * 50)
            for i, (doc, score) in enumerate(docs_with_scores):
                source = doc.metadata.get('source', 'bilinmiyor')
                # Kosinüs benzerliği genellikle [0-1] aralığında olur, 1 en yüksek benzerlik
                # Bazı implementasyonlarda L2 mesafesi kullanılır, bu durumda düşük değerler daha iyi benzerliği gösterir
                # Formata göre skoru ayarla
                score_display = score if score <= 1.0 else f"{1.0 / score:.4f}"
                similarity_percent = float(score_display) * 100 if score <= 1.0 else float(1.0 / score) * 100

                print(f"Belge {i + 1}: {source} - Benzerlik: {score_display} ({similarity_percent:.2f}%)")
                content_preview = doc.page_content[:100].replace('\n', ' ')
                print(f"  İçerik: {content_preview}...")

            # Filtreleme işlemleri
            filtered_docs_with_scores = []

            # 1. Benzerlik eşiği filtresi
            for doc, score in docs_with_scores:
                # Skor formatına göre kontrol et
                score_value = score if score <= 1.0 else 1.0 / score
                if score_value >= SIMILARITY_THRESHOLD:
                    filtered_docs_with_scores.append((doc, score))
                else:
                    print(
                        f"⚠️ Düşük benzerlik skoru ({score_value:.4f}) nedeniyle filtrelendi: {doc.metadata.get('source')}")

            # 2. Kategori filtresi (film, kitap, kişi vb.)
            if query_category and query_category != "other":
                category_docs = []
                for doc, score in filtered_docs_with_scores:
                    doc_category = detect_document_category(doc.page_content)
                    if doc_category == query_category:
                        category_docs.append((doc, score))

                # Eğer kategori filtrelemesi sonucunda belge kaldıysa, sadece onları kullan
                if category_docs:
                    print(
                        f"📌 '{query_category}' kategorisine göre filtreleme yapıldı: {len(category_docs)}/{len(filtered_docs_with_scores)} belge")
                    filtered_docs_with_scores = category_docs

            # Son olarak en benzer MAX_DOCUMENTS belge ile devam et
            filtered_docs_with_scores = sorted(filtered_docs_with_scores,
                                               key=lambda x: x[1] if x[1] <= 1.0 else 1.0 / x[1], reverse=True)[
                                        :MAX_DOCUMENTS]

            # Sadece belgeleri docs listesine ekle
            docs = [doc for doc, _ in filtered_docs_with_scores]

            print(f"📊 Filtreleme sonrası {len(docs)} belge kaldı")

        except Exception as e:
            print(f"Benzerlik skorları ile belge getirme hatası: {e}")

            # Backup olarak standart sorgu yöntemini dene
            try:
                retriever = db.as_retriever(search_kwargs={"k": MAX_DOCUMENTS})
                docs = retriever.get_relevant_documents(question)
                print(f"Standart retriever ile {len(docs)} belge bulundu")
            except Exception as e2:
                print(f"Standart retriever hatası: {e2}")

        # Veritabanı hatası durumunda yerel dosyalardan belgeleri yükleme işlemi devam ediyor...
        if not docs:
            try:
                # Tablo kontrolü ve yerel dosya yükleme işlemleri... (mevcut kod devam ediyor)
                pass
            except Exception as e:
                print(f"DEBUG - Veritabanı hatası: {e}")

    except Exception as e:
        print(f"DEBUG - Genel sorgu hatası: {e}")

    print(f"DEBUG - Sorgu: {question}")
    print(f"DEBUG - Toplam {len(docs)} belge getirildi")

    # Belgeleri formatla
    context = ""
    for i, doc in enumerate(docs):
        source = doc.metadata.get("source", f"Belge {i + 1}")
        context += f"[BELGE {i + 1}] {source}:\n{doc.page_content}\n\n"

    if not docs:
        context = "Hiç ilgili belge bulunamadı."

    # Kaynak içerik özetleri ve benzerlik skorları
    sources = []
    for i, doc in enumerate(docs):
        doc_source = doc.page_content[:100] + "..."
        # Benzerlik skoru varsa ekle
        if i < len(filtered_docs_with_scores):
            score = filtered_docs_with_scores[i][1]
            score_display = score if score <= 1.0 else f"{1.0 / score:.4f}"
            doc_source = f"{doc_source} [Benzerlik: {score_display}]"
        sources.append(doc_source)

    # Yapılandırılmış veri modelleri için özel işleme
    if model_name in ["FilmInfo", "BookInfo", "PersonInfo"] or template_name in ["film_query", "book_query",
                                                                                 "person_query", "structured_data"]:
        return parse_structured_data(question, context, model_name, template_name, sources)

    # Diğer işlemler aynen devam ediyor...
    # LLM çağrısı ve yanıt işleme kodları

    # Rest of the function remains the same...


# llm.py dosyasına SADECE BUNLARI ekleyin
# Fonksiyonların tanımları (en sonda olacak şekilde)

def detect_query_category(query):
    """
    Sorgu metnine göre hangi kategoriyle ilgili olduğunu tespit eder
    """
    query_lower = query.lower()

    # Film/dizi kategorisi
    film_keywords = ["film", "movie", "sinema", "cinema", "yönetmen", "director",
                     "oyuncu", "actor", "izle", "watch", "imdb", "çekim", "shooting"]

    # Kitap kategorisi
    book_keywords = ["kitap", "book", "yazar", "author", "eser", "roman", "novel",
                     "sayfa", "page", "okuma", "reading", "basım", "publication"]

    # Kişi/biyografi kategorisi
    person_keywords = ["kim", "who", "kişi", "person", "doğum", "birth", "ölüm", "death",
                       "hayat", "life", "ne zaman", "when", "meslek", "occupation", "biyografi", "biography"]

    # Kategori belirle
    film_score = sum(1 for word in film_keywords if word in query_lower)
    book_score = sum(1 for word in book_keywords if word in query_lower)
    person_score = sum(1 for word in person_keywords if word in query_lower)

    # En yüksek skora sahip kategoriyi döndür
    if film_score > book_score and film_score > person_score:
        return "film"
    elif book_score > film_score and book_score > person_score:
        return "book"
    elif person_score > film_score and person_score > book_score:
        return "person"

    # Belirsizse "other" döndür
    return "other"


def filter_documents_by_category(docs, category):
    """
    Belgeleri kategoriye göre filtreler
    """
    if category == "other":
        return docs

    # Kategori anahtar kelimeleri
    category_keywords = {
        "film": ["film", "movie", "sinema", "cinema", "yönetmen", "director", "cast", "oyuncu",
                 "imdb", "actor", "izle", "watch", "çekim", "shooting"],
        "book": ["kitap", "book", "yazar", "author", "eser", "roman", "novel", "sayfa",
                 "page", "okuma", "reading", "basım", "publication"],
        "person": ["kişi", "person", "doğum", "birth", "ölüm", "death", "hayat", "life",
                   "yaşam", "meslek", "occupation", "biyografi", "biography"]
    }

    # Seçilen kategorinin anahtar kelimeleri
    keywords = category_keywords.get(category, [])

    # İlgili belgeleri filtrele
    filtered_docs = []
    for doc in docs:
        doc_text = doc.page_content.lower()
        # En az 2 anahtar kelime eşleşmesi olan belgeleri seç
        keyword_matches = sum(1 for keyword in keywords if keyword in doc_text)
        if keyword_matches >= 2:
            filtered_docs.append(doc)

    # Eğer hiç belge kalmadıysa orijinal liste ile devam et
    if not filtered_docs and docs:
        print(f"⚠️ '{category}' kategorisi için uygun belge bulunamadı, tüm belgeler kullanılıyor")
        return docs

    print(f"ℹ️ '{category}' kategorisine göre {len(filtered_docs)}/{len(docs)} belge filtrelendi")
    return filtered_docs