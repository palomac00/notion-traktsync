import csv
import requests
import os
import time

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
CSV_FILE = "paloma00-history-all.csv"

def add_item(title, date):
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json", 
        "Notion-Version": "2022-06-28"
    }
    
    # SOLO Title + Date = NUNCA falla
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": title[:100] }}]
            },
            "Date": {
                "date": {"start": date}
            }
        }
    }
    
    try:
        r = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
        r.raise_for_status()
        print(f"✓ {title[:40]}...")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)[:100]}")
        return False

print("🚀 IMPORTANDO HISTORIAL TRAKT...")
count = 0
with open(CSV_FILE) as f:
    reader = csv.DictReader(f)
    for row in reader:
        title = row['title']
        date = row['watched_at'][:10]  # Solo YYYY-MM-DD
        
        if add_item(title, date):
            count += 1
            time.sleep(0.2)
        
        if count % 20 == 0:
            print(f"Progreso: {count}")

print(f"✅ TERMINÓ! {count} items agregados")
