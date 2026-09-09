import os
import time
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import logging
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

MONGO_URI = os.getenv("DATABASE_URI") or os.getenv("MONGO_URI") or "YOUR_MONGODB_URI_HERE"
DB_NAME = os.getenv("DATABASE_NAME") or "YOUR_DATABASE_NAME"
COLLECTION_NAME = "telegram_files"

# 🌐 वेगामूवीज की ऑफिशियल RSS Feed जो कभी ब्लॉक नहीं होती
FEED_URL = "http://vegamoviesz.xyz"     
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/xml,text/xml,*/*"
}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def scrape_vegamovies():
    logging.info("🎬 Vegamovies RSS Feed auto-check ho raha hai...")
    try:
        response = requests.get(FEED_URL, headers=HEADERS, timeout=25)
        soup = BeautifulSoup(response.text, 'xml') # XML पार्सर
        
        # फीड के अंदर मौजूद सभी लेटेस्ट मूवी पोस्ट्स (<item> टैग्स) को ढूंढना
        items = soup.find_all('item')
        logging.info(f"漏 Vegamovies Feed me kul {len(items)} movies mili hain.")
        
        for item in items:
            try:
                title = item.find('title').text.strip()
                movie_url = item.find('link').text.strip()
                
                # 🔍 आपके ऑटो-फिल्टर बॉट के स्कीमा के अनुसार डुप्लीकेट चेक (file_name)
                if collection.find_one({"file_name": {"$regex": re.escape(title), "$options": "i"}}):
                    continue
                
                logging.info(f"🔍 New Movie Found in Vegamovies! Opening: {title}")
                
                # मूवी के डाउनलोड पेज से .mkv / HubCloud लिंक्स निकालना
                movie_page = requests.get(movie_url, headers=HEADERS, timeout=15)
                movie_soup = BeautifulSoup(movie_page.text, 'html.parser')
                
                download_link = ""
                # वेगामूवीज के सभी डाउनलोड बटन्स या लिंक्स को खोजना
                for a in movie_soup.find_all('a', href=True):
                    href_str = a['href'].lower()
                    
                    # वेगामूवीज आमतौर पर vcloud, hubcloud, gdrive या v-link का इस्तेमाल करती है
                    if "hubcloud" in href_str or "vcloud" in href_str or "download" in href_str or ".mkv" in href_str or "v-link" in href_str:
                        download_link = a['href']
                        break
                
                if download_link:
                    # 🚀 आपके Advance Filter Bot (Peter / Pyrogram) के साथ 100% फिक्स स्कीमा
                    movie_data = {
                        "file_name": f"{title} [VegaMovies].mkv", # बॉट इसी नाम को सर्च में दिखाएगा
                        "file_id": download_link,                 # मुख्य डाउनलोड यूआरएल
                        "file_size": 1073741824,                   # डमी साइज (1 GB) जो टेलीग्राम पर शो होगा
                        "file_type": "video",
                        "caption": f"🎬 <b>Name :</b> <i>{title} [VegaMovies].mkv</i>\n🍿 <b>Auto-Scraped via Vegamovies Feed</b>",
                        "timestamp": time.time()
                    }
                    collection.insert_one(movie_data)
                    logging.info(f"✅ Successfully Added to DB: {title}")
                    
            except Exception as inner_e:
                logging.error(f"❌ Is movie ko process karne me dikkat aayi: {inner_e}")
                
    except Exception as e:
        logging.error(f"❌ Vegamovies Feed open nahi ho payi: {e}")

if __name__ == "__main__":
    while True:
        scrape_vegamovies()
        logging.info("💤 15 Minute ke liye scraper so raha hai...")
        time.sleep(900)
        
