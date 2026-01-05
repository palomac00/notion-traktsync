import csv
import requests
import os
import time

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
CSV_FILE = "paloma00-history-all.csv"

def add_item(row):
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # SOLO propiedades que SÍ existen
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Creator": {"rich_text": [{"text": {"content": "Trakt"}}]},
            "Date Finished": {"date": {"start": row['watched_at'][:10]}},
            "title": {"title": [{"text": {"content": row['title']}}]}  # title SÍ existe
        }
    }
    
    # Episode data SOLO si es episodio
    if row['type'] == 'episode':
        data["properties"]["Episode Format"] = {"rich_text": [{"text": {"content": f"S{row['season_number']}E{row['episode_number']}"}}]}
    
    try:
        r = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
        r.raise_for_status()
        print(f"✓ {row['title'][:40]}...")
        return True
    except Exception as e:
        print(f"✗ {str(e)[:80]}")
        return False

print("🚀 IMPORTANDO HISTORIAL...")
count = 0
with open(CSV_FILE) as f:
    reader = csv.DictReader(f)
    for row in reader:
        if add_item(row):
            count += 1
            time.sleep(0.3)
        if count % 10 == 0:
            print(f"Progreso: {count}")

print(f"✅ ¡LISTO! {count} items importados")
