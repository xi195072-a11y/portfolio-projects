"""Test bilibili_api module / 测试 bilibili_api 模块"""
import sys
sys.path.insert(0, r"d:\projects\portfolio-projects\02-social-media-analyzer")

from bilibili_api import fetch_up_full_data

print("=== Fetching 影视飓风 (UID: 946974) ===")
try:
    info, df = fetch_up_full_data(946974, max_videos=50)
    print(f"\nUP Info:")
    print(f"  Name: {info.name}")
    print(f"  Sign: {info.sign[:50]}")
    print(f"  Level: {info.level}")
    print(f"  Followers: {info.followers:,}")

    print(f"\nVideo Data:")
    print(f"  Total fetched: {len(df)} videos")
    print(f"  Columns: {list(df.columns)[:10]}")

    if len(df) > 0:
        print(f"\n  Latest 3 videos:")
        for _, row in df.head(3).iterrows():
            print(f"    - {row.get('title', '')[:40]}")
            print(f"      views={row.get('views', 0):,}, likes={row.get('likes', 0):,}")

        print(f"\n  Total views: {df['views'].sum():,}")
        print(f"  Total likes: {df['likes'].sum():,}")
        print(f"  Avg views: {df['views'].mean():,.0f}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
