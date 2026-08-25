"""Direct test of the bilibili_api module as it currently is."""
import sys, os
sys.path.insert(0, r"d:\projects\portfolio-projects\02-social-media-analyzer\.packages")
sys.path.insert(0, r"d:\projects\portfolio-projects\02-social-media-analyzer")

# Force reimport
import importlib
import bilibili_api
importlib.reload(bilibili_api)

from bilibili_api import BiliSession, fetch_up_videos

print("=== Creating session ===")
session = BiliSession()
session.warm_up()
print(f"WBI keys loaded: img={session._img_key[:16]}... sub={session._sub_key[:16]}...")

print("\n=== Fetching videos ===")
try:
    df, total = fetch_up_videos(session, 946974, max_videos=30)
    print(f"SUCCESS: Got {len(df)} videos, total_count={total}")
    if len(df) > 0:
        print(f"Columns: {list(df.columns[:10])}")
        print(f"First title: {df['title'].iloc[0][:50]}")
        print(f"First views: {df['views'].iloc[0]:,}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
