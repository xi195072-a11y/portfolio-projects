"""
AI Copywriting Tool — Streamlit Web App (Glassmorphism UI)
AI 文案生成器 — 基于 Streamlit 的毛玻璃风格 Web 应用

Powered by DeepSeek API (OpenAI-compatible).
"""
from __future__ import annotations

import os
from typing import Optional

import streamlit as st
from openai import (
    OpenAI,
    AuthenticationError,
    RateLimitError,
    APIStatusError,
    APITimeoutError,
    APIConnectionError,
)

# ── 配置 / Configuration ──────────────────────────────────────────
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
MAX_TOPIC_LENGTH = 200

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """返回缓存的 DeepSeek 客户端。"""
    global _client
    if _client is None:
        api_key = os.environ.get(DEEPSEEK_API_KEY_ENV)
        if not api_key:
            raise RuntimeError(
                f"{DEEPSEEK_API_KEY_ENV} environment variable is not set. "
                f"Get your API key at: https://platform.deepseek.com/"
            )
        _client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    return _client


# ── UI 映射表 / UI Maps ───────────────────────────────────────────
tone_map = {
    "Professional / 专业": "professional",
    "Casual / 休闲": "casual",
    "Humorous / 幽默": "humorous",
    "Inspirational / 励志": "inspirational",
    "Urgent / 紧迫": "urgent",
}

# Token limits optimized for cost savings / 优化 token 上限以节省成本
length_map = {
    "Short / 短 (50-100 words)": ("50-100 words", 180),
    "Medium / 中 (100-200 words)": ("100-200 words", 350),
    "Long / 长 (200-300 words)": ("200-300 words", 550),
}

lang_map = {
    "中文 / Chinese": "Chinese",
    "English / 英文": "English",
    "粤语 / Cantonese": "Cantonese",
}


def _build_prompt(topic: str, tone_value: str, length_desc: str, lang_value: str) -> str:
    return (
        f'Write {tone_value} marketing copy about "{topic}" '
        f'in {lang_value}. Length: {length_desc}. '
        f'Include headline and CTA.'
    )


def generate_copy(topic: str, tone: str, length: str, language: str) -> str:
    """生成营销文案。"""
    if not topic or not topic.strip():
        return "Error: Topic is empty. / 错误：主题不能为空。"

    topic = topic.strip()
    if len(topic) > MAX_TOPIC_LENGTH:
        topic = topic[:MAX_TOPIC_LENGTH]

    tone_value = tone_map.get(tone, "professional")
    length_desc, max_tokens = length_map.get(length, ("100-200 words", 350))
    lang_value = lang_map.get(language, "Chinese")

    prompt = _build_prompt(topic, tone_value, length_desc, lang_value)

    # Check cache / 检查缓存
    cache_key = f"{topic}|{tone_value}|{length_desc}|{lang_value}"
    if "cache" not in st.session_state:
        st.session_state.cache = {}
    if cache_key in st.session_state.cache:
        return st.session_state.cache[cache_key]

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "Marketing copywriter."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_completion_tokens=max_tokens,
        )
        result = response.choices[0].message.content
        st.session_state.cache[cache_key] = result  # Save to cache / 保存到缓存
        return result
    except AuthenticationError:
        return "Error: Invalid DeepSeek API key. / 错误：API key 无效。"
    except RateLimitError:
        return "Error: Rate limit reached. Please wait and retry. / 错误：请求过于频繁，请稍后重试。"
    except APITimeoutError:
        return "Error: Request timed out. / 错误：请求超时。"
    except APIConnectionError:
        return "Error: Cannot connect to API. / 错误：无法连接服务。"
    except APIStatusError as e:
        return f"Error: Service error (HTTP {e.status_code}). / 错误：服务异常。"
    except Exception:
        return "Error: Unexpected error. Please retry. / 错误：未知错误。"


