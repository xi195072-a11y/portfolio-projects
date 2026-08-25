"""Debug WBI signature - test different API endpoints.
调试 WBI 签名 - 测试不同 API 端点。
"""
import hashlib
import time
import urllib.request
import urllib.parse
import json

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
}

# Correct MIXIN_KEY_ENC_TAB from bilibili-API-collect
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 8, 12, 51, 55, 44, 38, 17, 28, 39, 19,
    41, 22, 62, 57, 4, 30, 6, 54, 36, 14, 48, 16, 50, 51, 52, 53,
    54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 0, 1, 2, 3, 4, 5,
]

def get_mixin_key(orig: str) -> str:
    return "".join(orig[i] for i in MIXIN_KEY_ENC_TAB)[:32]

def enc_wbi(params: dict, img_key: str, sub_key: str) -> dict:
    mixin_key = get_mixin_key(img_key + sub_key)
    params = dict(params)
    params["wts"] = round(time.time())
    params = dict(sorted(params.items()))
    query = urllib.parse.urlencode(params)
    w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params["w_rid"] = w_rid
    return params

def fetch_wbi_keys():
    url = "https://api.bilibili.com/x/web-interface/nav"
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    wbi_img = data["data"]["wbi_img"]
    img_key = wbi_img["img_url"].rsplit("/", 1)[1].split(".")[0]
    sub_key = wbi_img["sub_url"].rsplit("/", 1)[1].split(".")[0]
    return img_key, sub_key

def api_get(url, params=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

# Test 1: WBI keys
print("=== WBI Keys ===")
img_key, sub_key = fetch_wbi_keys()
print(f"img_key: {img_key}")
print(f"sub_key: {sub_key}")
mixin_key = get_mixin_key(img_key + sub_key)
print(f"mixin_key: {mixin_key}")

# Test 2: acc/info with wbi signature
print("\n=== Test acc/info (WBI) ===")
params = {"mid": 946974}
signed = enc_wbi(params, img_key, sub_key)
url = "https://api.bilibili.com/x/space/wbi/acc/info"
data = api_get(url, signed)
print(f"code: {data.get('code')}, msg: {data.get('message')}")
if data.get("code") == 0:
    d = data["data"]
    print(f"  name: {d.get('name')}")

# Test 3: arc/search with wbi signature
print("\n=== Test arc/search (WBI) ===")
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
url = "https://api.bilibili.com/x/space/wbi/arc/search"
data = api_get(url, signed)
print(f"code: {data.get('code')}, msg: {data.get('message')}")
if data.get("code") == 0:
    vlist = data["data"]["list"]["vlist"]
    print(f"  Got {len(vlist)} videos")
    for v in vlist[:2]:
        print(f"  - {v.get('title', '')[:40]} | play={v.get('play')}")

# Test 4: Try relation/stat (no wbi needed)
print("\n=== Test relation/stat (no WBI) ===")
data = api_get("https://api.bilibili.com/x/relation/stat", {"vmid": 946974})
print(f"code: {data.get('code')}, msg: {data.get('message')}")
if data.get("code") == 0:
    print(f"  followers: {data['data'].get('follower'):,}")
