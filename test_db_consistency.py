#!/usr/bin/env python3
"""
Veritabanı tutarlılığını test eden script.
Document_chunks ve langchain_pg_embedding tablolarını, (document_id, chunk_index) sıralamasına göre karşılaştırır.
"""
import psycopg2
from app.config import DB_CONNECTION

def fetch_document_chunks(cursor):
    cursor.execute("""
        SELECT document_id, title, content, embedding, chunk_index 
        FROM document_chunks 
        ORDER BY document_id, chunk_index
    """)
    return cursor.fetchall()

def fetch_langchain_embeddings(cursor):
    cursor.execute("""
        SELECT custom_id, embedding, chunk_index, cmetadata 
        FROM langchain_pg_embedding 
        ORDER BY custom_id, chunk_index
    """)
    return cursor.fetchall()

def parse_custom_id(custom_id_str):
    """
    'inception__chunk0' gibi bir str'den (doc_id='inception', chunk_idx=0) döndürür.
    Eğer '__chunk' yoksa chunk_idx=None döner.
    """
    if '__chunk' in custom_id_str:
        parts = custom_id_str.split('__chunk')
        doc_id = parts[0]
        try:
            chunk_idx = int(parts[1])
        except ValueError:
            chunk_idx = None
        return doc_id, chunk_idx
    else:
        return custom_id_str, None

def compare_records():
    conn = psycopg2.connect(DB_CONNECTION)
    cursor = conn.cursor()

    doc_chunks = fetch_document_chunks(cursor)
    langchain_records = fetch_langchain_embeddings(cursor)

    print("🔍 VERİTABANI TUTARLILIK TESTLERİ")
    print("=" * 60)
    print("📊 document_chunks tablosunda {} belge parçası bulunuyor".format(len(doc_chunks)))
    print("📊 langchain_pg_embedding tablosunda {} belge parçası bulunuyor".format(len(langchain_records)))

    min_count = min(len(doc_chunks), len(langchain_records))
    match_count = 0
    for i in range(min_count):
        doc = doc_chunks[i]
        lang = langchain_records[i]
        # doc: (document_id, title, content, embedding, chunk_index)
        doc_id, title, content, embedding, chunk_index = doc

        # lang: (custom_id, embedding, chunk_index, cmetadata)
        lang_custom_id, lang_embedding, lang_chunk_index, cmetadata = lang

        # custom_id parse ediyoruz => (parsed_doc_id, parsed_chunk_idx)
        parsed_doc_id, parsed_chunk_idx = parse_custom_id(lang_custom_id)

        # Şimdi karşılaştırma:
        # 1) doc_id == parsed_doc_id ?
        # 2) chunk_index == parsed_chunk_idx ?
        # 3) Eğer tabloya chunk_index dolduysa lang_chunk_index de olabilir,
        #    ama PGVector store default = None. Biz parse_custom_id ile chunk_index'i parse ediyoruz.
        if doc_id == parsed_doc_id and chunk_index == parsed_chunk_idx:
            match_count += 1
            status = "✅ Eşleşti"
        else:
            status = "❌ Farklı!"
        print(f"Belge {i+1}: doc_id={doc_id} (chunk {chunk_index}) | langchain_id={lang_custom_id} -> {status}")
    if min_count > 0:
        print("\n📊 Eşleşme Oranı: {:.2f}%".format((match_count / min_count) * 100))
    else:
        print("Veritabanında karşılaştırılacak kayıt yok.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    compare_records()
