# AGENTS.md - 01 项目：三语社媒文案生成器

> 最后更新：2026-08-25
> 项目状态：已上线 [Live Demo](https://portfolio-projects-hhqpm6fcbqyatir4qxjxcc.streamlit.app/)

---

## 项目概述

**01-ai-copywriting-tool**：AI 驱动的三语（中/英/粤）社媒文案生成器

**核心价值**：
- 输入产品/主题，一键生成多平台文案（小红书/抖音/Twitter）
- 支持中文、英文、粤语三种语言
- 内置爆款文案模板和钩子库
- 实时预览和复制功能

**目标用户**：
- 跨境电商卖家
- 多语言内容创作者
- 社媒运营人员

---

## 技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| **编程语言** | Python 3.12 | 主力语言 |
| **LLM 大模型** | DeepSeek API | OpenAI 兼容接口 |
| **前端框架** | Streamlit | 快速搭建 Web 界面 |
| **部署平台** | Streamlit Cloud | 免费部署 |

---

## API 调用规则

### DeepSeek API
- **API Base**: `https://api.deepseek.com/v1`
- **Temperature**: 0.7（文案生成需要创意）
- **Max Tokens**: 
  - 短文案（标题/钩子）: 180
  - 中文案（正文）: 350
  - 长文案（完整帖子）: 550
- **缓存机制**: 相同输入不重复调用 API（节省成本）

### Prompt 设计规则
1. **上下文完整**：把参考文案的关键内容直接放入 prompt，别只给链接
2. **指令明确**：用"怎么做"替代"别做什么"
3. **任务原子化**：单次任务规模要小，每个 prompt 自成一体
4. **思维链**：复杂文案先生成大纲，再填充内容

---

## 产品思维规则

### 需求分析（八步框架）
1. 用户真实目标：快速生成能发布的多语言文案
2. 传统流程痛点：手动翻译慢、不同平台风格难把握
3. 最小上下文：产品名、目标平台、语言
4. 任务推进深度：L2（生成草稿，人工修改后发布）
5. 业务结果追踪：复制按钮点击率、用户停留时间
6. 错误恢复：生成不满意可重新生成
7. 数据优化：记录用户修改行为，优化 prompt
8. 差异化价值：三语支持 + 多平台模板

### 任务闭环
- 不是"AI 写文案"（单点功能）
- 而是"从输入主题到复制发布的全流程"（完整闭环）

---

## 代码规范

### Python 风格
- 遵循 PEP 8
- 函数/类必须写 docstring
- 类型提示（Type Hints）必须写

### 项目结构
```
01-ai-copywriting-tool/
├── app.py                 # Streamlit 主入口
├── requirements.txt       # 依赖
├── AGENTS.md             # 本文件（项目规则）
├── src/
│   ├── prompts/          # Prompt 模板
│   ├── api_client/       # DeepSeek API 调用
│   ── utils/            # 工具函数
└── tests/                # 测试
```

### UI/UX 规则
- **API Key 输入框**: Secrets 存在时只显示"已设置"，不填充输入框 value
- **复制按钮**: 每个文案块都要有复制按钮
- **加载状态**: API 调用时显示 loading 动画
- **错误提示**: API 失败时显示友好错误信息

---

## 部署规则

### Streamlit Cloud
- **账号**: xi195072-a11y
- **Secrets**: DEEPSEEK_API_KEY（必须配置）
- **URL**: https://portfolio-projects-hhqpm6fcbqyatir4qxjxcc.streamlit.app/

### 环境变量
```bash
DEEPSEEK_API_KEY=sk-xxx
```

---

## 避坑指南

### API 调用
1. 不要逐字流式输出，一次性生成完整文案（用户体验更好）
2. 相同输入必须缓存，避免重复扣费
3. Temperature 不要设太高（0.7 最佳），否则文案太飘

### 产品相关
1. 不要追求完美文案，让用户自己修改（L2 层级）
2. 复制按钮必须显眼，这是核心转化点
3. 免费额度用完要友好提示，不要直接报错

---

## 学习资源

### 内部知识库
- `../knowledge-base/博主笔记/宝玉-dotey.md` - 提示词"三点半"法则
- `../knowledge-base/博主笔记/熠辉-yihui_indie.md` - 工具栈和方法论
- `../knowledge-base/学习笔记/产品思维详解 - 从需求出发做 AI 产品.md` - 八步框架

---

*Built with ❤️ and a lot of AI assistance.*
