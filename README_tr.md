# AI Agent Tools

🌐 [English](README.md) | **Türkçe**

Farklı rollerde çalışan yapay zeka agent'ları (LLM tabanlı agent'lar) kurmak için hazırlanmış küçük bir araç seti. Her aracı **bir kere** tanımlarsın, her agent'a sadece işinin gerektirdiği araçları verirsin ve istediğin agent'ı tek bir çağrıyla çalıştırırsın. Her araç, bir **Python fonksiyonu** ve OpenAI uyumlu bir **function calling şeması** olarak birlikte tanımlıdır; bu sayede NVIDIA, OpenAI veya `tools` parametresini destekleyen herhangi bir API ile kullanılabilir.

## İçindekiler

- [Özellikler](#özellikler)
- [Proje Yapısı](#proje-yapısı)
- [Kurulum](#kurulum)
- [Nasıl Çalışır](#nasıl-çalışır)
- [Araçlara Genel Bakış](#araçlara-genel-bakış)
- [Araç Detayları](#araç-detayları)
  - [read_file](#1-read_file)
  - [edit_file](#2-edit_file)
  - [web_search](#3-web_search)
  - [fetch_web_page](#4-fetch_web_page)
- [Registry Fonksiyonları](#registry-fonksiyonları)
- [Agent Profilleri](#agent-profilleri)
- [Agent Çalıştırma](#agent-çalıştırma)
- [Yeni Araç Ekleme](#yeni-araç-ekleme)
- [Yardımcı Fonksiyon: md_file_reading](#yardımcı-fonksiyon-md_file_reading)
- [Güvenlik Notları](#güvenlik-notları)
- [Lisans](#lisans)

## Özellikler

- **Bir kere tanımla:** Her araç tek bir kez kaydedilir, fonksiyonu ve şeması her zaman birlikte durur
- **Role dayalı agent'lar:** Her agent sadece kendisine verilen araçları görür ve sadece onları çalıştırabilir (örneğin `code_agent` ve `web_researcher`)
- **Kolay büyür:** Bir agent'a yeni araç vermek için profiline tek bir isim eklemen yeter, aracın koduna dokunmazsın
- **Hazır döngü:** Tek seferlik görevler için `run_agent`, hafızalı çok turlu sohbetler için `run_turn`
- **Güvenli çalıştırma:** Agent için izin verilmeyen araç çağrıları hiçbir şey çalışmadan reddedilir
- Tüm hatalar istisna fırlatmak yerine **metin (string)** olarak döndürülür; böylece agent hatayı görüp kendini düzeltebilir
- Dosya okuma ve yazma, DuckDuckGo ile web araması (API anahtarı gerekmez) ve web sayfalarından temizlenmiş metin çekme

## Proje Yapısı

```
my_agent_tools/
├── registry.py            # araç deposu, agent profilleri, execute
├── tools_and_schemas.py   # araç fonksiyonları ve şemaları (import edilince kaydolur)
├── agents.py              # agent profilleri: hangi agent hangi araçları alır
├── runner.py              # run_agent / run_turn döngüsü
├── helpers.py             # kendi kodunun kullandığı yardımcılar (agent aracı değil)
└── pyproject.toml
```

## Kurulum

```bash
git clone https://github.com/<kullanici-adi>/<repo-adi>.git
cd <repo-adi>
pip install -e .
```

`-e` (editable) bayrağı, Python'un klonladığın klasörü doğrudan kullanmasını sağlar. Böylece yeni araçlar ve profil değişiklikleri yeniden kurulum gerekmeden tüm projelerinde görünür. Bu komut bağımlılıkları da kurar:

| Paket | Amaç |
|-------|------|
| `requests` | Web sayfalarını indirme |
| `beautifulsoup4` | HTML'i ayrıştırma ve temizleme |
| `ddgs` | DuckDuckGo araması |

Aşağıdaki örnekler OpenAI uyumlu bir client da kullanır (`pip install openai`). Paketin kendisi buna bağımlı değildir.

**Kurulum yapmadan:** Yukarıdaki üç paketi elle kur ve klasörü Python'un yoluna ekle:

```python
import sys
sys.path.insert(0, "/klasorun/yolu/<repo-adi>")
```

Python 3.9 veya üzeri önerilir.

## Nasıl Çalışır

Araç seti üç katmandan oluşur:

1. **Registry (depo)** (`registry.py`, `tools_and_schemas.py`): Her araç, bir fonksiyon ve onun şemasını tutan bir "kart"tır. Kartlar `register_tool` ile bir kere kaydedilir ve `TOOLS` sözlüğünde saklanır.
2. **Agent profilleri** (`agents.py`): Profil, sadece araç **isimlerinden** oluşan bir listedir. Profiller `AGENTS` sözlüğünde saklanır ve depodaki kartlara işaret eder.
3. **Runner (çalıştırıcı)** (`runner.py`): Bir agent çalışırken modele sadece o agent'ın profilindeki şemalar gönderilir. Modelden gelen her araç çağrısı, çalıştırılmadan önce bu profile karşı kontrol edilir.

Araçlar, `tools_and_schemas` import edildiğinde kendiliğinden kaydolur. `agents.py` bunu import ettiği için programında `agents`'ı import etmen her şeyi yüklemeye yeter.

## Araçlara Genel Bakış

| Araç | Açıklama | Parametreler | Dönüş tipi |
|------|----------|--------------|------------|
| `read_file` | Bir metin dosyasını okur | `path` | `str` |
| `edit_file` | Dosyayı verilen içerikle yazar/üzerine yazar | `path`, `content` | `str` |
| `web_search` | İnternette arama yapar | `query`, `max_results` (opsiyonel) | `List[Dict]` |
| `fetch_web_page` | Bir web sayfasının metnini getirir | `url` | `str` |

Bir araç `execute` üzerinden çalıştığında, metin olmayan sonuçlar (örneğin `web_search`'ün döndürdüğü liste) modele geri gönderilmeden önce JSON metnine çevrilir.

## Araç Detayları

### 1. `read_file`

Verilen yoldaki metin dosyasını UTF-8 olarak okur ve içeriğini döndürür. Agent tarafından proje dosyalarını, kod dosyalarını veya notları incelemek için kullanılır.

**Parametreler**

| Ad | Tip | Zorunlu | Açıklama |
|----|-----|---------|----------|
| `path` | `string` | Evet | Okunacak dosyanın yolu |

**Dönüş**

- Başarılıysa: dosyanın tüm içeriği (`str`)
- Dosya yoksa: `Hata: Dosya bulunamadı: <path>`
- Başka bir hata olursa: `Hata: Dosya okunurken bir sorun oluştu: <error>`

**Örnek**

```python
read_file("main.py")
```

---

### 2. `edit_file`

Verilen dosyanın içeriğini sağlanan içerikle **tamamen üzerine yazar**. Dosya yoksa oluşturur. Agent tarafından kod veya metin dosyalarını oluşturmak ve güncellemek için kullanılır.

> ⚠️ Bu araç kısmi düzenleme yapmaz; dosyanın tüm içeriğini `content` ile değiştirir. Bir dosyayı düzenlemek için önce `read_file` ile mevcut içeriği oku, sonra güncellenmiş içeriğin **tamamını** gönder.

**Parametreler**

| Ad | Tip | Zorunlu | Açıklama |
|----|-----|---------|----------|
| `path` | `string` | Evet | Düzenlenecek dosyanın yolu |
| `content` | `string` | Evet | Dosyaya yazılacak yeni içerik (kod veya metin) |

**Dönüş**

- Başarılıysa: `Başarılı: Dosya güncellendi (<path>)`
- Hata olursa: `Hata: Dosya güncellenirken bir sorun oluştu: <error>`

**Örnek**

```python
edit_file("notes.txt", "Yeni içerik buraya gelir")
```

---

### 3. `web_search`

DuckDuckGo üzerinden internette arama yapar. Güncel bilgileri, haberleri ve web sitelerini bulmak için kullanılır. Her sonuç için başlık, URL ve kısa bir özet döndürür.

**Parametreler**

| Ad | Tip | Zorunlu | Varsayılan | Açıklama |
|----|-----|---------|------------|----------|
| `query` | `string` | Evet | – | Arama terimi veya soru |
| `max_results` | `integer` | Hayır | `5` | Döndürülecek maksimum sonuç sayısı |

**Dönüş**

Sözlüklerden oluşan bir liste:

```json
[
  {
    "title": "Sayfa başlığı",
    "url": "https://example.com/page",
    "snippet": "Sayfanın kısa bir özeti..."
  }
]
```

Arama sırasında hata olursa: `[{"error": "Arama sırasında hata oluştu: <error>"}]`

**Örnek**

```python
web_search("python asyncio nedir", max_results=3)
```

---

### 4. `fetch_web_page`

Verilen URL'deki web sayfasını indirir, HTML'den metin içeriğini çıkarır ve temizler. `web_search` ile bulunan bir sonucun detaylı içeriğini okumak için idealdir.

**Nasıl çalışır**

1. Sayfayı tarayıcı benzeri bir `User-Agent` ile indirir (zaman aşımı: 10 saniye).
2. `<script>`, `<style>`, `<header>`, `<footer>` ve `<nav>` etiketlerini kaldırır.
3. Boş satırları temizler.
4. Token kullanımını sınırlamak için sonucu **ilk 4000 karakterle** keser.

**Parametreler**

| Ad | Tip | Zorunlu | Açıklama |
|----|-----|---------|----------|
| `url` | `string` | Evet | Okunacak sayfanın tam URL'si |

**Dönüş**

- Başarılıysa: temizlenmiş sayfa metni (en fazla 4000 karakter)
- Hata olursa: `Sayfa içeriği çekilirken hata oluştu: <error>`

**Örnek**

```python
fetch_web_page("https://docs.python.org/3/library/asyncio.html")
```

> JavaScript ile dinamik olarak yüklenen içerik bu araçla çekilemez; sadece sunucunun döndürdüğü HTML işlenir.

## Registry Fonksiyonları

Hepsi `registry.py` içinde bulunur:

| Fonksiyon | Açıklama |
|-----------|----------|
| `register_tool(function, schema)` | Depoya bir araç ekler. İsim şemadan okunur. İsim zaten kayıtlıysa `ValueError` fırlatır |
| `define_agent(agent, tools)` | Araç isimlerinden oluşan bir listeyle agent profili oluşturur (varsa sıfırlar). Bir isim kayıtlı değilse `KeyError` fırlatır |
| `grant(agent, *tool_names)` | Mevcut bir profile araç ekler |
| `revoke(agent, *tool_names)` | Bir profilden araç çıkarır |
| `get_schemas(agent)` | Modele gönderilecek şemaları döndürür (`tools=` parametresi) |
| `execute(agent, name, args)` | Bir agent için araç çağrısını çalıştırır. `args` sözlük ya da JSON metni olabilir. Her zaman metin döndürür |
| `get_function(name)`, `get_schema(name)` | Kayıtlı bir aracın fonksiyonuna veya şemasına doğrudan erişir |

`execute` hiçbir zaman istisna fırlatmaz. Agent'ın bu aracı kullanma izni yoksa `Hata: '<name>' tool'u <agent> için tanımlı değil` döndürür, araç kendi içinde hata verirse `Hata (<name>): <HataTipi>: <mesaj>` döndürür. Model bu mesajları görür ve kendini düzeltebilir.

## Agent Profilleri

Profiller, en sık düzenleyeceğin dosya olan `agents.py` içinde tanımlanır:

```python
import tools_and_schemas   # araçları depoya yükler
from registry import define_agent

define_agent("code_agent", tools=["read_file", "edit_file"])
define_agent("web_researcher", tools=["web_search", "fetch_web_page"])
```

Bir agent'a eksik olan bir aracı vermek için aracın adını listesine ekle. Bir profili sadece program çalışırken değiştirmek için `grant` ve `revoke` kullan:

```python
import registry

registry.grant("web_researcher", "read_file")
registry.revoke("web_researcher", "read_file")
```

> `grant` ve `revoke` sadece çalışan programı etkiler. Kalıcı değişiklik için `agents.py` dosyasını düzenle.

## Agent Çalıştırma

`run_agent` tek bir görevi çalıştırır ve son cevabı döndürür. `client` ve `model` dışarıdan verilir; böylece paket hiçbir API anahtarı saklamaz ve aynı agent'lar OpenAI uyumlu her API ile çalışır:

```python
import os
from openai import OpenAI

import agents                      # araçları ve agent profillerini yükler
from runner import run_agent

client = OpenAI(base_url="<API_BASE_URL>", api_key=os.environ["<API_ANAHTARI_ORTAM_DEGISKENI>"])

cevap = run_agent(
    agent="web_researcher",
    task="Python 3.13'ün yeni özelliklerini araştır.",
    client=client,
    model="<MODEL_ADI>",
)
print(cevap)
```

Konuşmayı hatırlayan çok turlu bir sohbet için bir `messages` listesi tut ve her kullanıcı mesajında `run_turn` çağır. Liste yerinde güncellenir:

```python
from helpers import md_file_reading
from runner import run_turn

messages = [{"role": "system", "content": md_file_reading("code_agent.md")}]

while True:
    user_input = input("You > ")
    if user_input.strip().lower() == "quit":
        break
    messages.append({"role": "user", "content": user_input})
    print(run_turn("code_agent", messages, client, "<MODEL_ADI>"))
```

**Parametreler**

| Ad | Açıklama |
|----|----------|
| `agent` | Çalıştırılacak agent profilinin adı |
| `client`, `model` | OpenAI uyumlu bir client ve model adı |
| `max_turns` | İstek başına maksimum model çağrısı sayısı (varsayılan `10`). Sonsuz araç döngülerini engeller. Aşılırsa bir hata mesajı döndürülür |
| `on_tool_call` | Opsiyonel callback `(name, arguments)`. Her araç çalışmadan önce çağrılır, kendi arayüzünde ilerlemeyi yazdırmak için kullanışlıdır (sadece `run_turn`) |
| `system_prompt` | Opsiyonel system prompt (sadece `run_agent`) |

Her agent'a kendi system prompt'unu ver (örneğin agent başına bir Markdown dosyası). Profil agent'ın hangi araçlara sahip olacağını belirler, prompt ise ona rolünü anlatır.

## Yeni Araç Ekleme

1. `tools_and_schemas.py` içinde fonksiyonu yaz ve şemasıyla birlikte kaydet:

```python
def word_count(text: str) -> str:
    """Verilen metindeki kelimeleri sayar."""
    return str(len(text.split()))


register_tool(
    word_count,
    {
        "type": "function",
        "function": {
            "name": "word_count",
            "description": "Verilen metindeki kelimeleri sayar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Kelimeleri sayılacak metin"},
                },
                "required": ["text"],
            },
        },
    },
)
```

2. `agents.py` içinde, bu aracı kullanacak her agent'ın profiline `"word_count"` ekle.

Güncellenecek ikinci bir liste yok: fonksiyon ve şeması birlikte kaydedildiği için birbirinden kopamaz.

## Yardımcı Fonksiyon: `md_file_reading`

`helpers.py`, **agent aracı olmayan** fonksiyonları barındırır: bunlar hiçbir zaman kaydedilmez, model onları göremez ve doğrudan senin kodundan çağrılır.

`md_file_reading` bir Markdown dosyasını okur ve `{{ CURRENT_DATETIME }}` yer tutucusunu güncel tarih ve saatle (`%d %B %Y, %H:%M` formatında) değiştirir. Tipik kullanımı system prompt yüklemektir; böylece agent her çalıştırmada güncel zamanı bilir.

**Örnek**

`code_agent.md`:

```markdown
Sen yardımsever bir kod asistanısın.
Güncel tarih ve saat: {{ CURRENT_DATETIME }}
```

Kullanım:

```python
system_prompt = md_file_reading("code_agent.md")
```

## Güvenlik Notları

- `read_file` ve `edit_file` için **yol kısıtlaması yoktur**. Agent'a sistemdeki herhangi bir dosyayı okuma/yazma erişimi verirler. Güvenilmeyen ortamlarda çalıştırmadan önce bunları belirli bir çalışma klasörüyle sınırlamayı düşün.
- `execute` içindeki izin kontrolü, ancak profillerin kadar güvenlidir. Güçlü araçları (örneğin `edit_file`) sadece ihtiyacı olan agent'lara ve her zaman açıkça isimle ver.
- `fetch_web_page` ve `web_search` dışarıdan içerik getirir. Bu içerik agent'ın davranışını yönlendirmeye çalışan metinler barındırabilir (prompt injection); web'den gelen içeriği talimat değil, veri olarak değerlendir.
- API anahtarını koda yazmak yerine bir `.env` dosyasında tut ve bu dosyayı `.gitignore`'a ekle.

## Lisans

Lisans bilgini buraya ekle (örneğin MIT).