# ═══════════════════════════════════════════════════════════════════
# Glassmorphism Design System / 毛玻璃设计系统
# ═══════════════════════════════════════════════════════════════════
GLASS_CSS = """
<style>
:root {
    --bg: #0f1117;
    --txt: #ffffff;
    --txt-2: #e4e8f0;
    --muted: #b5bcc8;
    --accent: #818cf8;
    --accent-2: #c084fc;
    --pink: #f472b6;
    --cyan: #22d3ee;
    --r: 16px;
}

.stApp {
    background:
        radial-gradient(800px 500px at 10% 0%, rgba(99,102,241,0.15) 0%, transparent 55%),
        radial-gradient(700px 500px at 90% 10%, rgba(236,72,153,0.12) 0%, transparent 50%),
        radial-gradient(600px 400px at 50% 100%, rgba(6,182,212,0.08) 0%, transparent 50%),
        #0f1117;
}

/* 隐藏默认元素 */
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 900px; }

/* 字体 */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, 'Segoe UI', system-ui, sans-serif;
    color: var(--txt);
    -webkit-font-smoothing: antialiased;
}
h1, h2, h3 { color: var(--txt) !important; letter-spacing: -0.02em; }

/* 毛玻璃卡片核心样式 */
.glass {
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(20px) saturate(150%);
    -webkit-backdrop-filter: blur(20px) saturate(150%);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: var(--r);
    box-shadow: 0 8px 32px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.08);
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    animation: fadeUp 0.5s ease both;
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: none; }
}

/* 标题渐变 */
.gradient-title {
    background: linear-gradient(90deg, #818cf8, #c084fc, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
}

/* KPI 小卡片 */
.kpi-row { display: flex; gap: 0.7rem; margin-bottom: 1rem; }
.kpi-card {
    flex: 1;
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 0.8rem;
    text-align: center;
}
.kpi-card .label { font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }
.kpi-card .value { font-size: 1.1rem; font-weight: 700; color: var(--accent); margin-top: 0.3rem; }

/* Streamlit 组件覆盖 - 提高可读性 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label {
    color: #ffffff !important;
    font-weight: 600 !important;
}
.stTextInput [data-testid="stTextInput-label"],
.stTextArea [data-testid="stTextArea-label"] {
    color: #ffffff !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #8b8f9a !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(129,140,248,0.2) !important;
}
.stSelectbox > div > div > div[data-baseweb="select"] {
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    background: rgba(255,255,255,0.07) !important;
    color: #ffffff !important;
}
.stSelectbox [data-baseweb="select"] [aria-selected="true"] {
    color: #ffffff !important;
}
.stSelectbox ul {
    background: #1a1d26 !important;
    color: #ffffff !important;
}
.stMarkdown { color: #ffffff !important; }
.stMarkdown p, .stMarkdown li, .stMarkdown span { color: #e8eaed !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: #ffffff !important; }
.stMarkdown code { background: rgba(255,255,255,0.1) !important; color: #f472b6 !important; }

/* 按钮 */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.6rem 2rem !important;
    box-shadow: 0 4px 16px rgba(99,102,241,0.3) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(99,102,241,0.4) !important;
}

/* 侧边栏 */
section[data-testid="stSidebar"] {
    background: rgba(15,17,23,0.85) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}
section[data-testid="stSidebar"] .stMarkdown { color: #e8eaed !important; }
section[data-testid="stSidebar"] p { color: #d8dde6 !important; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4 { color: #ffffff !important; }
section[data-testid="stSidebar"] label { color: #ffffff !important; }
section[data-testid="stSidebar"] .stForm { color: #ffffff !important; }

/* st.success / st.warning 增强对比度 */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
}
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {
    color: #ffffff !important;
    font-weight: 500 !important;
}

/* 输出区 */
.output-box {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1.2rem;
    margin-top: 1rem;
    min-height: 120px;
}

/* 分割线 */
hr {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.08) !important;
    margin: 1.5rem 0 !important;
}
</style>
"""


def inject_glass_css():
    """注入毛玻璃 CSS。"""
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# Streamlit UI
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="AI Copywriting Tool / AI 文案生成器", page_icon="✍️", layout="centered")
inject_glass_css()

