# app/llm.py
"""
LLM işlemleri.
"""
import json
import os
from pydantic import create_model, Field
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

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

# app/llm.py - Update this function

def query(question, template_name="default", model_name="DocumentResponse", embedding_model="all-MiniLM-L6-v2"):
    """
    Sorgu yap ve yanıtı döndür.
    """
    # Bileşenleri hazırla
    db = get_vectorstore(get_embeddings(embedding_model))
    llm = get_llm()
    retriever = db.as_retriever(search_kwargs={"k": 3})

    # Doğrudan şablon dosyasından içeriği oku
    with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        templates = json.load(f)

    if template_name not in templates:
        template_name = "default"

    system_content = templates[template_name]["messages"][0]["content"]
    user_content = templates[template_name]["messages"][1]["content"]

    # Basit prompt oluştur - format talimatlarını eklemeden
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_content),
        ("user", user_content)
    ])

    # LCEL zinciri oluştur
    rag_chain = (
            {"query": RunnablePassthrough(), "context": retriever}
            | prompt
            | llm
            | StrOutputParser()
    )

    # Belgeleri al
    docs = retriever.invoke(question)
    sources = [doc.page_content[:100] + "..." for doc in docs]

    # Yanıtı oluştur
    raw_answer = rag_chain.invoke(question)

    # Şema modeli oluştur (ancak parse işlemini deneme amaçlı yapacağız)
    response_model = load_model_schema(model_name)
    parser = PydanticOutputParser(pydantic_object=response_model)

    # Yanıtı parse etmeyi dene
    try:
        parsed_answer = parser.parse(raw_answer)
        return parsed_answer, sources
    except Exception as e:
        # Parse hatası olursa ham yanıtı döndür
        print(f"Not: Yapılandırılmış yanıt analizi başarısız, ham yanıt döndürülüyor. ({str(e)})")
        return raw_answer, sources