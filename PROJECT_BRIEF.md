# Portfolio Projects — Project Brief

> This document is the **single source of truth** for all development work in this repository.
> Every code change, new feature, or project addition MUST align with the specifications below.
> 阅读本文档后再开始任何编码工作。

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
| **Experience Level** | Junior / Entry-level with practical project experience |

---

## 2. Project Goals

### Primary Objective
Build **3 portfolio projects** that demonstrate practical skills for Hong Kong tech job hunting. Each project must:
- Be **deployable** (preferably on HuggingFace Spaces)
- Have a **professional README** with screenshots, architecture diagrams, and installation guide
- Show **real-world applicability** — not just tutorials, but something a company could actually use
- Be **original enough** to stand behind in an interview — you must understand every line of code

### Secondary Objective
Use these projects to **learn by doing**. Each project should push your skills slightly beyond your comfort zone.

---

## 3. Technical Constraints (MUST FOLLOW)

| Constraint | Specification |
|-----------|---------------|
| **Python Version** | 3.12 (installed via winget) |
| **OS** | Windows 10/11 |
| **Project Root** | `D:/projects/portfolio-projects/` |
| **API Provider** | **DeepSeek** (NOT OpenAI). API base: `https://api.deepseek.com`. Model: `deepseek-chat`. API key via `DEEPSEEK_API_KEY` env var. |
| **Deployment Target** | HuggingFace Spaces (free tier) |
| **Code Comments** | Bilingual — English for logic, Chinese for complex explanations |
| **File Naming** | English only, snake_case for Python files |
| **Dependencies** | Pin versions in `requirements.txt`. Prefer lightweight packages. |
| **Git** | One repo, multiple project folders. Clean commit messages. |

---

## 4. Project Specifications

### Project 01: AI Copywriting Tool
**Folder:** `01-ai-copywriting-tool/`
**Status:** 🟡 In Progress (scaffolded, needs DeepSeek integration)

**What it is:** A web-based tool that generates marketing/social media copy based on user input (topic, tone, length, language).

**Tech Stack:**
- Gradio (UI)
- DeepSeek API (LLM)
- Python 3.12

**Core Features:**
1. Input: topic/product, tone (professional/casual/humorous/inspirational/urgent), length (short/medium/long), language (Chinese/English/Cantonese)
2. Output: Generated marketing copy displayed in UI
3. Example templates for quick testing
4. Copy history (optional enhancement)

**Reference Project:** Study how Gradio demos are structured on HuggingFace Spaces. Look at `gradio-app/gradio` examples.

**What Makes It Yours:**
- DeepSeek instead of OpenAI (cost-effective, China-friendly)
- Cantonese support (unique for HK market)
- Social media focused (not generic copywriting)

**Deployment:** HuggingFace Spaces with Gradio template.

---

### Project 02: Social Media Data Analyzer
**Folder:** `02-social-media-analyzer/`
**Status:** 🔴 Not Started

**What it is:** A tool that scrapes social media posts (Xiaohongshu, Douyin, Bilibili), analyzes trends, and generates visual reports.

**Tech Stack:**
- Python (requests, BeautifulSoup, or MediaCrawler as reference)
- pandas (data processing)
- matplotlib / plotly / pyecharts (visualization)
- Gradio or Streamlit (UI for report viewing)

**Core Features:**
1. Scrape posts by keyword from 1-2 platforms (start with Xiaohongshu)
2. Clean and structure the data
3. Analyze: word frequency, engagement metrics, trend over time
4. Generate visual report: word cloud, bar charts, line charts
5. Export report as HTML or PDF

**Reference Project:** Study `NanmiCoder/MediaCrawler` (60K stars) for scraping patterns. Do NOT copy their code directly — understand the approach, then write your own simpler version.

**What Makes It Yours:**
- Focus on **competitor analysis** use case (not just generic scraping)
- Automated report generation (not just raw data)
- HK market perspective (analyze HK-related content)

**Deployment:** HuggingFace Spaces (may need to mock data for demo since scraping requires local environment).

---

### Project 03: Automation Workflow Engine
**Folder:** `03-automation-workflow/`
**Status:** 🔴 Not Started

