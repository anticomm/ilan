import requests
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(product):
    message = f"📢 {product['title']}\n💰 {product['price']}\n🔗 {product['link']}"
    image_url = product['image']

    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        data = {
            "chat_id": CHAT_ID,
            "caption": message,
            "photo": image_url,
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, data=data)
            print(f"✅ Gönderildi: {product['title']}")
        except Exception as e:
            print(f"❌ Telegram gönderim hatası: {e}")
    else:
        print("❌ Telegram token veya chat ID eksik.")
