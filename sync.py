import requests
import os
from datetime import datetime
import time

# ===== CONFIGURATION (desde GitHub Secrets) =====
TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
TRAKT_ACCESS_TOKEN = os.getenv("TRAKT_ACCESS_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# ===== TRAKT API =====
def get_trakt_history(limit=50):
    """Fetch watch history from Trakt"""
    headers = {
        "Authorization": f"Bearer {TRAKT_ACCESS_TOKEN}",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_CLIENT_ID,
        "Content-Type": "application/json"
    }
    
    url = f"https://api.trakt.tv/users/me/history?limit={limit}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Trakt history: {e}")
        return []

def get_poster_url(entry):
    """Fetch poster URL from Trakt TMDB ID"""
    try:
        if "movie" in entry:
            tmdb_id = entry["movie"].get("ids", {}).get("tmdb")
        elif "show" in entry:
            tmdb_id = entry["show"].get("ids", {}).get("tmdb")
        else:
            return None
        
        if tmdb_id:
            return f"https://image.tmdb.org/t/p/w780/{tmdb_id}"
        return None
    except:
        return None

# ===== NOTION API =====
def check_if_exists_in_notion(title):
    """Check if item already exists in Notion database"""
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    filter_query = {
        "filter": {
            "property": "Title",
            "rich_text": {
                "contains": title
            }
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
    except requests.exceptions.RequestException as e:
        print(f"Error checking Notion: {e}")
        return False

def add_to_notion(item_data, poster_url=None):
    """Add item to Notion database with poster"""
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Build Poster property
    poster_prop = {"files": []}
    if poster_url:
        poster_prop["files"] = [{
            "name": f"{item_data['title']}.jpg",
            "external": {"url": poster_url}
        }]
    
    page_data = {
        "parent": {
            "database_id": NOTION_DATABASE_ID
        },
        "properties": {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": item_data["title"]
                        }
                    }
                ]
            },
            "Type": {
                "select": {
                    "name": item_data["type"]
                }
            },
            "Date Watched": {
                "date": {
                    "start": item_data["watched_at"]
                }
            },
            "Rating": {
                "select": {
                    "name": item_data.get("rating", "Unrated")
                }
            },
            "Status": {
                "status": {
                    "name": "Watching"
                }
            },
            "Poster": poster_prop
        }
    }
    
    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=page_data
        )
        response.raise_for_status()
        print(f"✓ Added to Notion: {item_data['title']}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Error adding to Notion: {e}")
        print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return False

# ===== MAIN SYNC FUNCTION =====
def sync_trakt_to_notion():
    """Main function to sync Trakt history to Notion"""
    print(f"\n{'='*50}")
    print(f"Starting Trakt to Notion Sync")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    print("Fetching Trakt history...")
    history = get_trakt_history(limit=20)
    
    if not history:
        print("No items found in Trakt history")
        return
    
    added_count = 0
    skipped_count = 0
    
    for entry in history:
        try:
            if "movie" in entry:
                item = entry["movie"]
                item_type = "Movie"
                title = item["title"]
            elif "show" in entry:
                item = entry["show"]
                item_type = "TV Show"
                title = item["title"]
            else:
                continue
            
            if check_if_exists_in_notion(title):
                print(f"- Already exists: {title}")
                skipped_count += 1
                continue
            
            watched_at = entry.get("watched_at", datetime.now().isoformat()).split("T")[0]
            rating = item.get("rating")
            
            # Convert rating to star format if numeric
            if isinstance(rating, (int, float)) and rating > 0:
                rating_str = "★ " * int(rating)
            else:
                rating_str = "Unrated"
            
            item_data = {
                "title": title,
                "type": item_type,
                "watched_at": watched_at,
                "rating": rating_str
            }
            
            poster_url = get_poster_url(entry)
            if add_to_notion(item_data, poster_url):
                added_count += 1
            
            time.sleep(0.3)  # Rate limiting
        except Exception as e:
            print(f"Error processing entry: {e}")
            continue
    
    print(f"\n{'='*50}")
    print(f"Sync Complete!")
    print(f"Added: {added_count} | Already existed: {skipped_count}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    sync_trakt_to_notion()
