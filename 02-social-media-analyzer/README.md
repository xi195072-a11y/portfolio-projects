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

- **📺 UP 主搜索**: 按 UID 查询 / 3 位预设 UP 主一键切换（影视飓风、老番茄、半佛仙人）
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
- **🎨 毛玻璃 UI**: Glassmorphism 深色主题，基于高星 GitHub 模板设计
- **🌐 中英双语**: 所有界面文字均支持中英文对照

## 🔧 Data Source / 数据来源

- **默认**: 预取 JSON 文件（`data/` 目录），稳定可靠，不受 B 站反爬限制
- **可选**: 实时 B 站 API（使用 `dm_img_*` 画布指纹 + WBI 签名绕过 412 反爬）

## 🛠️ Tech Stack / 技术栈

| Layer | Technology |
|-------|-----------|
| UI | Streamlit 1.62 + Glassmorphism CSS |
| Charts | Plotly (5 种交互式图表) |
| Data | Pandas (数据处理) |
| API | requests + WBI 签名 + dm_img_* 画布指纹 |
| Language | Python 3.12+ |

## 📂 Project Structure / 项目结构

```
02-social-media-analyzer/
├── streamlit_app.py    # Main Streamlit app (Glassmorphism UI)
├── bilibili_api.py     # B站 API client (WBI签名 + dm_img_*)
├── data/               # Pre-fetched JSON data
│   ├── up_946974.json   # 影视飓风 (30 videos, 17.2M followers)
│   ├── up_546195.json   # 老番茄 (30 videos, 20.7M followers)
│   └── up_37663924.json # 半佛仙人 (30 videos, 7.7M followers)
├── .streamlit/         # Streamlit config
│   └── config.toml
├── .packages/          # Local Python packages (streamlit, plotly, requests)
└── README.md
```

## 🚀 Quick Start / 快速开始

```bash
# 安装依赖（如果需要）
pip install streamlit plotly pandas requests --target ".packages"

# 运行应用
cd 02-social-media-analyzer
streamlit run streamlit_app.py --server.port 8502
```

打开浏览器访问 http://localhost:8502

## 📸 Screenshots / 截图

> 待更新 — 本地测试中

## 🔑 About B站反爬 / B站 Anti-Bot

本项目使用以下技术绕过 B 站 412 反爬检测：

1. **WBI 签名算法**: MIXIN_KEY_ENC_TAB 重排 + MD5 签名
2. **dm_img_* 画布指纹**: 4 个 JS 生成的指纹参数
3. **requests 库**: 更好的 TLS 指纹

注意：连续多个请求可能被限流，建议使用预取数据。

## 📝 Author / 作者

小希 · GitHub: [@xi195072-a11y](https://github.com/xi195072-a11y)
