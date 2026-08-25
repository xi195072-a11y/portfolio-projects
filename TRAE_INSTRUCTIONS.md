# AI Coding Assistant Instructions

> **IMPORTANT:** Read `PROJECT_BRIEF.md` and `PROJECT_PLAYBOOK.md` BEFORE writing any code.
> This file only contains AI-specific quick reference. For full specs, see the other two files.

---

## Quick Reference

### Hard Rules
1. **Python 3.12 only** — No 3.13+ features
2. **DeepSeek API only** — Never use OpenAI
3. **English file/folder names only** — No Chinese in paths
4. **Pin all dependency versions** in `requirements.txt`
5. **Never commit API keys** — Use environment variables
6. **Bilingual comments** — English for logic, Chinese for complex explanations
7. **Windows compatible** — All code must run on Windows 10/11

### DeepSeek API Pattern
```python
import os
from openai import OpenAI

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
```

### HuggingFace Spaces README Frontmatter
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

## Current Project Status

### ✅ Project 01: AI Copywriting Tool
- **Folder:** `01-ai-copywriting-tool/`
- **Status:** DeepSeek integrated, testing phase
- **Next:** Test locally → Deploy to HuggingFace Spaces

### 🔴 Project 02: Social Media Data Analyzer
- **Folder:** `02-social-media-analyzer/`
- **Status:** Not started

### 🔴 Project 03: Automation Workflow Engine
- **Folder:** `03-automation-workflow/`
- **Status:** Not started

---

## Before Writing Code — Checklist

1. Does this align with `PROJECT_BRIEF.md`?
2. Can this run on Windows with Python 3.12?
3. Does this use DeepSeek (not OpenAI)?
4. Will the user understand this code in an interview?
5. Is this the simplest working solution?

If any answer is "no", reconsider your approach.

---

## When Adding a New Feature
1. Read `PROJECT_BRIEF.md` for full context
2. Check existing code style — match it exactly
3. Write minimal, working code first
4. Add comments explaining WHY, not just WHAT
5. Update README if the feature changes user-facing behavior

## When Fixing a Bug
1. Explain what the bug is in Chinese before fixing
2. Fix the bug
3. Explain what you changed and why
