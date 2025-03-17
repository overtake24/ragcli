-- Blog veritabanı şeması

-- Blog gönderileri tablosu
CREATE TABLE blog_posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İndeksler
CREATE INDEX idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX idx_blog_posts_published ON blog_posts(is_published);

-- RAG ile entegrasyon durumu
CREATE TABLE rag_sync_status (
    post_id INTEGER PRIMARY KEY REFERENCES blog_posts(id),
    is_synced BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP,
    document_id VARCHAR(255),
    chunks_count INTEGER
);

-- Örnek veri
INSERT INTO blog_posts (title, slug, content, excerpt, is_published) VALUES
('RAG Sistemleri Nedir?', 'rag-sistemleri-nedir',
'# RAG Sistemleri Nedir?

RAG (Retrieval-Augmented Generation) sistemleri, büyük dil modellerini (LLM) harici veritabanlarıyla entegre eden modern yapay zeka sistemleridir. Bu yaklaşım, dil modellerinin kendi eğitim verilerinin ötesinde bilgiye erişmesini ve daha doğru, güncel yanıtlar üretmesini sağlar.

## RAG''in Çalışma Prensibi

RAG sistemleri temel olarak şu adımları izler:

1. **Belge İndeksleme**: Metinler vektör veritabanına aktarılır
2. **Sorgu İşleme**: Kullanıcı sorusu vektöre dönüştürülür
3. **Benzerlik Araması**: En alakalı belgeler bulunur
4. **Cevap Üretimi**: LLM, bulunan belgeleri kullanarak yanıt üretir

## RAG Sistemlerinin Avantajları

- Daha doğru ve güncel bilgiler
- Hallüsinasyon sorunlarının azaltılması
- Özel bilgi kaynaklarıyla entegrasyon
- Şeffaf kaynak gösterimi',
'RAG sistemleri, LLM''leri harici veritabanlarıyla entegre ederek daha doğru ve güncel yanıtlar üretmeyi sağlar.',
true),

('Vektör Veritabanları ve Kullanımları', 'vektor-veritabanlari-ve-kullanimlari',
'# Vektör Veritabanları ve Kullanımları

Vektör veritabanları, yüksek boyutlu vektörleri verimli şekilde depolayan ve benzerlik sorguları gerçekleştiren özel veritabanı sistemleridir. Günümüzde semantik arama, öneri sistemleri ve RAG (Retrieval-Augmented Generation) gibi birçok yapay zeka uygulamasında kullanılmaktadırlar.

## Popüler Vektör Veritabanları

- **pgvector**: PostgreSQL uzantısı
- **Pinecone**: Bulut tabanlı vektör veritabanı
- **Milvus**: Açık kaynaklı vektör veritabanı
- **Qdrant**: Yüksek performanslı vektör veritabanı

## pgvector Kullanım Örnekleri

PostgreSQL''in pgvector uzantısı, vektör işlemlerini standart SQL sorguları ile gerçekleştirmenize olanak tanır:

```sql
-- Vektör sütunu oluşturma
ALTER TABLE items ADD COLUMN embedding vector(384);

-- Benzerlik araması
SELECT * FROM items
ORDER BY embedding <-> ''[0.1, 0.2, ...]''
LIMIT 5;
```

Bu veritabanları, vektörel veri yapılarını kullanarak semantik arama ve benzer öğe bulma görevlerini hızlı ve verimli şekilde gerçekleştirir.',
'Vektör veritabanları, semantik arama ve yapay zeka uygulamaları için yüksek boyutlu vektörleri verimli şekilde depolayan sistemlerdir.',
true);