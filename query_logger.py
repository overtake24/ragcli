"""
Sorgu logları için yardımcı fonksiyonlar.
"""
import json
import os
import time
from datetime import datetime

LOG_FILE = "query_log.json"


def log_query(query, docs, response, start_time):
    """
    Sorguyu ve sonuçlarını loglar.
    """
    # Sorgu süresi
    end_time = time.time()
    response_time = int((end_time - start_time) * 1000)  # milisaniye

    # Log kaydı oluştur
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "doc_count": len(docs) if docs else 0,
        "response_time": response_time,
        "has_response": response is not None
    }

    # Mevcut logları oku
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        except:
            logs = []

    # Yeni log ekle
    logs.append(log_entry)

    # Son 1000 logu tut
    logs = logs[-1000:]

    # Logları yaz
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)


def get_recent_queries(limit=10):
    """
    Son sorguları döndürür.
    """
    if not os.path.exists(LOG_FILE):
        return []

    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)

        # Son N logu al
        logs = logs[-limit:] if len(logs) > limit else logs

        return logs
    except Exception as e:
        print(f"Sorgu logları okunamadı: {e}")
        return []