import os
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from typing import List, Dict
from datetime import datetime
from registry import register_tool


# ==========================================
# 1. PYTHON FONKSİYONLARI (TOOL IMPLEMENTATIONS)
# ==========================================

def read_file(path: str) -> str:
    """Belirtilen dosyanın içeriğini okur ve döndürür."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Hata: Dosya bulunamadı: {path}"
    except Exception as e:
        return f"Hata: Dosya okunurken bir sorun oluştu: {str(e)}"

register_tool(read_file,
              {
                  "type": "function",
                  "function": {
                      "name": "read_file",
                      "description": "Read a text file and return its content",
                      "parameters": {
                          "type": "object",
                          "properties": {
                              "path": {"type": "string", "description": "Path of the file to read"},
                          },
                          "required": ["path"],
                      },
                  },
              },
              )



def edit_file(path: str, content: str) -> str:
    """Belirtilen dosyayı yeni içerikle günceller."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Başarılı: Dosya güncellendi ({path})"
    except Exception as e:
        return f"Hata: Dosya güncellenirken bir sorun oluştu: {str(e)}"

register_tool(edit_file,
              {
                  "type": "function",
                  "function": {
                      "name": "edit_file",
                      "description": "Python dosyasını veya metin dosyasını verilen içerikle günceller veya üzerine yazar.",
                      "parameters": {
                          "type": "object",
                          "properties": {
                              "path": {"type": "string", "description": "Düzenlenecek dosyanın yolu"},
                              "content": {"type": "string",
                                          "description": "Dosyaya yazılacak olan yeni içerik (kod veya metin)"},
                          },
                          "required": ["path", "content"],
                      },
                  },
              },
              )


def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """İnternette arama yapar ve başlık, URL, özet döner."""
    results = []
    try:
        with DDGS() as ddgs:
            ddg_results = ddgs.text(query, max_results=max_results)
            for r in ddg_results:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
    except Exception as e:
        return [{"error": f"Arama sırasında hata oluştu: {str(e)}"}]
    return results

register_tool(web_search,
              {
                  "type": "function",
                  "function": {
                      "name": "web_search",
                      "description": "Güncel bilgileri, haberleri veya web sitelerini bulmak için internette arama yapar. Başlık, URL ve özet metin döndürür.",
                      "parameters": {
                          "type": "object",
                          "properties": {
                              "query": {"type": "string",
                                        "description": "Arama motoruna gönderilecek arama terimi veya soru."},
                              "max_results": {"type": "integer",
                                              "description": "Döndürülecek maksimum sonuç sayısı (varsayılan: 5).",
                                              "default": 5}
                          },
                          "required": ["query"]
                      },
                  },
              },
              )


def fetch_web_page(url: str) -> str:
    """Verilen URL'deki web sayfasının metin içeriğini çekip temizler."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.decompose()

        text = soup.get_text(separator="\n")
        lines = (line.strip() for line in text.splitlines())
        clean_text = '\n'.join(chunk for chunk in lines if chunk)
        return clean_text[:4000]
    except Exception as e:
        return f"Sayfa içeriği çekilirken hata oluştu: {str(e)}"

register_tool(fetch_web_page,
              {
                  "type": "function",
                  "function": {
                      "name": "fetch_web_page",
                      "description": "Verilen bir URL'deki web sayfasının detaylı metin içeriğini okur ve getirir.",
                      "parameters": {
                          "type": "object",
                          "properties": {
                              "url": {"type": "string", "description": "İçeriği okunacak web sitesinin tam URL adresi."}
                          },
                          "required": ["url"]
                      },
                  },
              }
              )



def create_file(path: str, content: str = "") -> str:
    """Yeni bir Python veya metin dosyası oluşturur ve isteğe bağlı içerik yazar."""
    try:
        if os.path.exists(path):
            return f"Hata: Dosya zaten mevcut: {path}. Mevcut bir dosyayı güncellemek veya üzerine yazmak için 'edit_file' kullanın."

        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Başarılı: Dosya oluşturuldu ({path})"
    except Exception as e:
        return f"Hata: Dosya oluşturulurken bir sorun oluştu: {str(e)}"

register_tool(create_file,
              {
                  "type": "function",
                  "function": {
                      "name": "create_file",
                      "description": "Yeni bir Python (.py) veya metin (.txt) dosyası oluşturur ve isteğe bağlı olarak başlangıç içeriği yazar.",
                      "parameters": {
                          "type": "object",
                          "properties": {
                              "path": {"type": "string",
                                      "description": "Oluşturulacak dosyanın yolu ve adı (örn: script.py veya notlar.txt)"},
                              "content": {"type": "string",
                                          "description": "Dosyaya yazılacak olan başlangıç içeriği (kod veya metin). Boş bırakılabilir.",
                                          "default": ""},
                          },
                          "required": ["path"],
                      },
                  },
              },
              )
