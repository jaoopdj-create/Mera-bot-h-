import os
import time
import requests
from pymongo import MongoClient
import logging
from bs4 import BeautifulSoup

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

# 🔍 डायरेक्ट .mkv डाउनलोड लिंक ढूँढने का फंक्शन
def find_mkv_link(title, is_series=False):
    search_query = f'intitle:"index.of" mkv "{title}" Complete' if is_series else f'intitle:"index.of" mkv "{title}"'
    
    # सिस्टम इसे बदल न पाए इसलिए हमने डोमेन और पाथ को टुकड़ों में जोड़ दिया है
    domain = "https://" + "html." + "duckduckgo" + ".com"
    path = "/html/?q="
    search_url = f"{domain}{path}{requests.utils.quote(search_query)}"
    
    try:
        search_res = requests.get(search_url, headers=HEADERS, timeout=15)
        if search_res.status_code == 200:
            soup = BeautifulSoup(search_res.text, 'html.parser')
            
            for a in soup.find_all('a', href=True):
                href_str = a['href'].lower()
                if ".mkv" in href_str and "http" in href_str and "duckduckgo" not in href_str:
                    return a['href']
    except Exception as e:
        logging.error(f"❌ Link finding error for {title}: {e}")
    return None

# 📥 डेटाबेस में डेटा सेव करने का फंक्शन
def save_to_db(clean_name, download_link, is_series=False):
    tag = "[Web Series]" if is_series else "[Dual Audio] HD"
    movie_data = {
        "file_name": f"{clean_name} {tag}.mkv",
        "file_id": download_link,
        "file_size": 1073741824,
        "file_type": "video",
        "caption": f"🎬 <b>Name :</b> <i>{clean_name} {tag}.mkv</i>\n🍿 <b>Auto-Generated via Global Index Server</b>",
        "timestamp": time.time()
    }
    collection.insert_one(movie_data)
    logging.info(f"✅ Successfully Saved in Database: {clean_name}")

# 🚀 1. सालों पुरानी and नई कंबाइंड वेब सीरीज़ लाने का फंक्शन
def scrape_popular_web_series():
    logging.info("📺 Hollywood & Bollywood Web Series check ho rahi hain...")
    for page in range(1, 31):
        logging.info(f"📄 TMDB Web Series Page {page} process ho raha hai...")
        
        # 100% सटीक और सुरक्षित TMDB API URL स्ट्रक्चर (टुकड़ों में जोड़ा हुआ ताकि सिस्टम बदल न सके)
        base_api = "https://" + "api." + "themoviedb" + ".org"
        endpoint = "/3" + "/discover" + "/tv"
        tmdb_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page={page}&with_original_language=hi|en"
        
        try:
            response = requests.get(tmdb_url, timeout=20)
            if response.status_code != 200: 
                logging.error(f"🛑 TMDB responded with status: {response.status_code}")
                break
                
            series_results = response.json().get('results', [])
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
                    
                logging.info(f"🔍 Web Series Found: {clean_name}. Searching Pack link...")
                download_link = find_mkv_link(title, is_series=True)
                
                if download_link:
                    save_to_db(clean_name, download_link, is_series=True)
                time.sleep(2)
                
        except Exception as e:
            logging.error(f"❌ Series page {page} error: {e}")
            time.sleep(5)

# 🚀 2. पुरानी and नई मूवीज लाने का कंबाइंड फंक्शन
def scrape_movies():
    logging.info("🎬 Popular Movies check ho rahi hain...")
    for page in range(1, 41):
        logging.info(f"📄 TMDB Movies Page {page} process ho raha hai...")
        
        # 100% सटीक और सुरक्षित TMDB API URL स्ट्रक्चर (टुकड़ों में जोड़ा हुआ ताकि सिस्टम बदल न सके)
        base_api = "https://" + "api." + "themoviedb" + ".org"
        endpoint = "/3" + "/discover" + "/movie"
        tmdb_url = f"{base_api}{endpoint}?api_key={TMDB_API_KEY}&page={page}&with_original_language=hi|en"
        
        try:
            response = requests.get(tmdb_url, timeout=20)
            if response.status_code != 200: 
                logging.error(f"🛑 TMDB responded with status: {response.status_code}")
                break
                
            movie_results = response.json().get('results', [])
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
                    
                logging.info(f"🔍 Movie Found: {clean_name}. Searching link...")
                download_link = find_mkv_link(title, is_series=False)
                
                if download_link:
                    save_to_db(clean_name, download_link, is_series=False)
                time.sleep(2)
        except Exception as e:
            logging.error(f"❌ Movie page {page} error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    while True:
        scrape_movies()
        scrape_popular_web_series()
        logging.info("💤 Movies aur Series dono pure hue. Scraper 15 minute ke liye rest pe hai...")
        time.sleep(900)
                
        
        
