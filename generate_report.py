#!/usr/bin/env python
"""
Basit RAG Sistem Raporu Oluşturucu
"""
import psycopg2
import os
from datetime import datetime
from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS


def generate_report():
    """Sistem durum raporu oluşturur."""
    report = f"RAG Sistemi Durum Raporu - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += "=" * 80 + "\n\n"

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()

        # Tablo satır sayıları
        cursor.execute("""
        SELECT 
            'document_chunks' as table_name, COUNT(*) FROM document_chunks
        UNION 
            SELECT 'langchain_pg_embedding' as table_name, COUNT(*) FROM langchain_pg_embedding
        UNION 
            SELECT 'langchain_pg_collection' as table_name, COUNT(*) FROM langchain_pg_collection;
        """)

        table_counts = {row[0]: row[1] for row in cursor.fetchall()}

        report += "📊 Tablo Satır Sayıları:\n"
        for table, count in table_counts.items():
            report += f"  - {table}: {count} satır\n"

        # Tutarlılık kontrolü
        consistent = table_counts.get('document_chunks', 0) == table_counts.get('langchain_pg_embedding', 0)
        report += f"\n🔍 Tutarlılık Durumu: {'✅ Tutarlı' if consistent else '⚠️ Tutarsız'}\n"

        if not consistent:
            diff = table_counts.get('document_chunks', 0) - table_counts.get('langchain_pg_embedding', 0)
            report += f"  - Fark: {diff} belge için embedding eksik\n"

        # Son eklenen belgeler
        cursor.execute("""
        SELECT document_id, title, created_at 
        FROM document_chunks 
        ORDER BY created_at DESC LIMIT 5;
        """)

        recent_docs = cursor.fetchall()

        report += "\n📄 Son Eklenen Belgeler:\n"
        if recent_docs:
            for doc in recent_docs:
                doc_id, title, created_at = doc
                created_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "Bilinmiyor"
                report += f"  - {title} (ID: {doc_id}, Eklenme: {created_str})\n"
        else:
            report += "  Belge bulunamadı.\n"

        cursor.close()
        conn.close()

    except Exception as e:
        report += f"\n❌ Rapor oluşturma hatası: {e}\n"

    report += "\n" + "=" * 80 + "\n"

    # Raporu dosyaya kaydet
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)

    report_file = os.path.join(report_dir, f"rag_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Rapor oluşturuldu: {report_file}")
    print(report)


if __name__ == "__main__":
    generate_report()