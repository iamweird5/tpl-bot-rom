import os
import time
import requests
import traceback
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# ---------------- CONFIG ----------------
LOGIN_URL = "https://epass-ca.quipugroup.net/login"
MAIN_URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"

USERNAME = os.environ.get("LIBRARY_USER")
PASSWORD = os.environ.get("LIBRARY_PASS")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

last_status = None

# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("📲 Telegram sent")
    except Exception as e:
        print("❌ Telegram error:", e)

# ---------------- DRIVER ----------------
def get_driver():
    options = Options()
    options.binary_location = "/usr/bin/chromium"

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    service = Service("/usr/bin/chromedriver")

    return webdriver.Chrome(service=service, options=options)

# ---------------- CHECK FUNCTION ----------------
def check():
    global last_status
    driver = get_driver()

    try:
        print("🚀 Starting check...")

        # ---------------- LOGIN ----------------
        driver.get(LOGIN_URL)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )

        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)

        login_btn = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
        driver.execute_script("arguments[0].click();", login_btn)

        # Wait for login confirmation
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Logout')]"))
        )

        print("✅ LOGIN SUCCESS")

        # ---------------- LOAD MAIN PAGE ----------------
        driver.get(MAIN_URL)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Let JS fully render
        time.sleep(6)

        # ---------------- READ FULL PAGE ----------------
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()

        print("\n📄 PAGE TEXT SAMPLE:\n")
        print(body_text[:1000])

        # ---------------- DETECT STATUS ----------------
        if "show first available offer" in body_text:
            status = "AVAILABLE"
            print("✅ AVAILABLE DETECTED")

        elif "no passes available at this time" in body_text or \
             "all passes for this attraction have been reserved" in body_text:
            status = "NOT AVAILABLE"
            print("❌ NOT AVAILABLE DETECTED")

        else:
            status = "UNKNOWN"
            print("⚠️ UNKNOWN STATUS")

        # ---------------- TELEGRAM ----------------
        if status != last_status:
            last_status = status

            if status == "AVAILABLE":
                send_telegram("🚨 ROM PASS AVAILABLE! BOOK NOW!")

        return status

    except Exception as e:
        print("❌ ERROR OCCURRED:")
        traceback.print_exc()
        return "ERROR"

    finally:
        driver.quit()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "ROM Bot Running"

@app.route("/check")
def run():
    result = check()
    return f"Check done: {result}"

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))