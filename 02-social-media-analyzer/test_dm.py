"""Try B站 API with dm_img_* canvas fingerprint parameters.
尝试带 dm_img_* 画布指纹参数绕过反爬。
"""
import sys, os, time, hashlib, json, random, string

sys.path.insert(0, r"d:\projects\portfolio-projects\02-social-media-analyzer\.packages")

import requests

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

def get_mixin_key(raw):
    return "".join(raw[i] for i in MIXIN_KEY_ENC_TAB)[:32]

def enc_wbi(params, img_key, sub_key):
    import urllib.parse
    mixin_key = get_mixin_key(img_key + sub_key)
    params = dict(params)
    params["wts"] = int(time.time())
    filtered = {k: "".join(c for c in str(v) if c not in "!'()*") for k, v in params.items() if v is not None}
    sorted_params = dict(sorted(filtered.items()))
    query = urllib.parse.urlencode(sorted_params)
    w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
    sorted_params["w_rid"] = w_rid
    return sorted_params

def add_dm_fingerprint(params):
    """Add canvas fingerprint parameters to bypass anti-bot.
    添加画布指纹参数绕过反爬。
    """
    dm_rand = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    params["dm_img_list"] = "[]"
    params["dm_img_str"] = "".join(random.sample(dm_rand, 2))
    params["dm_cover_img_str"] = "".join(random.sample(dm_rand, 2))
    params["dm_img_inter"] = '{"ds":[],"wh":[0,0,0],"of":[0,0,0]}'
    return params

session = requests.Session()
session.headers.update(HEADERS)

# Step 1: Visit homepage
print("=== Step 1: Visit Bilibili ===")
session.get("https://www.bilibili.com/", timeout=10)
print(f"Cookies: {list(session.cookies.keys())}")

# Step 2: Get WBI keys
print("\n=== Step 2: Get WBI keys ===")
resp = session.get("https://api.bilibili.com/x/web-interface/nav", timeout=10)
nav = resp.json()
img_key = nav["data"]["wbi_img"]["img_url"].rsplit("/", 1)[1].split(".")[0]
sub_key = nav["data"]["wbi_img"]["sub_url"].rsplit("/", 1)[1].split(".")[0]
print(f"img_key: {img_key[:16]}...")

# Step 3: Try with dm_img params
print("\n=== Step 3: Test arc/search with dm_img params ===")
params = {
    "mid": 946974, "pn": 1, "ps": 30, "order": "pubdate",
    "platform": "web", "web_location": 1550101, "order_avoided": "true",
}
params = add_dm_fingerprint(params)
signed = enc_wbi(params, img_key, sub_key)
resp = session.get("https://api.bilibili.com/x/space/wbi/arc/search", params=signed, timeout=15)
data = resp.json()
print(f"code: {data.get('code')}, msg: {data.get('message')}")
if data.get("code") == 0:
    vlist = data["data"]["list"]["vlist"]
    print(f"Got {len(vlist)} videos!")
    if vlist:
        print(f"First: {vlist[0].get('title','')[:40]} | play={vlist[0].get('play')}")
else:
    print(f"Full response: {json.dumps(data)[:300]}")

# Step 4: Also add x-bili-trace-id header
print("\n=== Step 4: Test with x-bili-trace-id + dm ===")
import uuid
trace_id = str(uuid.uuid4()).replace("-", "")
params2 = {
    "mid": 946974, "pn": 1, "ps": 30, "order": "pubdate",
    "platform": "web", "web_location": 1550101, "order_avoided": "true",
}
params2 = add_dm_fingerprint(params2)
signed2 = enc_wbi(params2, img_key, sub_key)
headers2 = dict(HEADERS)
headers2["x-bili-trace-id"] = trace_id
resp2 = session.get("https://api.bilibili.com/x/space/wbi/arc/search", params=signed2, headers=headers2, timeout=15)
data2 = resp2.json()
print(f"code: {data2.get('code')}, msg: {data2.get('message')}")
if data2.get("code") == 0:
    vlist2 = data2["data"]["list"]["vlist"]
    print(f"Got {len(vlist2)} videos!")
else:
    print(f"Full: {json.dumps(data2)[:300]}")

# Step 5: Try acc/info too
print("\n=== Step 5: Test acc/info ===")
params3 = {"mid": 946974}
params3 = add_dm_fingerprint(params3)
signed3 = enc_wbi(params3, img_key, sub_key)
resp3 = session.get("https://api.bilibili.com/x/space/wbi/acc/info", params=signed3, timeout=10)
data3 = resp3.json()
print(f"code: {data3.get('code')}, msg: {data3.get('message')}")
if data3.get("code") == 0:
    print(f"Name: {data3['data'].get('name')}")
