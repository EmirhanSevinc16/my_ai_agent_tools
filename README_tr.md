# AI Agent Tools

AI agent'larını (LLM tabanlı ajanlar) güçlendirmek için hazırlanmış, yeniden kullanılabilir Python tool koleksiyonu. Her tool hem bir **Python fonksiyonu** hem de OpenAI uyumlu **function calling şeması** olarak tanımlanmıştır; böylece NVIDIA, OpenAI veya benzeri `tools` parametresini destekleyen herhangi bir API ile kullanılabilir.

## İçindekiler

- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Toolların Genel Bakışı](#toolların-genel-bakışı)
- [Tool Detayları](#tool-detayları)
  - [read_file](#1-read_file)
  - [edit_file](#2-edit_file)
  - [web_search](#3-web_search)
  - [fetch_web_page](#4-fetch_web_page)
- [Yardımcı Fonksiyon: md_file_reading](#yardımcı-fonksiyon-md_file_reading)
- [Tool Haritası ve Şemalar](#tool-haritası-ve-şemalar)
- [Agent ile Kullanım Örneği](#agent-ile-kullanım-örneği)
- [Güvenlik Notları](#güvenlik-notları)

## Özellikler

- Dosya okuma ve yazma
- DuckDuckGo ile internet araması (API anahtarı gerekmez)
- Web sayfalarının temizlenmiş metin içeriğini çekme
- Tüm hatalar exception fırlatmak yerine **string olarak** döndürülür; böylece agent hatayı görüp kendini düzeltebilir
- `TOOL_MAP` ve `TOOL_SCHEMAS` ile agent döngüsüne kolay entegrasyon

## Kurulum

```bash
git clone https://github.com/<kullanici-adi>/<repo-adi>.git
cd <repo-adi>
pip install requests beautifulsoup4 ddgs
```

Gereksinimler:

| Paket | Kullanım amacı |
|-------|----------------|
| `requests` | Web sayfalarını indirme |
| `beautifulsoup4` | HTML'i ayrıştırma ve temizleme |
| `ddgs` | DuckDuckGo arama |

Python 3.9 veya üzeri önerilir.

## Toolların Genel Bakışı

| Tool | Açıklama | Parametreler | Dönüş tipi |
|------|----------|--------------|------------|
| `read_file` | Bir metin dosyasını okur | `path` | `str` |
| `edit_file` | Bir dosyayı verilen içerikle yazar/üzerine yazar | `path`, `content` | `str` |
| `web_search` | İnternette arama yapar | `query`, `max_results` (opsiyonel) | `List[Dict]` |
| `fetch_web_page` | Bir web sayfasının metnini çeker | `url` | `str` |

## Tool Detayları

### 1. `read_file`

Belirtilen yoldaki metin dosyasını UTF-8 olarak okur ve içeriğini döndürür. Agent'ın proje dosyalarını, kod dosyalarını veya notları incelemesi için kullanılır.

**Parametreler**

| Ad | Tip | Zorunlu | Açıklama |
|----|-----|---------|----------|
| `path` | `string` | Evet | Okunacak dosyanın yolu |

**Dönüş**

- Başarılıysa: dosyanın tüm içeriği (`str`)
- Dosya yoksa: `Hata: Dosya bulunamadı: <path>`
- Başka bir sorun olursa: `Hata: Dosya okunurken bir sorun oluştu: <hata>`

**Örnek**

```python
read_file("main.py")
```

---

### 2. `edit_file`

Belirtilen dosyayı verilen içerikle **tamamen üzerine yazar**. Dosya yoksa oluşturur. Agent'ın kod veya metin dosyası oluşturması ve güncellemesi için kullanılır.

> ⚠️ Bu tool kısmi düzenleme yapmaz; dosyanın tüm içeriğini `content` ile değiştirir. Bir dosyayı düzenlemeden önce `read_file` ile mevcut içeriği okuyup, değişikliği içeren **tam** içeriği göndermek gerekir.

**Parametreler**

| Ad | Tip | Zorunlu | Açıklama |
|----|-----|---------|----------|
| `path` | `string` | Evet | Düzenlenecek dosyanın yolu |
| `content` | `string` | Evet | Dosyaya yazılacak yeni içerik (kod veya metin) |

**Dönüş**

- Başarılıysa: `Başarılı: Dosya güncellendi (<path>)`
- Hata olursa: `Hata: Dosya güncellenirken bir sorun oluştu: <hata>`

**Örnek**

```python
edit_file("notlar.txt", "Yeni içerik burada")
```

---

### 3. `web_search`

DuckDuckGo üzerinden internette arama yapar. Güncel bilgiler, haberler ve web siteleri bulmak için kullanılır. Her sonuç için başlık, URL ve kısa özet döndürür.

**Parametreler**

| Ad | Tip | Zorunlu | Varsayılan | Açıklama |
|----|-----|---------|------------|----------|
| `query` | `string` | Evet | – | Arama terimi veya soru |
| `max_results` | `integer` | Hayır | `5` | Döndürülecek maksimum sonuç sayısı |

**Dönüş**

Sözlük listesi:

```json
[
  {
    "title": "Sayfa başlığı",
    "url": "https://ornek.com/sayfa",
    "snippet": "Sayfanın kısa özeti..."
  }
]
```

Arama sırasında hata olursa: `[{"error": "Arama sırasında hata oluştu: <hata>"}]`

**Örnek**

```python
web_search("python asyncio nedir", max_results=3)
```

---

### 4. `fetch_web_page`

Verilen URL'deki web sayfasını indirir, HTML'den metin içeriğini çıkarır ve temizler. `web_search` ile bulunan bir sonucun detaylı içeriğini okumak için idealdir.

**Nasıl çalışır?**

1. Tarayıcı benzeri bir `User-Agent` ile sayfayı indirir (zaman aşımı: 10 sn).
2. `<script>`, `<style>`, `<header>`, `<footer>` ve `<nav>` etiketlerini kaldırır.
3. Boş satırları temizler.
4. Token tüketimini sınırlamak için sonucu **ilk 4000 karakterle** keser.

**Parametreler**

| Ad | Tip | Zorunlu | Açıklama |
|----|-----|---------|----------|
| `url` | `string` | Evet | İçeriği okunacak sayfanın tam URL adresi |

**Dönüş**

- Başarılıysa: temizlenmiş sayfa metni (en fazla 4000 karakter)
- Hata olursa: `Sayfa içeriği çekilirken hata oluştu: <hata>`

**Örnek**

```python
fetch_web_page("https://docs.python.org/3/library/asyncio.html")
```

> JavaScript ile dinamik olarak yüklenen içerikler bu tool ile çekilemez; yalnızca sunucudan gelen HTML işlenir.

## Yardımcı Fonksiyon: `md_file_reading`

Bu bir **agent tool'u değildir** (`TOOL_MAP` ve `TOOL_SCHEMAS` içinde yer almaz); doğrudan kodunuzdan çağrılan bir yardımcı fonksiyondur. Tipik kullanımı, system prompt veya kural dosyalarını Markdown'dan yüklemektir.

Markdown dosyasını okur ve içindeki `{{ CURRENT_DATETIME }}` yer tutucusunu o anki tarih ve saatle (`%d %B %Y, %H:%M` formatında) değiştirir. Böylece agent her çalıştırmada güncel zamanı bilir.

**Örnek**

`rules.md`:

```markdown
Sen yardımcı bir asistansın.
Şu anki tarih ve saat: {{ CURRENT_DATETIME }}
```

Kullanım:

```python
system_prompt = md_file_reading("rules.md")
```

Dosya bulunamazsa: `Hata: Kurallar dosyası (<md_file>) bulunamadı.`

## Tool Haritası ve Şemalar

Kod iki ana yapı sunar:

- **`TOOL_MAP`**: Tool adını Python fonksiyonuna eşleyen sözlük. Modelden gelen tool çağrısını çalıştırmak için kullanılır.
- **`TOOL_SCHEMAS`**: Modele gönderilen, her toolun adını, açıklamasını ve parametrelerini tanımlayan JSON şema listesi.

```python
TOOL_MAP = {
    "read_file": read_file,
    "edit_file": edit_file,
    "web_search": web_search,
    "fetch_web_page": fetch_web_page,
}
```

Yeni bir tool eklemek için:

1. Python fonksiyonunu yazın.
2. `TOOL_MAP` içine ekleyin.
3. `TOOL_SCHEMAS` listesine şemasını ekleyin.

## Agent ile Kullanım Örneği

OpenAI uyumlu bir API (ör. NVIDIA API) ile temel agent döngüsü:

```python
import json
from openai import OpenAI

client = OpenAI(base_url="<API_BASE_URL>", api_key="<API_KEY>")
messages = [{"role": "user", "content": "Python 3.13'ün yeni özelliklerini araştır."}]

while True:
    response = client.chat.completions.create(
        model="<MODEL_ADI>",
        messages=messages,
        tools=TOOL_SCHEMAS,
    )
    msg = response.choices[0].message
    messages.append(msg)

    if not msg.tool_calls:
        print(msg.content)
        break

    for call in msg.tool_calls:
        func = TOOL_MAP[call.function.name]
        args = json.loads(call.function.arguments)
        result = func(**args)
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(result, ensure_ascii=False),
        })
```

> API anahtarınızı koda gömmek yerine `.env` dosyasında tutun ve `.gitignore`'a ekleyin.

## Güvenlik Notları

- `read_file` ve `edit_file` **herhangi bir yol kısıtlaması içermez**. Agent'a sistemdeki tüm dosyalara okuma/yazma erişimi verir. Güvenilmeyen ortamlarda çalıştırmadan önce belirli bir çalışma dizinine kısıtlamayı düşünün.
- `fetch_web_page` ve `web_search` dış içerik getirir. Bu içerik agent'ın davranışını yönlendirmeye çalışan metinler (prompt injection) barındırabilir; web'den gelen içeriği talimat olarak değil veri olarak ele alın.

## Lisans

Lisans bilgisini buraya ekleyin (ör. MIT).