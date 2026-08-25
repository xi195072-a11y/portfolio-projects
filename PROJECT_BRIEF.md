# Portfolio Projects — Project Brief

> This document is the **technical specification and code standard** for this repository.
> For development workflow, see `PROJECT_PLAYBOOK.md`.
> 阅读本文档了解技术规范，阅读 PROJECT_PLAYBOOK.md 了解开发流程。

---

## 1. Developer Profile

| Item | Detail |
|------|--------|
| **Name** | Zhong Jiaxi (钟嘉禧) |
| **GitHub** | [@xi195072-a11y](https://github.com/xi195072-a11y) |
| **Education** | MSc Chinese Environmental Studies, HKMU (2026-2027) |
| **Background** | CS/Big Data undergrad, Associate Degree in Computer Application |
| **Target Roles** | Data Analyst, AI Application Engineer, Tech Operations |
| **Target Market** | Hong Kong tech industry |

---

## 2. Project Goals

Build **3 portfolio projects** that demonstrate practical skills for Hong Kong tech job hunting. Each project must:
- Be **deployable** (preferably on HuggingFace Spaces)
- Have a **professional README** with screenshots, architecture diagrams, and installation guide
- Show **real-world applicability** — not just tutorials, but something a company could actually use
- Be **original enough** to stand behind in an interview — you must understand every line of code

---

## 3. Technical Constraints (MUST FOLLOW)

| Constraint | Specification |
|-----------|---------------|
| **Python Version** | 3.12 |
| **OS** | Windows 10/11 |
| **Project Root** | `D:/projects/portfolio-projects/` |
| **API Provider** | **DeepSeek** (NOT OpenAI). API base: `https://api.deepseek.com`. Model: `deepseek-chat`. API key via `DEEPSEEK_API_KEY` env var. |
| **Deployment Target** | HuggingFace Spaces (free tier) |
| **Code Comments** | Bilingual — English for logic, Chinese for complex explanations |
| **File Naming** | English only, snake_case for Python files |
| **Dependencies** | Pin versions in `requirements.txt`. Prefer lightweight packages. |
| **Git** | One repo, multiple project folders. Clean commit messages. |

### Tool Chain（工具链）

| Role | Tool | Purpose |
|------|------|---------|
| **AI Coding** | Trae | Reads PROJECT_BRIEF.md + TRAE_INSTRUCTIONS.md, writes code in project folders |
| **Daily Assistant** | 千问办公 | Research, documentation, analysis, learning notes |
| **Knowledge Base** | Obsidian | Learning notes, project retrospectives, blogger insights, interview prep. Local: `D:/projects/knowledge-base/`, GitHub: `xi195072-a11y/knowledge-base` |
| **LLM API** | DeepSeek | AI capabilities in project code |
| **Version Control** | GitHub | Code hosting + portfolio showcase |

> Tool chain philosophy (from 熠辉): Keep it simple. One tool for coding, one for knowledge, one for ideas. No bloat.

---

## 4. Project Specifications

### Project 01: AI Copywriting Tool
**Folder:** `01-ai-copywriting-tool/`
**Status:** ✅ Completed (testing phase)

A web-based tool that generates marketing/social media copy based on user input.

**Tech Stack:** Gradio + DeepSeek API + Python 3.12

**Core Features:**
- Input: topic/product, tone, length, language (Chinese/English/Cantonese)
- Output: Generated marketing copy
- Cantonese support (unique for HK market)

---

### Project 02: Social Media Data Analyzer
**Folder:** `02-social-media-analyzer/`
**Status:** 🔴 Not Started

A tool that scrapes social media posts, analyzes trends, and generates visual reports.

**Tech Stack:** Python (requests/BeautifulSoup) + pandas + matplotlib/plotly + Gradio

**Core Features:**
- Scrape posts by keyword from 1-2 platforms
- Clean and structure data
- Analyze: word frequency, engagement metrics, trend over time
- Generate visual report: word cloud, bar charts, line charts
- Export report as HTML or PDF

**Reference:** Study `NanmiCoder/MediaCrawler` for scraping patterns. Build a SIMPLIFIED version.

**What Makes It Yours:** Focus on competitor analysis use case, automated report generation, HK market perspective.

---

### Project 03: Automation Workflow Engine
**Folder:** `03-automation-workflow/`
**Status:** 🔴 Not Started

A Python-based automation tool that orchestrates multi-step workflows.

**Tech Stack:** Python (asyncio/schedule) + DeepSeek API + SQLite/JSON + Gradio or CLI

**Core Features:**
- Define workflows as YAML/JSON config files
- Execute workflows step by step (fetch → process → output)
- Support common steps: HTTP request, AI call, file I/O
- Log execution results

**Reference:** Study `n8n-io/n8n` and `prefecthq/prefect`. Build a **simplified** version.

**What Makes It Yours:** YAML-based workflow definition, DeepSeek integration, lightweight (no Docker required).

---

## 5. Code Quality Standards

### Every Python File Must Have:
```python
"""
Brief description of what this file does.
"""

# Imports at the top, grouped by:
# 1. Standard library
# 2. Third-party packages
# 3. Local modules

# Constants in UPPER_CASE
# Functions with docstrings
# Type hints where helpful
```

### Every Project Must Have:
- `README.md` — Project overview, features, tech stack, installation, usage, screenshots
- `requirements.txt` — Pinned dependencies
- `.gitignore` — Python, IDE, env files
- `app.py` or `main.py` — Entry point
- Clean folder structure (no flat file dumps)

### README Must Include:
1. Project title and one-line description
2. Features (bullet list)
3. Tech Stack
4. Architecture Diagram (ASCII or Mermaid)
5. Installation (step by step)
6. Usage (with screenshots)
7. Project Structure (file tree)
8. How It Works (brief technical explanation)
9. Future Enhancements
10. Author (your name + GitHub link)

---

## 6. Git Commit Convention

```
<type>: <short description>

Examples:
feat: add DeepSeek API integration
fix: resolve Gradio layout issue on mobile
docs: update README with architecture diagram
refactor: simplify data processing pipeline
```

---

## 7. Reference Projects to Study

| Project | Stars | What to Learn | URL |
|---------|-------|---------------|-----|
| **n8n** | 55K+ | Workflow orchestration, node-based design | github.com/n8n-io/n8n |
| **Dify** | 90K+ | LLM app platform, RAG, agent编排 | github.com/langgenius/dify |
| **Flowise** | 36K+ | Visual AI agent builder, LangChain integration | github.com/FlowiseAI/Flowise |
| **MediaCrawler** | 60K+ | Social media scraping patterns | github.com/NanmiCoder/MediaCrawler |
| **Gradio** | 30K+ | Web UI for ML apps, deployment patterns | github.com/gradio-app/gradio |
| **Prefect** | 17K+ | Python-native workflow, task orchestration | github.com/prefecthq/prefect |

**Rule:** Study the architecture and design patterns. Write your own code. Do NOT copy-paste.

---

## 8. Interview Preparation Notes

For each project, be ready to answer:
1. **Why did you build this?** (real problem you wanted to solve)
2. **How does it work?** (architecture, data flow)
3. **What was the hardest part?** (technical challenge you overcame)
4. **What would you improve?** (shows self-awareness)
5. **How does this relate to the role?** (connect to job requirements)

---

*Last updated: 2026-08-25*
*This is a living document. Update it as projects evolve.*