# ── 标题区 ────────────────────────────────────────────────────────
st.markdown("""
<div class="glass" style="text-align:center; padding:2rem 1.5rem;">
    <div style="font-size:2.5rem; margin-bottom:0.5rem;">✍️</div>
    <div class="gradient-title">AI Copywriting Tool</div>
    <div style="font-size:0.95rem; color:var(--txt-2); margin-top:0.3rem;">
        AI 文案生成器 · Powered by DeepSeek API
    </div>
    <div style="font-size:0.78rem; color:var(--muted); margin-top:0.5rem;">
        自定义语气 · 长度 · 语言 / Customizable Tone · Length · Language
    </div>
</div>
""", unsafe_allow_html=True)

# ── 侧边栏：API Key（不在界面上预显示） ─────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings / 设置")

    # 从环境变量读取
    saved_key = os.environ.get(DEEPSEEK_API_KEY_ENV, "")

    # st.text_input 在 rerun 时保留值，直接用
    api_key = st.text_input(
        "DeepSeek API Key",
        value="",
        type="password",
        placeholder="sk-... 粘贴你的 API Key",
        help="Key 仅存于本次会话中，不会硬编码 / Stored in session only",
    )

    # 只要输入框有值就设置到环境变量
    current_key = api_key or st.session_state.get("user_api_key", "") or saved_key
    if current_key:
        os.environ[DEEPSEEK_API_KEY_ENV] = current_key
        if api_key:
            st.session_state["user_api_key"] = api_key
        st.success("✅ Key 已就绪 / Key ready", icon="✅")
    else:
        st.warning("请输入 API Key / Enter API Key", icon="⚠️")

    st.markdown("---")
    st.markdown("#### 💡 Examples / 示例")
    examples = [
        ("📱 New iPhone launch", "Professional", "Medium", "English"),
        ("☕ Coffee shop opening", "Casual", "Short", "中文"),
        ("💪 Fitness app promotion", "Inspirational", "Long", "粤语"),
    ]
    for ex in examples:
        st.markdown(f"`{ex[0]}` · {ex[1]} · {ex[2]} · {ex[3]}")

# ── 主表单 ────────────────────────────────────────────────────────
st.markdown("""
<div class="glass">
""", unsafe_allow_html=True)

st.markdown("#### 📝 Create Copy / 创建文案")

# 用 form 包裹，确保所有输入在提交时一起传递
with st.form("copy_form"):
    topic = st.text_area(
        "Topic / Product (主题 / 产品)",
        placeholder="例如：New smartphone launch / 新手机发布会",
        height=70,
        help="Enter the product or topic you want copy for. / 输入产品或主题",
    )

    col1, col2 = st.columns(2)
    with col1:
        tone = st.selectbox("Tone (语气)", options=list(tone_map.keys()), index=0)
        language = st.selectbox("Language (语言)", options=list(lang_map.keys()), index=0)
    with col2:
        length = st.selectbox("Length (长度)", options=list(length_map.keys()), index=1)

    st.markdown("</div>", unsafe_allow_html=True)

    submitted = st.form_submit_button("🚀 Generate / 生成文案", use_container_width=True)

# form 外部处理结果
if submitted:
    if not os.environ.get(DEEPSEEK_API_KEY_ENV):
        st.error("Please enter your DeepSeek API Key in the sidebar. / 请在侧边栏输入 API Key。")
    elif not topic.strip():
        st.error("Please enter a topic. / 请输入主题。")
    else:
        with st.spinner("Generating... / 生成中..."):
            result = generate_copy(topic, tone, length, language)

        st.markdown("---")
        st.markdown("### 📋 Generated Copy / 生成的文案")
        st.markdown(f"""
        <div class="glass" style="min-height:150px;">
            <div style="white-space:pre-wrap; line-height:1.7; color:var(--txt);">
{result}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Copy button / 复制按钮
        st.code(result, language="text")
        st.caption(" Tip: Click the copy icon above to copy. / 点击上方复制图标即可复制。")

# ── 页脚 ──────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:1rem 0; color:var(--muted); font-size:0.75rem;">
    Built by 小希 · Powered by DeepSeek API · Streamlit + Glassmorphism UI
</div>
""", unsafe_allow_html=True)
