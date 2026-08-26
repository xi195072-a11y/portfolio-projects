"""
从 Chrome 浏览器读取 Bilibili Cookie 的脚本。

使用方法:
    python read_bilibili_cookies.py              # 自动扫描所有 Profile
    python read_bilibili_cookies.py --profile 1  # 指定 Profile 编号
    python read_bilibili_cookies.py --close      # 提示用户关闭 Chrome 后读取

原理:
    1. 扫描所有 Chrome Profile 的 Cookies 数据库
    2. 从 Local State 文件读取并解密 AES-GCM 密钥
       - Chrome v80-v126: 密钥前缀 "v10" (3 字节) + DPAPI blob
       - Chrome v127+: 密钥前缀 "DPAPI" (4 字节) + 4 字节 flags + DPAPI blob
    3. 用 AES-256-GCM 解密每个 Cookie 值
    4. 输出格式: SESSDATA=xxx; bili_jct=xxx; buvid3=xxx
"""

from __future__ import annotations

import base64
import glob
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

# ── 配置：把 .packages 加入 sys.path ──────────────────────────────────
PACKAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".packages")
_win32_dir = os.path.join(PACKAGES_DIR, "win32")
_win32_lib_dir = os.path.join(_win32_dir, "lib")
_pythonwin_dir = os.path.join(PACKAGES_DIR, "pythonwin")
_pywin32_system32 = os.path.join(PACKAGES_DIR, "pywin32_system32")

for sub in [PACKAGES_DIR, _win32_dir, _win32_lib_dir, _pythonwin_dir, _pywin32_system32]:
    if sub not in sys.path:
        sys.path.insert(0, sub)

if os.path.isdir(_pywin32_system32):
    os.add_dll_directory(_pywin32_system32)
if os.path.isdir(_win32_dir):
    os.add_dll_directory(_win32_dir)

# ── DPAPI 解密 (使用 ctypes 直接调用，确保返回原始字节) ──────────────
import ctypes
import ctypes.wintypes

class _DataBlob(ctypes.Structure):
    _fields_ = [
        ('cbData', ctypes.wintypes.DWORD),
        ('pbData', ctypes.POINTER(ctypes.c_char))
    ]

def _crypt_unprotect_data(cipher_text: bytes, entropy: bytes = b"") -> bytes:
    """
    使用 DPAPI 解密数据（底层 ctypes 实现，确保返回原始字节）。
    
    与 win32crypt.CryptUnprotectData 不同，此函数始终返回 bytes。
    """
    blob_in = _DataBlob(len(cipher_text), ctypes.create_string_buffer(cipher_text))
    blob_entropy = _DataBlob(len(entropy), ctypes.create_string_buffer(entropy))
    blob_out = _DataBlob(0, ctypes.create_string_buffer(b""))
    
    desc = ctypes.c_wchar_p()
    CRYPTPROTECT_UI_FORBIDDEN = 0x01
    
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        ctypes.byref(desc),
        ctypes.byref(blob_entropy),
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(blob_out)
    ):
        raise RuntimeError('DPAPI 解密失败')
    
    # 复制输出数据
    buffer_out = ctypes.create_string_buffer(int(blob_out.cbData))
    ctypes.memmove(buffer_out, blob_out.pbData, int(blob_out.cbData))
    
    # 释放内存
    ctypes.windll.kernel32.LocalFree(desc)
    ctypes.windll.kernel32.LocalFree(blob_out.pbData)
    
    return buffer_out.raw

try:
    from Crypto.Cipher import AES  # pycryptodome
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ── 可选: browser_cookie3 (如果已安装) ────────────────────────────────
try:
    import browser_cookie3
    HAS_BROWSER_COOKIE3 = True
except ImportError:
    HAS_BROWSER_COOKIE3 = False

# ── 要提取的重要 Cookie 名称 ────────────────────────────────────────
IMPORTANT_COOKIES = [
    "SESSDATA",
    "bili_jct",
    "buvid3",
    "buvid4",
    "DedeUserID",
    "DedeUserID__ckMd5",
    "bili_ticket",
    "bili_ticket_expires",
    "__at_once",
    "b_nut",
]

# ── Chrome 相关路径 ────────────────────────────────────────────────
LOCAL_APP_DATA = os.environ.get("LOCALAPPDATA", "")
CHROME_USER_DATA = os.path.join(LOCAL_APP_DATA, "Google", "Chrome", "User Data")
CHROME_LOCAL_STATE = os.path.join(CHROME_USER_DATA, "Local State")