**What it is:** A Python-based automation tool that orchestrates multi-step workflows — e.g., fetch data → process with AI → generate report → notify user.

**Tech Stack:**
- Python (asyncio, schedule)
- DeepSeek API (AI processing step)
- SQLite or JSON (data storage)
- Gradio or CLI (interface)

**Core Features:**
1. Define workflows as YAML/JSON config files
2. Execute workflows step by step (fetch → process → output)
3. Support common steps: HTTP request, AI call, file I/O, email/notification
4. Log execution results
5. Schedule recurring workflows (optional)

**Reference Project:** Study `n8n-io/n8n` (55K stars) for workflow concepts. Study `prefecthq/prefect` (17K stars) for Python-native workflow patterns. Build a **simplified** version — not a full n8n clone.

**What Makes It Yours:**
- YAML-based workflow definition (simple, readable)
- DeepSeek integration as a first-class step type
- Focus on content/marketing automation use cases
- Lightweight — no Docker required, runs with `python main.py`

**Deployment:** HuggingFace Spaces (demo mode with pre-built workflows).

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
- [ ] `README.md` — Project overview, features, tech stack, installation, usage, screenshots, architecture
- [ ] `requirements.txt` — Pinned dependencies
- [ ] `.gitignore` — Python, IDE, env files
- [ ] `app.py` or `main.py` — Entry point
- [ ] Clean folder structure (no flat file dumps)

### README Must Include:
1. **Project title and one-line description**
2. **Features** (bullet list)
3. **Tech Stack** (with logos if possible)
4. **Architecture Diagram** (can be ASCII or Mermaid)
5. **Installation** (step by step)
6. **Usage** (with screenshots)
7. **Project Structure** (file tree)
8. **How It Works** (brief technical explanation)
9. **Future Enhancements** (shows you think ahead)
10. **Author** (your name + GitHub link)

---

## 6. Development Workflow

### For Each New Project:
1. **Read this document** thoroughly
2. **Study the reference project** on GitHub (understand architecture, not copy code)
3. **Design your version** — what's different, what's simpler, what's better
4. **Build incrementally** — get a minimal version working first, then add features
5. **Write README as you go** — don't leave it for the end
6. **Test locally** before committing
7. **Commit with descriptive messages** — not "update", but "add DeepSeek API integration for copy generation"

### Git Commit Convention:
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
| **MediaCrawler** | 60K+ | Social media scraping patterns, multi-platform support | github.com/NanmiCoder/MediaCrawler |
| **Gradio** | 30K+ | Web UI for ML apps, deployment patterns | github.com/gradio-app/gradio |
| **Prefect** | 17K+ | Python-native workflow, task orchestration | github.com/prefecthq/prefect |

**Rule:** Study the architecture and design patterns. Write your own code. Do NOT copy-paste.

---

## 8. What NOT to Do

- ❌ Do NOT use OpenAI API (use DeepSeek)
- ❌ Do NOT create projects with Chinese file/folder names
- ❌ Do NOT leave `requirements.txt` without version pins
- ❌ Do NOT commit `.env` files with API keys
- ❌ Do NOT write code you can't explain in an interview
- ❌ Do NOT skip the README
- ❌ Do NOT build all 3 projects at once — finish one before starting the next

---

## 9. Interview Preparation Notes

For each project, be ready to answer:
1. **Why did you build this?** (real problem you wanted to solve)
2. **How does it work?** (architecture, data flow)
3. **What was the hardest part?** (technical challenge you overcame)
4. **What would you improve?** (shows self-awareness)
5. **How does this relate to the role?** (connect to job requirements)

---

## 10. Project Timeline

| Week | Milestone |
|------|-----------|
| Week 1 | Project 01: AI Copywriting Tool — complete, deployed |
| Week 2-3 | Project 02: Social Media Data Analyzer — complete, deployed |
| Week 4-5 | Project 03: Automation Workflow Engine — complete, deployed |
| Week 6 | Polish all READMEs, update CV, prepare interview answers |

---

*Last updated: 2026-08-24*
*This is a living document. Update it as projects evolve.*
