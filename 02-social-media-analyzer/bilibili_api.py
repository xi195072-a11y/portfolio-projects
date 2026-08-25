"""Bilibili (B 站) API client — 基于 requests 库 + dm_img_* 画布指纹。
Bilibili API client using requests library + canvas fingerprinting.

Key fixes (2026-08-25):
- dm_img_* params added to ALL API requests (not just signed ones)
- buvid3 cookie properly handled
- Rate limiting: delays between requests
- Better error messages
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests

# ── WBI 签名重排表（64 项） ─────────────────────────────────────────────
MIXIN_KEY_ENC_TAB: list[int] = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Sec-CH-UA": '"Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

_DM_RAND = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_SPECIAL_CHARS: set[str] = set("!'()*")

# B站可能需要访问的 API 域名
_API_HOSTS = ("api.bilibili.com", "api.bilibili.com")


def _filter_special(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch not in _SPECIAL_CHARS)


def _get_mixin_key(raw_key: str) -> str:
    return "".join(raw_key[i] for i in MIXIN_KEY_ENC_TAB)[:32]


def _add_dm_fingerprint(params: dict[str, Any]) -> dict[str, Any]:
    """添加画布指纹参数（绕过 B站 412 反爬）。
    必须在所有 API 请求中加入，包括不需要签名的请求。
    """
    # 生成随机 dm_img_str (2个字符) 和 dm_cover_img_str (2个字符)
    params["dm_img_list"] = "[]"
    params["dm_img_str"] = "".join(random.sample(_DM_RAND, 2))
    params["dm_cover_img_str"] = "".join(random.sample(_DM_RAND, 2))
    params["dm_img_inter"] = '{"ds":[],"wh":[0,0,0],"of":[0,0,0]}'
    return params


def _enc_wbi(params: dict[str, Any], img_key: str, sub_key: str) -> dict[str, Any]:
    """WBI 签名：mixin_key + md5(sorted_params + mixin_key)。"""
    mixin_key = _get_mixin_key(img_key + sub_key)
    params = dict(params)
    params["wts"] = int(time.time())
    filtered = {k: _filter_special(v) for k, v in params.items() if v is not None}
    sorted_params = dict(sorted(filtered.items()))
    query = urllib.parse.urlencode(sorted_params)
    w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
    sorted_params["w_rid"] = w_rid
    return sorted_params


class BiliSession:
    """B 站会话：requests Session + Cookie + WBI + 画布指纹。"""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._img_key: str | None = None
        self._sub_key: str | None = None
        self._wbi_cache_time: float = 0.0
        self._request_count: int = 0
        self._last_request_time: float = 0.0

    def _rate_limit(self) -> None:
        """请求间隔控制：每 3 个请求加 1s 延迟，避免触发反爬。"""
        self._request_count += 1
        if self._request_count % 3 == 0:
            time.sleep(1.0)
        elapsed = time.time() - self._last_request_time
        if elapsed < 0.3:
            time.sleep(0.3 - elapsed)
        self._last_request_time = time.time()

    def _refresh_wbi_keys(self) -> None:
        """获取 WBI 密钥（先访问首页拿 buvid3 Cookie）。"""
        # 先访问首页，获取 buvid3 等 Cookie
        try:
            self.session.get("https://www.bilibili.com/", timeout=10)
        except Exception:
            pass

        # 延迟一下再请求 nav，模拟浏览器行为
        time.sleep(0.5)

        # 用 dm_img_* 请求 nav 接口
        params = _add_dm_fingerprint({})
        resp = self.session.get(
            "https://api.bilibili.com/x/web-interface/nav",
            params=params,
            timeout=10,
        )
        data = resp.json()
        if not data.get("data") or not data["data"].get("wbi_img"):
            raise RuntimeError(
                f"获取 WBI 密钥失败 / Failed to get WBI keys: "
                f"code={data.get('code')}, msg={data.get('message')}"
            )

        wbi_img = data["data"]["wbi_img"]
        self._img_key = wbi_img["img_url"].rsplit("/", 1)[1].split(".")[0]
        self._sub_key = wbi_img["sub_url"].rsplit("/", 1)[1].split(".")[0]
        self._wbi_cache_time = time.time()

    def warm_up(self) -> None:
        """初始化会话：获取 Cookie + WBI 密钥。"""
        self._refresh_wbi_keys()

    def _sign_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """签名参数：dm_img_* + WBI 签名。"""
        if time.time() - self._wbi_cache_time > 3600:
            self._refresh_wbi_keys()
        assert self._img_key and self._sub_key
        params = _add_dm_fingerprint(params)
        return _enc_wbi(params, self._img_key, self._sub_key)

    def get(
        self, url: str, params: dict | None = None,
        signed: bool = False, timeout: int = 15,
    ) -> dict:
        """GET 请求 — 所有 API 请求自动加 dm_img_* 指纹。"""
        self._rate_limit()

        if params is None:
            params = {}

        # 关键修复：所有 API 请求都加 dm_img_*（不仅仅是 signed 请求）
        if signed:
            params = self._sign_params(params)
        else:
            params = _add_dm_fingerprint(params)

        try:
            resp = self.session.get(url, params=params, timeout=timeout)
            # 检查 B站业务层面的错误码
            body = resp.text
            # 尝试解析 JSON
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                # 非 JSON 响应（如 HTML），可能是被拦截
                if resp.status_code == 200 and ("<!DOCTYPE" in body or "<html" in body[:100]):
                    raise RuntimeError(
                        f"B站返回 HTML 拦截页（可能被反爬）/ "
                        f"Bilibili returned HTML block page"
                    )
                raise RuntimeError(f"非 JSON 响应 / Non-JSON response: {body[:200]}")

            # 检查 B站错误码
            code = data.get("code", -1)
            if code == -412:
                raise RuntimeError(
                    f"B站反爬拦截 (412) / Bilibili anti-bot blocked request. "
                    f"请稍后重试或使用其他网络。"
                )
            if code == -352:
                raise RuntimeError(
                    f"B站风控系统拦截 / Bilibili risk control blocked. "
                    f"请更换网络或稍后再试。"
                )
            if code != 0:
                # 其他错误码
                msg = data.get("message", "Unknown error")
                # -404 表示 UID 不存在
                if code == -404:
                    raise RuntimeError(f"UID 不存在 / UID not found: {msg}")
                raise RuntimeError(f"API 错误 (code={code}) / API error: {msg}")

            return data

        except requests.exceptions.Timeout:
            raise RuntimeError(f"请求超时 / Request timeout: {url}")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"连接失败 / Connection failed: {url}")


@dataclass
class UPInfo:
    """B 站 UP 主信息。"""
    mid: int
    name: str
    face: str
    sign: str
    level: int
    followers: int
    video_count: int


def fetch_up_info(
    session: BiliSession, mid: int, video_df: pd.DataFrame | None = None,
) -> UPInfo:
    """获取 UP 主信息。"""
    # 粉丝数（不需要 WBI 签名，但需要 dm_img_*）
    followers = 0
    try:
        stat = session.get(
            "https://api.bilibili.com/x/relation/stat",
            params={"vmid": mid},
            signed=False,
        )
        if stat.get("data"):
            followers = stat["data"].get("follower", 0)
    except Exception:
        pass

    # 昵称优先从视频数据提取（避免额外请求）
    name = ""
    face = ""
    if video_df is not None and len(video_df) > 0 and "author" in video_df.columns:
        name = str(video_df["author"].iloc[0])

    # 如果视频数据里没有名字，再请求 acc/info（需要 WBI 签名）
    if not name:
        try:
            # acc/info 接口已经在 session.get 里加了 dm_img_*
            # 但因为是 /wbi/ 路径，需要 WBI 签名
            data = session.get(
                "https://api.bilibili.com/x/space/wbi/acc/info",
                params={"mid": mid}, signed=True,
            )
            if data.get("data"):
                d = data["data"]
                name = d.get("name", "")
                face = d.get("face", "")
        except Exception:
            pass

    return UPInfo(
        mid=mid, name=name, face=face, sign="", level=0,
        followers=followers, video_count=0,
    )


def fetch_up_videos(
    session: BiliSession, mid: int, max_videos: int = 100, page_size: int = 30,
) -> tuple[pd.DataFrame, int]:
    """获取 UP 主视频列表（已加 dm_img_* + WBI 签名）。"""
    all_videos: list[dict[str, Any]] = []
    page = 1
    page_size = min(page_size, 50)
    total_count = 0

    while len(all_videos) < max_videos:
        params: dict[str, Any] = {
            "mid": mid,
            "pn": page,
            "ps": page_size,
            "order": "pubdate",
            "platform": "web",
            "web_location": 1550101,
            "order_avoided": "true",
        }

        data = session.get(
            "https://api.bilibili.com/x/space/wbi/arc/search",
            params=params, signed=True,
        )

        vlist = data.get("data", {}).get("list", {}).get("vlist", [])
        total_count = data.get("data", {}).get("page", {}).get("count", 0)
        if not vlist:
            break

        all_videos.extend(vlist)

        if len(all_videos) >= total_count or len(vlist) < page_size:
            break

        page += 1
        # 请求间隔：避免触发反爬
        time.sleep(0.8)

    if not all_videos:
        return pd.DataFrame(), total_count

    df = pd.DataFrame(all_videos)

    column_map: dict[str, str] = {
        "title": "title", "created": "timestamp", "play": "views",
        "video_review": "comments", "favorites": "favorites", "share": "shares",
        "like": "likes", "length": "duration_text", "bvid": "bvid",
        "description": "description", "author": "author",
    }
    df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})

    if "timestamp" in df.columns:
        df["date"] = pd.to_datetime(df["timestamp"], unit="s")
        df = df.drop(columns=["timestamp"])

    for col in ["views", "likes", "favorites", "comments", "shares"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["engagement"] = df["likes"] + df["favorites"] + df["comments"] + df["shares"]
    df["engagement_rate"] = df.apply(
        lambda r: round((r["engagement"] / r["views"] * 100), 2) if r["views"] > 0 else 0.0,
        axis=1,
    )
    df["platform"] = "Bilibili"
    if "duration_text" not in df.columns:
        df["duration_text"] = ""
    if "author" not in df.columns:
        df["author"] = ""

    if "date" in df.columns:
        df = df.sort_values("date", ascending=False).reset_index(drop=True)

    return df, total_count


def fetch_up_full_data(mid: int, max_videos: int = 100) -> tuple[UPInfo, pd.DataFrame]:
    """获取 UP 主全部数据。
    
    请求顺序（模拟浏览器行为，避免触发反爬）：
    1. 访问首页获取 buvid3 Cookie
    2. 获取 WBI 密钥（nav 接口）
    3. 获取粉丝数（relation/stat，不需要签名）
    4. 获取视频列表（arc/search，需要 WBI 签名）
    5. 获取 UP 主信息（acc/info，需要 WBI 签名）
    """
    session = BiliSession()
    session.warm_up()
    time.sleep(1.0)  # 模拟浏览器：nav 后需要缓冲

    # Step 1: 先获取粉丝数（简单请求，不需要签名）
    # 这样模拟正常用户行为：先看粉丝再看视频
    followers = 0
    try:
        stat = session.get(
            "https://api.bilibili.com/x/relation/stat",
            params={"vmid": mid}, signed=False,
        )
        if stat.get("data"):
            followers = stat["data"].get("follower", 0)
    except Exception:
        pass

    time.sleep(1.0)  # 请求间隔

    # Step 2: 获取视频列表
    df, total_count = fetch_up_videos(session, mid, max_videos=max_videos)
    if total_count == 0 and not df.empty:
        total_count = len(df)

    time.sleep(1.0)  # 请求间隔

    # Step 3: 获取 UP 主详细信息
    info = UPInfo(mid=mid, name="", face="", sign="", level=0,
                   followers=followers, video_count=total_count)

    # 从视频数据提取名字（最可靠的方式）
    if not df.empty and "author" in df.columns:
        info.name = str(df["author"].iloc[0])

    # 如果视频里没有名字，再请求 acc/info
    if not info.name:
        try:
            data = session.get(
                "https://api.bilibili.com/x/space/wbi/acc/info",
                params={"mid": mid}, signed=True,
            )
            if data.get("data"):
                d = data["data"]
                info.name = d.get("name", "")
                info.face = d.get("face", "")
        except Exception:
            pass

    if total_count > 0:
        info.video_count = total_count
    return info, df


def quick_fetch(mid: int, max_videos: int = 100) -> tuple[UPInfo, pd.DataFrame]:
    """便捷函数：快速获取指定 UP 主数据。"""
    return fetch_up_full_data(mid, max_videos=max_videos)