def find_all_cookie_dbs() -> list[tuple[str, str]]:
    """
    查找所有 Chrome Profile 的 Cookies 数据库。
    
    Returns:
        [(profile_name, cookies_db_path), ...]
    """
    results: list[tuple[str, str]] = []
    
    if not os.path.isdir(CHROME_USER_DATA):
        return results
    
    # 遍历所有 Profile 目录
    for name in os.listdir(CHROME_USER_DATA):
        path = os.path.join(CHROME_USER_DATA, name)
        if not os.path.isdir(path):
            continue
        
        # 检查 Cookies 文件（新旧两种路径）
        for sub in ["Network", ""]:
            cookie_file = os.path.join(path, sub, "Cookies")
            if os.path.isfile(cookie_file):
                results.append((name, cookie_file))
                break
    
    # 排序: Default 优先，然后 Profile 1, Profile 2, ...
    def sort_key(item):
        profile = item[0]
        if profile == "Default":
            return (0, 0)
        elif profile.startswith("Profile"):
            try:
                num = int(profile.split()[1])
                return (1, num)
            except (IndexError, ValueError):
                return (2, profile)
        else:
            return (3, profile)
    
    results.sort(key=sort_key)
    return results


def read_aes_key() -> bytes | None:
    """
    从 Chrome Local State 文件读取并解密 AES-GCM 密钥。
    
    支持两种格式:
    - Chrome v80-v126: "v10" (3 字节) + DPAPI blob
    - Chrome v127+: "DPAPI" (5 字节) + DPAPI blob
      (DPAPI 解密函数能自动处理 blob 前的额外数据)
    """
    if not os.path.exists(CHROME_LOCAL_STATE):
        return None

    try:
        with open(CHROME_LOCAL_STATE, "r", encoding="utf-8") as f:
            local_state = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    try:
        encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
    except KeyError:
        return None

    try:
        encrypted_key = base64.b64decode(encrypted_key_b64)
    except Exception:
        return None

    if len(encrypted_key) < 3:
        return None

    # 根据前缀确定偏移量
    if encrypted_key[:3] in (b"v10", b"v20"):
        # Chrome v80-v126: "v10" (3 字节) + DPAPI blob
        key_data = encrypted_key[3:]
    elif encrypted_key[:5] == b"DPAPI":
        # Chrome v127+: "DPAPI" (5 字节) + DPAPI blob
        # CryptUnprotectData 能自动处理 DPAPI blob 前的额外数据
        key_data = encrypted_key[5:]
    else:
        # 未知格式: 尝试整体解密
        key_data = encrypted_key

    try:
        return _crypt_unprotect_data(key_data)
    except Exception:
        return None


# ── Cookie 名称 → 正则表达式映射（用于从解密后的原始数据中提取值）───
# Chrome v127+ 解密后的明文结构: 35字节前缀 + Cookie值 + 尾部数据
# 使用正则表达式按 Cookie 名称智能提取
COOKIE_PATTERNS: dict[str, list[re.Pattern]] = {
    "SESSDATA": [
        # 长字符串: 字母数字 + _%-, 30+ 字符
        re.compile(rb'[A-Za-z0-9_%\-]{30,}'),
    ],
    "bili_jct": [
        # 短字符串: 字母数字，10-20 字符
        re.compile(rb'[A-Za-z0-9]{10,20}'),
    ],
    "buvid3": [
        # UUID 变体 + "infoc" 后缀 (Bilibili 格式，最后一段长度不固定)
        re.compile(rb'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4,}infoc'),
    ],
    "buvid4": [
        # UUID，可能带 URL 编码的后缀 (如 %3D%3D)，最后一段长度不固定
        re.compile(rb'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4,}[A-Za-z0-9%=_-]{0,30}'),
    ],
    "DedeUserID": [
        # 纯数字，5-10 位
        re.compile(rb'\d{5,10}'),
    ],
    "DedeUserID__ckMd5": [
        # 32 位十六进制 (MD5)
        re.compile(rb'[0-9a-fA-F]{32}'),
    ],
    # 其他有用的 Cookie
    "bili_ticket": [
        # JWT 格式: header.payload.signature
        re.compile(rb'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'),
    ],
    "bili_ticket_expires": [
        # Unix 时间戳 (10-13 位数字)
        re.compile(rb'\d{10,13}'),
    ],
    "__at_once": [
        # 字母数字混合 ID
        re.compile(rb'[A-Za-z0-9]{10,30}'),
    ],
    "b_nut": [
        # 纯数字 ID
        re.compile(rb'\d{10,20}'),
    ],
}


