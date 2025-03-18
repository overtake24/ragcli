#!/usr/bin/env python3
"""
LLM JSON yanıt ayrıştırma test aracı.
LLM'den gelen yanıtlardaki JSON verilerini ayrıştırma işlemlerini test eder.
"""
import re
import json
import argparse


def extract_json_from_text(text):
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


def clean_json_string(json_str):
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


def parse_json_safely(json_str):
    """
    JSON dizesini güvenli bir şekilde ayrıştırır, çeşitli düzeltmeler dener.
    """
    if not json_str:
        return None

    # İlk deneme: Orijinal metni ayrıştır
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"⚠️ İlk deneme başarısız: {e}")
        pass

    # İkinci deneme: Metni temizle ve tekrar dene
    try:
        cleaned_json = clean_json_string(json_str)
        return json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        print(f"⚠️ İkinci deneme başarısız: {e}")
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
    except (json.JSONDecodeError, IndexError) as e:
        print(f"⚠️ Üçüncü deneme başarısız: {e}")
        pass

    # Son çare: Regex ile JSON nesnesi ayıkla
    try:
        pattern = r'\{(?:[^{}]|(?R))*\}'
        matches = re.findall(pattern, json_str)
        if matches:
            return json.loads(matches[0])
    except (json.JSONDecodeError, re.error) as e:
        print(f"⚠️ Son deneme başarısız: {e}")
        pass

    return None


def display_json_structure(json_data, indent=0):
    """
    JSON veri yapısını hiyerarşik olarak görüntüler.
    """
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            if isinstance(value, (dict, list)):
                print(" " * indent + f"{key}:")
                display_json_structure(value, indent + 2)
            else:
                if isinstance(value, str) and len(value) > 50:
                    print(" " * indent + f"{key}: \"{value[:50]}...\"")
                else:
                    print(" " * indent + f"{key}: {value}")
    elif isinstance(json_data, list):
        for i, item in enumerate(json_data):
            if isinstance(item, (dict, list)):
                print(" " * indent + f"[{i}]:")
                display_json_structure(item, indent + 2)
            else:
                if isinstance(item, str) and len(item) > 50:
                    print(" " * indent + f"[{i}]: \"{item[:50]}...\"")
                else:
                    print(" " * indent + f"[{i}]: {item}")
    else:
        print(" " * indent + str(json_data))


def test_json_parser(sample_text):
    """
    JSON ayrıştırma işlemlerini test eder.
    """
    print("🔍 JSON AYRIŞTIRICISI TESTİ")
    print("=" * 60)

    print("📄 Örnek Metin:")
    print("-" * 40)
    print(sample_text[:500] + "..." if len(sample_text) > 500 else sample_text)
    print("-" * 40)

    # JSON bloğunu ayıkla
    print("\n🔍 JSON bloğu ayıklanıyor...")
    json_str = extract_json_from_text(sample_text)

    if json_str:
        print("✅ JSON bloğu bulundu:")
        print("-" * 40)
        print(json_str[:500] + "..." if len(json_str) > 500 else json_str)
        print("-" * 40)
    else:
        print("❌ JSON bloğu bulunamadı!")
        return False

    # JSON bloğunu temizle
    print("\n🔍 JSON bloğu temizleniyor...")
    cleaned_json = clean_json_string(json_str)

    print("📄 Temizlenen JSON:")
    print("-" * 40)
    print(cleaned_json[:500] + "..." if len(cleaned_json) > 500 else cleaned_json)
    print("-" * 40)

    # JSON'ı ayrıştır
    print("\n🔍 JSON ayrıştırılıyor...")
    json_data = parse_json_safely(cleaned_json)

    if json_data:
        print("✅ JSON başarıyla ayrıştırıldı!")
        print("\n📊 JSON Yapısı:")
        print("-" * 40)
        display_json_structure(json_data)
        print("-" * 40)
        return True
    else:
        print("❌ JSON ayrıştırılamadı!")
        return False


def main():
    parser = argparse.ArgumentParser(description="LLM JSON Yanıt Ayrıştırma Test Aracı")
    parser.add_argument("--file", "-f", type=str,
                        help="Test edilecek JSON içeren metin dosyası")

    args = parser.parse_args()

    if args.file:
        # Dosyadan metin oku
        with open(args.file, 'r', encoding='utf-8') as f:
            sample_text = f.read()
    else:
        # Varsayılan test metni
        sample_text = """
        Evet, işte Inception filmi hakkında bilgiler:

        ```json
        {
          "title": "Inception",
          "director": "Christopher Nolan",
          "release_year": "2010",
          "plot_summary": "Dom Cobb (Leonardo DiCaprio) çok yetenekli bir hırsızdır. Uzmanlık alanı, zihnin en savunmasız olduğu rüya görme anında, bilinçaltının derinliklerindeki değerli sırları çekip çıkarmak ve onları çalmaktır. Bu ender rastlanan yeteneği, onu kurumsal casusluğun tehlikeli yeni dünyasında çok aranan bir oyuncu yapmıştır.",
          "cast": [
            "Leonardo DiCaprio (Dom Cobb)",
            "Joseph Gordon-Levitt (Arthur)",
            "Ellen Page (Ariadne)",
            "Tom Hardy (Eames)",
            "Ken Watanabe (Saito)"
          ],
          "genre": ["Bilim Kurgu", "Aksiyon", "Gerilim"],
          "imdb_rating": "8.8/10"
        }
        ```

        Bu film, Christopher Nolan'ın en başarılı yapıtlarından biri olarak kabul edilir ve zihin bükücü hikayesiyle sinemaseverler arasında kült statüsüne ulaşmıştır.
        """

    test_json_parser(sample_text)


if __name__ == "__main__":
    main()