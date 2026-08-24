---
title: Social Media Analyzer
emoji: 📊
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 6.19.0
app_file: app.py
pinned: false
---

# Social Media Analyzer / 社媒数据分析器

A web-based social media analytics dashboard for HK content creators and marketers. Upload data or connect APIs to get engagement insights, audience demographics, and content performance trends.

面向香港内容创作者和营销人员的社媒数据分析仪表板。上传数据或连接 API，获取互动洞察、受众画像和内容表现趋势。

## Features (功能)

- **Multi-platform Support**: Analyze data from Instagram, Facebook, X/Twitter, and more (支持多平台数据分析)
- **Engagement Analytics**: Like, share, comment, and click trends over time (互动数据分析)
- **Audience Insights**: Demographics, growth rate, and active time analysis (受众画像洞察)
- **Content Performance**: Top-performing posts and optimal posting times (内容表现分析)
- **Data Export**: Export reports as CSV or visual charts (数据导出)

## Tech Stack (技术栈)

- **Frontend**: Gradio (Python UI framework)
- **Data Processing**: Pandas
- **Visualization**: Plotly
- **Language**: Python 3.12+

## Installation (安装)

```bash
pip install -r requirements.txt
```

## Usage (使用)

```bash
# Set API keys (optional, for live data)
$env:TWITTER_API_KEY = "your-key"

# Run the app
python app.py
```

## Screenshots (截图)

> TODO: Add screenshots after initial implementation.

## Deployment (部署)

Deploy to HuggingFace Spaces:
1. Push to GitHub
2. Connect repo to HuggingFace Spaces
3. Select Gradio SDK

## Project Structure (项目结构)

```
├── app.py              # Main Gradio application
├── requirements.txt   # Dependencies
├── sample_data/        # Sample datasets for testing
└── README.md           # This file
```

## Author (作者)

小希