def _extract_value_by_cookie_name(decrypted: bytes, cookie_name: str) -> str:
    """
    根据 Cookie 名称，从解密后的原始字节中提取实际的 Cookie 值。
    
    Chrome v127+ 的 Cookie 解密后，明文结构为:
    - 35 字节前缀 (domain hash 或序列化元数据)
    - Cookie 值 (可变长度)
    - 尾部数据 (可能是完整性校验，可变长度)
    
    此函数使用预定义的正则表达式，按 Cookie 名称匹配提取值。
    
    Args:
        decrypted: AES-GCM 解密后的原始字节
        cookie_name: Cookie 名称 (如 "buvid3", "SESSDATA" 等)
    
    Returns:
        提取到的 Cookie 值字符串，提取失败返回空字符串
    """
    patterns = COOKIE_PATTERNS.get(cookie_name)
    if not patterns:
        # 没有预定义模式，尝试直接 UTF-8 解码
        try:
            return decrypted.decode("utf-8")
        except UnicodeDecodeError:
            # 尝试跳过 35 字节前缀
            if len(decrypted) > 35:
                try:
                    return decrypted[35:].decode("utf-8")
                except UnicodeDecodeError:
                    pass
            return ""

    # 尝试所有预定义的正则模式
    for pattern in patterns:
        match = pattern.search(decrypted)
        if match:
            try:
                return match.group(0).decode("utf-8")
            except UnicodeDecodeError:
                continue

    # 如果没有匹配，回退到直接解码（适用于旧版 Chrome 无前缀的情况）
    try:
        return decrypted.decode("utf-8")
    except UnicodeDecodeError:
        pass

    # 最后回退: 跳过 35 字节前缀后尝试解码
    if len(decrypted) > 35:
        try:
            return decrypted[35:].decode("utf-8")
        except UnicodeDecodeError:
            pass

    return ""


def decrypt_cookie_value(encrypted_value: bytes, aes_key: bytes | None, cookie_name: str = "") -> str:
    """
    解密 Cookie 值。
    
    加密格式:
    - v10/v20: 3 字节前缀 + 12 字节 IV + ciphertext + 16 字节 GCM tag
    - 旧格式: 直接 DPAPI 加密
    
    Chrome v127+ 解密后的明文包含前缀和尾部数据，需要根据 Cookie 名称
    使用正则表达式智能提取。
    
    Args:
        encrypted_value: 加密的 Cookie 值 (来自数据库的 encrypted_value 字段)
        aes_key: AES-256 密钥 (用于 v10/v20 格式解密)
        cookie_name: Cookie 名称 (用于智能提取值)
    
    Returns:
        解密后的 Cookie 值字符串，失败返回空字符串
    """
    if not encrypted_value:
        return ""

    # AES-GCM 加密 (Chrome 80+)
    if len(encrypted_value) > 3 and encrypted_value[:3] in (b"v10", b"v20"):
        if HAS_CRYPTO and aes_key:
            try:
                data = encrypted_value[3:]
                iv = data[:12]
                ciphertext_and_tag = data[12:]
                cipher = AES.new(aes_key, AES.MODE_GCM, nonce=iv)
                decrypted = cipher.decrypt(ciphertext_and_tag)
                # 使用正则表达式按 Cookie 名称提取实际值
                if cookie_name:
                    return _extract_value_by_cookie_name(decrypted, cookie_name)
                # 没有 cookie 名称时的回退处理
                try:
                    return decrypted.decode("utf-8")
                except UnicodeDecodeError:
                    if len(decrypted) > 35:
                        try:
                            return decrypted[35:].decode("utf-8")
                        except UnicodeDecodeError:
                            pass
                    return ""
            except Exception:
                pass

        # 回退: 尝试 DPAPI 整体解密
        try:
            result = _crypt_unprotect_data(encrypted_value)
            return result.decode("utf-8")
        except Exception:
            return ""

    # 旧格式: 直接 DPAPI 加密
    try:
        result = _crypt_unprotect_data(encrypted_value)
        return result.decode("utf-8")
    except Exception:
        # 可能是未加密的明文
        try:
            return encrypted_value.decode("utf-8")
        except Exception:
            return ""


