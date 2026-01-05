import csv
import requests
import os
from datetime import datetime
import time

# ===== CONFIGURATION =====
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
CSV_FILE = "paloma00-history-all.csv"  # Your file

def check_if_exists_in_notion(title):
    """Check if item already exists"""
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    filter_query = {
        "filter": {
            "property": "Title",
            "rich_text": {"contains": title}
        }
    }
    
    try:
        response = requests.post(
            f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query",
            headers=headers,
            json=filter_query
        )
        response.raise_for_status()
        return len(response.json()["results"]) > 0
    except:
        return False

def get_poster_url_from_csv(tmdb_id):
    """Get poster from TMDB ID in CSV"""
    if not tmdb_id or tmdb_id == "":
        return None
    return f"https://image.tmdb.org/t/p/w780/{tmdb_id}"

def add_to_notion(item_data, poster_url=None):
    """Add item to Notion (same as sync.py)"""
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    poster_prop = {"files": []}
    if poster_url:
        poster_prop["files"] = [{
            "name": f"{item_data['title']}.jpg",
            "external": {"url": poster_url}
        }]
    
    page_data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": item_data["title"]}}]},
            "Type": {"select": {"name": item_data["type"]}},
            "Date Watched": {"date": {"start": item_data["watched_at"]}},
            "Rating": {"select": {"name": item_data.get("rating", "Unrated")}},
            "Status": {"status": {"name": "Watching"}},
            "Cover": poster_prop
        }
    }
    
    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=page_data
        )
        response.raise_for_status()
        print(f"✓ Added: {item_data['title']} ({poster_url[:50]}...)")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def import_csv_history():
    """Import entire Trakt history from CSV"""
    print(f"\n{'='*60}")
    print(f"COMPLETE TRAKT HISTORY IMPORT")
    print(f"CSV: {CSV_FILE}")
    print(f"{'='*60}\n")
    
    added_count = 0
    skipped_count = 0
    
    with open(CSV_FILE, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for i, row in enumerate(reader, 1):
            try:
                # Determine type and title
                if row['type'] == 'movie':
                    title = row['title']
                    item_type = "Movie"
                    tmdb_id = row['tmdb_id']
                elif row['type'] == 'episode':
                    title = f"{row['title']} S{row['season_number']}E{row['episode_number']}"
                    item_type = "TV Show"
                    tmdb_id = row['tmdb_id']  # Show TMDB ID
                else:
                    continue
                
                # Skip if exists
                if check_if_exists_in_notion(title):
                    print(f"- [{i:4d}] Already exists: {title}")
                    skipped_count += 1
                    continue
                
                # Prepare data
                watched_at = row['watched_at'].split('T')[0]  # YYYY-MM-DD
                rating = float(row.get('trakt_rating', 0))
                rating_str = "★ " * int(rating) if rating > 0 else "Unrated"
                
                item_data = {
                    "title": title,
                    "type": item_type,
                    "watched_at": watched_at,
                    "rating": rating_str[:20]  # Truncate for select options
                }
                
                poster_url = get_poster_url_from_csv(tmdb_id)
                
                if add_to_notion(item_data, poster_url):
                    added_count += 1
                
                time.sleep(0.5)  # Rate limit
                if i % 50 == 0:
                    print(f"Progress: {i} processed ({added_count} added)")
                    
            except Exception as e:
                print(f"✗ Error row {i}: {e}")
                continue
    
    print(f"\n{'='*60}")
    print(f"IMPORT COMPLETE!")
    print(f"Added: {added_count} | Skipped: {skipped_count}")
    print(f"{'='*60}")

if __name__ == "__main__":
    import_csv_history()
