# AGENTS.md - 02 项目：社媒数据分析与可视化

> 本项目继承根目录 AGENTS.md 的通用规则
> 以下是项目特有规则

---

## 项目概述

**02-social-media-analyzer**：AI 驱动的社媒数据分析与可视化工具

**核心价值**：
- 自动抓取竞品社媒数据（抖音/小红书/微博）
- AI 分析趋势、亮点、问题
- 生成可视化报告
- 定时推送日报

**目标用户**：中小企业主、市场运营人员

---

## 项目特有技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| **AI 框架** | LangChain 0.3.x | Agent + RAG 编排 |
| **向量数据库** | ChromaDB | 本地轻量 |
| **Embedding 模型** | BAAI/bge-small-zh-v1.5 | 中文效果好 |
| **数据抓取** | Playwright | 浏览器自动化 |

> 其他通用技术栈见根目录 AGENTS.md

---

## 02 项目结构

```
02-social-media-analyzer/
├── app.py                 # Streamlit 主入口
├── requirements.txt       # 依赖
├── AGENTS.md             # 本文件
├── 复盘记录.md            # 项目复盘（自动更新）
── src/
│   ├── crawler/          # 数据抓取模块（Playwright）
│   ├── analyzer/         # AI 分析模块（LangChain + DeepSeek）
│   ├── rag/              # RAG 知识库模块（ChromaDB）
│   └── reporter/         # 报告生成模块
├── data/                 # 数据存储（SQLite）
├── chroma_db/            # 向量数据库
└── tests/                # 测试
```

---

## 02 特有规则

### 数据抓取
- 优先抓公开数据，不登录不抓私有内容
- 每次抓取间隔 ≥ 3 秒，避免被封
- 抓取失败自动重试 2 次，再失败记录日志跳过

### 分析 Prompt 模板
- 分析方法论：趋势分析 + 亮点提取 + 问题诊断 + 建议
- 输出格式：结构化 Markdown，可直接渲染为报告
- 温度：0.1（分析需要确定性）

### MVP 范围
- **第一版只做**: 输入竞品账号 → 抓取 7 天数据 → AI 生成报告 → 显示图表
- **以后再加**: 定时抓取、多平台对比、自动推送、用户系统

---

## 02 开发计划

### 第 1 周：数据抓取
- [ ] 用 Playwright 抓取竞品数据
- [ ] 存储到 SQLite 数据库
- [ ] 测试数据质量

### 第 2 周：AI 分析
- [ ] 用 DeepSeek API 分析数据
- [ ] 设计 prompt（分析方法论）
- [ ] 生成文字报告

### 第 3 周：前端界面
- [ ] 用 Streamlit 搭建界面
- [ ] 显示数据表格和图表
- [ ] 添加交互功能

### 第 4 周：测试部署
- [ ] 功能测试、修复 bug
- [ ] 部署到 Streamlit Cloud
- [ ] 写 README 文档

---

*Built with ❤️ and a lot of AI assistance.*
