# app/llm_enhanced.py
"""
Geliştirilmiş LLM işlemleri ve JSON yanıt ayrıştırma
"""
import re
import json
from typing import Dict, Any, List, Tuple, Optional, Union
from pydantic import create_model, Field, ValidationError

from langchain_community.llms import Ollama
from app.config import LLM_MODEL


def get_llm(temperature=0.2):
    """
    LLM modelini döndürür.
    """
    return Ollama(model=LLM_MODEL, temperature=temperature)


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Metin içindeki JSON bloğunu ayıklar.
    """
    # JSON bloğunu kod bloğu içinden çıkartmaya çalış
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    matches = re.findall(code_block_pattern, text)

    if matches:
        return matches[0].strip()

    # Kod bloğu yoksa { } arasındaki metni bul
    json_pattern = r"\{[\s\S]*\}"
    matches = re.findall(json_pattern, text)

    if matches:
        return matches[0].strip()

    return None


def clean_json_string(json_str: str) -> str:
    """
    JSON dizesindeki yaygın sorunları temizler.
    """
    # Başlangıç ve sondaki fazla karakterleri temizle
    json_str = json_str.strip()

    # Başlangıçtaki ve sondaki gereksiz açıklamaları kaldır
    if json_str.startswith('```json'):
        json_str = json_str[len('```json'):].strip()
    if json_str.startswith('```'):
        json_str = json_str[len('```'):].strip()
    if json_str.endswith('```'):
        json_str = json_str[:-len('```')].strip()

    # Ek açıklamaları veya çıktıları temizle
    if "}" in json_str:
        json_str = json_str[:json_str.rindex("}") + 1]

    # JSON anahtarlarının etrafındaki tırnak işaretlerini düzelt
    # Örn: {key: "value"} -> {"key": "value"}
    json_str = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', json_str)

    return json_str


def parse_json_safely(json_str: str) -> Optional[Dict[str, Any]]:
    """
    JSON dizesini güvenli bir şekilde ayrıştırır, çeşitli düzeltmeler dener.
    """
    if not json_str:
        return None

    # İlk deneme: Orijinal metni ayrıştır
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # İkinci deneme: Metni temizle ve tekrar dene
    try:
        cleaned_json = clean_json_string(json_str)
        return json.loads(cleaned_json)
    except json.JSONDecodeError:
        pass

    # Üçüncü deneme: Her satırı ayrı ayrı kontrol et, fazla satırları temizle
    try:
        lines = json_str.split('\n')
        filtered_lines = []
        json_started = False
        brace_count = 0

        for line in lines:
            if '{' in line:
                json_started = True
                brace_count += line.count('{')

            if json_started:
                filtered_lines.append(line)
                brace_count += line.count('{') - line.count('}')

            if json_started and brace_count == 0:
                break

        cleaned_json = '\n'.join(filtered_lines)
        return json.loads(cleaned_json)
    except (json.JSONDecodeError, IndexError):
        pass

    # Son çare: Regex ile JSON nesnesi ayıkla
    try:
        pattern = r'\{(?:[^{}]|(?R))*\}'
        matches = re.findall(pattern, json_str)
        if matches:
            return json.loads(matches[0])
    except (json.JSONDecodeError, re.error):
        pass

    return None


def parse_llm_response(response: str, expected_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM yanıtını ayrıştırır ve beklenen şemaya uygun bir sözlük döndürür.
    """
    # JSON'ı ayıkla ve ayrıştır
    json_str = extract_json_from_text(response)
    parsed_data = parse_json_safely(json_str)

    if not parsed_data:
        # Ayrıştırma başarısız oldu, varsayılan değerlerle doldur
        return {field: None if field_type != "list" else [] for field, field_type in expected_schema.items()}

    # Beklenen şemaya göre veriyi doğrula ve dönüştür
    result = {}
    for field, field_type in expected_schema.items():
        if field in parsed_data:
            if field_type == "list" and not isinstance(parsed_data[field], list):
                # Liste olması gereken alanı liste yap
                if parsed_data[field] is None:
                    result[field] = []
                else:
                    result[field] = [parsed_data[field]]
            else:
                result[field] = parsed_data[field]
        else:
            # Alan yoksa varsayılan değer ata
            result[field] = None if field_type != "list" else []

    return result


