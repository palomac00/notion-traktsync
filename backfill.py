import csv
import requests
import os
import time

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")  # Tu "All media" database
CSV_FILE = "paloma00-history-all.csv"

def add_to_all_media(row):
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Tipo: movie o TV episode
    item_type = "Movie" if row['type'] == 'movie' else "TV"
    
    # Poster TMDB
    tmdb_id = row['tmdb_id']
    poster_url = f"https://image.tmdb.org/t/p/w780/{tmdb_id}" if tmdb_id else None
    
    # Rating como estrellas
    rating = "⭐⭐⭐⭐⭐" if float(row.get('trakt_rating', 0)) >= 7 else "⭐⭐⭐"
    
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "title": {"title": [{"text": {"content": row['title']}}]},
            "type": {"select": {"name": item_type}},
            "status": {"status": {"name": "Watched"}},
            "rating": {"select": {"name": rating}},
            "date finished": {"date": {"start": row['watched_at'][:10]}},
            "genre": {"rich_text": [{"text": {"content": row.get('genres', 'Unknown')}}]},
            "poster": {"files": [{"name": f"{row['title']}.jpg", "external": {"url": poster_url}}]} if poster_url else {"files": []},
            "creator": {"rich_text": [{"text": {"content": "Trakt"}}]}
        }
    }
    
    try:
        r = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
        r.raise_for_status()
        print(f"✓ {row['title'][:40]}... ({item_type})")
        return True
    except Exception as e:
        print(f"✗ {str(e)[:80]}")
        return False

print("🚀 IMPORTANDO A 'All media'...")
count = 0
with open(CSV_FILE, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if add_to_all_media(row):
            count += 1
            time.sleep(0.3)  # Rate limit
        if count % 10 == 0:
            print(f"Progreso: {count}")

print(f"✅ ¡LISTO! {count} items en 'All media'")
