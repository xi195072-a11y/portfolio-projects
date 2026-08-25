# Portfolio Projects / 作品集

> 3 个实战项目 — AI 文案生成器、社媒数据分析器、自动化工作流引擎。
> Three hands-on projects: AI Copywriting Tool, Social Media Analyzer, Automation Workflow Engine.

---

## 项目一览 / Projects Overview

| # | 项目 | 目录 | 状态 | 技术栈 |
|---|------|------|------|--------|
| 01 | **AI 文案生成器** / AI Copywriting Tool | [`01-ai-copywriting-tool/`](./01-ai-copywriting-tool/) |  **已上线** [Live Demo](https://portfolio-projects-hhqpm6fcbqyatir4qxjxcc.streamlit.app/) | Python · Streamlit · DeepSeek API |
| 02 | **社媒数据分析器** / Social Media Analyzer | [`02-social-media-analyzer/`](./02-social-media-analyzer/) | 🟡 开发中 | Python · Pandas · Streamlit |
| 03 | **自动化工作流引擎** / Automation Workflow Engine | [`03-automation-workflow/`](./03-automation-workflow/) | 🔴 待开发 | Python · DeepSeek API |

---

## 项目详情 / Project Details

### 01 · AI 文案生成器 / AI Copywriting Tool

**Live Demo:** [https://portfolio-projects-hhqpm6fcbqyatir4qxjxcc.streamlit.app/](https://portfolio-projects-hhqpm6fcbqyatir4qxjxcc.streamlit.app/)

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
- **UI 框架**: Streamlit
- **AI API**: DeepSeek API (`deepseek-chat`)
- **部署**: Streamlit Cloud

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
streamlit run streamlit_app.py
```

---

## 开发文档 / Documentation

| 文件 | 用途 |
|------|------|
| `PROJECT_BRIEF.md` | 技术规范与代码标准（给 AI 和开发者看） |
| `PROJECT_PLAYBOOK.md` | 新项目启动章程（每次开新项目时按这个流程走） |
| `TRAE_INSTRUCTIONS.md` | AI 编程助手快速参考（Trae/Cursor 等工具读取） |

---

## 关于 / About

小希
MSc Chinese Environmental Studies, HKMU (2026-2027) · CS/Big Data 本科。

- GitHub: [@xi195072-a11y](https://github.com/xi195072-a11y)
- 方向: Data Analyst · AI Application Engineer · Tech Operations
