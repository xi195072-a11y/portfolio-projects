"""
AI Copywriting Tool - Streamlit Web App
Generates marketing copy based on topic, tone, and length preferences.
AI 文案生成器 - 基于 Streamlit 的 Web 应用
根据主题、语气和长度偏好生成营销文案。

Powered by DeepSeek API (OpenAI-compatible).
"""

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

# --- Configuration / 配置 ---
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
MAX_TOPIC_LENGTH = 200

# --- Lazy client init / 延迟初始化 client ---
_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Return a cached DeepSeek OpenAI-compatible client. / 返回缓存的 DeepSeek 客户端。"""
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


# --- UI display string -> prompt value + max output tokens ---
tone_map = {
    "Professional / 专业": "professional",
    "Casual / 休闲": "casual",
    "Humorous / 幽默": "humorous",
    "Inspirational / 励志": "inspirational",
    "Urgent / 紧迫": "urgent",
}

length_map = {
    "Short / 短 (50-100 words)": ("50-100 words", 250),
    "Medium / 中 (100-200 words)": ("100-200 words", 450),
    "Long / 长 (200-300 words)": ("200-300 words", 700),
}

lang_map = {
    "中文 / Chinese": "Chinese",
    "English / 英文": "English",
    "粤语 / Cantonese": "Cantonese",
}


def _build_prompt(topic: str, tone_value: str, length_desc: str, lang_value: str) -> str:
    """Build a compact prompt to minimize input tokens. / 构建紧凑提示词以最小化输入 token。"""
    return (
        f'Write {tone_value} marketing copy about "{topic}" '
        f'in {lang_value}. Length: {length_desc}. '
        f'Include a headline and call-to-action.'
    )


def generate_copy(topic: str, tone: str, length: str, language: str) -> str:
    """
    Generate marketing copy using DeepSeek API.
    使用 DeepSeek API 生成营销文案。
    """
    if not topic or not topic.strip():
        return "Error: Topic is empty. / 错误：主题不能为空。"

    topic = topic.strip()
    if len(topic) > MAX_TOPIC_LENGTH:
        topic = topic[:MAX_TOPIC_LENGTH]

    tone_value = tone_map.get(tone, "professional")
    length_desc, max_tokens = length_map.get(length, ("100-200 words", 450))
    lang_value = lang_map.get(language, "Chinese")

    prompt = _build_prompt(topic, tone_value, length_desc, lang_value)

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "You are a marketing copywriter for social media."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_completion_tokens=max_tokens,
        )
        return response.choices[0].message.content

    except AuthenticationError:
        return f"Error: Invalid DeepSeek API key. / 错误：API key 无效。"
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


# --- Streamlit UI / Streamlit 界面 ---
st.set_page_config(page_title="AI Copywriting Tool", page_icon="✍️", layout="centered")

st.title("️ AI Copywriting Tool / AI 文案生成器")
st.caption(
    "Generate marketing copy for social media with customizable tone, length, and language. "
    "Powered by DeepSeek API."
)

# Sidebar: API key input
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input(
        "DeepSeek API Key",
        value=os.environ.get(DEEPSEEK_API_KEY_ENV, ""),
        type="password",
        help="Get your key at https://platform.deepseek.com/",
    )
    if api_key:
        os.environ[DEEPSEEK_API_KEY_ENV] = api_key

# Main form
with st.form("copy_form", clear_on_submit=False):
    topic = st.text_area(
        "Topic / Product (主题/产品)",
        placeholder="例如：New smartphone launch / 新手机发布会；Coffee shop opening / 咖啡店开业",
        height=80,
    )
    col1, col2 = st.columns(2)
    with col1:
        tone = st.selectbox(
            "Tone (语气)",
            options=list(tone_map.keys()),
            index=0,
        )
        language = st.selectbox(
            "Language (语言)",
            options=list(lang_map.keys()),
            index=0,
        )
    with col2:
        length = st.selectbox(
            "Length (长度)",
            options=list(length_map.keys()),
            index=1,
        )

    submitted = st.form_submit_button("🚀 Generate Copy / 生成文案", use_container_width=True)

if submitted:
    if not os.environ.get(DEEPSEEK_API_KEY_ENV):
        st.error("Please enter your DeepSeek API Key in the sidebar. / 请在侧边栏输入 API Key。")
    else:
        with st.spinner("Generating... / 生成中..."):
            result = generate_copy(topic, tone, length, language)
        st.markdown("### Generated Copy / 生成的文案")
        st.text_area("", value=result, height=200, label_visibility="collapsed")

# Examples section
st.markdown("---")
st.markdown("### 💡 Examples / 示例")
examples = [
    ("New iPhone launch", "Professional / 专业", "Medium / 中 (100-200 words)", "English / 英文"),
    ("Coffee shop grand opening", "Casual / 休闲", "Short / 短 (50-100 words)", "中文 / Chinese"),
    ("Fitness app promotion", "Inspirational / 励志", "Long / 长 (200-300 words)", "粤语 / Cantonese"),
]
for ex_topic, ex_tone, ex_length, ex_lang in examples:
    st.markdown(f"- **{ex_topic}** | {ex_tone} | {ex_length} | {ex_lang}")

# Footer
st.markdown("---")
st.markdown(
    "Built by [Jiaxi Zhong](https://github.com/xi195072-a11y) | "
    "Powered by DeepSeek API"
)
