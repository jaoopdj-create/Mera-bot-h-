import os
import time
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

MONGO_URI = os.getenv("DATABASE_URI") or os.getenv("MONGO_URI") or "YOUR_MONGODB_URI_HERE"
DB_NAME = os.getenv("DATABASE_NAME") or "YOUR_DATABASE_NAME"
COLLECTION_NAME = "telegram_files"

# 🌐 होमपेज के बजाय हम सीधे Sitemap यूज़ करेंगे जहाँ डिज़ाइन बदलने का खतरा नहीं होता
SITEMAP_URL = "https://movies4u.kg"     
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def scrape_via_sitemap():
    logging.info("🎬 Movies4u Sitemap auto-check ho raha hai...")
    try:
        response = requests.get(SITEMAP_URL, headers=HEADERS, timeout=25)
        soup = BeautifulSoup(response.text, 'xml') # XML पार्सर क्योंकि सैटमैप XML होता है
        
        # सैटमैप के अंदर मौजूद सभी मूवी लिंक्स (<loc> टैग्स) को ढूंढना
        urls = [loc.text for loc in soup.find_all('loc')]
        logging.info(f"📊 Sitemap me kul {len(urls)} movies ke links mile.")
        
        # लेटेस्ट 15-20 मूवीज को ही चेक करेंगे ताकि सर्वर पर लोड न आये
        for movie_url in urls[:20]:
            try:
                # यूआरएल से मूवी का साफ़ नाम निकालना
                clean_title = movie_url.split('/')[-2].replace('-', ' ').title()
                
                # DB में डुप्लीकेट चेक
                if collection.find_one({"file_name": {"$regex": clean_title, "$options": "i"}}):
                    continue
                
                logging.info(f"🔍 New Movie Found! Opening page: {clean_title}")
                movie_page = requests.get(movie_url, headers=HEADERS, timeout=15)
                movie_soup = BeautifulSoup(movie_page.text, 'html.parser')
                
                download_link = ""
                for a in movie_soup.find_all('a', href=True):
                    href_str = a['href'].lower()
                    if ".mkv" in href_str or "download" in href_str or "hubcloud" in href_str or "fastdrive" in href_str:
                        download_link = a['href']
                        break
                
                if download_link:
                    movie_data = {
                        "file_name": f"{clean_title} [Movies4u].mkv",
                        "file_id": download_link,
                        "file_size": 1073741824,
                        "file_type": "video",
                        "caption": f"🎬 **{clean_title}**\n\n🍿 **Downloaded via Auto-Sitemap**",
                        "timestamp": time.time()
                    }
                    collection.insert_one(movie_data)
                    logging.info(f"✅ Successful Added to DB: {clean_title}")
                    
            except Exception as inner_e:
                logging.error(f"❌ Is link ko process karne me dikkat aayi: {movie_url} -> {inner_e}")
                
    except Exception as e:
        logging.error(f"❌ Sitemap open nahi ho paya: {e}")

if __name__ == "__main__":
    while True:
        scrape_via_sitemap()
        logging.info("💤 15 Minute ke liye scraper so raha hai...")
        time.sleep(900)
        
