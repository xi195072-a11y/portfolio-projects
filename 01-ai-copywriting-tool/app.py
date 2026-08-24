"""
AI Copywriting Tool - Gradio Web App
Generates marketing copy based on topic, tone, and length preferences.
AI 文案生成器 - 基于 Gradio 的 Web 应用
根据主题、语气和长度偏好生成营销文案。

Powered by DeepSeek API (OpenAI-compatible).
"""

import os
from typing import Optional

import gradio as gr
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

# Truncate long topics to avoid prompt overflow / 截断过长主题避免 prompt 超限
MAX_TOPIC_LENGTH = 200

# --- Lazy client init / 延迟初始化 client ---
# Avoid module-level failure when API key is missing (e.g. during import for tests)
# 避免 import 时因缺少 API key 报错（便于单元测试导入模块）
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
# UI 显示文字 -> 提示词值 + 最大输出 token 数
tone_map = {
    "Professional / 专业": "professional",
    "Casual / 休闲": "casual",
    "Humorous / 幽默": "humorous",
    "Inspirational / 励志": "inspirational",
    "Urgent / 紧迫": "urgent",
}

# Each length maps to (prompt description, max_completion_tokens).
# 每种长度映射到 (提示词描述, 最大输出 token 数)
# Token limits calibrated to cover the upper word count + headline + CTA buffer.
# Token 上限按字数上限 + 标题 + CTA 缓冲设定（避免截断，不浪费调用次数）
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

    Args:
        topic: The product/topic to write about (产品/主题)
        tone: Desired tone, UI display value (语气 UI 显示值)
        length: Desired length, UI display value (长度 UI 显示值)
        language: Output language, UI display value (输出语言 UI 显示值)

    Returns:
        Generated marketing copy, or a user-friendly error message.
        生成的营销文案，或用户友好的错误提示。
    """
    # --- Input validation (before API call, saves tokens) ---
    # 输入校验（在调用 API 前做，避免浪费 token）
    if not topic or not topic.strip():
        return "Error: Topic is empty. / 错误：主题不能为空。"

    topic = topic.strip()
    if len(topic) > MAX_TOPIC_LENGTH:
        # Truncate instead of rejecting (still useful for the user)
        # 截断而非拒绝（对用户仍有用）
        topic = topic[:MAX_TOPIC_LENGTH]

    # Resolve UI values to prompt-friendly strings
    # 把 UI 显示值解析为提示词用的字符串
    tone_value = tone_map.get(tone, "professional")
    length_desc, max_tokens = length_map.get(length, ("100-200 words", 450))
    lang_value = lang_map.get(language, "Chinese")

    prompt = _build_prompt(topic, tone_value, length_desc, lang_value)

    try:
        client = _get_client()
        # max_completion_tokens is the openai 3.x parameter name (replaces max_tokens)
        # max_completion_tokens 是 openai 3.x 的新参数名（替代 max_tokens）
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a marketing copywriter for social media.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_completion_tokens=max_tokens,
        )
        return response.choices[0].message.content

    except AuthenticationError:
        return (
            f"Error: Invalid DeepSeek API key. / 错误：API key 无效。\n"
            f"Please check the {DEEPSEEK_API_KEY_ENV} environment variable."
        )
    except RateLimitError:
        # Do NOT auto-retry — would double token consumption.
        # 不自动重试 —— 会翻倍消耗 token
        return (
            "Error: DeepSeek rate limit reached. / 错误：请求过于频繁。\n"
            "Please wait a few seconds and try again. / 请稍后重试。"
        )
    except APITimeoutError:
        return "Error: Request timed out. / 错误：请求超时，请检查网络后重试。"
    except APIConnectionError:
        return "Error: Cannot connect to DeepSeek API. / 错误：无法连接 DeepSeek 服务。"
    except APIStatusError as e:
        # Server-side error (5xx). Do not leak response body.
        # 服务端错误，不泄漏响应体
        return f"Error: DeepSeek service error (HTTP {e.status_code}). / 错误：DeepSeek 服务异常。"
    except Exception:
        # Catch-all: do not leak internal details to users.
        # 兜底处理：不向用户泄漏内部信息
        return "Error: Unexpected error. Please retry. / 错误：未知错误，请重试。"


# --- Gradio interface / Gradio 界面 ---
demo = gr.Interface(
    fn=generate_copy,
    inputs=[
        gr.Textbox(
            label="Topic / Product (主题/产品)",
            placeholder="例如：New smartphone launch / 新手机发布会；Coffee shop opening / 咖啡店开业",
            lines=2,
            max_lines=3,
        ),
        gr.Dropdown(
            choices=list(tone_map.keys()),
            label="Tone (语气)",
            value="Professional / 专业",
        ),
        gr.Dropdown(
            choices=list(length_map.keys()),
            label="Length (长度)",
            value="Medium / 中 (100-200 words)",
        ),
        gr.Dropdown(
            choices=list(lang_map.keys()),
            label="Language (语言)",
            value="中文 / Chinese",
        ),
    ],
    outputs=gr.Textbox(label="Generated Copy / 生成的文案", lines=10),
    title="AI Copywriting Tool / AI 文案生成器",
    description=(
        "Generate marketing copy for social media with customizable tone, length, and language. "
        "Powered by DeepSeek API. / 生成社媒营销文案，支持自定义语气、长度、语言（中文/英文/粤语）。"
    ),
    examples=[
        ["New iPhone launch / 新款 iPhone 发布", "Professional / 专业", "Medium / 中 (100-200 words)", "English / 英文"],
        ["Coffee shop grand opening / 咖啡店盛大开业", "Casual / 休闲", "Short / 短 (50-100 words)", "中文 / Chinese"],
        ["Fitness app promotion / 健身 App 推广", "Inspirational / 励志", "Long / 长 (200-300 words)", "粤语 / Cantonese"],
        ["香港茶餐厅新品推广", "Casual / 休闲", "Medium / 中 (100-200 words)", "中文 / Chinese"],
    ],
    flagging_mode="never",
)

if __name__ == "__main__":
    # share=False: local development only, no public tunnel.
    # share=False：仅本地访问，不开公网链接（HF Spaces 部署时会自动处理）
    demo.launch(share=False)