def extract_bilibili_from_profile(profile_name: str, cookies_db: str, aes_key: bytes | None) -> dict[str, str]:
    """
    从指定 Profile 的 Cookies 数据库中提取 Bilibili Cookie。
    
    Args:
        profile_name: Profile 名称（如 "Default", "Profile 1"）
        cookies_db: Cookies 数据库文件路径
        aes_key: AES 密钥（用于解密 v10/v20 加密的 Cookie）
    
    Returns:
        {cookie_name: cookie_value}
    """
    cookies: dict[str, str] = {}
    
    # 复制数据库到临时文件（避免锁定冲突）
    tmp_dir = tempfile.mkdtemp(prefix="bili_cookie_")
    tmp_db = os.path.join(tmp_dir, "Cookies")
    
    try:
        shutil.copy2(cookies_db, tmp_db)
    except (PermissionError, OSError) as e:
        raise RuntimeError(f"无法复制 Cookies 数据库（Chrome 可能正在使用 Profile '{profile_name}'）: {e}")

    try:
        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()

        # 检查 cookies 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        if "cookies" not in tables:
            conn.close()
            return cookies

        # 查询 Bilibili 域名的 Cookie
        cursor.execute(
            "SELECT name, encrypted_value FROM cookies "
            "WHERE host_key LIKE '%bili%'"
        )
        rows = cursor.fetchall()

        for name, encrypted_value in rows:
            if name not in IMPORTANT_COOKIES and name not in COOKIE_PATTERNS:
                continue
            value = decrypt_cookie_value(encrypted_value, aes_key, cookie_name=name)
            if value:
                cookies[name] = value

        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"SQLite 查询失败: {e}")
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

    return cookies


def read_bilibili_cookies(profile: int | None = None) -> str:
    """
    从 Chrome 读取 Bilibili 相关 Cookie。
    
    Args:
        profile: Profile 编号（如 1 表示 "Profile 1"）。None = 自动扫描所有 Profile。
    
    Returns:
        格式化的 Cookie 字符串: "SESSDATA=xxx; bili_jct=xxx; buvid3=xxx; ..."
    """
    # 1. 查找所有 Profile 的 Cookies 数据库
    all_dbs = find_all_cookie_dbs()
    if not all_dbs:
        print("[错误] 找不到任何 Chrome Cookies 数据库")
        print(f"  路径: {CHROME_USER_DATA}")
        print("  请确认 Chrome 已安装")
        return ""

    # 如果指定了 profile 编号，只检查对应的 Profile
    if profile is not None:
        target = f"Profile {profile}"
        all_dbs = [(name, path) for name, path in all_dbs if name == target]
        if not all_dbs:
            print(f"[错误] 找不到 Profile '{target}'")
            print(f"  可用的 Profile: {[name for name, _ in find_all_cookie_dbs()]}")
            return ""

    print(f"[信息] 找到 {len(all_dbs)} 个 Chrome Profile:")
    for name, path in all_dbs:
        print(f"  - {name}: {path}")

    # 2. 读取 AES 密钥
    aes_key = read_aes_key()
    if aes_key:
        print(f"[信息] AES 密钥已获取 (长度: {len(aes_key)} 字节)")
    else:
        print("[警告] 无法获取 AES 密钥，将尝试 DPAPI 直接解密")

    # 3. 逐个 Profile 提取 Bilibili Cookie
    all_cookies: dict[str, str] = {}
    locked_profiles: list[str] = []

    for profile_name, cookies_db in all_dbs:
        print(f"\n[信息] 检查 Profile: {profile_name}")
        try:
            cookies = extract_bilibili_from_profile(profile_name, cookies_db, aes_key)
            if cookies:
                print(f"  [OK] 找到 {len(cookies)} 个 Bilibili Cookie:")
                for k, v in cookies.items():
                    display_val = v[:30] + "..." if len(v) > 30 else v
                    print(f"    {k} = {display_val}")
                all_cookies.update(cookies)
            else:
                print(f"  [--] 没有 Bilibili Cookie")
        except RuntimeError as e:
            print(f"  [LOCKED] 文件被锁定: {e}")
            locked_profiles.append(profile_name)

    # 4. 如果有锁定的 Profile，尝试用 browser_cookie3 重试
    if locked_profiles and HAS_BROWSER_COOKIE3:
        print(f"\n[信息] 尝试用 browser_cookie3 重试锁定的 Profiles...")
        for profile_name in locked_profiles:
            # 找到对应的 cookie 文件
            for name, path in all_dbs:
                if name == profile_name:
                    try:
                        cj = browser_cookie3.chrome(cookie_file=path)
                        bili_cookies = [c for c in cj if 'bilibili' in c.domain]
                        for c in bili_cookies:
                            if c.name in IMPORTANT_COOKIES and c.name not in all_cookies:
                                all_cookies[c.name] = c.value
                                print(f"  [OK] {c.name} = {c.value[:30]}")
                    except Exception as e:
                        print(f"  [FAIL] {profile_name}: {e}")
                    break

    # 5. 按重要性排序输出
    if not all_cookies:
        print("\n" + "=" * 60)
        print("[错误] 未能读取到任何 Bilibili Cookie")
        print("=" * 60)
        print("\n可能原因:")
        print("  1. 从未在 Chrome 中登录 Bilibili")
        print("  2. Cookie 已过期")
        print("  3. Bilibili Cookie 在其他 Profile 中（Chrome 正在运行导致锁定）")
        
        if locked_profiles:
            print(f"\n被锁定的 Profile: {', '.join(locked_profiles)}")
            print("  解决方法:")
            print("  a. 关闭 Chrome 浏览器后重试")
            print("  b. 以管理员身份运行此脚本 (可使用卷影复制)")
        
        print(f"\n  可用的 Profile: {[name for name, _ in all_dbs]}")
        return ""

    ordered_cookies = []
    for name in IMPORTANT_COOKIES:
        if name in all_cookies:
            ordered_cookies.append(f"{name}={all_cookies[name]}")

    cookie_str = "; ".join(ordered_cookies)
    print(f"\n[成功] 从 {len(ordered_cookies)} 个 Cookie 中提取到 {len(ordered_cookies)} 个有效 Cookie")
    return cookie_str


