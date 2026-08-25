import sys
sys.path.insert(0, '.packages')
sys.path.insert(0, '.')
from bilibili_api import fetch_up_full_data

info, df = fetch_up_full_data(946974, max_videos=20)
print(f"Name: {info.name}")
print(f"Followers: {info.followers:,}")
print(f"Videos fetched: {len(df)}")
print(f"Video count (total): {info.video_count:,}")
total_views = df["views"].sum()
avg_views = df["views"].mean()
print(f"Total views: {total_views:,}")
print(f"Avg views: {avg_views:,.0f}")
