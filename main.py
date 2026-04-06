import time
import requests
import os
from flask import Flask
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# CONFIG
URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"
CHECK_INTERVAL = 60
TARGET_TEXT = "Royal Ontario Museum"  # ROM

BOT_TOKEN = os.environ.get("8750333022:AAHYYfvVEuamVJTOmaX2-_1UaN5EOd3vaQQ")
CHAT_ID = os.environ.get("5287405098")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"


def send_telegram():
    message = f"🧪 TEST SUCCESS!\nROM detected on page.\n{URL}"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=data)
        print("📲 Telegram sent!")
    except Exception as e:
        print("Telegram error:", e)


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(options=options)


def check_availability():
    driver = None
    try:
        driver = create_driver()
        driver.get(URL)
        time.sleep(5)

        page_text = driver.find_element(By.TAG_NAME, "body").text

        # ✅ TEST CONDITION (just checks ROM exists)
        if TARGET_TEXT in page_text:
            print("✅ ROM FOUND — TEST TRIGGER")

            if not hasattr(check_availability, "alert_sent"):
                send_telegram()
                check_availability.alert_sent = True

            return True

        print("❌ ROM not found (unlikely)")
        return False

    except Exception as e:
        print("Error:", e)
        return False

    finally:
        if driver:
            driver.quit()


def run_bot():
    while True:
        check_availability()
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    threading.Thread(target=run_bot).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)