import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# CONFIG
LOGIN_URL = "https://epass-ca.quipugroup.net/login"  # adjust if different
PASS_URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"
CHECK_INTERVAL = 60
TARGET_TEXT = "Royal Ontario Museum"

# TELEGRAM CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# LIBRARY LOGIN (stored in Render environment variables)
USERNAME = os.environ.get("LIBRARY_USER")
PASSWORD = os.environ.get("LIBRARY_PASS")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📲 Telegram sent!")
    except Exception as e:
        print("Telegram error:", e)

def create_driver():
    options = Options()
    options.add_argument("--headless=new")  # headless Chrome
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def login(driver):
    driver.get(LOGIN_URL)
    time.sleep(2)
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "loginBtn").click()
    print("🔑 Logged in")
    time.sleep(5)  # wait for login to complete

def check_availability():
    driver = create_driver()
    try:
        login(driver)
        driver.get(PASS_URL)
        time.sleep(5)

        # Find ROM card
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{TARGET_TEXT}')]")
        for el in elements:
            try:
                el.click()
                print("👉 Clicked ROM card")
                break
            except:
                continue

        time.sleep(2)

        # Click Offers tab
        offers_tab = driver.find_element(By.XPATH, "//*[contains(text(), 'Offers')]")
        offers_tab.click()
        time.sleep(2)

        # Read offers section
        body_text = driver.find_element(By.TAG_NAME, "body").text

        if "No passes available at this time" not in body_text:
            print("✅ ROM PASS AVAILABLE!")
            send_telegram(f"✅ ROM Pass available!\n{PASS_URL}")
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

# Run bot loop
if __name__ == "__main__":
    import threading
    threading.Thread(target=bot_loop, daemon=True).start()

    from flask import Flask
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "ROM Bot is running"

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)