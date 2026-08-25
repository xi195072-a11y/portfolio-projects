"""预取 B站 UP 主数据（带延迟防封）。"""
import sys, os, json, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".packages"))
sys.path.insert(0, os.path.dirname(__file__))

from bilibili_api import quick_fetch

# 修正后的 UID 列表
PRESET_UPS = [
    ("影视飓风", 946974),
    ("老番茄", 546195),
    ("LexBurner", 474323),
    ("无穷小亮的科普日常", 574933986),
    ("回形针PaperClip", 399452817),
    ("半佛仙人", 37663924),
    ("罗翔说刑法", 517327498),
    ("LKs-", 433344737),
]

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 清理旧的 JSON
for f in os.listdir(DATA_DIR):
    if f.endswith(".json"):
        os.remove(os.path.join(DATA_DIR, f))

for i, (name, mid) in enumerate(PRESET_UPS):
    print(f"\n=== [{i+1}/{len(PRESET_UPS)}] Fetching {name} (UID: {mid}) ===")

    # 延迟防封（第一个请求无需延迟）
    if i > 0:
        delay = 5
        print(f"  Waiting {delay}s to avoid rate limit...")
        time.sleep(delay)

    try:
        info, df = quick_fetch(mid, max_videos=30)
        if df.empty:
            print(f"  SKIP: No videos for {name}")
            continue

        # 构建可序列化的数据
        videos = []
        for _, row in df.iterrows():
            v = {}
            for col in df.columns:
                val = row[col]
                if hasattr(val, 'item'):
                    val = val.item()
                if col == 'date' and hasattr(val, 'isoformat'):
                    val = val.isoformat()
                v[col] = str(val) if val is not None else ""
            videos.append(v)

        data = {
            "info": {
                "mid": info.mid,
                "name": info.name,
                "face": info.face,
                "followers": info.followers,
                "video_count": info.video_count or len(df),
            },
            "videos": videos,
        }

        filepath = os.path.join(DATA_DIR, f"up_{mid}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  OK: {len(videos)} videos, {info.followers:,} followers")

    except Exception as e:
        print(f"  FAILED: {e}")

print("\n=== Done. JSON files in data/ ===")
for f in sorted(os.listdir(DATA_DIR)):
    if f.endswith(".json"):
        size = os.path.getsize(os.path.join(DATA_DIR, f))
        print(f"  {f} ({size:,} bytes)")
