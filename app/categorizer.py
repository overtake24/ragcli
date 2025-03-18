# app/categorizer.py
"""
Belge kategori algılama ve filtreleme işlevleri
"""
import re
from typing import List, Dict, Any, Tuple, Optional


def detect_document_category(content: str) -> str:
    """
    İçerik metnine göre belgenin kategorisini tespit eder
    """
    content_lower = content.lower()

    # Film/dizi kategorisi
    film_keywords = ["film", "movie", "sinema", "cinema", "yönetmen", "director",
                     "oyuncu", "actor", "imdb", "cast", "inception"]

    # Kitap kategorisi
    book_keywords = ["kitap", "book", "yazar", "author", "sayfa", "page",
                     "roman", "novel", "yüzük", "lord of rings", "tolkien"]

    # Kişi/biyografi kategorisi
    person_keywords = ["doğum", "birth", "ölüm", "death", "hayat", "life",
                       "biyografi", "biography", "marie curie", "meslek", "occupation"]

    # Kategori belirle
    film_score = sum(1 for word in film_keywords if word in content_lower)
    book_score = sum(1 for word in book_keywords if word in content_lower)
    person_score = sum(1 for word in person_keywords if word in content_lower)

    # En yüksek skora sahip kategoriyi döndür
    if film_score > book_score and film_score > person_score:
        return "film"
    elif book_score > film_score and book_score > person_score:
        return "book"
    elif person_score > film_score and person_score > book_score:
        return "person"

    # Belirsizse "other" döndür
    return "other"


def detect_query_category(query: str) -> str:
    """
    Sorgu metnine göre belge kategorisini tespit eder.
    """
    query = query.lower()

    # Film ile ilgili anahtar kelimeler
    film_keywords = [
        'film', 'movie', 'sinema', 'izle', 'yönetmen',
        'director', 'oyuncu', 'actor', 'actress', 'cast',
        'imdb', 'oscar', 'vizyon', 'box office', 'gişe',
        'başrol', 'senaryo', 'screenplay'
    ]

    # Kitap ile ilgili anahtar kelimeler
    book_keywords = [
        'kitap', 'book', 'roman', 'novel', 'yazar', 'author',
        'oku', 'read', 'sayfa', 'page', 'bölüm', 'chapter',
        'yayınevi', 'publisher', 'basım', 'edition'
    ]

    # Kişi ile ilgili anahtar kelimeler
    person_keywords = [
        'kimdir', 'who is', 'doğum', 'birth', 'ölüm', 'death',
        'hayatı', 'life', 'biyografi', 'biography', 'kişi', 'person',
        'yaşamı', 'kariyeri', 'career', 'başarı', 'achievement'
    ]

    # Her kategorideki eşleşme sayısını hesapla
    film_matches = sum(1 for keyword in film_keywords if keyword in query)
    book_matches = sum(1 for keyword in book_keywords if keyword in query)
    person_matches = sum(1 for keyword in person_keywords if keyword in query)

    # En çok eşleşme olan kategoriyi belirle
    if film_matches > book_matches and film_matches > person_matches:
        return "film"
    elif book_matches > film_matches and book_matches > person_matches:
        return "book"
    elif person_matches > film_matches and person_matches > book_matches:
        return "person"

    # Belirli anahtar kelimeleri kontrol et
    if any(word in query for word in ['film', 'movie', 'sinema', 'izle']):
        return "film"
    elif any(word in query for word in ['kitap', 'book', 'novel', 'roman']):
        return "book"
    elif any(word in query for word in ['kimdir', 'who is', 'biyografi']):
        return "person"

    # Varsayılan kategori
    return "general"


def filter_documents_by_category(documents: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    """
    Belgeleri belirtilen kategoriye göre filtreler.
    """
    if category == "general":
        return documents

    filtered_docs = []

    for doc in documents:
        doc_id = doc.get('document_id', '')
        content = doc.get('content', '')

        # Film kategorisi için filtre
        if category == "film" and any(id_part in doc_id.lower() for id_part in ['film', 'movie', 'inception']):
            filtered_docs.append(doc)
        # Kitap kategorisi için filtre
        elif category == "book" and any(id_part in doc_id.lower() for id_part in ['book', 'kitap', 'lord', 'ring']):
            filtered_docs.append(doc)
        # Kişi kategorisi için filtre
        elif category == "person" and any(
                id_part in doc_id.lower() for id_part in ['person', 'kişi', 'marie', 'curie']):
            filtered_docs.append(doc)

    # Eğer filtre sonrası hiç belge kalmadıysa, orijinal belgeleri döndür
    if not filtered_docs:
        return documents

    return filtered_docs


def filter_documents_by_similarity(documents: List[Dict[str, Any]],
                                   similarities: List[Tuple[str, float]],
                                   threshold: float = 0.60) -> List[Dict[str, Any]]:
    """
    Belgeleri benzerlik skorlarına göre filtreler.
    """
    # Belge ID'lerini ve benzerlik skorlarını bir sözlükte eşleştir
    similarity_dict = {doc_id: score for doc_id, score in similarities}

    filtered_docs = []
    for doc in documents:
        doc_id = doc.get('document_id', '')

        # Benzerlik skoru eşiğin üstündeyse veya benzerlik skoru bulunamadıysa belgeyi dahil et
        if doc_id in similarity_dict:
            similarity_score = similarity_dict[doc_id]
            if similarity_score >= threshold:
                filtered_docs.append(doc)
        else:
            # Benzerlik skoru yoksa belgeyi dahil et
            filtered_docs.append(doc)

    # Eğer filtre sonrası hiç belge kalmadıysa, eşiği düşür
    if not filtered_docs and documents:
        # Tüm benzerlik skorlarını al ve sırala
        all_scores = [score for _, score in similarities]
        if all_scores:
            # En yüksek skoru al ve eşik olarak kullan
            max_score = max(all_scores)
            new_threshold = max(0.30, max_score - 0.1)  # Maksimum skordan biraz düşük bir eşik belirle

            # Yeni eşik ile tekrar filtrele
            for doc in documents:
                doc_id = doc.get('document_id', '')
                if doc_id in similarity_dict and similarity_dict[doc_id] >= new_threshold:
                    filtered_docs.append(doc)

    # Eğer hala hiç belge yoksa, en azından bir tane belge döndür
    if not filtered_docs and documents:
        # Benzerlik skorlarına göre sırala ve en yüksek olanı seç
        sorted_docs = sorted(
            [(doc, similarity_dict.get(doc.get('document_id', ''), 0)) for doc in documents],
            key=lambda x: x[1],
            reverse=True
        )
        if sorted_docs:
            filtered_docs.append(sorted_docs[0][0])

    return filtered_docs