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
import sys
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any

# ── 关键：确保 Streamlit Runtime 等子进程也能找到 .packages 里的依赖 ──
# （有些部署方式把子进程和主进程的 sys.path 隔离开了，这里直接硬编码注入）
_here_bili = os.path.dirname(os.path.abspath(__file__))
_pkgs_bili = os.path.join(_here_bili, ".packages")
if os.path.isdir(_pkgs_bili) and _pkgs_bili not in sys.path:
    sys.path.insert(0, _pkgs_bili)
if _here_bili not in sys.path:
    sys.path.insert(0, _here_bili)

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

    def __init__(self, user_cookie: str = "") -> None:
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._img_key: str | None = None
        self._sub_key: str | None = None
        self._wbi_cache_time: float = 0.0
        self._request_count: int = 0
        self._last_request_time: float = 0.0

        # 注入用户 Cookie（从浏览器复制的完整 Cookie 字符串）
        if user_cookie:
            self._inject_cookie(user_cookie)

    def _inject_cookie(self, cookie_str: str) -> None:
        """解析并注入 Cookie 字符串到 Session。"""
        # 格式：SESSDATA=xxx; bili_jct=xxx; buvid3=xxx; ...
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                key, val = item.split("=", 1)
                self.session.cookies.set(key.strip(), val.strip(), domain=".bilibili.com")

    def _rate_limit(self) -> None:
        """请求间隔控制：随机延迟 0.5-2s，模拟人类浏览节奏。"""
        self._request_count += 1
        # 随机延迟：0.5s ~ 2s，避免固定间隔被检测
        delay = random.uniform(0.5, 2.0)
        if self._request_count % 5 == 0:
            delay += random.uniform(1.0, 3.0)  # 每 5 个请求额外加 1-3s
        elapsed = time.time() - self._last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
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
        # 请求间隔：避免触发反爬（每间隔 2.5-4.5 秒）
        time.sleep(random.uniform(2.5, 4.5))

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


def fetch_up_full_data(mid: int, max_videos: int = 100, user_cookie: str = "") -> tuple[UPInfo, pd.DataFrame]:
    """获取 UP 主全部数据。
    
    请求顺序（模拟浏览器行为，避免触发反爬）：
    1. 访问首页获取 buvid3 Cookie
    2. 获取 WBI 密钥（nav 接口）
    3. 获取粉丝数（relation/stat，不需要签名）
    4. 获取视频列表（arc/search，需要 WBI 签名）
    5. 获取 UP 主信息（acc/info，需要 WBI 签名）
    
    Args:
        mid: B站 UID
        max_videos: 最大视频数
        user_cookie: 从浏览器复制的 Cookie 字符串（可选，有则更稳定）
    """
    session = BiliSession(user_cookie=user_cookie)
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


def quick_fetch(mid: int, max_videos: int = 100, user_cookie: str = "") -> tuple[UPInfo, pd.DataFrame]:
    """便捷函数：快速获取指定 UP 主数据。"""
    return fetch_up_full_data(mid, max_videos=max_videos, user_cookie=user_cookie)


# ═══════════════════════════════════════════════════════════════════
# 自动从 Chrome 读取 Cookie
# ═══════════════════════════════════════════════════════════════════

def auto_read_chrome_cookie() -> str:
    """尝试从本机 Chrome 自动读取 B站 Cookie。
    
    成功返回 Cookie 字符串（如 'SESSDATA=xxx; buvid3=xxx'），失败返回空字符串。
    注意：Chrome 正在运行时 Cookie 数据库可能被锁定。
    """
    try:
        from read_bilibili_cookies import read_bilibili_cookies
        return read_bilibili_cookies()
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════
# Playwright 模式：无头真实浏览器请求，自带完整浏览器指纹
# 优点：无需 Cookie、完全绕过 412；缺点：需要安装 playwright + chromium
# ═══════════════════════════════════════════════════════════════════

