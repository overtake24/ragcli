# app/utils.py
"""
Yardımcı fonksiyonlar.
"""
import os
import json
from app.config import MODEL_SCHEMA_FILE, PROMPT_TEMPLATE_FILE


def ensure_template_files_exist():
    """
    Şablon dosyalarının var olduğundan emin ol.
    """
    if not os.path.exists(PROMPT_TEMPLATE_FILE):
        os.makedirs(os.path.dirname(PROMPT_TEMPLATE_FILE), exist_ok=True)
        default_templates = {
            "default": {
                "messages": [
                    {"role": "system",
                     "content": "Sen bir uzman asistansın. Kullanıcının sorgusunu, verilen bağlamı kullanarak yanıtla."},
                    {"role": "user", "content": "Soru: {query}\nBağlam: {context}\nCevap:"}
                ]
            },
            "academic": {
                "messages": [
                    {"role": "system",
                     "content": "Sen bir akademik araştırma asistanısın. Kullanıcının sorgusunu bilimsel yaklaşımla, verilen bağlamı kullanarak yanıtla. Cevabında referanslara atıf yap."},
                    {"role": "user", "content": "Soru: {query}\nBağlam: {context}\nAkademik yanıt:"}
                ]
            },
            "summary": {
                "messages": [
                    {"role": "system",
                     "content": "Sen bir metin özetleme uzmanısın. Verilen bağlamı kullanarak kullanıcının sorusuna kısa ve öz bir cevap ver."},
                    {"role": "user", "content": "Soru: {query}\nBağlam: {context}\nÖzet:"}
                ]
            }
        }
        with open(PROMPT_TEMPLATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_templates, f, indent=2, ensure_ascii=False)

    if not os.path.exists(MODEL_SCHEMA_FILE):
        os.makedirs(os.path.dirname(MODEL_SCHEMA_FILE), exist_ok=True)
        default_schema = {
            "DocumentResponse": {
                "fields": {
                    "title": {"type": "str", "description": "Belgenin başlığı"},
                    "summary": {"type": "str", "description": "İçerik özeti"},
                    "key_points": {"type": "list[str]", "description": "Anahtar noktalar"}
                }
            },
            "QuestionAnswer": {
                "fields": {
                    "answer": {"type": "str", "description": "Sorunun cevabı"},
                    "confidence": {"type": "float", "description": "Cevabın güven değeri (0-1)"},
                    "references": {"type": "list[str]", "description": "Referans kaynaklar"}
                }
            }
        }
        with open(MODEL_SCHEMA_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_schema, f, indent=2, ensure_ascii=False)