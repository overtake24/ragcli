#!/usr/bin/env python3
"""
RAG sorgu tanılama aracı - bağlam ve LLM yanıt aşamalarını inceler
"""
import os
import sys
import json
import numpy as np
from typing import List, Dict, Any, Optional

from app.db import get_db_connection
from app.embedding import get_embedding_model
from app.config import PROMPT_TEMPLATE_FILE, LLM_MODEL
from langchain_community.llms import Ollama


def cosine_similarity(a, b):
    """İki vektör arasındaki kosinüs benzerliğini hesaplar"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def debug_query(query: str):
    """RAG sorgu sürecini adım adım inceler"""
    print(f"🔍 Sorgu inceleniyor: '{query}'")

    try:
        # 1. Embedding oluştur
        print("\n1️⃣ Embedding modeli yükleniyor...")
        model = get_embedding_model()
        query_vector = model.encode(query)
        print(f"   Sorgu vektörü boyutu: {len(query_vector)}")

        # 2. Benzer belgeleri ara
        print("\n2️⃣ Veritabanında benzer belgeler aranıyor...")
        conn = get_db_connection()
        cursor = conn.cursor()

        # 2.1 Scandinavia içeren dokümanları kontrol et
        cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE content ILIKE %s", ('%scandinavia%',))
        scandinavia_count = cursor.fetchone()[0]
        print(f"   'Scandinavia' içeren belge sayısı: {scandinavia_count}")

        # 2.2 Manuel benzerlik hesapla
        cursor.execute("SELECT id, document_id, title, content FROM document_chunks")
        documents = cursor.fetchall()
        print(f"   Toplam belge sayısı: {len(documents)}")

        similarities = []
        for doc_id, document_id, title, content in documents:
            doc_vector = model.encode(content[:1000])  # İlk 1000 karakter yeterli olacaktır
            sim = cosine_similarity(query_vector, doc_vector)
            similarities.append((doc_id, document_id, title, sim))

        # En benzer 3 belgeyi yazdır
        top_similar = sorted(similarities, key=lambda x: x[3], reverse=True)[:3]
        print("\n   En benzer belgeler:")
        for doc_id, document_id, title, sim in top_similar:
            print(f"     - {document_id} ({title}): {sim:.4f}")

        # 3. Benzer belgelerden bağlam oluştur
        print("\n3️⃣ Bağlam oluşturuluyor...")
        context_docs = []
        for doc_id, document_id, title, sim in top_similar:
            cursor.execute("SELECT content FROM document_chunks WHERE id = %s", (doc_id,))
            content = cursor.fetchone()[0]
            context_docs.append(content[:300] + "...")  # İlk 300 karakter

        context = "\n\n".join(context_docs)
        print(f"   Oluşturulan bağlam (ilk 200 karakter):")
        print(f"   {context[:200]}...")

        # 4. Promptu hazırla
        print("\n4️⃣ Prompt hazırlanıyor...")
        with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            templates = json.load(f)

        template_name = "default"
        system_content = templates[template_name]["messages"][0]["content"]
        user_content = templates[template_name]["messages"][1]["content"]

        # Prompt'u biçimlendir
        prompt = user_content.replace("{query}", query).replace("{context}", context)
        print(f"   Sistem mesajı (ilk 100 karakter): {system_content[:100]}...")
        print(f"   Kullanıcı mesajı (ilk 100 karakter): {prompt[:100]}...")

        # 5. LLM'e gönder
        print("\n5️⃣ LLM yanıtı alınıyor...")
        llm = Ollama(model=LLM_MODEL)
        response = llm.invoke(system_content + "\n\n" + prompt)

        print("\n📝 LLM Yanıtı:")
        print("=" * 50)
        print(response)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ Hata: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = input("Sorgunuzu girin: ")

    debug_query(query)