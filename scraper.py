import os
import time
import requests
from pymongo import MongoClient
import logging
import unicodedata
import random

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("DATABASE_URI") or "YOUR_MONGODB_URI_HERE"
DB_NAME = os.getenv("DATABASE_NAME") or "MovieBotDB_New"          
COLLECTION_NAME = "telegram_files"  

TMDB_API_KEY = "4ddf0b7a546f08c65537521628e11a46"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def clean_accent_characters(text):
    if not text: return ""
    normalized = unicodedata.normalize('NFD', text)
    return "".join([c for c in normalized if unicodedata.category(c) != 'Mn'])

def find_mkv_link(title):
    clean_title = title.replace(":", "").replace("-", " ").replace("  ", " ").strip()
    slug = clean_title.replace(" ", "-").lower()
    return f"https://netmirror.center{slug}"

def save_to_db(clean_name, download_link, title_only, is_series=False):
    tag = "[Web Series]" if is_series else "[Dual Audio] HD"
    search_friendly_name = clean_accent_characters(title_only.strip().strip('"').strip("'").strip())
    
    movie_data = {
        "file_name": search_friendly_name,              
        "file_id": f"DOWNLOAD_LINK_MODE_{int(time.time())}", 
        "file_size": 1073741824,                       
        "file_type": "video",
        "download_link": download_link,                
        "link": download_link,                         
        "caption": f"🎬 <b>Name :</b> <i>{clean_name.strip()} {tag}.mkv</i>\n🍿 <b>Auto-Generated via Global Index Server</b>\n\n📥 <b>Direct Link:</b> {download_link}",
        "timestamp": time.time()
    }
    collection.insert_one(movie_data)
    logging.info(f"✅ Saved Clean Name: {search_friendly_name}")

def get_tmdb_data(url):
    for attempt in range(4):
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            if response.status_code == 200:
                if response.text and not response.text.strip().startswith("<!DOCTYPE html>"):
                    return response.json()
            elif response.status_code in:
                logging.warning(f"⚠️ TMDB Rate Limit! Sleeping for 20s...")
                time.sleep(20)
                continue
        except Exception as e:
            logging.error(f"❌ Connection glitch: {e}")
        time.sleep(4)
    return None

def scrape_all_web_series():
    logging.info("📺 Year 2000 se 2026 ki All Languages Web Series Extraction shuru...")
    base_url = "https://themoviedb.org"
    for year in range(2000, 2027):
        logging.info(f"📅 [WEB SERIES] Year {year} fetch ho raha hai...")
        for page in range(1, 31): 
            tmdb_url = f"{base_url}?api_key={TMDB_API_KEY}&page={page}&first_air_date_year={year}"
            data = get_tmdb_data(tmdb_url)
            if not data or 'results' not in data: break
            
            results = data.get('results', [])
            if not results: break
            for series in results:
                title = series.get('name')
                if not title: continue
                search_friendly_name = clean_accent_characters(title.strip().strip('"').strip("'").strip())
                if collection.find_one({"file_name": search_friendly_name}): continue
                
                save_to_db(f"{title} ({year})", find_mkv_link(title), title, is_series=True)
                time.sleep(random.uniform(1.5, 2.5))

def scrape_all_movies():
    logging.info("🎬 Year 2000 se 2026 ki All Languages Movies Extraction shuru...")
    base_url = "https://themoviedb.org"
    for year in range(2000, 2027):
        logging.info(f"📅 [MOVIES] Year {year} fetch ho raha hai...")
        for page in range(1, 31):
            tmdb_url = f"{base_url}?api_key={TMDB_API_KEY}&page={page}&primary_release_year={year}"
            data = get_tmdb_data(tmdb_url)
            if not data or 'results' not in data: break
            
            results = data.get('results', [])
            if not results: break
            for movie in results:
                title = movie.get('title')
                if not title: continue
                search_friendly_name = clean_accent_characters(title.strip().strip('"').strip("'").strip())
                if collection.find_one({"file_name": search_friendly_name}): continue
                
                save_to_db(f"{title} ({year})", find_mkv_link(title), title, is_series=False)
                time.sleep(random.uniform(1.5, 2.5))

if __name__ == "__main__":
    while True:
        scrape_all_movies()
        scrape_all_web_series()
        logging.info("💤 Loop complete. 15 minute rest...")
        time.sleep(900)
                
