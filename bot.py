import requests
from bs4 import BeautifulSoup
import time
import json
import os

BOT_TOKEN = "8683911523:AAHqxkUnBb7IgBMpR8aeiQ5pmEeh5ATEB8U"
CHAT_ID = "1129385768"

URL = "https://nafezly.com/projects"
DATA_FILE = "data.json"

# ================== LOAD DATA ==================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {
        "last_jobs": []
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================== TELEGRAM ==================
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================== SCRAPER ==================
def get_jobs():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = soup.find_all("h3")

    results = []
    for job in jobs[:10]:
        title = job.text.strip()
        link = URL

        results.append({
            "title": title,
            "link": link
        })

    return results

# ================== CHECK JOBS ==================
def check_jobs():
    jobs = get_jobs()

    for job in jobs:
        if job["title"] not in data["last_jobs"]:

            msg = f"""🚀 NEW JOB ALERT

📌 {job['title']}
🔗 {job['link']}
"""

            send_message(msg)

            data["last_jobs"].append(job["title"])

            # نخزن آخر 100 وظيفة فقط
            data["last_jobs"] = data["last_jobs"][-100:]

            save_data()

# ================== START ==================
send_message("🤖 Job Bot Started Successfully")

while True:
    try:
        check_jobs()
        time.sleep(20)

    except Exception as e:
        print(e)
        time.sleep(20)