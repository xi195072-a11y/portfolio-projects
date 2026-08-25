# AGENTS.md - 02 项目：社媒数据分析与可视化

> 最后更新：2026-08-25
> 项目状态：开发中

---

## 项目概述

**02-social-media-analyzer**：AI 驱动的社媒数据分析与可视化工具

**核心价值**：
- 自动抓取竞品社媒数据（抖音/小红书/微博）
- AI 分析趋势、亮点、问题
- 生成可视化报告
- 定时推送日报

**目标用户**：
- 中小企业主、市场运营人员
- 需要快速了解竞品动态，节省人工分析时间

---

## 技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| **编程语言** | Python 3.12 | 主力语言 |
| **AI 框架** | LangChain 0.3.x | Agent + RAG 编排 |
| **向量数据库** | ChromaDB | 本地轻量，开发阶段够用 |
| **Embedding 模型** | BAAI/bge-small-zh-v1.5 | 中文效果好，本地运行免费 |
| **LLM 大模型** | DeepSeek API | OpenAI 兼容接口 |
| **前端框架** | Streamlit | 快速搭建 Web 界面 |
| **数据抓取** | Playwright | 浏览器自动化 |
| **部署平台** | Streamlit Cloud | 免费部署 |

---

## RAG 实现规则

### 文档处理
- **chunk_size**: 500-800 字符（中文场景）
- **chunk_overlap**: 10%-20%（50-100 字符）
- **分隔符优先级**: `\n\n` → `\n` → `。` → `!` → `?` → ` ` → `""`

### 向量存储
- **数据库**: ChromaDB（开发）→ Milvus（生产）
- **持久化路径**: `./chroma_db`
- **Embedding 模型**: `BAAI/bge-small-zh-v1.5`（本地 CPU 运行）

### 检索策略
- **默认 k 值**: 3-5（过多引入噪声）
- **混合检索**: 向量检索（70%）+ BM25 关键词检索（30%）
- **重排序**: 使用 `BAAI/bge-reranker-large` 对召回结果重排

### 拒答机制（防幻觉）
```python
prompt = "基于以下上下文回答问题。如果上下文没有相关信息，请回答'抱歉，知识库中未找到相关信息'。\n\n上下文:\n{context}\n\n问题: {question}\n\n回答:"
```

---

## Agent 开发规则

### 工具调用
- **协议**: 优先使用 MCP 协议（Model Context Protocol）
- **工具描述**: 必须编写详尽的文档字符串，这是模型理解工具用途的唯一依据
- **权限控制**: 最小权限原则，敏感操作（删除/支付）必须人工确认

### 工作流设计
1. **感知层**: 接收用户指令，理解意图
2. **规划层**: 拆解任务为子步骤
3. **执行层**: 调用工具（抓取/分析/生成）
4. **记忆层**: 存储历史操作和用户偏好

### 错误处理
- **重试机制**: 失败自动重试 1-2 次
- **降级策略**: API 限流时切换到备用模型
- **人工介入**: 高风险操作暂停等待确认

---

## 产品思维规则

### 需求分析（八步框架）
1. 用户真实目标是什么？（不是"想要 AI"，而是"想要解决 XX 问题"）
2. 传统流程痛点在哪？
3. 最小且合法的上下文需求是什么？
4. 任务推进深度选哪层？（L1 建议 → L4 全自动）
5. 怎么追踪业务结果？
6. 错误恢复机制怎么设计？
7. 数据怎么优化？
8. 差异化价值是什么？

### MVP 策略
- **第一版只做**: 输入竞品账号 → 抓取 7 天数据 → AI 生成报告 → 显示图表
- **以后再加**: 定时抓取、多平台对比、自动推送、用户系统

### 任务闭环
- 不是"AI 分析数据"（单点功能）
- 而是"从数据抓取到报告推送的全流程自动化"（完整闭环）

---

## 代码规范

### Python 风格
- 遵循 PEP 8
- 函数/类必须写 docstring
- 类型提示（Type Hints）必须写

### 项目结构
```
02-social-media-analyzer/
├── app.py                 # Streamlit 主入口
├── requirements.txt       # 依赖
├── AGENTS.md             # 本文件（项目规则）
├── src/
│   ├── crawler/          # 数据抓取模块
│   ├── analyzer/         # AI 分析模块
│   ├── rag/              # RAG 知识库模块
│   └── reporter/         # 报告生成模块
├── data/                 # 数据存储
├── chroma_db/            # 向量数据库
└── tests/                # 测试
```

### API 调用规范
- **DeepSeek API Base**: `https://api.deepseek.com/v1`
- **Temperature**: 0.1（分析任务需要确定性）
- **Max Tokens**: Short 180 / Medium 350 / Long 550
- **缓存机制**: 相同输入不重复调用 API

---

## 部署规则

### Streamlit Cloud
- **账号**: xi195072-a11y
- **Secrets**: DEEPSEEK_API_KEY（必须配置）
- **API Key 输入框**: Secrets 存在时只显示"已设置"，不填充输入框 value

### 环境变量
```bash
DEEPSEEK_API_KEY=sk-xxx
CHROMA_DB_PATH=./chroma_db
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

---

## 避坑指南

### RAG 相关
1. 文档入库不能只做一次，必须做增量更新
2. 分片不是越小越精准，500-800 字符最佳
3. 不能只用向量搜索，必须混合检索
4. 接入 RAG 后仍会产生幻觉，必须配置拒答机制

### Agent 相关
1. 工具描述模糊会导致模型误判
2. 上下文溢出会撑爆模型窗口，必须截断或摘要
3. 多个工具功能相似会干扰决策，需严格划分边界
4. 忽视输入参数校验会引发注入攻击

### 产品相关
1. 不要从技术出发，要从用户需求出发
2. 不要追求大而全，先做 MVP 验证
3. 高风险操作必须保留人工审核
4. 不追踪数据就不知道哪里好哪里差

---

## 学习资源

### 内部知识库
- `../knowledge-base/学习笔记/RAG 技术详解 - 给 AI 加知识库.md`
- `../knowledge-base/学习笔记/Agent 开发详解 - 让 AI 能调用工具.md`
- `../knowledge-base/学习笔记/产品思维详解 - 从需求出发做 AI 产品.md`
- `../knowledge-base/学习笔记/LangChain-RAG 企业知识库实战代码.md`
- `../knowledge-base/学习笔记/Coze 扣子-Dify 平台对比研究.md`

### 外部参考
- LangChain 官方文档：https://python.langchain.com/
- ChromaDB 官方教程：https://docs.trychroma.com/
- DeepSeek API 文档：https://platform.deepseek.com/

---

## 开发计划

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
