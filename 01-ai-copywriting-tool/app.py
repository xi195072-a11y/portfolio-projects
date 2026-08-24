"""
AI Copywriting Tool - Gradio Web App
Generates marketing copy based on topic, tone, and length preferences.
"""

import gradio as gr
import os
from openai import OpenAI

# Initialize OpenAI client (uses OPENAI_API_KEY environment variable)
client = OpenAI()

def generate_copy(topic, tone, length, language):
    """
    Generate marketing copy using OpenAI API
    
    Args:
        topic (str): The product/topic to write about
        tone (str): Desired tone (professional, casual, humorous, etc.)
        length (str): Desired length (short, medium, long)
        language (str): Output language (Chinese, English, Cantonese)
    
    Returns:
        str: Generated marketing copy
    """
    
    # Map length to word count
    length_map = {
        "Short (50-100 words)": "50-100 words",
        "Medium (100-200 words)": "100-200 words",
        "Long (200-300 words)": "200-300 words"
    }
    
    # Map language to prompt language
    lang_map = {
        "Chinese (中文)": "Chinese",
        "English": "English",
        "Cantonese (粤语)": "Cantonese"
    }
    
    prompt = f"""Write a marketing copy about "{topic}" with the following requirements:
- Tone: {tone}
- Length: {length_map[length]}
- Language: {lang_map[language]}

The copy should be engaging, persuasive, and suitable for social media platforms.
Include a catchy headline and call-to-action."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional marketing copywriter with expertise in social media content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error: {str(e)}\n\nPlease make sure OPENAI_API_KEY environment variable is set."


# Create Gradio interface
demo = gr.Interface(
    fn=generate_copy,
    inputs=[
        gr.Textbox(
            label="Topic / Product",
            placeholder="e.g., New smartphone launch, Coffee shop opening, Fitness app",
            lines=2
        ),
        gr.Dropdown(
            choices=["Professional", "Casual", "Humorous", "Inspirational", "Urgent"],
            label="Tone",
            value="Professional"
        ),
        gr.Dropdown(
            choices=["Short (50-100 words)", "Medium (100-200 words)", "Long (200-300 words)"],
            label="Length",
            value="Medium (100-200 words)"
        ),
        gr.Dropdown(
            choices=["Chinese (中文)", "English", "Cantonese (粤语)"],
            label="Language",
            value="Chinese (中文)"
        )
    ],
    outputs=gr.Textbox(label="Generated Copy", lines=10),
    title="AI Copywriting Tool",
    description="Generate marketing copy for social media with customizable tone, length, and language. Powered by OpenAI GPT-3.5.",
    examples=[
        ["New iPhone launch", "Professional", "Medium (100-200 words)", "English"],
        ["Coffee shop grand opening", "Casual", "Short (50-100 words)", "Chinese (中文)"],
        ["Fitness app promotion", "Inspirational", "Long (200-300 words)", "Cantonese (粤语)"]
    ],
    allow_flagging="never"
)

if __name__ == "__main__":
    demo.launch(share=True)
