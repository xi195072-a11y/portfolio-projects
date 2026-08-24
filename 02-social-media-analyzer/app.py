"""
Social Media Analyzer / 社媒数据分析器
A web-based social media analytics dashboard for HK content creators and marketers.
Supports CSV data upload, multi-dimensional analysis, and visual report generation.

面向香港内容创作者和营销人员的社媒数据分析仪表板。
支持 CSV 数据上传、多维度分析和可视化报告生成。
"""
import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import tempfile
import os

# --- Configuration ---
DEFAULT_DAYS = 30
SUPPORTED_PLATFORMS = ["Instagram", "Facebook", "X", "小红书", "抖音", "Bilibili"]
METRIC_COLUMNS = ["likes", "shares", "comments", "views"]

# --- Sample Data Generation ---
def generate_sample_data(days: int = DEFAULT_DAYS) -> pd.DataFrame:
    """Generate realistic sample social media data for HK market.
    生成面向香港市场的真实社媒示例数据。

    Data includes: date, platform, post_id, content, likes, shares, comments,
    views, hashtags, post_type, and hour posted.
    """
    import random
    random.seed(42)

    platforms = ["Instagram", "Facebook", "X", "小红书", "抖音"]
    post_types = ["image", "video", "carousel", "story", "reel"]
    hk_hashtags = [
        "#香港美食", "#HKFoodie", "#香港打卡", "#HongKong", "#HK生活",
        "#香港探店", "#HKTravel", "#香港摄影", "#HKFashion", "#香港健身",
        "#HKTech", "#香港创业", "#HKArt", "#香港音乐", "#HKSports"
    ]

    records = []
    for day_offset in range(days):
        date = datetime.now() - timedelta(days=day_offset)
        # 3-8 posts per day
        num_posts = random.randint(3, 8)
        for _ in range(num_posts):
            platform = random.choice(platforms)
            post_type = random.choice(post_types)
            hour = random.randint(7, 23)  # 7am to 11pm

            # Platform-typical engagement rates
            base_likes = {
                "Instagram": random.randint(50, 500),
                "Facebook": random.randint(30, 300),
                "X": random.randint(20, 200),
                "小红书": random.randint(100, 800),
                "抖音": random.randint(200, 1500),
            }
            likes = base_likes.get(platform, 100)
            shares = max(1, int(likes * random.uniform(0.02, 0.15)))
            comments = max(1, int(likes * random.uniform(0.03, 0.20)))
            views = likes * random.randint(3, 20)

            # Peak hours get more engagement
            if 12 <= hour <= 14 or 19 <= hour <= 22:
                likes = int(likes * 1.5)
                shares = int(shares * 1.3)
                comments = int(comments * 1.4)

            selected_hashtags = random.sample(hk_hashtags, random.randint(1, 4))

            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "hour": hour,
                "platform": platform,
                "post_id": f"{platform[:2].lower()}_{date.strftime('%Y%m%d')}_{len(records):04d}",
                "post_type": post_type,
                "content": f"Sample {platform} post for HK market #{random.randint(100,999)}",
                "likes": likes,
                "shares": shares,
                "comments": comments,
                "views": views,
                "hashtags": " ".join(selected_hashtags),
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["total_engagement"] = df["likes"] + df["shares"] + df["comments"]
    return df


# --- Data Processing ---
def process_uploaded_file(file) -> pd.DataFrame:
    """Read and validate uploaded CSV file.
    读取并验证上传的 CSV 文件。

    Expected columns: date, platform, likes, shares, comments, views (optional).
    """
    if file is None:
        return None

    try:
        df = pd.read_csv(file.name)
    except Exception as e:
        raise ValueError(f"无法读取文件 / Cannot read file: {str(e)}")

    required_cols = {"date", "platform"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"缺少必要列 / Missing required columns: {', '.join(missing)}. "
            f"需要列: date, platform, likes, shares, comments, views"
        )

    # Fill missing metric columns with 0
    for col in METRIC_COLUMNS:
        if col not in df.columns:
            df[col] = 0

    # Parse date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "platform"])

    # Ensure numeric
    for col in METRIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Add derived columns
    df["total_engagement"] = df["likes"] + df["shares"] + df["comments"]
    if "hour" not in df.columns:
        df["hour"] = df["date"].dt.hour
    else:
        df["hour"] = pd.to_numeric(df["hour"], errors="coerce").fillna(12).astype(int)

    return df


