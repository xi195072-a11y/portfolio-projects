# Project 02 改为 B站 UP 主数据分析器 — 实施计划

## 调研结论

### B站 API 现状（2026 年）

1. **WBI 签名是硬要求**：`arc/search` 和 `acc/info` 接口必须带 `w_rid` + `wts` 参数
2. **正确的 MIXIN_KEY_ENC_TAB**：64 项重排表（从 bilibili-API-collect 官方文档确认）
3. **需要 cookie**：至少需要 `buvid3`（从首页访问获取），否则 412 风控
4. **需要过滤特殊字符**：参数中的 `!'()*` 必须过滤
5. **需要 `web_location`**：部分接口需要此参数
6. **`relation/stat` 接口无签名**：可直接获取粉丝数

### 之前失败的原因
- MIXIN_KEY_ENC_TAB 错误（多了 2 项）
- 未过滤 `!'()*` 字符
- 未使用 cookie 会话

### 技术方案
- 使用 `requests` 库（gradio 的依赖，已间接安装）做 HTTP 请求
- 实现正确的 WBI 签名
- 使用 `urllib.request.HTTPCookieProcessor` 管理 cookie
- 重写 `bilibili_api.py` 模块
- 重写 `app.py` 为 B站 UP 主分析仪表板

## 文件与模块

| 文件 | 操作 | 说明 |
|------|------|------|
| `02-social-media-analyzer/bilibili_api.py` | 重写 | 正确 WBI 签名 + cookie 会话 + 全量视频抓取 |
| `02-social-media-analyzer/app.py` | 重写 | B站 UP 主分析仪表板，漂亮布局 |
| `02-social-media-analyzer/requirements.txt` | 更新 | 加 `requests`、`plotly`、`pandas` 版本锁定 |
| `02-social-media-analyzer/README.md` | 重写 | B站 UP 主分析器说明 |
| `02-social-media-analyzer/.env.example` | 保留 | API key 示例 |
| 根目录 `README.md` | 更新 | Project 02 描述改为 B站 UP 主分析器 |

## 实施步骤

### 1. 修复 B站 API 客户端
- 修正 MIXIN_KEY_ENC_TAB（64 项）
- 实现 cookie 会话管理（先访问首页拿 buvid3）
- 实现正确的 WBI 签名（含 `!'()*` 过滤）
- 实现全量视频抓取（分页 + 礼貌延迟）
- 增加异常处理和重试

### 2. 测试 API
- 用影视飓风（UID: 946974）测试
- 验证能拿到用户信息 + 视频列表
- 验证数据字段完整（title/views/likes/favorites/comments）

### 3. 重写 App.py
- 单页面仪表板（不再分多 Tab，全在一页展示）
- 顶部：UP 主信息卡片（头像、昵称、粉丝数、视频数）
- 核心指标栏：总播放、总点赞、平均互动
- 中部：趋势图 + 平台/类型对比
- 底部：Top 10 热门视频 + 标签词频
- 输入区：UID 输入 + 加载示例按钮
- 双语 UI

### 4. 安装依赖 + 测试
- `pip install requests plotly pandas --target .packages`
- 启动 app.py
- 测试完整流程

### 5. 更新文档 + 推送
- 更新 README
- 截图
- Git commit + push

## 依赖与注意事项
- `requests` 需安装到本地 `.packages` 目录（沙箱限制）
- B站 API 限流：每次请求间隔 0.5 秒
- 数据仅供个人学习分析
- 示例 UP 主：影视飓风（UID: 946974）

## 验证
- API 能成功获取影视飓风的视频数据
- 仪表板能正确显示所有图表
- 无控制台错误
- README 截图正常

## 风险
- **B站风控升级**：如果仍被风控，备选方案是用 `curl_cffi` 做 TLS 指纹伪装（需额外安装）
- **API 字段变更**：B站可能随时更改 API 字段，需做好字段映射
- **网络问题**：国内访问 B站 API 在海外网络环境下可能受限
