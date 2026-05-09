import os
import time
import json
import requests
from bs4 import BeautifulSoup

# ================== CONFIG (SECURE) ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

DATA_FILE = "data.json"
USERS_FILE = "users.json"

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

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = []

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# ================== TELEGRAM FUNCTIONS ==================
def send_private_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": chat_id,
            "text": text
        })
    except Exception as e:
        print(f"Error sending to {chat_id}: {e}")

def get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url).json()
        for result in response.get("result", []):
            message = result.get("message")
            if message:
                chat_id = str(message["chat"]["id"])
                text = message.get("text", "")

                # التصحيح هنا: لازم الكود اللي تحت الـ if يكون واخد مسافة لداخل
                if text == "/start":
                    if chat_id not in users:
                        users.append(chat_id)
                        save_users()

                        # رسالة للمستخدم الجديد
                        send_private_message(
                            chat_id,
                            "✅ You are now subscribed to job alerts!"
                        )

                        # إشعار للأدمن (إنت)
                        admin_message = f"🚀 New User Joined\n\n👤 User ID: {chat_id}\n📛 Username: @{message['from'].get('username', 'NoUsername')}"
                        send_private_message(CHAT_ID, admin_message)
    except Exception as e:
        print("Update Error:", e)

def send_message_to_all(text):
    for user in users:
        send_private_message(user, text)

# ================== SCRAPING ==================
def get_nafezly_jobs():
    url = "https://nafezly.com/projects"
    try:
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
    except:
        return []

# ================== CORE LOGIC ==================
def check_jobs():
    jobs = get_nafezly_jobs()
    for job in jobs:
        unique_id = job["title"] + job["source"]
        if unique_id not in data["last_jobs"]:
            message = f"🚀 NEW JOB ALERT\n\n📌 {job['title']}\n🌍 Source: {job['source']}\n🔗 {job['link']}"
            send_message_to_all(message)
            data["last_jobs"].append(unique_id)
            data["last_jobs"] = data["last_jobs"][-200:]
            save_data()

# ================== START ==================
send_private_message(CHAT_ID, "🤖 Public Job Bot Started Successfully")

while True:
    try:
        get_updates()
        check_jobs()
        time.sleep(30) # زودت الوقت شوية عشان الأمان
    except Exception as e:
        print("ERROR:", e)
        time.sleep(20)
