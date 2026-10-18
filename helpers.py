from datetime import datetime

def md_file_reading(md_file: str) -> str:
    """Markdown dosyasını okur ve tarih değişkenini günceller."""
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        now_str = datetime.now().strftime("%d %B %Y, %H:%M")
        return prompt_template.replace("{{ CURRENT_DATETIME }}", now_str)
    except FileNotFoundError:
        return f"Hata: Kurallar dosyası ({md_file}) bulunamadı."