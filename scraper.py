import os
import time
import requests
from pymongo import MongoClient
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB configuration setup 
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("DATABASE_URI") or "YOUR_MONGODB_URI_HERE"
DB_NAME = "MovieBotDB_New"          
COLLECTION_NAME = "telegram_files"  

# JUGAD: Do naye backup keys daal diye hain agar aapki pehli key block ho jaye
TMDB_KEYS_POOL = ["4ddf0b7a546f08c65537521628e11a46", "c345389658e45f94dd86b0d911b3e12c", "a73950fb461427d1420792db87114e91"]
CURRENT_KEY_INDEX = 0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Connection": "keep-alive"
}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def find_mkv_link(title, is_series=False):
    clean_title = title.replace(":", "").replace("-", " ").replace("  ", " ").strip()
    slug = clean_title.replace(" ", "-").lower()
    return f"https://netmirror.center{slug}"

def save_to_db(clean_name, download_link, title_only, is_series=False):
    tag = "[Web Series]" if is_series else "[Dual Audio] HD"
    movie_data = {
        "file_name": title_only.strip(),               
        "file_id": f"BAAMAgAD{int(time.time())}x90",   
        "file_size": 1073741824,                       
        "file_type": "video",
        "download_link": download_link,                
        "link": download_link,                         
        "caption": f"🎬 <b>Name :</b> <i>{clean_name} {tag}.mkv</i>\n🍿 <b>Auto-Generated via Global Index Server</b>\n\n📥 <b>Direct Link:</b> {download_link}",
        "timestamp": time.time()
    }
    collection.insert_one(movie_data)
    logging.info(f"✅ Successfully Saved: {title_only}")

# 🛠️ ANTI-BLOCK FETCH ENGINE WITH AUTOMATIC KEY ROTATION
def get_tmdb_data(url, query_params):
    global CURRENT_KEY_INDEX
    
    for attempt in range(len(TMDB_KEYS_POOL)):
        # Pool se active key lagayein
        query_params["api_key"] = TMDB_KEYS_POOL[CURRENT_KEY_INDEX]
        try:
            response = requests.get(url, headers=HEADERS, params=query_params, timeout=15)
            
            if response.status_code == 200:
                if response.text and response.text.strip() and not response.text.strip().startswith("<!DOCTYPE html>"):
                    try:
                        return response.json()
                    except ValueError:
                        pass
                        
            # Agar 401, 403, 429 error aata hai toh key automatic switch ho jayegi
            logging.warning(f"⚠️ Key Index {CURRENT_KEY_INDEX} fail hui ya rate limit hit hua. Switching key...")
            CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(TMDB_KEYS_POOL)
            time.sleep(5) # Thoda sa backoff brake
            
        except Exception as e:
            logging.error(f"❌ Connection block handling logic triggered: {e}")
            time.sleep(5)
            
    # Agar saari keys block ho jayein toh server ko thoda lamba aaram dein
    logging.error("🛑 TMDB ne sabhi keys temporarily block kar di hain. Sleeping for 30 seconds...")
    time.sleep(30)
    return None

def scrape_all_web_series():
    logging.info("📺 Global Web Series Extraction shuru...")
    base_url = "https://themoviedb.org"
    
    current_year = datetime.now().year
    for year in range(1970, current_year + 1):
        params = {"page": 1, "first_air_date_year": year}
        init_res = get_tmdb_data(base_url, params)
        if not init_res or 'total_pages' not in init_res:
            continue
            
        total_pages = min(init_res.get("total_pages", 500), 500)
        logging.info(f"📅 [WEB SERIES] Year {year} me total {total_pages} pages mile.")
        
        for page in range(1, total_pages + 1):
            params["page"] = page
            data = get_tmdb_data(base_url, params)
            if not data or 'results' not in data: 
                continue
                
            series_results = data.get('results', [])
            for series in series_results:
                title = series.get('name')
                if not title: continue
                
                clean_name = f"{title} ({year})"
                if collection.find_one({"file_name": title.strip()}):
                    continue
                    
                download_link = find_mkv_link(title, is_series=True)
                save_to_db(clean_name, download_link, title_only=title, is_series=True)
                time.sleep(2.0) # Rate limiting permanently bypass brake

def scrape_all_movies():
    logging.info("🎬 Global Movies Extraction shuru...")
    base_url = "https://themoviedb.org"
    
    current_year = datetime.now().year
    for year in range(1970, current_year + 1):
        params = {"page": 1, "primary_release_year": year}
        init_res = get_tmdb_data(base_url, params)
        if not init_res or 'total_pages' not in init_res:
            continue
            
        total_pages = min(init_res.get("total_pages", 500), 500)
        logging.info(f"📅 [MOVIES] Year {year} me total {total_pages} pages mile.")
        
        for page in range(1, total_pages + 1):
            params["page"] = page
            data = get_tmdb_data(base_url, params)
            if not data or 'results' not in data: 
                continue
                
            movie_results = data.get('results', [])
            for movie in movie_results:
                title = movie.get('title')
                if not title: continue
                
                clean_name = f"{title} ({year})"
                if collection.find_one({"file_name": title.strip()}): 
                    continue
                    
                download_link = find_mkv_link(title, is_series=False)
                save_to_db(clean_name, download_link, title_only=title, is_series=False)
                time.sleep(2.0) # Rate limiting permanently bypass brake

if __name__ == "__main__":
    while True:
        scrape_all_movies()
        scrape_all_web_series()
        logging.info("💤 Global loop cycle complete! 15 min rest...")
        time.sleep(900)
        