# --- Analysis Functions ---
def compute_overview(df: pd.DataFrame) -> dict:
    """Compute high-level engagement overview metrics.
    计算高层次互动概览指标。
    """
    if df.empty:
        return {}

    total = {
        "total_posts": len(df),
        "total_likes": int(df["likes"].sum()),
        "total_shares": int(df["shares"].sum()),
        "total_comments": int(df["comments"].sum()),
        "total_views": int(df["views"].sum()) if "views" in df.columns else 0,
        "total_engagement": int(df["total_engagement"].sum()),
        "avg_engagement_per_post": round(df["total_engagement"].mean(), 1),
        "engagement_rate": round(
            df["total_engagement"].sum() / max(df["views"].sum(), 1) * 100, 2
        ),
        "date_range": f"{df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}",
        "platforms": df["platform"].nunique(),
    }
    return total


def compute_platform_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Compare engagement metrics across platforms.
    跨平台对比互动指标。
    """
    if df.empty:
        return pd.DataFrame()

    platform_stats = df.groupby("platform").agg({
        "likes": ["sum", "mean"],
        "shares": ["sum", "mean"],
        "comments": ["sum", "mean"],
        "views": ["sum", "mean"],
        "total_engagement": ["sum", "mean"],
    }).reset_index()

    # Flatten multi-level columns
    platform_stats.columns = [
        "_".join(col).strip("_") for col in platform_stats.columns.to_flat_index()
    ]

    platform_stats["engagement_rate"] = (
        platform_stats["total_engagement_sum"] /
        platform_stats["views_sum"].clip(lower=1) * 100
    ).round(2)

    return platform_stats


def compute_top_posts(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Get top N posts by engagement.
    按互动量获取前 N 条帖子。
    """
    if df.empty:
        return pd.DataFrame()

    top = df.nlargest(top_n, "total_engagement")
    cols = ["date", "platform", "post_type", "content", "likes", "shares",
            "comments", "views", "total_engagement"]
    available_cols = [c for c in cols if c in df.columns]
    return top[available_cols].reset_index(drop=True)


def compute_optimal_time(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze engagement by posting hour to find optimal times.
    按发帖时间分析互动，找出最佳发帖时段。
    """
    if df.empty:
        return pd.DataFrame()

    hourly = df.groupby("hour").agg({
        "total_engagement": ["sum", "mean", "count"],
        "likes": "sum",
    }).reset_index()

    hourly.columns = ["hour", "engagement_sum", "engagement_avg", "post_count", "likes_sum"]
    hourly["engagement_rate"] = (
        hourly["engagement_sum"] / hourly["engagement_sum"].max() * 100
    ).round(1)

    return hourly


def compute_word_frequency(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Analyze hashtag/content word frequency.
    分析标签/内容词频。
    """
    if df.empty:
        return pd.DataFrame()

    # Extract hashtags
    if "hashtags" in df.columns:
        all_tags = []
        for tags in df["hashtags"].dropna():
            all_tags.extend(str(tags).split())

        if all_tags:
            from collections import Counter
            counter = Counter(all_tags)
            freq = counter.most_common(top_n)
            return pd.DataFrame(freq, columns=["hashtag", "count"])

    return pd.DataFrame(columns=["hashtag", "count"])


# --- Visualization ---
def create_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Create engagement trend line chart.
    创建互动趋势折线图。
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据 / No data", showarrow=False, font_size=20)
        return fig

    daily = df.groupby("date")["total_engagement"].sum().reset_index()
    daily = daily.sort_values("date")

    fig = px.line(
        daily, x="date", y="total_engagement",
        title="互动趋势 / Engagement Trend Over Time",
        labels={"date": "日期 / Date", "total_engagement": "总互动 / Total Engagement"},
    )
    fig.update_traces(line=dict(width=2), marker=dict(size=6))
    fig.update_layout(
        xaxis_title="日期 / Date",
        yaxis_title="总互动 / Total Engagement",
        hovermode="x unified",
    )
    return fig


def create_platform_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create grouped bar chart comparing platforms.
    创建跨平台对比柱状图。
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据 / No data", showarrow=False, font_size=20)
        return fig

    platform_stats = compute_platform_comparison(df)
    if platform_stats.empty:
        return go.Figure()

    fig = go.Figure()
    metrics = [
        ("likes_sum", "点赞 / Likes", "#636EFA"),
        ("shares_sum", "转发 / Shares", "#EF553B"),
        ("comments_sum", "评论 / Comments", "#00CC96"),
    ]

    for col, name, color in metrics:
        if col in platform_stats.columns:
            fig.add_trace(go.Bar(
                name=name,
                x=platform_stats["platform"],
                y=platform_stats[col],
                marker_color=color,
            ))

    fig.update_layout(
        title="平台互动对比 / Platform Engagement Comparison",
        barmode="group",
        xaxis_title="平台 / Platform",
        yaxis_title="数量 / Count",
        hovermode="closest",
    )
    return fig


def create_optimal_time_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create heatmap of engagement by hour and platform.
    创建按时段和平台的互动热力图。
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据 / No data", showarrow=False, font_size=20)
        return fig

    # Create pivot: hour x platform
    pivot = df.pivot_table(
        values="total_engagement",
        index="hour",
        columns="platform",
        aggfunc="mean",
        fill_value=0,
    )

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=[f"{h:02d}:00" for h in pivot.index],
        colorscale="YlOrRd",
        colorbar=dict(title="平均互动 / Avg Engagement"),
    ))

    fig.update_layout(
        title="最佳发帖时间 / Optimal Posting Time (Heatmap)",
        xaxis_title="平台 / Platform",
        yaxis_title="时段 / Hour",
    )
    return fig


