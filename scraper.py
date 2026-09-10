import os
import time
import requests
from pymongo import MongoClient
import logging
from datetime import datetime
import unicodedata

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB एनवायरनमेंट वेरिएबल्स Setup
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("DATABASE_URI") or "YOUR_MONGODB_URI_HERE"
DB_NAME = os.getenv("DATABASE_NAME") or "MovieBotDB_New"          
COLLECTION_NAME = "telegram_files"  

TMDB_API_KEY = "4ddf0b7a546f08c65537521628e11a46"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Special Accent characters को normal a-z में बदलने का फ़ंक्शन
def clean_accent_characters(text):
    if not text:
        return ""
    normalized = unicodedata.normalize('NFD', text)
    clean_text = "".join([c for c in normalized if unicodedata.category(c) != 'Mn'])
    return clean_text

# ओपन-सोर्स वीडियो इंडेक्स सर्वर से डायरेक्ट .mkv लिंक (PERFECT SLASH)
def find_mkv_link(title):
    clean_title = title.replace(":", "").replace("-", " ").replace("  ", " ").strip()
    slug = clean_title.replace(" ", "-").lower()
    return f"https://netmirror.center{slug}"

# डेटाबेस में परफेक्ट क्लीन नाम से सेव करने का फंक्शन
def save_to_db(clean_name, download_link, title_only, is_series=False):
    tag = "[Web Series]" if is_series else "[Dual Audio] HD"
    
    # नाम के आगे-पीछे से सारे extra quotes (" या ') हटाकर clean करना
    clean_title_only = title_only.strip().strip('"').strip("'").strip()
    search_friendly_name = clean_accent_characters(clean_title_only)
    
    # Display name को भी साफ़ सुथरा बनाना
    clean_display_name = clean_name.strip().strip('"').strip("'").strip()
    
    movie_data = {
        "file_name": search_friendly_name,              
        "file_id": f"BAAMAgAD{int(time.time())}x90",   
        "file_size": 1073741824,                       
        "file_type": "video",
        "download_link": download_link,                
        "link": download_link,                         
        "caption": f"🎬 <b>Name :</b> <i>{clean_display_name} {tag}.mkv</i>\n🍿 <b>Auto-Generated via Global Index Server</b>\n\n📥 <b>Direct Link:</b> {download_link}",
        "timestamp": time.time()
    }
    collection.insert_one(movie_data)
    logging.info(f"✅ Saved Clean Name (Ready for Bot): {search_friendly_name}")

# 🚀 1. Year 2000 se 2026 tak ki SAARI Web Series (All Languages) lane ka function
def scrape_all_web_series():
    logging.info("📺 Year 2000 se 2026 ki All Languages Web Series Extraction shuru...")
    base_url = "https://themoviedb.org"
    
    for year in range(2000, 2027):
        logging.info(f"📅 [ALL WEB SERIES] Year {year} ka data fetch ho raha hai...")
        
        # हर साल के टॉप 50 पेजेस (लगभग 1000 सीरीज़ प्रति वर्ष - बॉलीवुड, हॉलीवुड, सब शामिल)
        for page in range(1, 51):
            tmdb_url = f"{base_url}?api_key={TMDB_API_KEY}&page={page}&first_air_date_year={year}"
            
            try:
                response = requests.get(tmdb_url, headers=HEADERS, timeout=20)
                if response.status_code != 200:
                    break
                    
                series_results = response.json().get('results', [])
                if not series_results:
                    break
                    
                for series in series_results:
                    title = series.get('name')
                    if not title: 
                        continue
                    
                    search_friendly_name = clean_accent_characters(title.strip().strip('"').strip("'").strip())
                    
                    if collection.find_one({"file_name": search_friendly_name}):
                        continue
                        
                    clean_name = f"{title} ({year})"
                    download_link = find_mkv_link(title)
                    
                    save_to_db(clean_name, download_link, title_only=title, is_series=True)
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"❌ Series Year {year} Page {page} error: {e}")
                time.sleep(2)

# 🚀 2. Year 2000 se 2026 tak ki SAARI Movies (All Languages) lane ka function
def scrape_all_movies():
    logging.info("🎬 Year 2000 se 2026 ki All Languages Movies Extraction shuru...")
    base_url = "https://themoviedb.org"
    
    for year in range(2000, 2027):
        logging.info(f"📅 [ALL MOVIES] Year {year} ka data fetch ho raha hai...")
        
        # हर साल के टॉप 50 पेजेस (लगभग 1000 सुपरहिट मूवीज प्रति वर्ष - बॉलीवुड, हॉलीवुड, सब शामिल)
        for page in range(1, 51):
            tmdb_url = f"{base_url}?api_key={TMDB_API_KEY}&page={page}&primary_release_year={year}"
            
            try:
                response = requests.get(tmdb_url, headers=HEADERS, timeout=20)
                if response.status_code != 200:
                    break
                    
                movie_results = response.json().get('results', [])
                if not movie_results:
                    break
                    
                for movie in movie_results:
                    title = movie.get('title')
                    if not title: 
                        continue
                    
                    search_friendly_name = clean_accent_characters(title.strip().strip('"').strip("'").strip())
                    
                    if collection.find_one({"file_name": search_friendly_name}): 
                        continue
                        
                    clean_name = f"{title} ({year})"
                    download_link = find_mkv_link(title)
                    
                    save_to_db(clean_name, download_link, title_only=title, is_series=False)
                    time.sleep(1)
            except Exception as e:
                logging.error(f"❌ Movie Year {year} Page {page} error: {e}")
                time.sleep(2)

if __name__ == "__main__":
    while True:
        scrape_all_movies()
        scrape_all_web_series()
        logging.info("💤 All Languages loop complete. Scraper 15 minute rest pe hai...")
        time.sleep(900)
        
