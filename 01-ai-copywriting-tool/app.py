"""
AI Copywriting Tool - Gradio Web App
Generates marketing copy based on topic, tone, and length preferences.
AI 文案生成器 - 基于 Gradio 的 Web 应用
根据主题、语气和长度偏好生成营销文案。

Powered by DeepSeek API (OpenAI-compatible).
"""

import os
import gradio as gr
from openai import OpenAI

# Initialize DeepSeek client
# DeepSeek API is OpenAI-compatible, just change base_url and model name
# DeepSeek 与 OpenAI API 兼容，只需修改 base_url 和模型名称
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", "your-api-key-here"),
    base_url="https://api.deepseek.com"
)


def generate_copy(topic, tone, length, language):
    """
    Generate marketing copy using DeepSeek API.
    使用 DeepSeek API 生成营销文案。
    
    Args:
        topic (str): The product/topic to write about (产品/主题)
        tone (str): Desired tone (语气: professional/casual/humorous/inspirational/urgent)
        length (str): Desired length (长度: short/medium/long)
        language (str): Output language (输出语言: Chinese/English/Cantonese)
    
    Returns:
        str: Generated marketing copy (生成的营销文案)
    """
    
    # Map length to word count (长度映射到字数)
    length_map = {
        "Short (50-100 words)": "50-100 words",
        "Medium (100-200 words)": "100-200 words",
        "Long (200-300 words)": "200-300 words"
    }
    
    # Map language to prompt language (语言映射)
    lang_map = {
        "Chinese (中文)": "Chinese",
        "English": "English",
        "Cantonese (粤语)": "Cantonese"
    }
    
    # Construct the prompt (构建提示词)
    prompt = f"""Write a marketing copy about "{topic}" with the following requirements:
- Tone: {tone}
- Length: {length_map[length]}
- Language: {lang_map[language]}

The copy should be engaging, persuasive, and suitable for social media platforms.
Include a catchy headline and call-to-action."""

    try:
        # Call DeepSeek API (调用 DeepSeek API)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional marketing copywriter with expertise in social media content. "
                               "你是一位专业的社交媒体营销文案撰写专家。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        error_msg = str(e)
        if "DEEPSEEK_API_KEY" in error_msg or "api_key" in error_msg.lower():
            return "Error: Please set the DEEPSEEK_API_KEY environment variable.\n错误：请设置 DEEPSEEK_API_KEY 环境变量。\n\nGet your API key at: https://platform.deepseek.com/"
        return f"Error: {error_msg}"


# Create Gradio interface (创建 Gradio 界面)
demo = gr.Interface(
    fn=generate_copy,
    inputs=[
        gr.Textbox(
            label="Topic / Product (主题/产品)",
            placeholder="e.g., New smartphone launch, Coffee shop opening, Fitness app",
            lines=2
        ),
        gr.Dropdown(
            choices=["Professional", "Casual", "Humorous", "Inspirational", "Urgent"],
            label="Tone (语气)",
            value="Professional"
        ),
        gr.Dropdown(
            choices=["Short (50-100 words)", "Medium (100-200 words)", "Long (200-300 words)"],
            label="Length (长度)",
            value="Medium (100-200 words)"
        ),
        gr.Dropdown(
            choices=["Chinese (中文)", "English", "Cantonese (粤语)"],
            label="Language (语言)",
            value="Chinese (中文)"
        )
    ],
    outputs=gr.Textbox(label="Generated Copy (生成的文案)", lines=10),
    title="AI Copywriting Tool (AI 文案生成器)",
    description="Generate marketing copy for social media with customizable tone, length, and language. "
                "Powered by DeepSeek API. 支持中文、英文、粤语，可自定义语气和长度。",
    examples=[
        ["New iPhone launch", "Professional", "Medium (100-200 words)", "English"],
        ["Coffee shop grand opening", "Casual", "Short (50-100 words)", "Chinese (中文)"],
        ["Fitness app promotion", "Inspirational", "Long (200-300 words)", "Cantonese (粤语)"],
        ["香港茶餐厅新品推广", "Casual", "Medium (100-200 words)", "Chinese (中文)"]
    ],
    allow_flagging="never"
)

if __name__ == "__main__":
    demo.launch(share=True)
