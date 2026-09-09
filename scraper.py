import os
import time
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import logging

# ⚙️ Logging सेटअप ताकि रेंडर के Logs में सब दिखाई दे
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📥 ऑटो-डिटेक्ट सिस्टम: यह रेंडर या आपके बॉट की सेटिंग्स से डेटा अपने आप उठाएगा
# अगर आप मैन्युअली डालना चाहें, तो नीचे "" के अंदर अपनी डिटेल्स लिख सकते हैं
MONGO_URI = os.getenv("DATABASE_URI") or os.getenv("MONGO_URI") or "YOUR_MONGODB_URI_HERE"
DB_NAME = os.getenv("DATABASE_NAME") or "YOUR_DATABASE_NAME"
COLLECTION_NAME = "telegram_files"  # ऑटो-फिल्टर बॉट का डिफ़ॉल्ट कलेक्शन नाम

WEBSITE_URL =  "https://movies4u.kg"    # Movies4u का एक्टिव लिंक
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# डेटाबेस कनेक्शन चेक
if not MONGO_URI or "YOUR_MONGODB_URI_HERE" in MONGO_URI:
    logging.error("❌ DATABASE_URI या MONGO_URI नहीं मिला! कृपया रेंडर एनवायरनमेंट चेक करें या कोड में मैन्युअली भरें।")
    exit(1)

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def scrape_and_save():
    logging.info("🎬 Movies4u website check ho rahi hai...")
    try:
        response = requests.get(WEBSITE_URL, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        movies = soup.find_all('article') 
        
        for movie in movies:
            title_tag = movie.find('h2')
            if not title_tag:
                continue
                
            title = title_tag.text.strip()
            link_tag = movie.find('a')
            if not link_tag:
                continue
            movie_url = link_tag['href']
            
            # Check karein kya yeh movie pehle se database me hai? (Schema matched with Auto-Filter Bot)
            if collection.find_one({"file_name": {"$regex": title, "$options": "i"}}):
                logging.info(f"⏭️ Pehle se database me hai: {title}")
                continue
            
            # Movie ke page ke andar se download link nikalna
            logging.info(f"🔍 Opening movie page: {title}")
            movie_page = requests.get(movie_url, headers=HEADERS, timeout=15)
            movie_soup = BeautifulSoup(movie_page.text, 'html.parser')
            
            download_link = ""
            for a in movie_soup.find_all('a', href=True):
                href_str = a['href'].lower()
                if ".mkv" in href_str or "download" in href_str or "hubcloud" in href_str or "fastdrive" in href_str:
                    download_link = a['href']
                    break
            
            if download_link:
                # ✅ आपके ऑटो-फिल्टर बॉट के आर्किटेक्चर के हिसाब से 100% फिक्स डेटा स्ट्रक्चर
                movie_data = {
                    "file_name": f"{title} [Movies4u].mkv",  # बॉट इसी नाम को सर्च में पकड़ेगा
                    "file_id": download_link,               # डाउनलोड या हबक्लाउड का यूआरएल
                    "file_size": 1073741824,                 # डमी साइज (1 GB) जो टेलीग्राम पर शो होगा
                    "file_type": "video",
                    "caption": f"🎬 **{title}**\n\n🍿 **Downloaded via Auto-Scraper**",
                    "timestamp": time.time()
                }
                
                # Database me save karna
                collection.insert_one(movie_data)
                logging.info(f"✅ New Movie Added to DB: {title}")
                
    except Exception as e:
        logging.error(f"❌ Scraper me error aaya: {e}")

# Har 15 minute me automatic check karega
if __name__ == "__main__":
    while True:
        scrape_and_save()
        logging.info("💤 15 Minute ke liye scraper so raha hai...")
        time.sleep(900)
