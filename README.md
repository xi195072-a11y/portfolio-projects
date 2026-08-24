# 香港科技岗求职作品集 / HK Tech Job Portfolio

> 为求职香港科技行业（数据分析师、AI 应用工程师、技术运营）而构建的 3 个实战项目。
> Three hands-on projects for Hong Kong tech job applications (Data Analyst, AI Application Engineer, Tech Operations).

---

## 项目一览 / Projects Overview

| # | 项目 | 目录 | 状态 | 技术栈 |
|---|------|------|------|--------|
| 01 | **AI 文案生成器** / AI Copywriting Tool | [`01-ai-copywriting-tool/`](./01-ai-copywriting-tool/) | ✅ 已完成 | Python · Gradio · DeepSeek API |
| 02 | **社媒数据分析器** / Social Media Analyzer | [`02-social-media-analyzer/`](./02-social-media-analyzer/) | 🔴 待开发 | Python · Pandas · Gradio |
| 03 | **自动化工作流引擎** / Automation Workflow Engine | [`03-automation-workflow/`](./03-automation-workflow/) | 🔴 待开发 | Python · Gradio · API 集成 |

---

## 项目详情 / Project Details

### 01 · AI 文案生成器 / AI Copywriting Tool

一个基于 DeepSeek API 的社媒营销文案生成工具，支持中/英/粤三语，可自定义语气、长度和语言。

A web-based AI copywriting tool that generates marketing copy for social media, supporting Chinese, English, and Cantonese with customizable tone, length, and language.

**亮点 / Highlights：**
- 🌏 三语支持（中文 / English / 粵語）
- 🎨 5 种语气（Professional / Casual / Humorous / Inspirational / Urgent）
- 📏 3 种长度（Short / Medium / Long）
- 💰 Token 用量优化，成本可控
- 🛡️ 完善的错误处理（认证错误 / 限流 / 超时）

**截图 / Screenshots：**

![Main UI](01-ai-copywriting-tool/screenshots/main-ui.png)

![Generated Output](01-ai-copywriting-tool/screenshots/generated-output.png)

---

## 技术栈 / Tech Stack

- **语言**: Python 3.12+
- **UI 框架**: Gradio
- **AI API**: DeepSeek API (`deepseek-chat`)
- **部署**: HuggingFace Spaces

---

## 快速开始 / Quick Start

```bash
# 克隆仓库
git clone https://github.com/xi195072-a11y/portfolio-projects.git

# 进入项目目录
cd 01-ai-copywriting-tool

# 安装依赖
pip install -r requirements.txt

# 设置 API Key
# Windows PowerShell:
$env:DEEPSEEK_API_KEY = "your-api-key-here"
# macOS/Linux:
# export DEEPSEEK_API_KEY="your-api-key-here"

# 运行
python app.py
```

---

## 关于作者 / About

钟嘉禧 (Zhong Jiaxi) — 香港科技岗求职者，专注数据与 AI 应用方向。
MSc Chinese Environmental Studies, HKMU (2026-2027) · CS/Big Data 本科。

- GitHub: [@xi195072-a11y](https://github.com/xi195072-a11y)
- 求职方向: Data Analyst · AI Application Engineer · Tech Operations
