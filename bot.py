import os
import time
import json
import requests
from bs4 import BeautifulSoup
# === حطه هنا بالظبط ===
start_time = time.time()

# ================== CONFIG ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
# تأكد إن CHAT_ID في Railway هو الـ ID بتاعك أنت كأدمن
ADMIN_ID = os.environ.get("CHAT_ID") 

DATA_FILE = "data.json"
USERS_FILE = "users.json"

# ================== LOAD DATA ==================
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_json(DATA_FILE, {"last_jobs": []})
users = load_json(USERS_FILE, [])

# ================== TELEGRAM FUNCTIONS ==================
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def check_for_new_users():
    """بتشوف مين بعت /start وتضيفه فوراً"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        r = requests.get(url, timeout=10).json()
        if r.get("ok"):
            for update in r["result"]:
                if "message" in update and "text" in update["message"]:
                    chat_id = str(update["message"]["chat"]["id"])
                    if update["message"]["text"] == "/start":
                        if chat_id not in users:
                            users.append(chat_id)
                            save_json(USERS_FILE, users)
                            send_telegram(chat_id, "✅ تم تفعيل إشعارات نيوتن بنجاح!")
                            # إشعار ليك أنت كأدمن
                            send_telegram(ADMIN_ID, f"🚀 مستخدم جديد انضم: {chat_id}")
    except:
        pass

# ================== SCRAPERS ==================
def fetch_jobs():
    jobs = []
    sources = {
        "Nafezly": "https://nafezly.com/projects",
        "Mostaql": "https://mostaql.com/projects",
        "Khamsat": "https://khamsat.com/community/requests"
    }
    
    for name, url in sources.items():
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            # منطق بسيط لجمع الروابط (تقدر تطوره لكل موقع)
            for a in soup.find_all("a", href=True):
                title = a.text.strip()
                href = a['href']
                if len(title) > 10 and ("/project" in href or "/requests/" in href):
                    full_link = href if href.startswith("http") else url.split(".com")[0] + ".com" + href
                    jobs.append({"title": title, "link": full_link, "source": name})
        except:
            continue
    return jobs

# ================== MAIN ENGINE (INSTANT MODE) ==================
if ADMIN_ID:
    send_telegram(ADMIN_ID, "🚀 وضع 'صياد اللحظة' اشتغل.. القديم مش هيتبعت نهائياً.")

print("🚀 Newton Scraper: Time-Filter Active...")

while True:
    try:
        check_for_new_users()
        found_jobs = fetch_jobs()
        
        for job in found_jobs:
            # الفلترة بقت مزدوجة: الرابط مش في الذاكرة + البوت شغال من مدة
            if job["link"] not in data["last_jobs"]:
                
                # السطر ده هو "الجوكر": لو البوت شغال من أقل من 5 دقائق
                # بيسجل المشاريع بس مبيبعتش رسايل (بيملى الذاكرة)
                uptime = time.time() - start_time
                if uptime < 300: # أول 5 دقائق صمت تام
                    if job["link"] not in data["last_jobs"]:
                        data["last_jobs"].append(job["link"])
                    continue

                # لو عدينا أول 5 دقائق، أي حاجة جديدة هتوصلك فوراً
                msg = f"🌟 مشروع جديد ({job['source']})\n\n📌 {job['title']}\n🔗 {job['link']}"
                
                for user_id in users:
                    send_telegram(user_id, msg)
                
                if ADMIN_ID and ADMIN_ID not in users:
                    send_telegram(ADMIN_ID, msg)

                data["last_jobs"].append(job["link"])
                data["last_jobs"] = data["last_jobs"][-500:]
                save_json(DATA_FILE, data)
        
        time.sleep(120) 
        
    except Exception as e:
        print(f"Loop Error: {e}")
        time.sleep(30)
