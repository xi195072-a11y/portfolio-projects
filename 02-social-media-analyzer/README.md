---
title: Bilibili Creator Data Analyzer
emoji: 📺
colorFrom: blue
colorTo: pink
sdk: streamlit
sdk_version: 1.62.0
app_file: streamlit_app.py
pinned: false
---

# B站 UP 主数据分析器 / Bilibili Creator Data Analyzer

A glassmorphism-style Streamlit dashboard for analyzing Bilibili UP main creators' video performance. Features real-time API fetching, pre-cached data, and multi-dimensional visualizations.

毛玻璃风格的 B 站 UP 主视频数据分析仪表板。支持实时 API 获取与预取缓存数据，提供多维度可视化分析。

## ✨ Features / 功能

- **📺 UP 主搜索**: 按 UID 查询 / 预设 UP 主一键切换（影视飓风、老番茄、半佛仙人、UID 2/3/4/14476927…）
- **🎯 两种抓取模式 / Two Fetch Modes**：
  - **🤖 自动模式（推荐）**：如果装了 Playwright，直接用「真实浏览器」搜，**无需登录 B站、无需复制 Cookie**
  - **🎭 Playwright 真实浏览器**：强制使用 Playwright（复用系统 Chrome，不用额外下浏览器）
  - **🍪 Cookie 模式（requests）**：走 requests 库 + SESSDATA，支持自动从 Chrome 读取 Cookie / 手动粘贴
- **📊 8 个 KPI 卡片**: 总播放量、粉丝数、视频总数、总评论、平均播放、最高单作、互动率、近 30 天播放
- **📈 5 个交互式图表**:
  - 播放量趋势（含 7 日均线）
  - Top 10 热门视频
  - 月度发布分布（双轴图）
  - 互动构成饼图
  - 发布时间热力图
- **💡 智能洞察**: 最佳发布时间、头部集中度、互动率水平、更新频率、近期趋势
- **📋 视频数据表**: 详细数据表格，支持滚动查看
- **⬇️ CSV 导出**: 一键导出全量数据
- **🎨 毛玻璃 UI**: Glassmorphism 深色主题
- **🌐 中英双语**: 所有界面文字均支持中英文对照

## 🔧 Data Source / 数据来源

- **默认**: 预取 JSON 文件（`data/` 目录），稳定可靠，不受 B 站反爬限制
- **Playwright 实时抓取（推荐）**: 用真实浏览器开 `bilibili.com` → 在页面上下文里 `fetch` API，带 `dm_img_*` 画布指纹 + WBI 签名，绕过 412 反爬。**全程匿名，不用登录，不用复制 Cookie**
- **Cookie 回退（requests + SESSDATA）**: 用账号登录态请求 B 站 API。Chrome 关闭时可自动读 Cookie DB，也可手动粘贴

## 🛠️ Tech Stack / 技术栈

| Layer | Technology |
|-------|-----------|
| UI | Streamlit 1.62 + Glassmorphism CSS |
| Charts | Plotly (5 种交互式图表) |
| Data | Pandas (数据处理) |
| API (Playwright) | Playwright（`add_init_script` 去自动化指纹 + 复用系统 Chrome + page.evaluate fetch）+ WBI 签名 + dm_img_* 画布指纹 |
| API (Cookie) | requests + SESSDATA + WBI 签名 + dm_img_* |
| Language | Python 3.10+ |

## 📂 Project Structure / 项目结构

```
02-social-media-analyzer/
├── streamlit_app.py        # Main Streamlit UI (Glassmorphism)
├── bilibili_api.py         # API client: BiliSession(requests) + PlaywrightBiliSession(复用系统Chrome)
├── read_bilibili_cookies.py # Chrome Cookie DB 读取器 (v127+ DPAPI/AES-GCM)
├── run_app.py              # 启动脚本：设置 PYTHONPATH -> python -m streamlit run ...
├── requirements.txt        # 依赖
├── data/                   # 预取缓存 JSON
│   ├── up_946974.json      # 影视飓风
│   ├── up_546195.json      # 老番茄
│   ├── up_37663924.json    # 半佛仙人
│   └── up_450542066.json   # 一琳琳琳琳零（22 条，Playwright 端到端验证通过）
└── .streamlit/config.toml  # Streamlit 配置
```

## 🚀 Quick Start / 快速开始

### 1) 安装依赖

```bash
cd 02-social-media-analyzer

# 方式 A（推荐，免 Cookie 直接搜）
pip install -r requirements.txt

# 方式 B（最小安装，没装 Playwright 也能跑——自动走 Cookie 模式）
pip install streamlit plotly pandas requests
```

> **Playwright 装完需要 `playwright install chromium` 吗？** 通常不需要。
> `PlaywrightBiliSession` 会自动探测你系统里已有的 Chrome / Edge / Chromium：
> - Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe` 、`%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe`、Edge 对应路径
> - macOS: `/Applications/Google Chrome.app`、Edge、Chromium
> - Linux: `google-chrome` / `chromium` / `chromium-browser`
>
> 只有**系统没装浏览器**时才需要：`playwright install chromium`

### 2) 运行

```bash
# 方式 1 — 用自带启动脚本（推荐，自动设置 PYTHONPATH）
python run_app.py

# 方式 2 — 直接 streamlit 命令
streamlit run streamlit_app.py --server.port 8502
```

浏览器打开 http://localhost:8502

### 3) 怎么用？

1. 侧边栏选「🤖 自动（推荐）」模式
2. 输入任意 B站 UID（例如 `450542066`）
3. 点「🚀 缓存分析」或「🌐 实时获取」
4. 出图！📊

> 如果 Playwright 没装，UI 会提示安装命令 `pip install playwright`，切到 🍪 Cookie 模式也能正常用。

## 🧪 已验证 / Verified

| 场景 | 结果 |
|---|---|
| Playwright headless=True，直接搜 UID 450542066 无 Cookie | ✅ 成功：UP「一琳琳琳琳零」，2136 粉丝，22 视频，14s 返回  |
| quick_fetch(450542066, use_playwright=True) 端到端 | ✅ code 0，无 412 / -352 |
| Cookie 模式回退（requests + SESSDATA）搜 UID 450542066 | ✅ 成功 |
| 预设切换 + 自定义 UID 输入保留 | ✅（修复了 session_state 死循环 bug） |
| Streamlit UI 无 st.stop() 导致的 React DOM removeChild 报错 | ✅（全部改为 if/elif/else 条件渲染） |

## 🔑 About B站反爬 / B站 Anti-Bot

本项目的 Playwright 绕过策略（`bilibili_api.py` `PlaywrightBiliSession`）：

1. **复用系统 Chrome**：找本地已装 Chrome/Edge，不用下载 Chromium for Testing
2. **去自动化指纹 init_script**：`navigator.webdriver→undefined`、补 `plugins/languages/window.chrome`
3. **启动参数**：`--disable-blink-features=AutomationControlled --no-sandbox`
4. **warm_up**：先 `goto("https://www.bilibili.com/", wait_until="networkidle")` + sleep 2s，等 `buvid3/buvid4/buvid_fp` 风控 Cookie 生成
5. **所有 API 请求都在页面上下文 `page.evaluate(fetch)`** 里发起，附带 `Referer: https://www.bilibili.com/`、`credentials: include`，保持真实浏览器的 Sec-Fetch 链
6. **WBI 签名 + `dm_img_*` 画布指纹**：和 requests 模式一致

## 📝 Author / 作者

小希 · GitHub: [@xi195072-a11y](https://github.com/xi195072-a11y)
