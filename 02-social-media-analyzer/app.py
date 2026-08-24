"""
Social Media Analyzer / 社媒数据分析器
A web-based social media analytics dashboard for HK content creators.
"""
import gradio as gr
import pandas as pd
from datetime import datetime, timedelta

# --- Configuration ---
DEFAULT_DAYS = 30

# --- Core Logic ---
def load_sample_data(days: int = DEFAULT_DAYS) -> pd.DataFrame:
    """Generate sample social media data for demonstration.
    生成示例社媒数据用于演示。
    """
    dates = pd.date_range(end=datetime.now(), periods=days, freq="D")
    data = {
        "date": dates,
        "platform": ["Instagram", "Facebook", "X"] * (days // 3 + 1),
        "likes": [100, 200, 50] * (days // 3 + 1),
        "shares": [20, 15, 5] * (days // 3 + 1),
        "comments": [30, 25, 10] * (days // 3 + 1),
    }
    df = pd.DataFrame(data)
    return df


def analyze_engagement(df: pd.DataFrame) -> dict:
    """Analyze engagement metrics from social media data.
    分析社媒数据的互动指标。
    """
    if df.empty:
        return {"error": "数据为空 / No data"}
    
    # Group by platform and sum engagement
    platform_stats = df.groupby("platform").agg({
        "likes": "sum",
        "shares": "sum",
        "comments": "sum"
    }).reset_index()
    
    platform_stats["total_engagement"] = (
        platform_stats["likes"] + platform_stats["shares"] + platform_stats["comments"]
    )
    
    return platform_stats.to_dict("records")


def generate_summary(engagement_data: dict) -> str:
    """Generate a text summary of engagement insights.
    生成互动洞察的文本摘要。
    """
    if isinstance(engagement_data, dict) and "error" in engagement_data:
        return engagement_data["error"]
    
    lines = ["## 互动分析摘要 / Engagement Summary\n"]
    lines.append("| 平台 | 点赞 | 转发 | 评论 | 总互动 |")
    lines.append("|------|------|------|------|--------|")
    
    for row in engagement_data:
        lines.append(
            f"| {row['platform']} | {row['likes']} | {row['shares']} | "
            f"{row['comments']} | {row['total_engagement']} |"
        )
    
    return "\n".join(lines)


# --- UI ---
with gr.Blocks(title="Social Media Analyzer / 社媒数据分析器") as demo:
    gr.Markdown("# 社媒数据分析器 / Social Media Analyzer")
    gr.Markdown(
        "Upload social media data or use sample data to analyze engagement trends. "
        "/ 上传社媒数据或使用示例数据分析互动趋势。"
    )
    
    with gr.Row():
        days_input = gr.Slider(
            minimum=7, maximum=90, value=DEFAULT_DAYS, step=1,
            label="分析天数 / Days to Analyze"
        )
        load_btn = gr.Button("加载示例数据 / Load Sample Data", variant="primary")
    
    with gr.Row():
        summary_output = gr.Markdown(label="分析摘要 / Analysis Summary")
    
    with gr.Row():
        chart_output = gr.Plot(label="互动趋势图 / Engagement Trend")
    
    # --- Event Handlers ---
    def on_load_sample(days):
        """Handle sample data loading button click.
        处理示例数据加载按钮点击。
        """
        df = load_sample_data(days)
        engagement = analyze_engagement(df)
        summary = generate_summary(engagement)
        
        # Create a simple plot
        fig = gr.LinePlot(
            df, x="date", y="likes", color="platform",
            title="点赞趋势 / Like Trend"
        )
        
        return summary, fig
    
    load_btn.click(
        fn=on_load_sample,
        inputs=[days_input],
        outputs=[summary_output, chart_output]
    )

# --- Entry Point ---
if __name__ == "__main__":
    demo.launch(share=False)
