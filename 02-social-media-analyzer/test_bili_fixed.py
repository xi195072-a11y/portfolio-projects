"""Test Bilibili API client with correct WBI signature.
测试 B站 API 客户端（影视飓风 UID: 946974）。
"""
import sys
sys.path.insert(0, r"d:\projects\portfolio-projects\02-social-media-analyzer")

from bilibili_api import BiliSession, fetch_up_info, fetch_up_videos

print("=== Step 1: Initialize session + get WBI keys ===")
session = BiliSession()
session.warm_up()
print(f"img_key: {session._img_key}")
print(f"sub_key: {session._sub_key}")

print("\n=== Step 2: Fetch UP info (影视飓风) ===")
try:
    info = fetch_up_info(session, 946974)
    print(f"Name: {info.name}")
    print(f"Level: Lv.{info.level}")
    print(f"Followers: {info.followers:,}")
    print(f"Video count: {info.video_count:,}")
    print(f"Sign: {info.sign[:60]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Step 3: Fetch videos (max 20) ===")
try:
    df = fetch_up_videos(session, 946974, max_videos=20)
    print(f"Fetched {len(df)} videos")
    if len(df) > 0:
        print(f"\nColumns: {list(df.columns)}")
        print(f"\nLatest 3 videos:")
        for _, row in df.head(3).iterrows():
            print(f"  - {row['title'][:50]}")
            print(f"    views={row['views']:,}, likes={row['likes']:,}, favorites={row['favorites']:,}")
            print(f"    engagement_rate={row['engagement_rate']}%")
        
        print(f"\nTotal views: {df['views'].sum():,}")
        print(f"Avg views: {df['views'].mean():,.0f}")
        print(f"Max views: {df['views'].max():,}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