def is_playwright_available() -> bool:
    """检测 Playwright Python 包和浏览器是否安装。

    只检查 Python 包，浏览器二进制在首次启动时再检测并报错。
    """
    try:
        import playwright  # noqa: F401
        return True
    except Exception as _e:
        import logging
        logging.getLogger(__name__).warning(
            "Playwright not available: %s | sys.path[:5]=%s", _e, sys.path[:5]
        )
        return False


def _find_system_chrome() -> str | None:
    """在 Windows / macOS / Linux 上寻找系统已安装的 Chrome / Chromium / Edge 可执行文件。

    Playwright 默认需要它自己分发的 "Chromium for Testing"，
    但我们其实可以复用系统已装的 Chrome（节省 ~200MB 下载）。
    """
    import shutil

    # 1. 常见位置硬编码（Windows）
    win_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for p in win_paths:
        if os.path.exists(p):
            return p
    # 2. macOS
    mac_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for p in mac_paths:
        if os.path.exists(p):
            return p
    # 3. PATH 查找
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        p = shutil.which(name)
        if p:
            return p
    return None


class PlaywrightBiliSession:
    """基于 Playwright 同步 API 的 B站会话。

    用无头真实浏览器 + 页面内 fetch() 发 API 请求，天然拥有：
      - 真实 TLS 指纹（系统 Chrome/Edge）
      - 完整浏览器 Cookie + Referer + Origin + Sec-Fetch-* 头链
      - 页面内 fetch 走正常浏览器通道，几乎不会被 B站 412 误拦

    接口和 BiliSession 一致（warm_up / get），所以 fetch_up_* 函数通过
    duck typing 可以无缝替换 BiliSession。
    """

    def __init__(self, user_cookie: str = "") -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise RuntimeError(
                "未安装 Playwright / Playwright not installed. "
                "请运行: pip install playwright（复用系统 Chrome 无需再下载浏览器）\n"
                "Install: pip install playwright (reuses system Chrome/Edge)"
            ) from e

        self._sync_pw = sync_playwright().start()

        # 优先复用系统 Chrome（节省 ~200MB Chromium for Testing 下载）
        system_chrome = _find_system_chrome()
        launch_kwargs: dict[str, Any] = {"headless": True}
        if system_chrome:
            launch_kwargs["executable_path"] = system_chrome
            launch_kwargs["args"] = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        try:
            self._browser = self._sync_pw.chromium.launch(**launch_kwargs)
        except Exception as e:
            # 指定系统 Chrome 失败，回退 Playwright 自带 Chromium
            if system_chrome:
                try:
                    self._sync_pw.stop()
                except Exception:
                    pass
                self._sync_pw = sync_playwright().start()
                self._browser = self._sync_pw.chromium.launch(headless=True)
            else:
                raise RuntimeError(
                    "启动浏览器失败 / Failed to launch browser.\n"
                    "请执行: playwright install chromium  或先安装 Chrome/Edge。\n"
                    "Run: playwright install chromium, or install Chrome first."
                ) from e

        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
            viewport={"width": 1440, "height": 900},
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Sec-CH-UA": '"Chromium";v="131", "Not_A Brand";v="24"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
            },
        )
        # 去除自动化特征：navigator.webdriver 必须为 false，chrome 对象得有
        self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN','zh','en'] });
            window.chrome = window.chrome || { runtime: {} };
        """)
        self._fetch_page: Any = None  # 懒加载

        self._img_key: str | None = None
        self._sub_key: str | None = None
        self._wbi_cache_time: float = 0.0
        self._request_count: int = 0
        self._last_request_time: float = 0.0

        if user_cookie:
            self._inject_cookie(user_cookie)

    # ── 生命周期 ────────────────────────────────────────────────
    def close(self) -> None:
        try:
            if self._fetch_page is not None and not self._fetch_page.is_closed():
                self._fetch_page.close()
        except Exception:
            pass
        try:
            self._context.close()
        except Exception:
            pass
        try:
            self._browser.close()
        except Exception:
            pass
        try:
            self._sync_pw.stop()
        except Exception:
            pass

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # ── 工具方法（对齐 BiliSession 同名接口） ───────────────────
    def _inject_cookie(self, cookie_str: str) -> None:
        cookies: list[dict] = []
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                key, val = item.split("=", 1)
                cookies.append({
                    "name": key.strip(),
                    "value": val.strip(),
                    "domain": ".bilibili.com",
                    "path": "/",
                })
        if cookies:
            self._context.add_cookies(cookies)

    def _rate_limit(self) -> None:
        self._request_count += 1
        # 基础间隔：2-4 秒（加大间隔，降低反爬触发概率）
        delay = random.uniform(2.0, 4.0)
        # 每 3 次请求额外加 3-6 秒
        if self._request_count % 3 == 0:
            delay += random.uniform(3.0, 6.0)
        elapsed = time.time() - self._last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request_time = time.time()
        # 每 15 次请求自动重建页面（刷新 cookie 和指纹）
        if self._request_count % 15 == 0 and self._fetch_page is not None:
            try:
                if not self._fetch_page.is_closed():
                    self._fetch_page.close()
            except Exception:
                pass
            self._fetch_page = None

    # ── 页面内 fetch（关键：绕过 412 的核心） ──────────────────
    def _ensure_fetch_page(self) -> Any:
        """确保有一个 bilibili.com 页面上下文供 fetch 执行。

        诊断验证：
        - wait_until="networkidle" 可确保 bilibili.com 首页相关的异步 JS 执行完成，
          buvid_fp 等风控 Cookie 正确生成。过早取 (domcontentloaded) 会导致 -352
        - 2~3 秒的等待让预取脚本 (prefetch JS) 落地 cookie
        """
        need_new = (
            self._fetch_page is None
            or self._fetch_page.is_closed()
            or getattr(self, "_force_new_page", False)
        )
        if need_new:
            self._fetch_page = self._context.new_page()
            # 打开 bilibili.com 主站，等网络稳定
            try:
                self._fetch_page.goto(
                    "https://www.bilibili.com/",
                    wait_until="networkidle",
                    timeout=30000,
                )
            except Exception:
                # 网络忙时 networkidle 可能超时，fallback 到 domcontentloaded
                try:
                    self._fetch_page.goto(
                        "https://www.bilibili.com/",
                        wait_until="domcontentloaded",
                        timeout=30000,
                    )
                except Exception:
                    pass
            # 等待 cookie 和预取 JS 充分落地 — 3 秒比 2 秒更稳
            time.sleep(3.0)
            # 验证 cookie 是否生成
            try:
                cookies = self._context.cookies()
                cookie_names = {c["name"] for c in cookies}
                if "buvid3" not in cookie_names:
                    # 关键 cookie 缺失，再等 2 秒
                    time.sleep(2.0)
            except Exception:
                pass
            self._force_new_page = False
        return self._fetch_page

    def _json_fetch(self, url: str, params: dict[str, Any], timeout: int) -> tuple[int, str]:
        """通过页面 window.fetch 发请求，返回 (status, body_text)。

        关键：headers 必须显式包含 Referer=https://www.bilibili.com/，
        这是真实浏览器访问 UP主 space 页时 API 请求的标准 Referer。
        """
        page = self._ensure_fetch_page()
        query = urllib.parse.urlencode(params, doseq=True)
        sep = "&" if "?" in url else "?"
        full_url = url + (sep + query if query else "")

        status, text = page.evaluate(
            """async ({fullUrl, timeoutMs}) => {
                const ctrl = new AbortController();
                const t = setTimeout(() => ctrl.abort(), timeoutMs);
                try {
                    const resp = await fetch(fullUrl, {
                        method: 'GET',
                        credentials: 'include',
                        signal: ctrl.signal,
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Referer': 'https://www.bilibili.com/',
                        },
                    });
                    clearTimeout(t);
                    return [resp.status, await resp.text()];
                } catch (err) {
                    clearTimeout(t);
                    return [0, String(err && err.message ? err.message : err)];
                }
            }""",
            {"fullUrl": full_url, "timeoutMs": timeout * 1000},
        )
        return int(status), str(text)

    def warm_up(self) -> None:
        """初始化：先打开 bilibili.com 拿 Cookie/buvid3 → nav 拿 WBI 密钥。"""
        # 确保 fetch_page 已生成（会自动打开 bilibili.com 首页）
        self._ensure_fetch_page()
        self._refresh_wbi_keys()

    def _refresh_wbi_keys(self) -> None:
        params = _add_dm_fingerprint({})
        status, body = self._json_fetch(
            "https://api.bilibili.com/x/web-interface/nav",
            params=params, timeout=15,
        )
        if status < 200 or status >= 400:
            raise RuntimeError(f"nav 请求失败 / nav request failed: HTTP {status}")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise RuntimeError(f"nav 返回非 JSON / nav non-JSON: {body[:200]}")
        if not data.get("data") or not data["data"].get("wbi_img"):
            raise RuntimeError(
                f"获取 WBI 密钥失败 / Failed to get WBI keys: "
                f"code={data.get('code')}, msg={data.get('message')}"
            )
        wbi_img = data["data"]["wbi_img"]
        self._img_key = wbi_img["img_url"].rsplit("/", 1)[1].split(".")[0]
        self._sub_key = wbi_img["sub_url"].rsplit("/", 1)[1].split(".")[0]
        self._wbi_cache_time = time.time()

    def _sign_params(self, params: dict[str, Any]) -> dict[str, Any]:
        if time.time() - self._wbi_cache_time > 3600:
            self._refresh_wbi_keys()
        assert self._img_key and self._sub_key
        params = _add_dm_fingerprint(params)
        return _enc_wbi(params, self._img_key, self._sub_key)

    def get(
        self, url: str, params: dict | None = None,
        signed: bool = False, timeout: int = 15,
    ) -> dict:
        """GET 请求（接口对齐 BiliSession.get）。"""
        self._rate_limit()
        if params is None:
            params = {}
        if signed:
            params = self._sign_params(params)
        else:
            params = _add_dm_fingerprint(params)

        try:
            status, body = self._json_fetch(url, params=params, timeout=timeout)
        except RuntimeError:
            raise
        except Exception as e:
            if "Timeout" in str(type(e).__name__) or "timeout" in str(e).lower():
                raise RuntimeError(f"请求超时 / Request timeout: {url}")
            raise RuntimeError(f"连接失败 / Connection failed ({type(e).__name__}): {e}")

        if status == 0:
            raise RuntimeError(f"请求未返回 / No response ({body[:200]}): {url}")

        # 解析 JSON，判断拦截
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            if status == 200 and ("<!DOCTYPE" in body or "<html" in (body[:100] if body else "")):
                raise RuntimeError(
                    "B站返回 HTML 拦截页（可能被反爬）/ "
                    "Bilibili returned HTML block page"
                )
            raise RuntimeError(f"非 JSON 响应 / Non-JSON response (HTTP {status}): {body[:200]}")

        code = data.get("code", -1)
        if code == -412:
            # 触发反爬 → 销毁旧页面、重新 warm up 刷新 cookie 后重试一次
            if not getattr(self, "_retry_on_412", False):
                self._retry_on_412 = True
                # 销毁 fetch_page，下次请求会重新打开 bilibili.com
                try:
                    if self._fetch_page is not None and not self._fetch_page.is_closed():
                        self._fetch_page.close()
                except Exception:
                    pass
                self._fetch_page = None
                self._request_count = 0  # 重置请求计数
                self._force_new_page = True
                # 冷却 5 秒再重试
                time.sleep(5.0)
                # 重新 warm up
                self.warm_up()
                # 用刷新后的 session 重试
                return self.get(url, params=params, signed=signed, timeout=timeout)
            else:
                self._retry_on_412 = False
                raise RuntimeError(
                    "B站反爬拦截 (412) / Bilibili anti-bot blocked request. "
                    "建议等待几分钟后重试，或切换到 Cookie 模式。"
                )
        if code == -352:
            raise RuntimeError("B站风控系统拦截 / Bilibili risk control blocked.")
        if code != 0:
            msg = data.get("message", "Unknown error")
            if code == -403:
                raise RuntimeError(
                    "该 UP 主需要登录才能查看视频列表 / "
                    "This UP requires login. 请切换到 Cookie 模式 / "
                    "Switch to Cookie mode and paste your Bilibili cookie."
                )
            if code == -404:
                raise RuntimeError(f"UID 不存在 / UID not found: {msg}")
            raise RuntimeError(f"API 错误 (code={code}) / API error: {msg}")
        return data


# ═══════════════════════════════════════════════════════════════════
# 抓取入口：自动选择模式（Playwright 优先，回退 Cookie）
# ═══════════════════════════════════════════════════════════════════

def fetch_up_full_data(
    mid: int,
    max_videos: int = 100,
    user_cookie: str = "",
    use_playwright: bool | None = None,
) -> tuple[UPInfo, pd.DataFrame]:
    """获取 UP 主全部数据。

    Args:
        mid: B站 UID
        max_videos: 最大视频数
        user_cookie: 浏览器 Cookie 字符串（requests 模式用；Playwright 模式可选）
        use_playwright:
            - True  → 强制用 Playwright（没装会报错）
            - False → 强制用 requests（配合 user_cookie）
            - None  → 自动：Playwright 可用就用，否则回退 requests+Cookie
    """
    # ── 决定用哪种 Session ──
    pw_available = is_playwright_available()
    if use_playwright is None:
        use_session_pw = pw_available
    else:
        use_session_pw = bool(use_playwright)
        if use_session_pw and not pw_available:
            raise RuntimeError(
                "选择了 Playwright 模式但未安装 / Playwright mode selected but not installed. "
                "请运行: pip install playwright && playwright install chromium"
            )

    session: BiliSession | PlaywrightBiliSession
    if use_session_pw:
        session = PlaywrightBiliSession(user_cookie=user_cookie)
    else:
        session = BiliSession(user_cookie=user_cookie)

    try:
        session.warm_up()
        time.sleep(2.0)

        # Step 1: 粉丝数（简单请求）
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

        time.sleep(2.0)

        # Step 2: 视频列表
        df, total_count = fetch_up_videos(session, mid, max_videos=max_videos)
        if total_count == 0 and not df.empty:
            total_count = len(df)

        time.sleep(2.0)

        # Step 3: UP 主信息
        info = UPInfo(mid=mid, name="", face="", sign="", level=0,
                       followers=followers, video_count=total_count)
        if not df.empty and "author" in df.columns:
            info.name = str(df["author"].iloc[0])
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
    finally:
        # Playwright 需要显式释放资源；requests 的 session 不用
        if isinstance(session, PlaywrightBiliSession):
            try:
                session.close()
            except Exception:
                pass


def quick_fetch(
    mid: int,
    max_videos: int = 100,
    user_cookie: str = "",
    use_playwright: bool | None = None,
) -> tuple[UPInfo, pd.DataFrame]:
    """便捷函数：快速获取指定 UP 主数据。

    use_playwright: None=自动, True=Playwright, False=requests+Cookie
    """
    return fetch_up_full_data(
        mid,
        max_videos=max_videos,
        user_cookie=user_cookie,
        use_playwright=use_playwright,
    )
