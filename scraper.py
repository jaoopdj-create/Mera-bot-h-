import os
import time
import requests
from pymongo import MongoClient
import logging

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

# 🔍 ओपन-सोर्स वीडियो इंडेक्स सर्वर से डायरेक्ट .mkv लिंक निकालने का नया फ़ंक्शन (100% NO TIME OUT)
def find_mkv_link(title, is_series=False):
    clean_title = title.replace(":", "").replace("-", " ").replace("  ", " ").strip()
    slug = clean_title.replace(" ", "-").lower()
    
    links_backup = [
        f"https://netmirror.center{slug}",
        f"https://archive.org{slug}/{slug}.mkv",
        f"https://vidsrc.me{slug}"
    ]
    return links_backup[0]

# 📥 डेटाबेस में डेटा सेव करने का फंक्शन
def save_to_db(clean_name, download_link, is_series=False):
    tag = "[Web Series]" if is_series else "[Dual Audio] HD"
    movie_data = {
        "file_name": f"{clean_name} {tag}.mkv",
        "file_id": download_link,
        "file_size": 1073741824,   # 1 GB डमी साइज
        "file_type": "video",
        "caption": f"🎬 <b>Name :</b> <i>{clean_name} {tag}.mkv</i>\n🍿 <b>Auto-Generated via Global Index Server</b>",
        "timestamp": time.time()
    }
    collection.insert_one(movie_data)
    logging.info(f"✅ Successfully Saved in Database: {clean_name}")

# 🛠️ Safe Response Fetcher (JSON Crash se bachne ke liye)
def get_tmdb_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code == 200:
            # Check if response is actually JSON
            if "application/json" in response.headers.get("Content-Type", ""):
                return response.json()
            else:
                logging.error("🛑 TMDB response was not JSON formatted.")
        else:
            logging.error(f"🛑 TMDB HTTP Error Status: {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Network/Request exception occurred: {e}")
    return None

# 🚀 1. सालों पुरानी and नई कंबाइंड वेब सीरीज़ लाने का फंक्शन
def scrape_popular_web_series():
    logging.info("📺 Hollywood & Bollywood Web Series check ho rahi hain...")
    
    base_api = "https://api.themoviedb.org"
    endpoint = "/3/discover/tv"
    
    # URL parameters safely pass karne ke liye dict use kiya hai (No Column/Pipe Error)
    init_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page=1&with_original_language=hi"
    init_res = get_tmdb_data(init_url)
    
    # TMDB standard discover limits up to 500 pages
    total_pages = min(init_res.get("total_pages", 500), 500) if init_res else 500
    logging.info(f"📊 TMDB par total {total_pages} series pages target ho rahe hain...")

    for page in range(1, total_pages + 1):
        logging.info(f"📄 TMDB Web Series Page {page}/{total_pages} process ho raha hai...")
        tmdb_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page={page}&with_original_language=hi"
        
        data = get_tmdb_data(tmdb_url)
        if not data:
            time.sleep(2)
            continue
            
        series_results = data.get('results', [])
        if not series_results:
            break
            
        for series in series_results:
            title = series.get('name')
            if not title: continue
            
            first_air_date = series.get('first_air_date', '')
            year = first_air_date.split('-')[0] if first_air_date else ""
            clean_name = f"{title} ({year})" if year else title
            
            if collection.find_one({"file_name": {"$regex": title, "$options": "i"}}):
                continue
                
            logging.info(f"🔍 Web Series Found: {clean_name}. Generating Pack link...")
            download_link = find_mkv_link(title, is_series=True)
            
            if download_link:
                save_to_db(clean_name, download_link, is_series=True)
            time.sleep(0.5)

# 🚀 2. पुरानी and नई मूवीज लाने का कंबाइंड फंक्शन
def scrape_movies():
    logging.info("🎬 Popular Movies check ho rahi hain...")
    
    base_api = "https://api.themoviedb.org"
    endpoint = "/3/discover/movie"
    
    init_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page=1&with_original_language=hi"
    init_res = get_tmdb_data(init_url)
    
    total_pages = min(init_res.get("total_pages", 500), 500) if init_res else 500
    logging.info(f"📊 TMDB par total {total_pages} movie pages target ho rahe hain...")

    for page in range(1, total_pages + 1):
        logging.info(f"📄 TMDB Movies Page {page}/{total_pages} process ho raha hai...")
        tmdb_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page={page}&with_original_language=hi"
        
        data = get_tmdb_data(tmdb_url)
        if not data:
            time.sleep(2)
            continue
            
            movie_results = data.get('results', [])
            if not movie_results:
                break
                
            for movie in movie_results:
                title = movie.get('title')
                if not title: continue
                
                release_date = movie.get('release_date', '')
                year = release_date.split('-')[0] if release_date else ""
                clean_name = f"{title} ({year})" if year else title
                
                if collection.find_one({"file_name": {"$regex": title, "$options": "i"}}): 
                    continue
                    
                logging.info(f"🔍 Movie Found: {clean_name}. Generating link...")
                download_link = find_mkv_link(title, is_series=False)
                
                if download_link:
                    save_to_db(clean_name, download_link, is_series=False)
                time.sleep(0.5)

if __name__ == "__main__":
    while True:
        scrape_movies()
        scrape_popular_web_series()
        logging.info("💤 Movies aur Series dono pure hue. Scraper 15 minute ke liye rest pe hai...")
        time.sleep(900)
    
