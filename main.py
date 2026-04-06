from flask import Flask
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import threading

app = Flask(__name__)

BOT_TOKEN = os.environ.get("8750333022:AAHYYfvVEuamVJTOmaX2-_1UaN5EOd3vaQQ")
CHAT_ID = os.environ.get("5287405098")

URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"
TARGET_TEXT = "Royal Ontario Museum"
CHECK_INTERVAL = 60

def send_telegram():
    message = f"🧪 TEST SUCCESS!\nROM detected.\n{URL}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    print("📲 Telegram sent!")

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def check_availability():
    driver = create_driver()
    try:
        driver.get(URL)
        time.sleep(5)

        # Step 1: find ROM card
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Royal Ontario Museum')]")
        for el in elements:
            try:
                el.click()
                break
            except:
                continue
        time.sleep(2)

        # Step 2: click Offers tab
        offers_tab = driver.find_element(By.XPATH, "//*[contains(text(), 'Offers')]")
        offers_tab.click()
        time.sleep(2)

        # Step 3: check if any passes
        body_text = driver.find_element(By.TAG_NAME, "body").text
        if "No passes available at this time" not in body_text:
            print("✅ PASS AVAILABLE!")
            send_telegram()
        else:
            print("❌ No passes available")

    except Exception as e:
        print("Error:", e)
    finally:
        driver.quit()

def bot_loop():
    while True:
        check_availability()
        time.sleep(CHECK_INTERVAL)

# Start bot in a separate thread
threading.Thread(target=bot_loop, daemon=True).start()

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))