def create_film_info_model():
    """
    Film bilgisi için Pydantic modeli oluşturur.
    """
    return create_model("FilmInfo",
                        title=(str, Field(description="Film başlığı")),
                        director=(str, Field(description="Film yönetmeni")),
                        release_year=(str, Field(description="Filmin yayın yılı")),
                        plot_summary=(str, Field(description="Film özeti")),
                        cast=(List[str], Field(description="Oyuncular listesi")),
                        genre=(List[str], Field(description="Film türleri")),
                        imdb_rating=(str, Field(description="IMDb puanı"))
                        )


def create_book_info_model():
    """
    Kitap bilgisi için Pydantic modeli oluşturur.
    """
    return create_model("BookInfo",
                        title=(str, Field(description="Kitap başlığı")),
                        author=(str, Field(description="Kitap yazarı")),
                        publication_year=(str, Field(description="Yayın yılı")),
                        summary=(str, Field(description="Kitap özeti")),
                        genre=(List[str], Field(description="Kitap türleri")),
                        page_count=(str, Field(description="Sayfa sayısı"))
                        )


def create_person_info_model():
    """
    Kişi bilgisi için Pydantic modeli oluşturur.
    """
    return create_model("PersonInfo",
                        name=(str, Field(description="Kişinin adı")),
                        birth_date=(str, Field(description="Doğum tarihi")),
                        death_date=(str, Field(description="Ölüm tarihi (hayattaysa boş)")),
                        nationality=(str, Field(description="Milliyeti")),
                        occupation=(List[str], Field(description="Meslek(ler)i")),
                        achievements=(List[str], Field(description="Önemli başarıları")),
                        biography=(str, Field(description="Kısa biyografi"))
                        )


def get_model_for_category(category: str):
    """
    Belge kategorisine göre uygun modeli döndürür.
    """
    if category == "film":
        return create_film_info_model()
    elif category == "book":
        return create_book_info_model()
    elif category == "person":
        return create_person_info_model()
    else:
        # Varsayılan genel model
        return create_model("GeneralInfo",
                            title=(str, Field(description="Başlık")),
                            summary=(str, Field(description="Özet")),
                            key_points=(List[str], Field(description="Anahtar noktalar"))
                            )


