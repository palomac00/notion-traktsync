import csv
import requests
import os
import json

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
CSV_FILE = "paloma00-history-all.csv"

print("🔍 DIAGNÓSTICO NOTION API...")

# 1. VERIFICAR DATABASE
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28"
}

print("📋 Database info...")
try:
    r = requests.get(f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}", headers=headers)
    print(f"Database OK: {r.status_code}")
    print("Properties:", json.dumps(r.json()["properties"], indent=2)[:500])
except Exception as e:
    print(f"❌ DATABASE ERROR: {e}")
    exit()

# 2. PROBAR 1 SOLO ITEM MÍNIMO
print("\n🧪 Test 1 item...")
with open(CSV_FILE) as f:
    reader = csv.DictReader(f)
    first_row = next(reader)
    
data = {
    "parent": {"database_id": NOTION_DATABASE_ID},
    "properties": {
        "title": {"title": [{"text": {"content": "TEST FRINGE"}}]},
        "type": {"select": {"name": "TV"}}
    }
}

try:
    r = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
    print(f"TEST RESULT: {r.status_code}")
    if r.status_code != 200:
        print("❌ ERROR DETALLE:", r.text)
    else:
        print("✅ Test OK! Properties funcionan")
except Exception as e:
    print(f"❌ TEST ERROR: {e}")
