"""Quick test script for B站 API connectivity."""
import sys, os

# Add .packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.packages'))

# Test importing bilibili_api
print("=== Test 1: Import bilibili_api ===")
try:
    from bilibili_api import quick_fetch
    print("SUCCESS: bilibili_api imported")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test fetching UID 14476927
print("\n=== Test 2: Fetch UID 14476927 ===")
try:
    info, df = quick_fetch(14476927, max_videos=5)
    print(f"SUCCESS: info.mid={info.mid}, info.name={info.name}")
    print(f"Videos count: {len(df)}")
    if not df.empty:
        print(f"First video title: {df.iloc[0].get('title', 'N/A')}")
except Exception as e:
    print(f"FETCH ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Also test a known-good UID
print("\n=== Test 3: Fetch UID 946974 (影视飓风) ===")
try:
    info2, df2 = quick_fetch(946974, max_videos=3)
    print(f"SUCCESS: info.mid={info2.mid}, info.name={info2.name}")
    print(f"Videos count: {len(df2)}")
except Exception as e:
    print(f"FETCH ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()