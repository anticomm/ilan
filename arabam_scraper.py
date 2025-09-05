import os
import re
import time
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram_cep import send_message

URL = "https://www.arabam.com/ikinci-el/otomobil/bmw-fiyati-dusenler?minYear=2015&sort=startedAt.desc&take=50"
SENT_FILE = "send_products.txt"

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36")
    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)

def inject_cookie_from_b64(driver):
    b64 = os.getenv("COOKIE_B64")
    if not b64:
        print("❌ COOKIE_B64 bulunamadı.")
        return

    try:
        raw = base64.b64decode(b64).decode("utf-8")
    except Exception as e:
        print("❌ Base64 çözümleme hatası:", e)
        return

    driver.get(URL)
    time.sleep(2)

    for pair in raw.split(";"):
        if "=" in pair:
            name, value = pair.strip().split("=", 1)
            driver.add_cookie({"name": name.strip(), "value": value.strip()})

    print("✅ Cookie başarıyla enjekte edildi.")

def load_sent_data():
    if not os.path.exists(SENT_FILE):
        return {}
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return dict(line.strip().split(" | ") for line in f if " | " in line)

def save_sent_data(products_to_send):
    existing = load_sent_data()
    for product in products_to_send:
        existing[product["id"].strip()] = product["price"].strip()
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        for ilan_id, price in existing.items():
            f.write(f"{ilan_id} | {price}\n")

def extract_data_from_onclick(span):
    try:
        onclick = span.get_attribute("onclick")
        match = re.search(r"handleClickComparePopup\(\{(.*?)\},", onclick)
        if not match:
            return None
        raw = match.group(1)

        def extract(key):
            pattern = rf"{key}:\s*'([^']+)'"
            found = re.search(pattern, raw)
            return found.group(1) if found else None

        return {
            "id": extract("id"),
            "price": extract("price"),
            "link": "https://www.arabam.com" + extract("url"),
            "image": extract("image"),
            "title": extract("title").replace("&quot;", '"') if extract("title") else "Başlık yok"
        }
    except Exception as e:
        print("⚠️ Onclick parse hatası:", e)
        return None

def run():
    driver = get_driver()
    inject_cookie_from_b64(driver)
    driver.get(URL)
    time.sleep(5)

    print("🔍 Sayfa başlığı:", driver.title)
    print("🔍 Sayfa URL:", driver.current_url)
    print("🔍 Sayfa kaynak uzunluğu:", len(driver.page_source))

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.toolbox-item[id^='compare-container']"))
        )
    except:
        print("⚠️ Sayfa yüklenemedi.")
        driver.quit()
        return

    spans = driver.find_elements(By.CSS_SELECTOR, "span.toolbox-item[id^='compare-container']")
    print(f"🔍 {len(spans)} ilan bulundu.")

    products = [extract_data_from_onclick(span) for span in spans]
    products = [p for p in products if p]

    driver.quit()

    sent_data = load_sent_data()
    products_to_send = []

    for product in products:
        ilan_id = product["id"]
        price = product["price"].strip()

        if ilan_id in sent_data:
            if price != sent_data[ilan_id]:
                print(f"📉 Fiyat değişti: {product['title']} → {sent_data[ilan_id]} → {price}")
                products_to_send.append(product)
        else:
            print(f"🆕 Yeni ilan: {product['title']}")
            products_to_send.append(product)

    if products_to_send:
        for p in products_to_send:
            send_message(p)
        save_sent_data(products_to_send)
        print(f"📁 Dosya güncellendi: {len(products_to_send)} ilan eklendi/güncellendi.")
    else:
        print("⚠️ Yeni veya indirimli ilan bulunamadı.")

if __name__ == "__main__":
    run()