def create_top_posts_chart(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Create horizontal bar chart of top posts.
    创建热门帖子横向柱状图。
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据 / No data", showarrow=False, font_size=20)
        return fig

    top = compute_top_posts(df, top_n)
    if top.empty:
        return go.Figure()

    # Create label with platform + content snippet
    labels = [
        f"[{row['platform']}] {str(row.get('content', ''))[:40]}"
        for _, row in top.iterrows()
    ]

    fig = go.Figure(go.Bar(
        x=top["total_engagement"],
        y=labels,
        orientation="h",
        marker_color="#636EFA",
        text=top["total_engagement"],
        textposition="outside",
    ))

    fig.update_layout(
        title=f"Top {top_n} 热门帖子 / Top {top_n} Posts by Engagement",
        xaxis_title="总互动 / Total Engagement",
        yaxis_title="帖子 / Post",
        height=max(400, top_n * 35),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def create_hashtag_chart(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Create bar chart of top hashtags.
    创建热门标签柱状图。
    """
    freq = compute_word_frequency(df, top_n)
    if freq.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无标签数据 / No hashtag data", showarrow=False, font_size=20)
        return fig

    fig = px.bar(
        freq, x="count", y="hashtag",
        orientation="h",
        title=f"Top {top_n} 热门标签 / Top {top_n} Hashtags",
        labels={"count": "出现次数 / Count", "hashtag": "标签 / Hashtag"},
        color="count",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig


# --- Report Generation ---
def generate_summary_markdown(overview: dict, platform_stats: pd.DataFrame) -> str:
    """Generate a markdown summary report.
    生成 Markdown 摘要报告。
    """
    if not overview:
        return "暂无数据，请上传 CSV 或加载示例数据。\nNo data. Please upload CSV or load sample data."

    lines = ["## 📊 数据分析摘要 / Analysis Summary\n"]
    lines.append(f"**分析周期 / Period**: {overview.get('date_range', 'N/A')}")
    lines.append(f"**帖子总数 / Total Posts**: {overview.get('total_posts', 0)}")
    lines.append(f"**覆盖平台 / Platforms**: {overview.get('platforms', 0)}")
    lines.append("")

    lines.append("### 互动指标 / Engagement Metrics\n")
    lines.append("| 指标 / Metric | 数值 / Value |")
    lines.append("|--------------|-------------|")
    lines.append(f"| 总点赞 / Total Likes | {overview.get('total_likes', 0):,} |")
    lines.append(f"| 总转发 / Total Shares | {overview.get('total_shares', 0):,} |")
    lines.append(f"| 总评论 / Total Comments | {overview.get('total_comments', 0):,} |")
    lines.append(f"| 总浏览 / Total Views | {overview.get('total_views', 0):,} |")
    lines.append(f"| 总互动 / Total Engagement | {overview.get('total_engagement', 0):,} |")
    lines.append(f"| 平均互动 / Avg per Post | {overview.get('avg_engagement_per_post', 1):,} |")
    lines.append(f"| 互动率 / Engagement Rate | {overview.get('engagement_rate', 0)}% |")
    lines.append("")

    if not platform_stats.empty:
        lines.append("### 平台对比 / Platform Comparison\n")
        lines.append("| 平台 / Platform | 总互动 / Total | 平均互动 / Avg | 互动率 / Rate |")
        lines.append("|----------------|---------------|---------------|-------------|")
        for _, row in platform_stats.iterrows():
            lines.append(
                f"| {row['platform']} | {row['total_engagement_sum']:,.0f} | "
                f"{row['total_engagement_mean']:,.0f} | {row.get('engagement_rate', 0)}% |"
            )

    return "\n".join(lines)


def export_summary_csv(overview: dict, platform_stats: pd.DataFrame) -> str:
    """Export summary data as CSV file path.
    将摘要数据导出为 CSV。
    """
    import tempfile, os

    # Create summary DataFrame
    summary_data = {
        "metric": [
            "total_posts", "total_likes", "total_shares", "total_comments",
            "total_views", "total_engagement", "avg_engagement_per_post",
            "engagement_rate", "date_range"
        ],
        "value": [
            overview.get("total_posts", 0),
            overview.get("total_likes", 0),
            overview.get("total_shares", 0),
            overview.get("total_comments", 0),
            overview.get("total_views", 0),
            overview.get("total_engagement", 0),
            overview.get("avg_engagement_per_post", 0),
            overview.get("engagement_rate", 0),
            overview.get("date_range", ""),
        ],
    }
    summary_df = pd.DataFrame(summary_data)

    # Save to temp file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(tempfile.gettempdir(), f"social_media_summary_{timestamp}.csv")

    with open(filepath, "w", encoding="utf-8-sig") as f:
        f.write("=== Social Media Analysis Summary ===\n")
        summary_df.to_csv(f, index=False)
        if not platform_stats.empty:
            f.write("\n=== Platform Comparison ===\n")
            platform_stats.to_csv(f, index=False)

    return filepath


# --- Main Analysis Pipeline ---
def run_analysis(df: pd.DataFrame) -> dict:
    """Run full analysis pipeline and return all results.
    运行完整分析管线并返回所有结果。
    """
    if df is None or df.empty:
        return {
            "summary_md": "请上传 CSV 数据或加载示例数据。\nPlease upload CSV or load sample data.",
            "overview": {},
            "platform_stats": pd.DataFrame(),
            "top_posts": pd.DataFrame(),
            "optimal_time": pd.DataFrame(),
            "word_freq": pd.DataFrame(),
            "fig_trend": go.Figure(),
            "fig_platform": go.Figure(),
            "fig_optimal_time": go.Figure(),
            "fig_top_posts": go.Figure(),
            "fig_hashtag": go.Figure(),
            "csv_path": None,
        }

    # Run all analyses
    overview = compute_overview(df)
    platform_stats = compute_platform_comparison(df)
    top_posts = compute_top_posts(df, top_n=10)
    optimal_time = compute_optimal_time(df)
    word_freq = compute_word_frequency(df, top_n=15)

    # Generate summary
    summary_md = generate_summary_markdown(overview, platform_stats)

    # Generate all charts
    fig_trend = create_trend_chart(df)
    fig_platform = create_platform_bar_chart(df)
    fig_optimal_time = create_optimal_time_heatmap(df)
    fig_top_posts = create_top_posts_chart(df, top_n=10)
    fig_hashtag = create_hashtag_chart(df, top_n=15)

    # Export CSV
    csv_path = export_summary_csv(overview, platform_stats)

    return {
        "summary_md": summary_md,
        "overview": overview,
        "platform_stats": platform_stats,
        "top_posts": top_posts,
        "optimal_time": optimal_time,
        "word_freq": word_freq,
        "fig_trend": fig_trend,
        "fig_platform": fig_platform,
        "fig_optimal_time": fig_optimal_time,
        "fig_top_posts": fig_top_posts,
        "fig_hashtag": fig_hashtag,
        "csv_path": csv_path,
    }


# --- Gradio UI ---
# Global state to hold analyzed data for export
_state = {"df": None, "results": None}


def on_upload_csv(file):
    """Handle CSV file upload.
    处理 CSV 文件上传。
    """
    try:
        df = process_uploaded_file(file)
        _state["df"] = df
        results = run_analysis(df)
        _state["results"] = results
        return _display_results(results)
    except Exception as e:
        error_md = f"❌ **错误 / Error**: {str(e)}"
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="请上传有效 CSV / Upload valid CSV", showarrow=False, font_size=20)
        return (error_md, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, None)


def on_load_sample(days):
    """Handle sample data loading.
    处理示例数据加载。
    """
    df = generate_sample_data(days)
    _state["df"] = df
    results = run_analysis(df)
    _state["results"] = results
    return _display_results(results)


def _display_results(results: dict):
    """Unpack results tuple for Gradio outputs.
    解包结果元组供 Gradio 输出。
    """
    return (
        results["summary_md"],
        results["fig_trend"],
        results["fig_platform"],
        results["fig_optimal_time"],
        results["fig_top_posts"],
        results["fig_hashtag"],
        results["csv_path"],
    )


def on_export_csv():
    """Handle CSV export button.
    处理 CSV 导出按钮。
    """
    if _state["results"] and _state["results"]["csv_path"]:
        return _state["results"]["csv_path"]
    return None


# --- Build UI ---
with gr.Blocks(title="Social Media Analyzer / 社媒数据分析器") as demo:
    gr.Markdown("""
    # 📊 社媒数据分析器 / Social Media Analyzer

    Upload your social media data or use sample data to generate a full analytics report.
    上传社媒数据或使用示例数据生成完整分析报告。
    """)

    with gr.Tab("数据输入 / Data Input"):
        with gr.Row():
            file_upload = gr.File(
                label="上传 CSV 文件 / Upload CSV File",
                file_types=[".csv"],
                file_count="single",
            )
        with gr.Row():
            gr.Markdown("""
            **CSV 格式要求 / CSV Format Requirements:**

            Required columns: `date`, `platform`
            Optional columns: `likes`, `shares`, `comments`, `views`, `content`, `hashtags`, `post_type`, `hour`

            必需列：`date`（日期）, `platform`（平台）
            可选列：`likes`（点赞）, `shares`（转发）, `comments`（评论）, `views`（浏览）, `content`（内容）, `hashtags`（标签）, `post_type`（类型）, `hour`（时段）
            """)

        with gr.Row():
            sample_days = gr.Slider(
                minimum=7, maximum=90, value=30, step=1,
                label="示例数据天数 / Sample Data Days"
            )
            load_sample_btn = gr.Button(
                "📥 加载示例数据 / Load Sample Data",
                variant="primary",
            )

    with gr.Tab("分析报告 / Analysis Report"):
        summary_output = gr.Markdown(
            label="分析摘要 / Summary",
            value="上传 CSV 或加载示例数据开始分析。\nUpload CSV or load sample data to start analysis.",
        )

    with gr.Tab("可视化图表 / Visualizations"):
        with gr.Row():
            fig_trend = gr.Plot(label="互动趋势 / Engagement Trend")
        with gr.Row():
            fig_platform = gr.Plot(label="平台对比 / Platform Comparison")
        with gr.Row():
            fig_optimal_time = gr.Plot(label="最佳发帖时间 / Optimal Posting Time")
        with gr.Row():
            fig_top_posts = gr.Plot(label="热门帖子 / Top Posts")
        with gr.Row():
            fig_hashtag = gr.Plot(label="热门标签 / Top Hashtags")

    with gr.Tab("导出 / Export"):
        gr.Markdown("下载分析结果 CSV 文件。\nDownload analysis results as CSV.")
        export_btn = gr.Button("📥 导出报告 / Export Report", variant="primary")
        csv_output = gr.File(label="下载 / Download", file_count="single")

    # --- Wire up events ---
    file_upload.change(
        fn=on_upload_csv,
        inputs=[file_upload],
        outputs=[summary_output, fig_trend, fig_platform, fig_optimal_time,
                 fig_top_posts, fig_hashtag, csv_output],
    )

    load_sample_btn.click(
        fn=on_load_sample,
        inputs=[sample_days],
        outputs=[summary_output, fig_trend, fig_platform, fig_optimal_time,
                 fig_top_posts, fig_hashtag, csv_output],
    )

    export_btn.click(
        fn=on_export_csv,
        outputs=[csv_output],
    )

# --- Entry Point ---
if __name__ == "__main__":
    demo.launch(share=False, server_port=7861)
