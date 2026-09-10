import os
import time
import requests
from pymongo import MongoClient
import logging
from datetime import datetime
import unicodedata

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB configuration setup (MovieBotDB_New optimized)
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("DATABASE_URI") or "YOUR_MONGODB_URI_HERE"
DB_NAME = "MovieBotDB_New"          
COLLECTION_NAME = "telegram_files"  

TMDB_BEARER_TOKEN = (
    "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZGRmMGI3YTU0NmYwOGM2NTUzNzUyMTYyOGUxM"
    "GE0NiIsInN1YiI6IjVkOGIyYzkzN2E0OGFiMDAxMThjZGEzOSIsInNjb3BlcyI6WyJhcGl"
    "fcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.aXnZc4E546_TmdB_System_Bypass_Heavy_Token"
)
TMDB_API_KEY = "4ddf0b7a546f08c65537521628e11a46"

HEADERS = {
    "Authorization": f"Bearer {TMDB_BEARER_TOKEN}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Connection": "keep-alive"
}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# JUGAD FIXED: Special Accent characters (जैसे ó, á, é) को normal a-z में बदलने का फ़ंक्शन
def clean_accent_characters(text):
    normalized = unicodedata.normalize('NFD', text)
    clean_text = "".join([c for c in normalized if unicodedata.category(c) != 'Mn'])
    return clean_text

def find_mkv_link(title, is_series=False):
    clean_title = title.replace(":", "").replace("-", " ").replace("  ", " ").strip()
    slug = clean_title.replace(" ", "-").lower()
    return f"https://netmirror.center{slug}"

def save_to_db(clean_name, download_link, title_only, is_series=False):
    tag = "[Web Series]" if is_series else "[Dual Audio] HD"
    
    # Bot search filter ke liye name ko permanently pure clean standardized normal kar diya
    search_friendly_name = clean_accent_characters(title_only.strip())
    
    movie_data = {
        "file_name": search_friendly_name,              # Output: "El cronicon" (No Accent block now)
        "file_id": f"BAAMAgAD{int(time.time())}x90",   
        "file_size": 1073741824,                       
        "file_type": "video",
        "download_link": download_link,                
        "link": download_link,                         
        "caption": f"🎬 <b>Name :</b> <i>{clean_name} {tag}.mkv</i>\n🍿 <b>Auto-Generated via Global Index Server</b>\n\n📥 <b>Direct Link:</b> {download_link}",
        "timestamp": time.time()
    }
    collection.insert_one(movie_data)
    logging.info(f"✅ Successfully Saved Accent-Free Name: {search_friendly_name}")

def get_tmdb_data(url, query_params):
    query_params["api_key"] = TMDB_API_KEY
    for attempt in range(4):
        try:
            response = requests.get(url, headers=HEADERS, params=query_params, timeout=20)
            if response.status_code == 200:
                if response.text and response.text.strip() and not response.text.strip().startswith("<!DOCTYPE html>"):
                    try:
                        return response.json()
                    except ValueError:
                        pass
            elif response.status_code in:
                logging.warning(f"⚠️ TMDB server security cool-down (Code: {response.status_code}). Sleeping for 15s...")
                time.sleep(15)
                continue
            else:
                logging.error(f"🛑 TMDB HTTP error status: {response.status_code}")
        except Exception as e:
            logging.error(f"❌ Connection glitch on attempt {attempt + 1}: {e}")
        time.sleep(6)
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
                search_friendly_name = clean_accent_characters(title.strip())
                if collection.find_one({"file_name": search_friendly_name}):
                    continue
                    
                download_link = find_mkv_link(title, is_series=True)
                save_to_db(clean_name, download_link, title_only=title, is_series=True)
                time.sleep(2.5)

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
                search_friendly_name = clean_accent_characters(title.strip())
                if collection.find_one({"file_name": search_friendly_name}): 
                    continue
                    
                download_link = find_mkv_link(title, is_series=False)
                save_to_db(clean_name, download_link, title_only=title, is_series=False)
                time.sleep(2.5)

if __name__ == "__main__":
    while True:
        scrape_all_movies()
        scrape_all_web_series()
        logging.info("💤 Global loop cycle complete! 15 min rest...")
        time.sleep(900)
    
        
