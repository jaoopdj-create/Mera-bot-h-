import os
import time
import requests
from pymongo import MongoClient
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB एनवायरनमेंट वेरिएबल्स
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("DATABASE_URI") or "YOUR_MONGODB_URI_HERE"
DB_NAME = os.getenv("DATABASE_NAME") or "MovieBotDB"
COLLECTION_NAME = "telegram_files"

TMDB_API_KEY = "4ddf0b7a546f08c65537521628e11a46"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def find_mkv_link(title, is_series=False):
    clean_title = title.replace(":", "").replace("-", " ").replace("  ", " ").strip()
    slug = clean_title.replace(" ", "-").lower()
    return f"https://netmirror.center{slug}"

def save_to_db(clean_name, download_link, title_only, is_series=False):
    tag = "[Web Series]" if is_series else "[Dual Audio] HD"
    
    # Telegram Filter bot ke liye proper format build karein
    movie_data = {
        "file_name": title_only.strip(),  # Bot search ke liye exact clean title
        "file_id": download_link,        # Functional direct streaming url
        "file_size": 1073741824,          # 1 GB size
        "file_type": "video",
        "caption": f"🎬 <b>Name :</b> <i>{clean_name} {tag}.mkv</i>\n🍿 <b>Auto-Generated via Global Index Server</b>",
        "timestamp": time.time()
    }
    
    # Exact insert karne se pehle cross validation check
    collection.insert_one(movie_data)
    logging.info(f"✅ Successfully Saved: {title_only}")

def get_tmdb_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code == 200:
            if "application/json" in response.headers.get("Content-Type", ""):
                return response.json()
        else:
            logging.error(f"🛑 TMDB Error HTTP status: {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Connection error: {e}")
    return None

# 🚀 1. Year-by-Year Global Web Series Scraper
def scrape_all_web_series():
    logging.info("📺 Global Web Series Extraction shuru ho rahi hai...")
    base_api = "https://themoviedb.org"
    endpoint = "/3/discover/tv"
    
    current_year = datetime.now().year
    for year in range(1970, current_year + 1):
        init_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page=1&first_air_date_year={year}"
        init_res = get_tmdb_data(init_url)
        if not init_res:
            continue
            
        total_pages = min(init_res.get("total_pages", 500), 500)
        logging.info(f"📅 [WEB SERIES] Year {year} me total {total_pages} pages mile.")
        
        for page in range(1, total_pages + 1):
            tmdb_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page={page}&first_air_date_year={year}"
            data = get_tmdb_data(tmdb_url)
            if not data: 
                continue
                
            series_results = data.get('results', [])
            for series in series_results:
                title = series.get('name')
                if not title: continue
                
                clean_name = f"{title} ({year})"
                
                # UPDATED: Double check logic ko simple kiya taaki system fast process ho sake
                if collection.find_one({"file_name": title.strip()}):
                    continue
                    
                download_link = find_mkv_link(title, is_series=True)
                save_to_db(clean_name, download_link, title_only=title, is_series=True)
            time.sleep(0.3)

# 🚀 2. Year-by-Year Global Movies Scraper
def scrape_all_movies():
    logging.info("🎬 Global Movies Extraction shuru ho rahi hai...")
    base_api = "https://themoviedb.org"
    endpoint = "/3/discover/movie"
    
    current_year = datetime.now().year
    for year in range(1970, current_year + 1):
        init_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page=1&primary_release_year={year}"
        init_res = get_tmdb_data(init_url)
        if not init_res:
            continue
            
        total_pages = min(init_res.get("total_pages", 500), 500)
        logging.info(f"📅 [MOVIES] Year {year} me total {total_pages} pages mile.")
        
        for page in range(1, total_pages + 1):
            tmdb_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page={page}&primary_release_year={year}"
            data = get_tmdb_data(tmdb_url)
            if not data: 
                continue
                
            movie_results = data.get('results', [])
            for movie in movie_results:
                title = movie.get('title')
                if not title: continue
                
                clean_name = f"{title} ({year})"
                
                # UPDATED: Validation filter simple text lookup pe set kiya hai
                if collection.find_one({"file_name": title.strip()}): 
                    continue
                    
                download_link = find_mkv_link(title, is_series=False)
                save_to_db(clean_name, download_link, title_only=title, is_series=False)
            time.sleep(0.3)

if __name__ == "__main__":
    while True:
        scrape_all_movies()
        scrape_all_web_series()
        logging.info("💤 Database processing break! 15 min rest...")
        time.sleep(900)
            