def get_prompt_for_model(model_name: str, query: str, context: str) -> str:
    """
    Belirli bir model için uygun prompt oluşturur.
    """
    if model_name == "FilmInfo":
        return f"""Sen bir film uzmanısın. Aşağıdaki belgeleri kullanarak, filmle ilgili bilgileri JSON formatında hazırla.
Lütfen aşağıdaki JSON şemasına uygun yanıt ver:

{{
  "title": "Film başlığı",
  "director": "Yönetmen",
  "release_year": "Yayın yılı",
  "plot_summary": "Film özeti",
  "cast": ["Oyuncu 1", "Oyuncu 2"],
  "genre": ["Tür 1", "Tür 2"],
  "imdb_rating": "IMDb puanı"
}}

Soru: {query}

Belge içerikleri:
{context}

JSON yanıtı (sadece JSON, başka açıklama ekleme):"""

    elif model_name == "BookInfo":
        return f"""Sen bir kitap uzmanısın. Aşağıdaki belgeleri kullanarak, kitapla ilgili bilgileri JSON formatında hazırla.
Lütfen aşağıdaki JSON şemasına uygun yanıt ver:

{{
  "title": "Kitap başlığı",
  "author": "Yazar",
  "publication_year": "Yayın yılı",
  "summary": "Kitap özeti",
  "genre": ["Tür 1", "Tür 2"],
  "page_count": "Sayfa sayısı"
}}

Soru: {query}

Belge içerikleri:
{context}

JSON yanıtı (sadece JSON, başka açıklama ekleme):"""

    elif model_name == "PersonInfo":
        return f"""Sen bir biyografi uzmanısın. Aşağıdaki belgeleri kullanarak, kişiyle ilgili bilgileri JSON formatında hazırla.
Lütfen aşağıdaki JSON şemasına uygun yanıt ver:

{{
  "name": "Kişinin adı",
  "birth_date": "Doğum tarihi",
  "death_date": "Ölüm tarihi (hayattaysa boş bırak)",
  "nationality": "Milliyeti",
  "occupation": ["Meslek 1", "Meslek 2"],
  "achievements": ["Başarı 1", "Başarı 2"],
  "biography": "Kısa biyografi"
}}

Soru: {query}

Belge içerikleri:
{context}

JSON yanıtı (sadece JSON, başka açıklama ekleme):"""

    else:
        return f"""Sen bir bilgi uzmanısın. Aşağıdaki belgeleri kullanarak soruyu yanıtla ve bilgileri JSON formatında hazırla.
Lütfen aşağıdaki JSON şemasına uygun yanıt ver:

{{
  "title": "Başlık",
  "summary": "Detaylı özet",
  "key_points": ["Anahtar nokta 1", "Anahtar nokta 2", "Anahtar nokta 3"]
}}

Soru: {query}

Belge içerikleri:
{context}

JSON yanıtı (sadece JSON, başka açıklama ekleme):"""


def process_structured_query(query: str, context: str, model_name: str) -> Dict[str, Any]:
    """
    Yapılandırılmış veri sorgusunu işler ve yanıtı döndürür.
    """
    from app.categorizer import detect_document_category

    # Belge kategorisini tespit et
    category = detect_document_category(query)
    print(f"INFO - Algılanan sorgu kategorisi: {category}")

    # Uygun modeli seç
    if model_name == "FilmInfo" or category == "film":
        model_name = "FilmInfo"
    elif model_name == "BookInfo" or category == "book":
        model_name = "BookInfo"
    elif model_name == "PersonInfo" or category == "person":
        model_name = "PersonInfo"

    print(f"INFO - Yapılandırılmış veri sorgusu algılandı: {model_name} modeli ile işleniyor...")

    # Prompt oluştur
    prompt = get_prompt_for_model(model_name, query, context)

    # LLM'i çağır
    llm = get_llm()
    raw_answer = llm(prompt)

    print(f"DEBUG - Yapılandırılmış veri LLM yanıtı: {raw_answer[:100]}...")

    # Model şemasını belirle
    if model_name == "FilmInfo":
        schema = {
            "title": "str",
            "director": "str",
            "release_year": "str",
            "plot_summary": "str",
            "cast": "list",
            "genre": "list",
            "imdb_rating": "str"
        }
    elif model_name == "BookInfo":
        schema = {
            "title": "str",
            "author": "str",
            "publication_year": "str",
            "summary": "str",
            "genre": "list",
            "page_count": "str"
        }
    elif model_name == "PersonInfo":
        schema = {
            "name": "str",
            "birth_date": "str",
            "death_date": "str",
            "nationality": "str",
            "occupation": "list",
            "achievements": "list",
            "biography": "str"
        }
    else:
        schema = {
            "title": "str",
            "summary": "str",
            "key_points": "list"
        }

    try:
        # Yanıtı ayrıştır
        return parse_llm_response(raw_answer, schema)
    except Exception as e:
        print(f"HATA: Yapılandırılmış veri ayrıştırılamadı: {e}")

        # Boş şablonu döndür
        return {field: None if field_type != "list" else [] for field, field_type in schema.items()}