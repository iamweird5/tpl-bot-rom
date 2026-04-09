import os
import time
import json
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

LIBRARY_ID = os.environ.get("LIBRARY_ID")
LIBRARY_PASSWORD = os.environ.get("LIBRARY_PASSWORD")

ATTRACTIONS = {
    "Ripley's Aquarium": 18,
    "ROM": 19,
    "Toronto Zoo": 22
}

LOGIN_URL = "https://epass-ca.quipugroup.net/epass/login.php"

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def login(driver):
    driver.get(LOGIN_URL)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.NAME, "txtPatronNumber"))
    )

    driver.find_element(By.NAME, "txtPatronNumber").send_keys(LIBRARY_ID)
    driver.find_element(By.NAME, "txtPassword").send_keys(LIBRARY_PASSWORD)
    driver.find_element(By.NAME, "btnLogin").click()

    # Wait for login to succeed (check presence of logout or home element)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "divHeader"))
    )

def check_availability(driver, attraction_id):
    url = f"https://epass-ca.quipugroup.net/epass_server.php?dataType=json&method=AttractionInfo&functionFile=Attractions&attractionID={attraction_id}&language=en"
    driver.get(url)
    # Wait for page to load JSON
    time.sleep(2)
    body = driver.find_element(By.TAG_NAME, "pre").text
    data = json.loads(body)

    # Look at description text for availability
    description = data.get("AttractionDescription", "")
    if "Show first available offer" in description:
        return "AVAILABLE"
    else:
        return "NOT AVAILABLE"

@app.route("/check")
def check_all():
    driver = get_driver()
    try:
        login(driver)
        results = {}
        for name, attr_id in ATTRACTIONS.items():
            status = check_availability(driver, attr_id)
            results[name] = status
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        driver.quit()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)