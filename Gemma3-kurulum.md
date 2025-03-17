# Gemma 3:12B Model Kurulumu ve Yapılandırması

Ollama üzerinde Gemma 3:12B modelini RAG CLI ile kullanmak için aşağıdaki adımları izleyin.

## 1. Gemma 3:12B Modelini İndirme

Gemma 3:12B modelini Ollama aracılığıyla indirin:

```bash
# Modeli indirme
ollama pull gemma3:12b
```

Bu işlem, modelin boyutu nedeniyle biraz zaman alabilir (yaklaşık 10-20 GB disk alanı gerektirir).

## 2. Yapılandırma Dosyasını Güncelleme

RAG CLI'ın Gemma 3:12B modelini kullanması için `app/config.py` dosyasını güncelleyin:

```bash
# config.py dosyasını açma
nano app/config.py
```

`LLM_MODEL` değişkenini aşağıdaki gibi değiştirin:

```python
# Model ayarları
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "gemma3:12b"  # "llama2" yerine "gemma3:12b" kullanın
```

Dosyayı kaydedin ve çıkın.

## 3. Sistem Parametrelerini Ayarlama (İsteğe Bağlı)

Gemma 3:12B daha büyük bir model olduğu için, yanıt üretimini optimize etmek isteyebilirsiniz:

```bash
# Ollama modelini özel parametrelerle çalıştırmak için llm.py'yi düzenleyin
nano app/llm.py
```

Aşağıdaki güncellemeleri yapın:

```python
def get_llm():
    """
    LLM modelini döndür.
    """
    return Ollama(
        model=LLM_MODEL,
        temperature=0.1,  # Daha düşük sıcaklık (deterministik yanıtlar için)
        top_p=0.9,        # Top-p örnekleme (daha tutarlı yanıtlar için)
        num_ctx=4096      # Bağlam penceresi boyutu
    )
```

## 4. Önerilen Sistem Gereksinimleri

Gemma 3:12B modeli için önerilen minimum sistem gereksinimleri:

- **RAM**: 16 GB veya daha fazla
- **GPU**: 12 GB VRAM veya daha fazla (Mümkünse)
- **Disk**: En az 20 GB boş alan
- **CPU**: 8 çekirdek veya daha fazla

Eğer sisteminizdeki donanım kaynakları sınırlıysa, daha küçük bir model kullanabilirsiniz (örn. `gemma:2b`).

## 5. Test Etme

Kurulumu test etmek için:

```bash
# Veritabanını başlatma (zaten yapıldıysa gerekli değil)
python cli.py init

# Gemma 3:12B ile sorgu yapma
python cli.py ask "Yapay zeka modelleri nasıl çalışır?"
```

## 6. Olası Sorunlar ve Çözümleri

### Yetersiz Bellek / Kaynak Hatası

Eğer `Out of memory` veya benzer bir hata alırsanız:

```bash
# Daha düşük parametrelerle Ollama'yı yapılandırın
ollama rm gemma3:12b
ollama pull gemma3:12b -q

# Ollama'ya daha düşük bellek kullanımı için parametre ekleyin
nano app/llm.py

# get_llm fonksiyonunu güncelleme:
def get_llm():
    return Ollama(
        model=LLM_MODEL,
        num_gpu=1,          # Sadece 1 GPU kullan
        num_thread=4,       # İş parçacığı sayısını sınırla
        f16_kv=True,        # 16-bit öntanımlı kv hesaplamaları kullan
        stop=["Human:", "</answer>"]  # Özel durdurma koşulları
    )
```

### Yanıt Formatı Sorunları

Eğer Gemma 3:12B doğru yanıt formatını üretmiyorsa, sistem mesajını kuvvetlendirin:

```bash
# Prompt şablonunu düzenle
python cli.py edit-prompt

# Örnek geliştirilmiş sistem mesajı:
{
  "default": {
    "messages": [
      {"role": "system", "content": "Sen profesyonel bir asistansın. Kullanıcının sorgusunu sadece verilen bağlam bilgilerini kullanarak yanıtla. Eğer verilen bağlamda bilgi yoksa, 'Bu konuda yeterli bilgim yok' de. Yanıtını yapılandırılmış ve bilgilendirici şekilde ver."},
      {"role": "user", "content": "Soru: {query}\nBağlam: {context}\nCevap:"}
    ]
  }
}
```

## 7. Ek Bilgi

Gemma hakkında daha fazla bilgi için:
- [Gemma 3 Teknik Dokümantasyonu](https://ai.google.dev/gemma/)
- [Ollama Model Parametreleri](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)