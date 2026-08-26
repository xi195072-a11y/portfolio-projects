"""
Streamlit 启动器 —— 确保 .packages 在 PYTHONPATH 里
关键：设置环境变量 PYTHONPATH（不是 sys.path.insert），这样 Streamlit Runtime fork 的
子进程也能正确看到 .packages 里的依赖。
"""
import os
import sys
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGES_DIR = os.path.join(PROJECT_DIR, ".packages")

# ── 构造正确的子进程启动方式 ──
env = os.environ.copy()
existing_pp = env.get("PYTHONPATH", "")
entries = existing_pp.split(os.pathsep) if existing_pp else []
# 去重且保证优先级
if PACKAGES_DIR in entries:
    entries.remove(PACKAGES_DIR)
entries.insert(0, PACKAGES_DIR)
env["PYTHONPATH"] = os.pathsep.join(filter(None, entries))
# 把项目根目录也放进去（import bilibili_api / read_bilibili_cookies）
entries2 = env.get("PYTHONPATH", "").split(os.pathsep)
if PROJECT_DIR not in entries2:
    entries2.insert(0, PROJECT_DIR)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, entries2))

args = [
    sys.executable, "-m", "streamlit", "run",
    "streamlit_app.py",
    "--server.port", "8502",
    "--server.headless", "true",
]
os.chdir(PROJECT_DIR)
print(f"> Running: {' '.join(args)}")
print(f"> PYTHONPATH = {env['PYTHONPATH']}")
sys.exit(subprocess.call(args, env=env))
