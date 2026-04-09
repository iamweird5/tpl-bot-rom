import os
import time
import json
import requests
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
LIBRARY_CARD = os.environ.get("LIBRARY_CARD")
PIN = os.environ.get("PIN")

EPASS_LOGIN_URL = "https://epass-ca.quipugroup.net/"
BASE_URL = "https://epass-ca.quipugroup.net/epass_server.php"

ATTRACTIONS = {
    "Ripley's Aquarium": 18,
    "ROM": 19,
    "Toronto Zoo": 22
}

last_status = {k: None for k in ATTRACTIONS}

# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("📲 Telegram sent")
    except Exception as e:
        print("❌ Telegram error:", e)

# ---------------- SELENIUM LOGIN ----------------
def get_epass_cookie():
    options = Options()
    options.binary_location = "/usr/bin/chromium"

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(EPASS_LOGIN_URL)
        time.sleep(4)

        # 🔥 Find inputs dynamically
        inputs = driver.find_elements(By.TAG_NAME, "input")

        card_input = None
        pin_input = None

        for inp in inputs:
            t = inp.get_attribute("type")
            name = (inp.get_attribute("name") or "").lower()

            if "text" in t and not card_input:
                card_input = inp
            elif "password" in t and not pin_input:
                pin_input = inp

        if not card_input or not pin_input:
            raise Exception("Login fields not found")

        card_input.send_keys(LIBRARY_CARD)
        pin_input.send_keys(PIN)

        # 🔥 Find login button dynamically
        buttons = driver.find_elements(By.TAG_NAME, "button")

        login_button = None
        for btn in buttons:
            if "login" in btn.text.lower() or "sign" in btn.text.lower():
                login_button = btn
                break

        if not login_button:
            raise Exception("Login button not found")

        login_button.click()
        time.sleep(5)

        # 🔥 Get cookies
        cookies = driver.get_cookies()

        epass = None
        remember = None

        for c in cookies:
            if c["name"] == "ePASS":
                epass = c["value"]
            elif c["name"] == "ePASSRememberMe":
                remember = c["value"]

        if not epass or not remember:
            raise Exception("Cookies not found after login")

        print("✅ Login successful")
        return epass, remember

    finally:
        driver.quit()

# ---------------- CHECK FUNCTION ----------------
def check_attraction(name, attraction_id, epass, remember):
    headers = {
        "Cookie": f"ePASS={epass}; ePASSRememberMe={remember}",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    params = {
        "dataType": "json",
        "method": "ePASS_Search",
        "functionFile": "Attractions",
        "searchType": "Offers",
        "dateSelected": "None",
        "limits[searches][attractionID]": attraction_id,
        "language": "en"
    }

    try:
        r = requests.get(BASE_URL, headers=headers, params=params, timeout=15)
        data = r.json()

        print(f"🔍 {name} RAW:", str(data)[:200])

        offers = data.get("results") or data.get("data") or data

        if isinstance(offers, list) and len(offers) > 0:
            return "AVAILABLE"
        else:
            return "NOT AVAILABLE"

    except Exception as e:
        print(f"❌ Error checking {name}:", e)
        return "ERROR"

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "Auto ePass Bot Running 🚀"

@app.route("/check")
def run_check():
    global last_status

    try:
        epass, remember = get_epass_cookie()
    except Exception as e:
        print("❌ Login failed:", e)
        return json.dumps({"error": "LOGIN FAILED"})

    results = {}

    for name, aid in ATTRACTIONS.items():
        status = check_attraction(name, aid, epass, remember)
        results[name] = status

        if status == "AVAILABLE" and last_status[name] != "AVAILABLE":
            send_telegram(f"🚨 {name} PASS AVAILABLE!")

        last_status[name] = status

    return json.dumps(results)

# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)