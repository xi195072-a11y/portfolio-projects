"""Test with requests library instead of urllib."""
import sys, os, time, hashlib, json

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

session = requests.Session()
session.headers.update(HEADERS)

# Step 1: Visit homepage for cookies
print("=== Step 1: Visit Bilibili ===")
resp = session.get("https://www.bilibili.com/", timeout=10)
print(f"Status: {resp.status_code}, Cookies: {list(session.cookies.keys())}")

# Step 2: Get WBI keys
print("\n=== Step 2: Get WBI keys ===")
resp = session.get("https://api.bilibili.com/x/web-interface/nav", timeout=10)
nav = resp.json()
print(f"code: {nav.get('code')}")
if nav.get("data") and nav["data"].get("wbi_img"):
    img_url = nav["data"]["wbi_img"]["img_url"]
    sub_url = nav["data"]["wbi_img"]["sub_url"]
    img_key = img_url.rsplit("/", 1)[1].split(".")[0]
    sub_key = sub_url.rsplit("/", 1)[1].split(".")[0]
    print(f"img_key: {img_key}")
    print(f"sub_key: {sub_key}")

# Step 3: Test arc/search
print("\n=== Step 3: Test arc/search ===")
params = {"mid": 946974, "pn": 1, "ps": 30, "order": "pubdate", "platform": "web", "web_location": 1550101}
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
    if data.get("data", {}).get("v_voucher"):
        print(f"v_voucher: {data['data']['v_voucher']}")

# Step 4: Test relation/stat
print("\n=== Step 4: Test relation/stat ===")
resp = session.get("https://api.bilibili.com/x/relation/stat", params={"vmid": 946974}, timeout=10)
data = resp.json()
print(f"code: {data.get('code')}, followers: {data.get('data', {}).get('follower', 0):,}")
