#!/usr/bin/env python3
"""
API ile içerik indeksleme scripti
"""
import requests
import time

# API adresi
API_URL = "http://localhost:8000/index_text"


def index_content_via_api():
    """API üzerinden İskandinav içeriğini indeksle"""

    # İçerik
    content = """Scandinavia and the Nordic region are historical and geographical regions covering much of Northern Europe. Extending from above the Arctic Circle to the North and Baltic Seas, the Scandinavian Peninsula is the largest peninsula in Europe.

Popular tourist destinations Denmark, Norway, Sweden, Finland, Iceland, and on occasion, Greenland, all make up the Nordic countries. As a whole, Scandinavia has some of the most beautiful landscapes in the world and is enriched with its own culture and way of life.

The best time to visit Nordic countries is during summer when they have long daylight hours. Northern Norway and Finland experience almost no darkness during June and July. The winter months are ideal for seeing the Northern Lights due to less light pollution.

Languages spoken in the region include Danish, Swedish, Norwegian, Icelandic, and Faroese. Each country has its own currency, with Denmark using the Danish krone, Finland using the Euro, Norway using the Norwegian krone, Sweden using the Swedish krona, and Iceland using the Icelandic krona."""

    # API isteği
    payload = {
        "text": content,
        "document_id": "scandinavia_guide",
        "title": "Scandinavia and Nordic Countries Guide"
    }

    try:
        print("İçerik API üzerinden indeksleniyor...")
        response = requests.post(API_URL, json=payload)

        if response.status_code == 200:
            result = response.json()
            print(f"Başarılı! {result.get('message', 'İçerik indekslendi')}")
            return True
        else:
            print(f"API hatası: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"Hata: {e}")
        return False


if __name__ == "__main__":
    # API servisini başlat
    print("Not: Bu script çalıştırılmadan önce API servisi başlatılmalıdır:")
    print("python cli.py serve")

    # API servisinin başlaması için bekle
    input("API servisi çalışıyorsa ENTER tuşuna basın...")

    # İçeriği indeksle
    index_content_via_api()