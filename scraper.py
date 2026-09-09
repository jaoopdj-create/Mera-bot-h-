import os
import time
import requests
from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

MONGO_URI = os.getenv("DATABASE_URI") or os.getenv("MONGO_URI") or "YOUR_MONGODB_URI_HERE"
DB_NAME = os.getenv("DATABASE_NAME") or "YOUR_DATABASE_NAME"
COLLECTION_NAME = "telegram_files"

# 🌐 TMDB की ऑफिशियल फ्री API की (यह कभी ब्लॉक नहीं होती)
TMDB_API_KEY = "a8c9b32a74c431cb0272b1124adfb8a4" 

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def get_latest_movies_and_links():
    logging.info("🎬 TMDB API aur Google Index ke jariye movies check ho rahi hain...")
    try:
        # 1. TMDB से इस समय की सबसे ट्रेंडिंग और नई मूवीज की लिस्ट लाना
        tmdb_url = f"https://themoviedb.org{TMDB_API_KEY}"
        response = requests.get(tmdb_url, timeout=20)
        
        if response.status_code != 200:
            logging.warning("⚠️ TMDB API se connect nahi ho paya.")
            return
            
        movie_results = response.json().get('results', [])
        logging.info(f"📊 TMDB se kul {len(movie_results)} trending movies mili hain.")
        
        for movie in movie_results:
            title = movie.get('title')
            release_date = movie.get('release_date', '')
            year = release_date.split('-')[0] if release_date else ""
            clean_name = f"{title} {year}".strip()
            
            # 🔍 MongoDB डुप्लीकेट चेक (file_name)
            if collection.find_one({"file_name": {"$regex": title, "$options": "i"}}):
                continue
                
            logging.info(f"🔍 New Movie Found! Finding .mkv link for: {clean_name}")
            
            # 2. गूगल ओपन इंडेक्स सर्वर्स से इस मूवी का डायरेक्ट .mkv लिंक ढूँढना (बिना किसी वेबसाइट पर जाए)
            search_query = f'intitle:"index.of" mkv "{title}"'
            google_url = f"https://duckduckgo.com{requests.utils.quote(search_query)}"
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            search_res = requests.get(google_url, headers=headers, timeout=15)
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(search_res.text, 'html.parser')
            
            download_link = ""
            # सर्च रिजल्ट्स में से डायरेक्ट डाउनलोड सर्वर्स (.mkv वाले) निकालना
            for a in soup.find_all('a', href=True):
                href_str = a['href'].lower()
                if ".mkv" in href_str and "http" in href_str and "google" not in href_str:
                    download_link = a['href']
                    break
            
            # अगर डायरेक्ट लिंक मिल जाए, तो आपके ऑटो-फिल्टर बॉट के स्कीमा में सेव करें
            if download_link:
                movie_data = {
                    "file_name": f"{clean_name} [Dual Audio] HD.mkv",
                    "file_id": download_link,
                    "file_size": 1073741824, # 1 GB डमी साइज
                    "file_type": "video",
                    "caption": f"🎬 <b>Name :</b> <i>{clean_name} HD.mkv</i>\n🍿 <b>Auto-Generated via Global Index Server</b>",
                    "timestamp": time.time()
                }
                collection.insert_one(movie_data)
                logging.info(f"✅ Successfully Saved in Database: {clean_name}")
                
            time.sleep(2) # गूगल ब्लॉक से बचने के लिए छोटा गैप
            
    except Exception as e:
        logging.error(f"❌ Core Search System Error: {e}")

if __name__ == "__main__":
    while True:
        get_latest_movies_and_links()
        logging.info("💤 Scraper 15 minute ke liye rest pe hai...")
        time.sleep(900)
        
