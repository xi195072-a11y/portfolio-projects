"""Debug B站 API - test and capture actual error responses."""
import sys, os, json, time, hashlib, urllib.request, urllib.parse, http.cookiejar

sys.path.insert(0, r"d:\projects\portfolio-projects\02-social-media-analyzer\.packages")

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
    mixin_key = get_mixin_key(img_key + sub_key)
    params = dict(params)
    params["wts"] = int(time.time())
    filtered = {k: "".join(c for c in str(v) if c not in "!'()*") for k, v in params.items() if v is not None}
    sorted_params = dict(sorted(filtered.items()))
    query = urllib.parse.urlencode(sorted_params)
    w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
    sorted_params["w_rid"] = w_rid
    return sorted_params

# Setup session
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Step 1: Visit homepage
print("=== Step 1: Visit Bilibili ===")
try:
    opener.open(urllib.request.Request("https://www.bilibili.com/", headers=HEADERS), timeout=10)
    print(f"Cookies: {[(c.name, c.value[:20]) for c in cj]}")
except Exception as e:
    print(f"Error: {e}")

# Step 2: Get WBI keys
print("\n=== Step 2: Get WBI keys ===")
resp = opener.open(urllib.request.Request("https://api.bilibili.com/x/web-interface/nav", headers=HEADERS), timeout=10)
nav = json.loads(resp.read().decode())
print(f"code: {nav.get('code')}")
if nav.get("data") and nav["data"].get("wbi_img"):
    img_url = nav["data"]["wbi_img"]["img_url"]
    sub_url = nav["data"]["wbi_img"]["sub_url"]
    img_key = img_url.rsplit("/", 1)[1].split(".")[0]
    sub_key = sub_url.rsplit("/", 1)[1].split(".")[0]
    print(f"img_key: {img_key}")
    print(f"sub_key: {sub_key}")
else:
    print("No wbi_img found!")
    sys.exit(1)

# Step 3: Test arc/search with minimal params
print("\n=== Step 3: Test arc/search (minimal params) ===")
params = {"mid": 946974, "pn": 1, "ps": 30, "order": "pubdate"}
signed = enc_wbi(params, img_key, sub_key)
url = "https://api.bilibili.com/x/space/wbi/arc/search?" + urllib.parse.urlencode(signed)
print(f"URL params: {list(signed.keys())}")
try:
    req = urllib.request.Request(url, headers=HEADERS)
    resp = opener.open(req, timeout=15)
    data = json.loads(resp.read().decode())
    print(f"code: {data.get('code')}, msg: {data.get('message')}")
    if data.get("code") == 0:
        vlist = data["data"]["list"]["vlist"]
        print(f"Got {len(vlist)} videos")
        if vlist:
            v = vlist[0]
            print(f"First video: {v.get('title', '')[:40]}")
            print(f"Fields: {list(v.keys())[:15]}")
    elif data.get("data", {}).get("v_voucher"):
        print(f"v_voucher: {data['data']['v_voucher']}")
except urllib.error.HTTPError as e:
    body = e.read().decode()[:500]
    print(f"HTTP {e.code}: {body}")
except Exception as e:
    print(f"Error: {e}")

# Step 4: Test with web_location
print("\n=== Step 4: Test with web_location ===")
params2 = {"mid": 946974, "pn": 1, "ps": 30, "order": "pubdate", "web_location": 1550101}
signed2 = enc_wbi(params2, img_key, sub_key)
url2 = "https://api.bilibili.com/x/space/wbi/arc/search?" + urllib.parse.urlencode(signed2)
try:
    req2 = urllib.request.Request(url2, headers=HEADERS)
    resp2 = opener.open(req2, timeout=15)
    data2 = json.loads(resp2.read().decode())
    print(f"code: {data2.get('code')}, msg: {data2.get('message')}")
    if data2.get("code") == 0:
        vlist2 = data2["data"]["list"]["vlist"]
        print(f"Got {len(vlist2)} videos")
except urllib.error.HTTPError as e:
    body = e.read().decode()[:500]
    print(f"HTTP {e.code}: {body}")

# Step 5: Test relation/stat (no WBI)
print("\n=== Step 5: Test relation/stat ===")
try:
    req3 = urllib.request.Request("https://api.bilibili.com/x/relation/stat?vmid=946974", headers=HEADERS)
    resp3 = opener.open(req3, timeout=10)
    data3 = json.loads(resp3.read().decode())
    print(f"code: {data3.get('code')}, msg: {data3.get('message')}")
    if data3.get("data"):
        print(f"followers: {data3['data'].get('follower', 0):,}")
except Exception as e:
    print(f"Error: {e}")
