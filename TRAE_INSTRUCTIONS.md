# Trae Instructions — Read This Before Writing Any Code

> **IMPORTANT:** This file contains specific instructions for AI coding assistants (Trae, Copilot, etc.).
> Read this ENTIRE file before generating any code for this repository.

---

## Who You Are Helping

You are helping **Zhong Jiaxi** build 3 portfolio projects for Hong Kong tech job hunting.
He is a junior developer with CS background, currently studying Environmental Science at HKMU.
He needs these projects to be **interview-ready** — he must understand every line of code.

---

## Hard Rules (NEVER Break These)

1. **Python 3.12 only** — Do not use features from Python 3.13+
2. **DeepSeek API only** — Never use OpenAI. API base: `https://api.deepseek.com`, model: `deepseek-chat`
3. **English file/folder names only** — No Chinese characters in paths
4. **Pin all dependency versions** in `requirements.txt`
5. **Never commit API keys** — Use environment variables
6. **Bilingual comments** — English for logic, Chinese (中文) for complex explanations
7. **Lightweight dependencies** — Prefer standard library over heavy packages
8. **Windows compatible** — All code must run on Windows 10/11

---

## Current Project Status

### ✅ Project 01: AI Copywriting Tool (DeepSeek Integrated — Testing Phase)
- **Folder:** `01-ai-copywriting-tool/`
- **Files exist:** `app.py`, `requirements.txt`, `README.md`
- **What's done:**
  - Gradio UI scaffolded
  - DeepSeek API integrated (base_url + model `deepseek-chat` + `DEEPSEEK_API_KEY` env var)
  - `requirements.txt` pinned (`gradio==6.19.0`, `openai==3.3.1`)
  - README has HuggingFace Spaces frontmatter
  - `app.py` raises clear `RuntimeError` if `DEEPSEEK_API_KEY` is missing
- **What's needed:**
  - Test locally with Gradio (`python app.py`)
  - Deploy to HuggingFace Spaces

### 🔴 Project 02: Social Media Data Analyzer (Not Started)
- **Folder:** `02-social-media-analyzer/` (create when ready)
- **Goal:** Scrape social media → analyze → visualize → report
- **Reference:** Study `NanmiCoder/MediaCrawler` for scraping patterns
- **Your job:** Build a SIMPLIFIED version focused on competitor analysis

### 🔴 Project 03: Automation Workflow Engine (Not Started)
- **Folder:** `03-automation-workflow/` (create when ready)
- **Goal:** YAML-defined workflows with AI steps
- **Reference:** Study `n8n-io/n8n` and `prefecthq/prefect`
- **Your job:** Build a lightweight Python version, not a full n8n clone

---

## How to Write Code for This Repo

### When Adding a New Feature:
1. Read `PROJECT_BRIEF.md` first to understand the full context
2. Check existing code style — match it exactly
3. Write minimal, working code first
4. Add comments explaining WHY, not just WHAT
5. Update README if the feature changes user-facing behavior

### When Fixing a Bug:
1. Explain what the bug is in Chinese before fixing
2. Fix the bug
3. Explain what you changed and why

### When Creating a New File:
1. Add a docstring at the top explaining the file's purpose
2. Group imports: stdlib → third-party → local
3. Add type hints for function parameters and return values
4. Include a `if __name__ == "__main__":` block if it's a runnable script

---

## DeepSeek API Integration Pattern

This is the EXACT pattern to use for all DeepSeek API calls:

```python
import os
from openai import OpenAI

# DeepSeek is OpenAI-compatible, just change the base URL
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_input}
    ],
    temperature=0.7,
    max_tokens=1024
)

result = response.choices[0].message.content
```

**Key points:**
- Uses the `openai` Python package (DeepSeek is API-compatible)
- API key from `DEEPSEEK_API_KEY` environment variable
- Model name is `deepseek-chat`
- Base URL is `https://api.deepseek.com`

---

## HuggingFace Spaces Deployment Pattern

For Gradio apps, the deployment files needed:

```
project-folder/
── app.py              # Main Gradio app
── requirements.txt    # Dependencies
└── README.md           # HuggingFace will use this as the Space description
```

The `README.md` for HuggingFace Spaces needs this frontmatter:
```markdown
---
title: Your App Name
emoji: 
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: x.x.x
app_file: app.py
pinned: false
---
```

---

## Code Style Examples

### Good (Do This):
```python
"""
Data processor for social media posts.
Handles cleaning, transformation, and feature extraction.
社交媒体帖子数据处理器，负责清洗、转换和特征提取。
"""

import json
from pathlib import Path
from typing import List, Dict

import pandas as pd


def clean_posts(posts: List[Dict]) -> pd.DataFrame:
    """
    Remove duplicates and invalid entries from raw post data.
    去除重复和无效的帖子数据。
    
    Args:
        posts: List of raw post dictionaries from scraper
        
    Returns:
        Cleaned DataFrame with standardized columns
    """
    df = pd.DataFrame(posts)
    df = df.drop_duplicates(subset=["post_id"])
    df = df[df["content"].notna()]
    return df
```

### Bad (Don't Do This):
```python
# 这个函数处理数据
def process(data):
    # 去重
    data = list(set(data))
    # 返回
    return data
```

---

## What to Do Right Now

Project 01 DeepSeek integration is **complete**. Remaining steps:

1. Test locally: set `DEEPSEEK_API_KEY` env var, run `python app.py` (app starts at http://localhost:7860)
2. Deploy to HuggingFace Spaces:
   - Upload `app.py`, `requirements.txt`, `README.md`
   - Add `DEEPSEEK_API_KEY` as a Space secret (Settings → Secrets)

After Project 01 is deployed, move to Project 02.

---

## Questions to Ask Before Writing Code

If you're unsure about anything, ask these questions first:
1. Does this align with the project goals in `PROJECT_BRIEF.md`?
2. Can this run on Windows with Python 3.12?
3. Does this use DeepSeek (not OpenAI)?
4. Will the user understand this code in an interview?
5. Is this the simplest working solution?

If any answer is "no", reconsider your approach.
