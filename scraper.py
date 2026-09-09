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

# 🌐 वेगामूवीज की एक्टिव मिरर साइट
TARGET_URL = "https://vegamovies.ngo"

# 🔑 फ्री स्क्रैपर API की (यह बिना ब्लॉक हुए क्लाउडफ्लेयर को तोड़ देगी)
# आप scraperapi.com पर जाकर 5 सेकंड में अपनी फ्री की (Key) भी जनरेट कर सकते हैं
SCRAPER_API_KEY = "5a7f920875e53bc3a2d201124adfb8a4" 

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def get_protected_html(url):
    # यह फंक्शन रिक्वेस्ट को प्रॉक्सी सर्वर के जरिए घुमाकर भेजेगा ताकि ब्लॉक न हो
    proxy_url = f"http://scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    try:
        response = requests.get(proxy_url, timeout=30)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logging.error(f"❌ Proxy Request Failed for {url}: {e}")
    return None

def scrape_vegamovies_bypass():
    logging.info("🚀 Cloudflare Security Bypass mode me Vegamovies check ho raha hai...")
    
    html_content = get_protected_html(TARGET_URL)
    if not html_content:
        logging.warning("⚠️ वेबसाइट से कोई डेटा नहीं मिला। अगले राउंड में प्रयास करेंगे।")
        return
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # वेगामूवीज के पोस्ट्स/आर्टिकल्स के डिब्बे ढूँढना
    articles = soup.find_all(['article', 'div'], class_=['post', 'blog-post', 'post-column', 'content-area'])
    
    if not articles:
        articles = soup.find_all('h2')

    logging.info(f"📊 Proxy bypass ke sath kul {len(articles)} movies mili hain!")
    
    for art in articles[:10]: # सर्वर लोड से बचने के लिए टॉप 10 लेटेस्ट मूवीज
        try:
            a_tag = art.find('a', href=True)
            if not a_tag:
                continue
                
            title = a_tag.text.strip() if a_tag.text else a_tag.get('title', '').strip()
            movie_url = a_tag['href']
            
            if not title or "page" in movie_url:
                continue
            
            # 🔍 MongoDB डुप्लीकेट चेक (file_name)
            if collection.find_one({"file_name": {"$regex": re.escape(title), "$options": "i"}}):
                continue
            
            logging.info(f"🔍 New Movie Detected! Fetching Download Page: {title}")
            
            # मूवी के अंदरूनी पेज का कंटेंट भी प्रॉक्सी से लाएं
            inner_html = get_protected_html(movie_url)
            if not inner_html:
                continue
                
            movie_soup = BeautifulSoup(inner_html, 'html.parser')
            
            download_link = ""
            for a in movie_soup.find_all('a', href=True):
                href_str = a['href'].lower()
                if any(x in href_str for x in ["hubcloud", "vcloud", "download", ".mkv", "v-link", "fastdrive"]):
                    download_link = a['href']
                    break
            
            if download_link:
                # 🚀 आपके एडवांस ऑटो-फिल्टर बॉट का परफेक्ट स्कीमा
                movie_data = {
                    "file_name": f"{title} [VegaMovies].mkv",
                    "file_id": download_link,
                    "file_size": 1073741824, # 1 GB डमी साइज
                    "file_type": "video",
                    "caption": f"🎬 <b>Name :</b> <i>{title} [VegaMovies].mkv</i>\n🍿 <b>Auto-Scraped via Cloudflare Bypass</b>",
                    "timestamp": time.time()
                }
                collection.insert_one(movie_data)
                logging.info(f"✅ Successfully Saved in MongoDB: {title}")
                
        except Exception as inner_e:
            logging.error(f"Error processing inner movie: {inner_e}")

if __name__ == "__main__":
    while True:
        scrape_vegamovies_bypass()
        logging.info("💤 Scraper 15 minute ke liye rest pe hai...")
        time.sleep(900)
        
