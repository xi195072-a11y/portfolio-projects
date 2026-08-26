"""自动截图脚本 — 用 Playwright 截取两个 Streamlit 项目的界面

用法: python take_screenshots.py
依赖: playwright (已在 .packages 中)
"""
from __future__ import annotations

import os
import sys
import time

# 确保能 import 到 .packages 里的 playwright
_here = os.path.dirname(os.path.abspath(__file__))
_pkgs = os.path.join(_here, "02-social-media-analyzer", ".packages")
if os.path.isdir(_pkgs) and _pkgs not in sys.path:
    sys.path.insert(0, _pkgs)
# 也把 02 自身加进去（bilibili_api 可能需要）
_dir02 = os.path.join(_here, "02-social-media-analyzer")
if os.path.isdir(_dir02) and _dir02 not in sys.path:
    sys.path.insert(0, _dir02)

from playwright.sync_api import sync_playwright

# 配置
SHOT_TARGETS = [
    {
        "url": "http://localhost:8501",
        "save_to": os.path.join(_here, "01-ai-copywriting-tool", "screenshots", "main-ui.png"),
        "wait_selector": "text=AI Copywriting Tool",
        "label": "01 Copywriting Tool",
    },
    {
        "url": "http://localhost:8502",
        "save_to": os.path.join(_here, "01-ai-copywriting-tool", "screenshots", "main-ui.png"),  # placeholder, overwritten below
        "wait_selector": "text=UP主数据分析",
        "label": "02 Social Media Analyzer",
    },
]
# 修正 02 的路径
SHOT_TARGETS[1]["save_to"] = os.path.join(_here, "02-social-media-analyzer", "screenshots", "main-ui.png")

# 视口大小
VIEWPORT = {"width": 1280, "height": 900}


def find_chrome():
    """复用系统 Chrome，和 bilibili_api 里的 _find_system_chrome 保持一致。"""
    candidates = []
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

    if local_appdata:
        candidates.append(os.path.join(local_appdata, "Google", "Chrome", "Application", "chrome.exe"))
        candidates.append(os.path.join(local_appdata, "Microsoft", "Edge", "Application", "msedge.exe"))
    candidates.append(os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"))
    candidates.append(os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe"))
    candidates.append(os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"))
    candidates.append(os.path.join(program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"))

    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def take_screenshot(url: str, save_to: str, wait_selector: str, label: str):
    """打开 URL，等待渲染完成，截取全页面截图。"""
    print(f"\n📸 Taking screenshot: {label}")
    print(f"   URL: {url}")
    print(f"   Save: {save_to}")

    chrome_path = find_chrome()
    if chrome_path:
        print(f"   Using system Chrome: {chrome_path}")
    else:
        print("   System Chrome not found, using Playwright bundled browser")

    with sync_playwright() as pw:
        launch_args = ["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        launch_kwargs = {"headless": True, "args": launch_args}
        if chrome_path:
            launch_kwargs["executable_path"] = chrome_path

        browser = pw.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            viewport=VIEWPORT,
            locale="zh-CN",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            # 打开页面
            resp = page.goto(url, wait_until="networkidle", timeout=30000)
            print(f"   HTTP {resp.status}")

            # 等关键元素出现（Streamlit 动态渲染需要时间）
            try:
                page.wait_for_selector(wait_selector, timeout=15000)
                print(f"   Found: {wait_selector}")
            except Exception:
                print(f"   ⚠️  Selector not found (page may still be loading), waiting 3s...")

            # 额外等 2s 让动画/渲染完成
            time.sleep(2)

            # 截取全页面
            os.makedirs(os.path.dirname(save_to), exist_ok=True)
            page.screenshot(path=save_to, full_page=True)
            size_kb = os.path.getsize(save_to) / 1024
            print(f"   ✅ Saved: {save_to} ({size_kb:.0f} KB)")

        except Exception as e:
            print(f"   ❌ Error: {e}")
        finally:
            browser.close()


def main():
    print("=" * 50)
    print("📸 Auto Screenshot Tool for Portfolio Projects")
    print("=" * 50)

    # 确保目录存在
    for t in SHOT_TARGETS:
        d = os.path.dirname(t["save_to"])
        os.makedirs(d, exist_ok=True)

    for target in SHOT_TARGETS:
        take_screenshot(
            url=target["url"],
            save_to=target["save_to"],
            wait_selector=target["wait_selector"],
            label=target["label"],
        )

    print("\n" + "=" * 50)
    print("✅ All screenshots taken!")
    print("=" * 50)


if __name__ == "__main__":
    main()
