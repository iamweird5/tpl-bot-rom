import os
import time
import requests
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
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
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("📲 Telegram sent!")
    except Exception as e:
        print("❌ Telegram error:", e)

# ---------------- DRIVER ----------------
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

# ---------------- CHECK FUNCTION ----------------
def check():
    global last_status
    driver = get_driver()

    try:
        # ---------------- LOGIN ----------------
        driver.get(LOGIN_URL)
        time.sleep(3)

        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)

        login_btn = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
        driver.execute_script("arguments[0].click();", login_btn)

        # Wait for login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Logout')]"))
        )
        print("✅ LOGIN SUCCESS")

        # ---------------- OPEN MAIN PAGE ----------------
        driver.get(MAIN_URL)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(5)

        # ---------------- DEBUG FULL PAGE ----------------
        print("\n================ DEBUG START ================\n")

        full_text = driver.find_element(By.TAG_NAME, "body").text
        print("🔹 FULL PAGE TEXT (first 2000 chars):\n")
        print(full_text[:2000])

        # ---------------- FIND ROM CARD ----------------
        print("\n🔍 Searching for ROM elements...\n")

        elements = driver.find_elements(By.XPATH, "//*[contains(text(),'Royal Ontario Museum')]")

        print(f"🔹 Found {len(elements)} matching elements\n")

        if not elements:
            print("❌ ROM NOT FOUND")
            return "ERROR"

        # Pick first match
        rom_card = elements[0]

        # ---------------- DEBUG ELEMENT ----------------
        print("\n🔹 ROM ELEMENT HTML:\n")
        print(rom_card.get_attribute("outerHTML")[:1000])

        print("\n🔹 ROM ELEMENT TEXT:\n")
        description_text = rom_card.text
        print(description_text[:500])

        print("\n================ DEBUG END ================\n")

        # ---------------- DETECT STATUS ----------------
        text_lower = full_text.lower()

        if "show first available offer" in text_lower:
            status = "AVAILABLE"
            print("✅ AVAILABLE")

        elif "no passes available at this time" in text_lower or \
             "all passes for this attraction have been reserved" in text_lower:
            status = "NOT AVAILABLE"
            print("❌ NOT AVAILABLE")

        else:
            status = "UNKNOWN"
            print("⚠️ UNKNOWN")

        # ---------------- TELEGRAM ----------------
        if status != last_status:
            last_status = status
            if status == "AVAILABLE":
                send_telegram("🚨 ROM PASS AVAILABLE! BOOK NOW!")

        return status

    except Exception as e:
        print("❌ ERROR:", e)
        return "ERROR"

    finally:
        driver.quit()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "ROM Debug Bot Running"

@app.route("/check")
def run():
    result = check()
    return f"Check done: {result}"

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))