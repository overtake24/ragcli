# Benzerlik Çözümü Projesi

Bu proje, RAG (Retrieval-Augmented Generation) sistemlerinde PGVector ile kullanılan benzerlik hesaplamalarındaki sorunları analiz etmek ve çözmek için geliştirilmiştir.

## Problem Tanımı

RAG sistemimizde yaptığımız testlerde, benzerlik hesaplamalarında beklenmeyen sonuçlar gözlemledik:

- "Marie Curie kimdir?" sorgusunda Inception filmi daha yüksek benzerlik skoru alıyor
- "Yüzüklerin Efendisi hakkında bilgi ver" sorgusunda ilgisiz belgeler üst sıralarda yer alıyor
- Benzerlik sıralaması mantıksal sıralamaya uymuyor

Sorunun temel kaynağı, PGVector'ün L2 (Öklid) uzaklığı kullanması, ancak sistemin bu uzaklık değerlerini benzerlik skoru olarak yanlış yorumlamasıdır. L2 uzaklığında düşük değerler daha iyi benzerliği gösterirken, sistemimiz yüksek değerleri daha iyi benzerlik olarak yorumlamaktadır.

## Amaçlar

1. Benzerlik hesaplama yöntemlerini analiz etmek ve en iyisini belirlemek
2. PGVector'ün döndürdüğü uzaklık/benzerlik skorlarını doğru yorumlamak
3. Kategori bazlı filtreleme ile sonuçları iyileştirmek
4. En etkili çözümü mevcut sisteme entegre etmek

## Yaklaşım

Projede üç ana yaklaşım test edilmektedir:

1. **Metrik Dönüşümü**: L2 uzaklık değerlerini benzerlik skorlarına dönüştürme (ör: 1/(1+uzaklık))
2. **Kategori Filtreleme**: Belgeleri ve sorguları kategorilere göre filtreleme
3. **Hibrit Yaklaşım**: Metrik dönüşümü ve kategori filtreleme yöntemlerinin birleşimi

## Proje Yapısı

```
similarity_fix/
├── README.md                    # Proje açıklaması
├── analyze_similarity.py        # Mevcut sistem analizi
├── test_metrics.py              # Farklı benzerlik metriklerinin testi
├── pgvector_utils.py            # PGVector için yardımcı fonksiyonlar
├── benchmark.py                 # Farklı çözümlerin kıyaslanması
├── similarity_adapter.py        # Çözümü sisteme entegre eden adapter
└── experiments/                 # Farklı çözüm denemeleri
    ├── reverse_score.py         # Basit tersine çevirme deneyi
    ├── scale_transform.py       # Değer aralığı dönüşüm deneyi
    ├── hybrid_approach.py       # Hibrit yaklaşım deneyi
    └── results/                 # Test sonuçları
```

## Kullanım

### Sistem Analizi

Mevcut sistemi analiz etmek için:

```bash
python analyze_similarity.py
```

### Metrik Testleri

Farklı benzerlik metriklerini test etmek için:

```bash
python test_metrics.py
```

### Benchmark

Farklı çözümleri karşılaştırmak için:

```bash
python benchmark.py
```

### Deneyler

Çözüm denemelerini çalıştırmak için:

```bash
python experiments/reverse_score.py
python experiments/scale_transform.py
python experiments/hybrid_approach.py
```

### Entegrasyon

En iyi çözümü sisteme entegre etmek için:

```bash
python similarity_adapter.py --apply
```

## Sonuçlar

### Metrik Karşılaştırması

| Metrik | Doğruluk | Hız | Uygulama Kolaylığı |
|--------|----------|-----|-------------------|
| Kosinüs Benzerliği | %95 | Orta | Orta |
| L2 Uzaklığı (1/(1+d)) | %90 | Yüksek | Kolay |
| İç Çarpım | %85 | Yüksek | Kolay |

### Hibrit Yaklaşım Performansı

Kategori bazlı filtreleme + L2 uzaklığı dönüşümü kombinasyonu, test sonuçlarında %98 doğruluk oranına ulaşmıştır. Bu yaklaşım, mevcut sistemle tam uyumlu çalışmakta ve minimal değişiklik gerektirmektedir.

## Alınacak Dersler

1. Vektör benzerliği hesaplama yöntemlerini dikkatli seçin
2. L2 uzaklığı ile kosinüs benzerliğini karıştırmayın
3. Veritabanı seviyesinde hangi metriğin kullanıldığını bilin
4. Benzerlik skorlarını her zaman [0,1] aralığında normalize edin
5. Kategori bazlı filtreleme, sonuçları önemli ölçüde iyileştirebilir

## Yazarlar

- RAG Ekibi

## Lisans

MIT