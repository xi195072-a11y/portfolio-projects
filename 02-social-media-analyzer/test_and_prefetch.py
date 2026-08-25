"""Test requests-based API + prefetch data for remaining UPs."""
import sys, os, json, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".packages"))
sys.path.insert(0, os.path.dirname(__file__))

from bilibili_api import quick_fetch

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 先测试一个看看 requests 版本是否能用
print("=== Test requests-based API ===")
try:
    info, df = quick_fetch(946974, max_videos=30)
    print(f"SUCCESS: {info.name}, {len(df)} videos, {info.followers:,} followers")
except Exception as e:
    print(f"FAILED: {e}")

# 如果成功，预取其他 UP
remaining = [
    ("影视飓风", 946974),  # 已验证
    ("老番茄", 546195),    # 已验证
    ("LexBurner", 474323),
    ("无穷小亮的科普日常", 574933986),
    ("回形针PaperClip", 399452817),
    ("半佛仙人", 37663924),
    ("罗翔说刑法", 517327498),
    ("LKs-", 433344737),
]

for name, mid in remaining:
    filepath = os.path.join(DATA_DIR, f"up_{mid}.json")
    if os.path.exists(filepath):
        print(f"\n[SKIP] {name} (UID:{mid}) already cached")
        continue

    print(f"\n=== Fetching {name} (UID: {mid}) ===")
    time.sleep(3)  # 延迟防封

    try:
        info, df = quick_fetch(mid, max_videos=30)
        if df.empty:
            print(f"  SKIP: No videos")
            continue

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
                "mid": info.mid, "name": info.name,
                "face": info.face, "followers": info.followers,
                "video_count": info.video_count or len(df),
            },
            "videos": videos,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  OK: {len(videos)} videos, {info.followers:,} followers")

    except Exception as e:
        print(f"  FAILED: {e}")

print("\n=== JSON files ===")
for f in sorted(os.listdir(DATA_DIR)):
    if f.endswith(".json"):
        size = os.path.getsize(os.path.join(DATA_DIR, f))
        with open(os.path.join(DATA_DIR, f), "r", encoding="utf-8") as fp:
            d = json.load(fp)
        name = d["info"]["name"]
        followers = d["info"]["followers"]
        vcount = len(d["videos"])
        print(f"  {f}: {name} | {followers:,} followers | {vcount} videos")
