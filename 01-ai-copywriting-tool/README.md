# AI Copywriting Tool

A web-based AI copywriting tool that generates marketing copy for social media platforms. Built with Gradio and OpenAI GPT-3.5, supporting multiple languages (Chinese, English, Cantonese) and customizable tone/length.

## Features

- **Multi-language Support**: Generate copy in Chinese, English, or Cantonese
- **Customizable Tone**: Professional, Casual, Humorous, Inspirational, or Urgent
- **Flexible Length**: Short (50-100 words), Medium (100-200 words), or Long (200-300 words)
- **One-Click Deployment**: Launch locally or share via Gradio public URL
- **Example Templates**: Pre-built examples for quick testing

## Tech Stack

- **Frontend**: Gradio (Python UI framework)
- **AI Model**: OpenAI GPT-3.5-turbo
- **Language**: Python 3.8+

## Installation

1. Clone this repository:
```bash
git clone https://github.com/xi195072-a11y/portfolio-projects.git
cd portfolio-projects/01-ai-copywriting-tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your OpenAI API key:
```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"

# Windows (CMD)
set OPENAI_API_KEY=your-api-key-here

# macOS/Linux
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

Run the application:
```bash
python app.py
```

The app will start at `http://localhost:7860` and provide a public URL for sharing.

## Project Structure

```
01-ai-copywriting-tool/
├── app.py                  # Main Gradio application
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## How It Works

1. User inputs topic, selects tone, length, and language
2. Gradio UI sends parameters to `generate_copy()` function
3. Function constructs a prompt for OpenAI API
4. GPT-3.5 generates marketing copy based on the prompt
5. Result is displayed in the UI

## Customization

### Add More Tones
Edit the `gr.Dropdown` in `app.py`:
```python
gr.Dropdown(
    choices=["Professional", "Casual", "Humorous", "Inspirational", "Urgent", "YOUR_TONE"],
    ...
)
```

### Change AI Model
Modify the model parameter in `app.py`:
```python
response = client.chat.completions.create(
    model="gpt-4",  # Change to GPT-4 or other models
    ...
)
```

### Add More Languages
Update the `lang_map` dictionary and dropdown choices.

## Screenshots

*Add screenshots of your app running here*

## Future Enhancements

- [ ] Add image generation for social media posts
- [ ] Support more languages (Japanese, Korean, etc.)
- [ ] Add copy history and favorites
- [ ] Integrate with social media APIs for direct posting
- [ ] Add A/B testing for multiple copy variations

## Author

**Zhong Jiaxi**
- GitHub: [@xi195072-a11y](https://github.com/xi195072-a11y)
- Email: 1005270675@qq.com

## License

MIT License - feel free to use this project for learning or commercial purposes.
