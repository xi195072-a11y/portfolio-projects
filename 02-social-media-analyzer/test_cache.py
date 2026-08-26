"""Test cache loading for all 3 preset UIDs."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.packages'))
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

for mid in [946974, 546195, 37663924]:
    filepath = os.path.join(DATA_DIR, f"up_{mid}.json")
    print(f"\n=== UID {mid} ===")
    print(f"File exists: {os.path.exists(filepath)}")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        info = data.get("info", {})
        videos = data.get("videos", [])
        print(f"Info keys: {list(info.keys())}")
        print(f"Name: {info.get('name', 'N/A')}")
        print(f"Followers: {info.get('followers', 'N/A')}")
        print(f"Videos count: {len(videos)}")
        if videos:
            print(f"First video keys: {list(videos[0].keys())}")
            print(f"First video title: {videos[0].get('title', 'N/A')[:50]}")
            # Try loading as DataFrame
            df = pd.DataFrame(videos)
            print(f"DataFrame shape: {df.shape}")
            print(f"Date column dtype: {df['date'].dtype if 'date' in df.columns else 'MISSING'}")
    print()