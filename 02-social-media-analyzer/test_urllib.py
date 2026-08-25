"""Test if urllib-based API works with dm_img_* params."""
import sys
sys.path.insert(0, ".packages")
sys.path.insert(0, ".")

from bilibili_api import BiliSession, _add_dm_fingerprint, fetch_up_full_data

print("=== Test 1: fetch_up_full_data (uses urllib internally) ===")
try:
    info, df = fetch_up_full_data(946974, max_videos=30)
    print(f"SUCCESS: {info.name}, {len(df)} videos")
    if len(df) > 0:
        print(f"First video: {df['title'].iloc[0][:40]}")
except Exception as e:
    print(f"FAILED: {e}")

print("\n=== Test 2: Single signed request ===")
try:
    session = BiliSession()
    session.warm_up()
    print("Warm up OK")
    
    params = {
        "mid": 946974, "pn": 1, "ps": 30, "order": "pubdate",
        "platform": "web", "web_location": 1550101, "order_avoided": "true",
    }
    params = _add_dm_fingerprint(params)
    print(f"dm params added: {list(params.keys())}")
    
    data = session.get(
        "https://api.bilibili.com/x/space/wbi/arc/search",
        params=params, signed=True,
    )
    print(f"code: {data.get('code')}, msg: {data.get('message')}")
    if data.get("code") == 0:
        vlist = data["data"]["list"]["vlist"]
        print(f"Got {len(vlist)} videos")
except Exception as e:
    print(f"FAILED: {e}")
