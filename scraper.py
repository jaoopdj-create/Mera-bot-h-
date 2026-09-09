import os
import time
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import logging
import urllib.parse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

MONGO_URI = os.getenv("DATABASE_URI") or os.getenv("MONGO_URI") or "YOUR_MONGODB_URI_HERE"
DB_NAME = os.getenv("DATABASE_NAME") or "YOUR_DATABASE_NAME"
COLLECTION_NAME = "telegram_files"

# 🌐 डायरेक्ट साइट के बजाय हम Google index का उपयोग करेंगे जो कभी ब्लॉक नहीं हो सकता
TARGET_SITE = "movies4u.kg"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def scrape_via_google():
    logging.info("🎬 Google Search API ke jariye Movies4u check ho raha hai...")
    try:
        # गूगल पर साइट की लेटेस्ट पोस्ट्स सर्च करने की क्वेरी
        query = f"site:{TARGET_SITE}"
        google_url = f"https://duckduckgo.com{urllib.parse.quote(query)}"
        
        response = requests.get(google_url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # सर्च रिज़ल्ट्स से लिंक्स और टाइटल्स निकालना
        links = soup.find_all('a', class_='result__url')
        logging.info(f"📊 Search me kul {len(links)} movies mili hain.")
        
        for link_tag in links:
            try:
                movie_url = link_tag['href'].strip()
                # केवल मूवी पोस्ट के लिंक्स ही प्रोसेस करें
                if TARGET_SITE not in movie_url or "page" in movie_url:
                    continue
                    
                # साफ़ नाम (Title) जनरेट करें
                title = link_tag.text.replace(TARGET_SITE, "").replace("...", "").strip()
                if not title:
                    title = movie_url.split('/')[-2].replace('-', ' ').title()

                # DB में डुप्लीकेट चेक (file_name)
                if collection.find_one({"file_name": {"$regex": title, "$options": "i"}}):
                    continue
                
                logging.info(f"🔍 New Movie Found! Opening page: {title}")
                
                # मूवी पेज ओपन करके डाउनलोड लिंक निकालना
                movie_page = requests.get(movie_url, headers=HEADERS, timeout=15)
                movie_soup = BeautifulSoup(movie_page.text, 'html.parser')
                
                download_link = ""
                for a in movie_soup.find_all('a', href=True):
                    href_str = a['href'].lower()
                    if ".mkv" in href_str or "download" in href_str or "hubcloud" in href_str or "fastdrive" in href_str or "gdflix" in href_str:
                        download_link = a['href']
                        break
                
                if download_link:
                    # 🚀 आपके बॉट के स्कीमा के साथ फिक्स डेटा
                    movie_data = {
                        "file_name": f"{title} [Movies4u].mkv",
                        "file_id": download_link,
                        "file_size": 1073741824,
                        "file_type": "video",
                        "caption": f"🎬 <b>Name :</b> <i>{title} [Movies4u].mkv</i>\n🍿 <b>Auto-Scraped via Google Index</b>",
                        "timestamp": time.time()
                    }
                    collection.insert_one(movie_data)
                    logging.info(f"✅ Successfully Added to DB: {title}")
                    
            except Exception as inner_e:
                pass
                
    except Exception as e:
        logging.error(f"❌ Google Scraper me error aaya: {e}")

if __name__ == "__main__":
    while True:
        scrape_via_google()
        logging.info("💤 15 Minute ke liye scraper so raha hai...")
        time.sleep(900)
        
