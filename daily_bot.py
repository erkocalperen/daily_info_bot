import random
import json
import datetime
import os
import requests
import re
from bs4 import BeautifulSoup
from gtts import gTTS
import locale
from telegram import Bot
from dotenv import load_dotenv


load_dotenv()

# === AYARLAR ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# === VERİ YÜKLEYİCİ ===
def load_words(filename="words_clean.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Kelime dosyası bulunamadı.")
        return []

# === GÜNLÜK KELİMELER ===
def get_random_words(words, count=3):
    return random.sample(words, count)

# === WIKIPEDIA'DAN OLAY ÇEK ===
def get_turkish_today_in_history():
    try:
        locale.setlocale(locale.LC_TIME, 'tr_TR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Turkish_Turkey.1254')
        except locale.Error:
            return "⚠️ Türkçe tarih formatı desteklenemedi."

    if os.name == "nt":
        bugun = datetime.datetime.now().strftime("%#d_%B")
    else:
        bugun = datetime.datetime.now().strftime("%-d_%B")

    url = f"https://tr.wikipedia.org/wiki/{bugun}"
    print(f"🔍 Wikipedia'dan çekiliyor: {url}")

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        headers = soup.find_all("h2")
        olaylar_basligi = next((h for h in headers if "Olaylar" in h.get_text()), None)
        if not olaylar_basligi:
            return f"❌ 'Olaylar' başlığı bulunamadı ({url})"

        ul = olaylar_basligi.find_next("ul")
        if not ul:
            return f"❌ Olay listesi yok ({url})"

        olaylar = ul.find_all("li")
        if not olaylar:
            return f"❌ Olay listesi boş ({url})"

        secili = random.sample(olaylar, min(3, len(olaylar)))
        metinler = []
        for o in secili:
            olay_metin = re.sub(r"\s+", " ", o.text.strip())
            metinler.append(f"• {olay_metin}")
        return "\n".join(metinler)

    except Exception as e:
        return f"⚠️ Hata: {e}"

# === SESLİ OKUMA ===
def speak_words(words):
    text = ". ".join([f"{w['word']}. {w['example']}" for w in words])
    tts = gTTS(text=text, lang="en")
    tts.save("output.mp3")
    os.system("start output.mp3")  # Mac: 'afplay', Linux: 'mpg123'

# === TELEGRAM MESAJ GÖNDER ===
def send_telegram_message(token, chat_id, message):
    try:
        bot = Bot(token=token)
        bot.send_message(chat_id=chat_id, text=message)
        print("✅ Telegram mesajı gönderildi.")
    except Exception as e:
        print(f"❌ Telegram mesaj hatası: {e}")

# === ANA FONKSİYON ===
def main():
    words = load_words("words_clean.json")
    if not words:
        return

    todays_words = get_random_words(words)
    today_fact = get_turkish_today_in_history()

    # Terminal yazdır
    print("\n🧠 Bugünün İngilizce Kelimeleri:\n")
    for w in todays_words:
        print(f"🔹 {w['word']} ({w['meaning']})")
        print(f"    Örnek: {w['example']}\n")

    print("📜 Bugün Tarihte:\n")
    print(today_fact + "\n")

    # Telegram mesajı hazırla
    message = "🧠 Bugünün İngilizce Kelimeleri:\n\n"
    for w in todays_words:
        message += f"🔹 {w['word']} ({w['meaning']})\n    {w['example']}\n\n"
    message += "📜 Bugün Tarihte:\n" + today_fact

    # Gönder
    send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)

    # Sesli oku
    speak_words(todays_words)

if __name__ == "__main__":
    main()
