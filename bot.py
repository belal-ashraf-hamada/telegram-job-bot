import os
import time
import json
import requests
from bs4 import BeautifulSoup

# ================== CONFIG (SECURE) ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

DATA_FILE = "data.json"

# ================== SAFE CHECK ==================
if not BOT_TOKEN or not CHAT_ID:
    raise Exception("Missing BOT_TOKEN or CHAT_ID in environment variables")

# ================== LOAD DATA ==================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"last_jobs": []}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================== TELEGRAM ==================
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text,
            "disable_web_page_preview": False
        })
    except Exception as e:
        print("Telegram Error:", e)

# ================== SCRAPING ==================
def get_nafezly_jobs():
    url = "https://nafezly.com/projects"

    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []

    for a in soup.find_all("a"):
        title = a.text.strip()
        href = a.get("href", "")

        if title and "/projects/" in href:
            if href.startswith("/"):
                href = "https://nafezly.com" + href

            jobs.append({
                "title": title,
                "link": href,
                "source": "Nafezly"
            })

    return jobs

# ================== ALL SOURCES ==================
def get_all_jobs():
    jobs = []
    jobs += get_nafezly_jobs()
    return jobs

# ================== CORE LOGIC ==================
def check_jobs():
    jobs = get_all_jobs()

    for job in jobs:
        unique_id = job["title"] + job["source"]

        if unique_id not in data["last_jobs"]:

            message = f"""🚀 NEW JOB ALERT

📌 {job['title']}
🌍 Source: {job['source']}
🔗 {job['link']}
"""

            send_message(message)

            data["last_jobs"].append(unique_id)
            data["last_jobs"] = data["last_jobs"][-200:]

            save_data()

# ================== START ==================
send_message("🤖 Job Bot Started Successfully (PRO MODE)")

while True:
    try:
        check_jobs()
        time.sleep(20)

    except Exception as e:
        print("Error:", e)
        time.sleep(20)