if __name__ == "__main__":
    import argparse
    import subprocess

    parser = argparse.ArgumentParser(
        description="从 Chrome 读取 Bilibili Cookie"
    )
    parser.add_argument(
        "--profile", "-p",
        type=int,
        default=None,
        help="指定 Profile 编号 (如 1 表示 Profile 1)，不指定则自动扫描所有 Profile",
    )
    parser.add_argument(
        "--close", "-c",
        action="store_true",
        help="提示用户关闭 Chrome 后再运行",
    )
    parser.add_argument(
        "--kill-chrome", "-k",
        action="store_true",
        help="自动关闭 Chrome 浏览器（保存 Cookie 后可重新打开）",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Bilibili Cookie 提取工具 (Chrome)")
    print("=" * 60)

    if args.close:
        input("\n请先关闭 Chrome 浏览器，然后按回车键继续...")
    
    if args.kill_chrome:
        print("\n[信息] 正在关闭 Chrome...")
        # 检查是否有 Chrome 进程
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq chrome.exe'],
                capture_output=True, text=True, timeout=5
            )
            if 'chrome.exe' in result.stdout.lower():
                print("  发现 Chrome 正在运行，尝试优雅关闭...")
                # 使用 taskkill 优雅关闭 Chrome
                subprocess.run(
                    ['taskkill', '/F', '/IM', 'chrome.exe'],
                    capture_output=True, text=True, timeout=10
                )
                import time
                time.sleep(2)  # 等待进程完全退出
                print("  Chrome 已关闭")
            else:
                print("  Chrome 未在运行")
        except Exception as e:
            print(f"  关闭 Chrome 失败: {e}")

    cookie_string = read_bilibili_cookies(profile=args.profile)

    if cookie_string:
        print("\n" + "=" * 60)
        print("  Cookie 字符串（可直接复制使用）:")
        print("=" * 60)
        print()
        print(cookie_string)
        print()
        print("=" * 60)
        print("  使用方法:")
        print("=" * 60)
        print()
        print(f'  from read_bilibili_cookies import read_bilibili_cookies')
        print(f'  cookie = read_bilibili_cookies()')
        print(f'  session = BiliSession(user_cookie=cookie)')
        
        if args.kill_chrome:
            input("\n按回车键重新打开 Chrome...")
            subprocess.Popen('chrome.exe', shell=True)
    else:
        print("\n[失败] 未能提取到 Cookie")
        sys.exit(1)