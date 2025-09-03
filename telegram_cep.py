import os
import requests

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_message(product):
    title = product.get("title", "Başlık yok")
    price = product.get("price", "Fiyat yok")
    link = product.get("link", "")
    image = product.get("image", "")

    message = f"📢 {title}\n💰 {price}\n🔗 {link}"

    if not TOKEN or not CHAT_ID:
        print("❌ Telegram token veya chat ID eksik.")
        return

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={
                "chat_id": CHAT_ID,
                "caption": message,
                "photo": image,
                "parse_mode": "HTML"
            }
        )
        if response.status_code == 200:
            print(f"✅ Gönderildi: {title}")
        else:
            print(f"❌ Telegram API hatası: {response.text}")
    except Exception as e:
        print(f"❌ Telegram gönderim hatası: {e}")
