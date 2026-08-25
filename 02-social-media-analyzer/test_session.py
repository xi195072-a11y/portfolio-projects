"""Test Bilibili API with session cookies.
用 session cookie 测试 B站 API。
"""
import http.cookiejar
import urllib.request
import urllib.parse
import json
import hashlib
import time

# Correct MIXIN_KEY_ENC_TAB
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 8, 12, 51, 55, 44, 38, 17, 28, 39, 19,
    41, 22, 62, 57, 4, 30, 6, 54, 36, 14, 48, 16, 50, 51, 52, 53,
    54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 0, 1, 2, 3, 4, 5,
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
}

# Create cookie-enabled opener / 创建带 cookie 的 opener
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Step 1: Visit Bilibili homepage to get cookies
print("=== Step 1: Get cookies from homepage ===")
req = urllib.request.Request("https://www.bilibili.com/", headers=HEADERS)
opener.open(req, timeout=10)
print(f"Got {len(list(cj))} cookies:")
for c in cj:
    print(f"  {c.name}: {c.value[:30]}...")

# Step 2: Get WBI keys
print("\n=== Step 2: Get WBI keys ===")
req = urllib.request.Request("https://api.bilibili.com/x/web-interface/nav", headers=HEADERS)
resp = opener.open(req, timeout=10)
nav_data = json.loads(resp.read().decode())
wbi_img = nav_data["data"]["wbi_img"]
img_key = wbi_img["img_url"].rsplit("/", 1)[1].split(".")[0]
sub_key = wbi_img["sub_url"].rsplit("/", 1)[1].split(".")[0]
print(f"img_key: {img_key}")
print(f"sub_key: {sub_key}")

# Step 3: Sign and request arc/search
def get_mixin_key(orig):
    return "".join(orig[i] for i in MIXIN_KEY_ENC_TAB)[:32]

def enc_wbi(params, img_key, sub_key):
    mixin_key = get_mixin_key(img_key + sub_key)
    params = dict(params)
    params["wts"] = round(time.time())
    params = dict(sorted(params.items()))
    query = urllib.parse.urlencode(params)
    w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params["w_rid"] = w_rid
    return params

print("\n=== Step 3: Test arc/search with cookies + WBI ===")
params = {
    "mid": 946974,
    "pn": 1,
    "ps": 5,
    "order": "pubdate",
    "platform": "web",
    "web_location": 1550101,
    "order_avoided": "true",
}
signed = enc_wbi(params, img_key, sub_key)
url = "https://api.bilibili.com/x/space/wbi/arc/search?" + urllib.parse.urlencode(signed)
req = urllib.request.Request(url, headers=HEADERS)
resp = opener.open(req, timeout=15)
data = json.loads(resp.read().decode())
print(f"code: {data.get('code')}, msg: {data.get('message')}")
if data.get("code") == 0:
    vlist = data["data"]["list"]["vlist"]
    print(f"Got {len(vlist)} videos!")
    for v in vlist[:3]:
        print(f"  - {v.get('title', '')[:40]} | play={v.get('play')}")

# Step 4: Also test acc/info
print("\n=== Step 4: Test acc/info with cookies + WBI ===")
params = {"mid": 946974}
signed = enc_wbi(params, img_key, sub_key)
url = "https://api.bilibili.com/x/space/wbi/acc/info?" + urllib.parse.urlencode(signed)
req = urllib.request.Request(url, headers=HEADERS)
resp = opener.open(req, timeout=15)
data = json.loads(resp.read().decode())
print(f"code: {data.get('code')}, msg: {data.get('message')}")
if data.get("code") == 0:
    d = data["data"]
    print(f"  name: {d.get('name')}, level: {d.get('level')}")
