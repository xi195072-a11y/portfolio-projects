# AGENTS.md - 02 项目：B 站 UP 主数据分析器

> 通用规则母版：`../knowledge-base/项目模板/AGENTS.md`
> 本项目只写特有规则，通用规则见母版

---

## 项目概述

**02-social-media-analyzer**：B 站 UP 主数据可视化分析工具

**核心价值**：
- 输入 B 站 UID，一键生成 UP 主数据分析仪表板
- 展示粉丝数、视频数、总播放量等核心指标
- 可视化图表：视频播放趋势、点赞评论分布、互动率
- 支持预设 UP 主快速切换 + 自定义 UID 搜索

**目标用户**：内容创作者、社媒运营人员、UP 主经纪人

---

## 项目特有技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| **Web 框架** | Streamlit 1.62 | 毛玻璃风格仪表板 |
| **数据源** | B 站 Web API | WBI 签名 + dm_img_* 画布指纹 |
| **数据处理** | Pandas | DataFrame 分析 |
| **可视化** | Plotly | 交互式图表 |
| **HTTP 客户端** | requests | 自实现 BiliSession |

> 其他通用技术栈见母版文件

---

## 02 项目结构

```
02-social-media-analyzer/
├── streamlit_app.py       # Streamlit 主入口（UI + 业务逻辑）
├── bilibili_api.py        # B 站 API 客户端（WBI 签名 + dm_img_*）
├── requirements.txt       # 依赖列表
├── AGENTS.md              # 本文件
├── 复盘记录.md            # 项目复盘
├── data/                  # JSON 缓存文件（按 UID 命名）
│   ├── up_946974.json     # 预设：影视飓风
│   ├── up_546195.json     # 预设：老番茄
│   └── up_37663924.json   # 预设：半佛仙人
├── .packages/             # 本地 Python 依赖（requests 等）
└── .streamlit/           # Streamlit 配置
```

---

## 02 特有规则

### B 站 API 调用
- **WBI 签名**：每次请求必须带 `w_rid` 参数（MIXIN_KEY_ENC_TAB + MD5）
- **dm_img_* 画布指纹**：所有请求必须带 `dm_img_*` 参数绕过 412 反爬
- **频率限制**：请求间隔 ≥ 2 秒，B 站 IP 级限流严格（可能几分钟）
- **错误处理**：412（反爬）→ 提示用户稍后重试；352（风控）→ 同样提示

### 缓存策略
- JSON 缓存优先，避免重复 API 调用
- 缓存 miss 时自动 fallback 到实时 API
- 实时成功后自动保存为 JSON 缓存（Timestamp/NaN 需序列化处理）
- 缓存文件命名：`up_{mid}.json`

### 侧边栏逻辑
- **预设模式**：radio 选择预设 UP 主 → 自动加载缓存
- **自定义模式**：number_input 输入 UID → 点击按钮才加载（避免每输入一位触发请求）
- 切换预设时触发 `mid_changed`，自动重新加载

### UI/UX 规则
- 毛玻璃风格（Glassmorphism）：blur + 半透明背景
- 双语 UI：所有文本中文 + English
- 字体颜色：--txt=#ffffff, --txt-2=#d4d8e0, --muted=#a8afba（确保深色背景可读）
- KPI 卡片：8 列布局，展示核心指标
- 图表：Plotly 交互式图表

### 数据序列化
- Timestamp 类型 → `.isoformat()` 字符串
- NaN/NaT → `None`
- 普通类型直接写入 JSON

### 浏览器测试规范
- **必须在 Chrome 中测试**：所有 UI 验证、功能测试、截图都使用 Chrome 浏览器
- **先检测再操作**：每次测试前先检查 Chrome 是否已打开目标页面
  - ✅ 已有目标页面 → 直接刷新（`browser_navigate` 同一 URL 或 `browser_wait_for` 触发 rerun）
  - ❌ 没有目标页面 → 新开标签页（`browser_navigate` 打开 URL）
- **测试后截图**：每次功能验证完毕必须截图并存档

### 避坑
1. B 站 API 返回的 `pubdate` 是 Unix 时间戳，需用 `pd.to_datetime()` 转换
2. `df.to_dict(orient="records")` 会把 Timestamp 转成字符串，但 NaN 会变成 `None`，需要额外处理
3. Streamlit session_state 在 widget key 变化时会重置，不要依赖复杂的 session_state 同步
4. 自定义 UID 模式不要自动触发加载（用户可能还在输入）

---

## 02 开发状态

- [x] B 站 API 客户端（WBI 签名 + dm_img_*）
- [x] Streamlit 毛玻璃 UI
- [x] 预设 UP 主缓存加载
- [x] 自定义 UID 实时获取 + 自动缓存
- [x] 错误提示（API 封锁时双语显示）
- [x] Plotly 交互式图表
- [ ] 扩展到其他平台（抖音/小红书）
- [ ] 定时数据更新
- [ ] AI 智能分析（趋势预测、竞品对比）

---

*Built with ❤️ and a lot of AI assistance.*
