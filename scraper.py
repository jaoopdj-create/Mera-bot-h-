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

# 🔍 डायरेक्ट स्ट्रीमिंग लिंक जनरेटर
def find_mkv_link(title, is_series=False):
    clean_title = title.replace(":", "").replace("-", " ").replace("  ", " ").strip()
    slug = clean_title.replace(" ", "-").lower()
    return f"https://netmirror.center{slug}"

# 📥 डेटाबेस में डेटा सेव करने का फंक्शन
def save_to_db(clean_name, download_link, title_only, is_series=False):
    tag = "[Web Series]" if is_series else "[Dual Audio] HD"
    
    movie_data = {
        "file_name": title_only.strip(),  # Bot search clear system matching
        "file_id": download_link,        # Direct functional netmirror URL
        "file_size": 1073741824,          # 1 GB standard dummy size
        "file_type": "video",
        "caption": f"🎬 <b>Name :</b> <i>{clean_name} {tag}.mkv</i>\n🍿 <b>Auto-Generated via Global Index Server</b>",
        "timestamp": time.time()
    }
    
    collection.insert_one(movie_data)
    logging.info(f"✅ Successfully Saved: {title_only}")

# 🛠️ Safe Response Fetcher (404 and Format Handling Fix)
def get_tmdb_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code == 200:
            if "application/json" in response.headers.get("Content-Type", ""):
                return response.json()
        elif response.status_code == 404:
            # 404 ko break karne ke bajaye skip mode me logs handle karega
            logging.warning(f"⚠️ Endpoint not found (404) for this filter. Skipping gracefully...")
        else:
            logging.error(f"🛑 TMDB Error HTTP status: {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Network request exception occurred: {e}")
    return None

# 🚀 1. Year-by-Year Unlimited Global Web Series Scraper
def scrape_all_web_series():
    logging.info("📺 Global Web Series Year-by-Year extraction shuru...")
    base_api = "https://api.themoviedb.org"
    endpoint = "/3/discover/tv"
    
    current_year = datetime.now().year
    # 1970 se lekar current saal tak sabhi blocks fetch honge
    for year in range(1970, current_year + 1):
        init_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page=1&first_air_date_year={year}"
        init_res = get_tmdb_data(init_url)
        
        # 404 fail check protection fix
        if not init_res or 'total_pages' not in init_res:
            continue
            
        total_pages = min(init_res.get("total_pages", 500), 500)
        logging.info(f"📅 [WEB SERIES] Year {year} me total {total_pages} pages loop target ho rahe hain.")
        
        for page in range(1, total_pages + 1):
            tmdb_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page={page}&first_air_date_year={year}"
            data = get_tmdb_data(tmdb_url)
            if not data or 'results' not in data: 
                continue
                
            series_results = data.get('results', [])
            for series in series_results:
                title = series.get('name')
                if not title: continue
                
                clean_name = f"{title} ({year})"
                
                # Simple exact collection matching bypass check
                if collection.find_one({"file_name": title.strip()}):
                    continue
                    
                download_link = find_mkv_link(title, is_series=True)
                save_to_db(clean_name, download_link, title_only=title, is_series=True)
            time.sleep(0.3)

# 🚀 2. Year-by-Year Unlimited Global Movies Scraper
def scrape_all_movies():
    logging.info("🎬 Global Movies Year-by-Year extraction shuru...")
    base_api = "https://api.themoviedb.org"
    endpoint = "/3/discover/movie"
    
    current_year = datetime.now().year
    for year in range(1970, current_year + 1):
        init_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page=1&primary_release_year={year}"
        init_res = get_tmdb_data(init_url)
        
        # 404 fail check protection fix
        if not init_res or 'total_pages' not in init_res:
            continue
            
        total_pages = min(init_res.get("total_pages", 500), 500)
        logging.info(f"📅 [MOVIES] Year {year} me total {total_pages} pages loop target ho rahe hain.")
        
        for page in range(1, total_pages + 1):
            tmdb_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page={page}&primary_release_year={year}"
            data = get_tmdb_data(tmdb_url)
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
            time.sleep(0.3)

if __name__ == "__main__":
    while True:
        scrape_all_movies()
        scrape_all_web_series()
        logging.info("💤 Global structural loop cycle complete! 15 min rest...")
        time.sleep(900)
                
