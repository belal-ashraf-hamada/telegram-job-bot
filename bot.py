import os
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ================== CONFIG (SECURE) ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID") 

DATA_FILE = "data.json"
USERS_FILE = "users.json"
STATS_FILE = "stats.json"

# ================== DATA HELPERS ==================
def load_json(file, default):
    return json.load(open(file, "r", encoding="utf-8")) if os.path.exists(file) else default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_json(DATA_FILE, {"last_jobs": []})
users = load_json(USERS_FILE, [])
stats = load_json(STATS_FILE, {"total": 0, "platforms": {}, "keywords": {}})

# ================== SCRAPERS (THE COMMAND CENTERS) ==================

def fetch_nafezly():
    """كشّاف موقع نفذلي"""
    jobs = []
    try:
        r = requests.get("https://nafezly.com/projects", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a"):
            title, href = a.text.strip(), a.get("href", "")
            if title and "/projects/" in href:
                link = "https://nafezly.com" + href if href.startswith("/") else href
                jobs.append({"title": title, "link": link, "source": "Nafezly"})
    except: pass
    return jobs

def fetch_mostaql():
    """كشّاف موقع مستقل"""
    jobs = []
    try:
        r = requests.get("https://mostaql.com/projects", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.select('a[href*="/project/"]'):
            title, href = link.text.strip(), link.get("href", "")
            if title and len(title) > 10:
                jobs.append({"title": title, "link": href, "source": "Mostaql"})
    except: pass
    return jobs

def fetch_khamsat():
    """كشّاف مجتمع خمسات (طلبات الخدمات غير الموجودة)"""
    jobs = []
    try:
        r = requests.get("https://khamsat.com/community/requests", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.select('a[href*="/community/requests/"]'):
            title = link.text.strip()
            if title and len(title) > 10:
                jobs.append({"title": title, "link": link.get("href"), "source": "Khamsat"})
    except: pass
    return jobs

# ================== MARKET INSIGHTS LOGIC ==================

def process_stats(job):
    stats["total"] += 1
    stats["platforms"][job["source"]] = stats["platforms"].get(job["source"], 0) + 1
    
    # كلمات مفتاحية للتحليل (تقدر تزودها)
    key_tags = ["برمجة", "python", "رياضيات", "security", "ترجمة", "تصميم", "excel"]
    for tag in key_tags:
        if tag in job["title"].lower():
            stats["keywords"][tag] = stats["keywords"].get(tag, 0) + 1
    save_json(STATS_FILE, stats)

# ================== CORE ENGINE ==================

def check_for_updates():
    # جمع كل المشاريع من كل المصادر
    all_found = fetch_nafezly() + fetch_mostaql() + fetch_khamsat()
    
    for job in all_found:
        if job["link"] not in data["last_jobs"]:
            process_stats(job)
            
            alert = f"🌟 مشروع جديد مكتشف!\n\n📌 {job['title']}\n🏢 المصدر: {job['source']}\n🔗 {job['link']}"
            
            # إرسال للكل
            for u in users:
                send_telegram(u, alert)
            
            data["last_jobs"].append(job["link"])
            data["last_jobs"] = data["last_jobs"][-500:] # حفظ آخر 500 لمنع التكرار
            save_json(DATA_FILE, data)

def send_telegram(id, txt):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": id, "text": txt})

# ================== START EXECUTION ==================
print("🚀 Newton Scout Global Scraper is active...")

while True:
    try:
        check_for_updates()
        # وقت الانتظار 5 دقائق (300 ثانية) إلزامي لتجنب الـ Ban من مستقل
        time.sleep(300) 
    except Exception as e:
        print(f"Alert: {e}")
        time.sleep(60)
