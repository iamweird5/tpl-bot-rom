import os
import requests
import json
import traceback
from flask import Flask

app = Flask(__name__)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

EPASS = os.environ.get("EPASS")
REMEMBER = os.environ.get("REMEMBER")  # URL-ENCODED

BASE_URL = "https://epass-ca.quipugroup.net/epass_server.php"

HEADERS = {
    "Cookie": f"ePASS={EPASS}; ePASSRememberMe={REMEMBER}",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

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

# ---------------- CHECK FUNCTION ----------------
def check_attraction(name, attraction_id):
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
        r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)

        print(f"\n🔍 {name} STATUS CODE:", r.status_code)
        print(f"🔍 RAW RESPONSE:\n{r.text[:300]}")

        if r.status_code != 200:
            return "ERROR"

        data = r.json()

        # 🔥 REAL CHECK
        offers = data.get("results") or data.get("data") or data

        print(f"🎯 {name} OFFERS FOUND:", len(offers) if isinstance(offers, list) else "UNKNOWN")

        if isinstance(offers, list) and len(offers) > 0:
            return "AVAILABLE"
        else:
            return "NOT AVAILABLE"

    except Exception:
        print(f"❌ ERROR checking {name}:")
        traceback.print_exc()
        return "ERROR"

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "FINAL API BOT 🚀"

@app.route("/check")
def run_check():
    global last_status

    results = {}

    for name, aid in ATTRACTIONS.items():
        status = check_attraction(name, aid)
        results[name] = status

        # Send alert only when becomes AVAILABLE
        if status == "AVAILABLE" and last_status[name] != "AVAILABLE":
            send_telegram(f"🚨 {name} PASS AVAILABLE!")

        last_status[name] = status

    return json.dumps(results)

# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)