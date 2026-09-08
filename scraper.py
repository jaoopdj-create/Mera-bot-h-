import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import time

# ⚠️ YAHAN APNE MAIN BOT KI DETAILS DALEIN
MONGO_URI = "YOUR_MONGODB_URI_HERE"        # Jo aapke main bot me use ho raha hai
DB_NAME = "YOUR_DATABASE_NAME"            # Aapke Database ka naam
COLLECTION_NAME = "YOUR_COLLECTION_NAME"  # Wo collection jahan aapka bot files dhoondta hai

WEBSITE_URL = "https://movies4u.vip"     # Movies4u ka active link

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def scrape_and_save():
    print("Movies4u website check ho rahi hai...")
    try:
        response = requests.get(WEBSITE_URL, headers={"User-Agent": "Mozilla/5.0"})
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
            
            # Check karein kya yeh movie pehle se database me hai?
            if collection.find_one({"title": title}):
                continue
            
            # Movie ke page ke andar se download link nikalna
            movie_page = requests.get(movie_url, headers={"User-Agent": "Mozilla/5.0"})
            movie_soup = BeautifulSoup(movie_page.text, 'html.parser')
            
            download_link = ""
            for a in movie_soup.find_all('a', href=True):
                if ".mkv" in a['href'] or "download" in a['href'].lower():
                    download_link = a['href']
                    break
            
            if download_link:
                # ⚠️ Dhayan dein: Aapke bot ke schema ke mutabik ye keys badal sakti hain
                movie_data = {
                    "title": title,
                    "file_link": download_link,
                    "file_type": "mkv",
                    "timestamp": time.time()
                }
                
                # Database me save karna
                collection.insert_one(movie_data)
                print(f"New Movie Added: {title}")
                
    except Exception as e:
        print(f"Error aaya: {e}")

# Har 15 minute me automatic check karega
while True:
    scrape_and_save()
    time.sleep(900)
  
