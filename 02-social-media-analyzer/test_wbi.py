"""Test Bilibili WBI signature / 测试 B站 WBI 签名"""
import urllib.request
import json
import hashlib
from urllib.parse import urlencode

# WBI key mixin table / WBI 密钥重排表
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 8, 12, 51, 55, 44, 38, 17, 28, 39, 19,
    41, 22, 62, 57, 4, 30, 6, 54, 36, 14, 48, 16, 50, 51, 52, 53,
    54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69,
]


def get_mixin_key(orig: str) -> str:
    """Generate mixin key from original key.
    从原始 key 生成 mixin key。
    """
    return "".join(orig[i] for i in MIXIN_KEY_ENC_TAB)[:32]


def enc_wbi(params: dict, img_key: str, sub_key: str) -> dict:
    """Sign params with WBI.
    用 WBI 签名参数。
    """
    mixin_key = get_mixin_key(img_key + sub_key)
    curr_time = round(__import__("time").time())
    params["wts"] = curr_time
    # Sort and urlencode / 排序并 URL 编码
    params = dict(sorted(params.items()))
    query = urlencode(params)
    wbi_sign = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params["w_rid"] = wbi_sign
    return params


def get_wbi_keys() -> tuple:
    """Get WBI keys from nav API.
    从 nav 接口获取 WBI 密钥。
    """
    url = "https://api.bilibili.com/x/web-interface/nav"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    img_url = data["data"]["wbi_img"]["img_url"]
    sub_url = data["data"]["wbi_img"]["sub_url"]
    img_key = img_url.rsplit("/", 1)[1].split(".")[0]
    sub_key = sub_url.rsplit("/", 1)[1].split(".")[0]
    return img_key, sub_key


# Test
print("=== Getting WBI keys ===")
img_key, sub_key = get_wbi_keys()
print(f"img_key: {img_key}")
print(f"sub_key: {sub_key}")

print("\n=== Testing signed video list ===")
params = {"mid": 946974, "pn": 1, "ps": 5, "order": "pubdate"}
signed = enc_wbi(params, img_key, sub_key)

url = "https://api.bilibili.com/x/space/wbi/arc/search?" + urlencode(signed)
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://space.bilibili.com/946974",
})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print(f"code: {data.get('code')}, msg: {data.get('message')}")
        if data.get("data", {}).get("list", {}).get("vlist"):
            vlist = data["data"]["list"]["vlist"]
            print(f"Got {len(vlist)} videos:")
            for v in vlist[:3]:
                print(f"  - {v.get('title', '')[:40]} | play={v.get('play')}")
except Exception as e:
    print(f"Error: {e}")
