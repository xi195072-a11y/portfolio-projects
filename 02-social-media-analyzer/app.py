"""B站 UP 主数据分析器 - Single-page dashboard.
Bilibili Creator Data Analyzer — 单页面仪表板。

数据来源：
- 默认：预取 JSON 文件（data/ 目录，稳定可靠）
- 可选：实时 B站 API（dm_img_* + WBI 签名）

Features:
- 真实 B站数据（3 位知名 UP 主）
- KPI 卡片 + 4 种 Plotly 图表 + 智能洞察 + CSV 导出
- 中英双语界面
"""
from __future__ import annotations

import sys
import os
import json

# 本地依赖路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".packages"))

import gradio as gr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# 预设 UP 主（有预取数据的）
PRESET_UPS: list[tuple[str, int]] = [
    ("影视飓风 / Stormstorm", 946974),
    ("老番茄 / OldTomato", 546195),
    ("半佛仙人 / Bafo", 37663924),
]

# B站 品牌配色
COLOR_PRIMARY = "#00AEEC"
COLOR_SECONDARY = "#FB7299"


def _fmt_num(n: int) -> str:
    """格式化数字：1.2M / 3.4K。"""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _load_from_json(mid: int) -> tuple[dict | None, pd.DataFrame]:
    """从 JSON 文件加载数据。"""
    filepath = os.path.join(DATA_DIR, f"up_{mid}.json")
    if not os.path.exists(filepath):
        return None, pd.DataFrame()

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    info = data["info"]
    videos = data["videos"]

    # 转换为 DataFrame
    df = pd.DataFrame(videos)

    # 转换日期列
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # 转换数值列
    for col in ["views", "likes", "favorites", "comments", "shares", "engagement", "engagement_rate"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float if col == "engagement_rate" else int)
        else:
            if col == "engagement_rate":
                df[col] = 0.0
            elif col == "engagement":
                df[col] = 0
            else:
                df[col] = 0

    if "engagement" not in df.columns:
        df["engagement"] = df["likes"] + df["favorites"] + df["comments"] + df["shares"]
    if "engagement_rate" not in df.columns:
        df["engagement_rate"] = df.apply(
            lambda r: round((r["engagement"] / r["views"] * 100), 2) if r["views"] > 0 else 0.0,
            axis=1,
        )
    if "platform" not in df.columns:
        df["platform"] = "Bilibili"

    df = df.sort_values("date", ascending=False, na_position="last").reset_index(drop=True)
    return info, df


def _fetch_live(mid: int, max_videos: int = 30) -> tuple[dict | None, pd.DataFrame]:
    """从 B站 API 实时获取数据。"""
    try:
        from bilibili_api import quick_fetch
        info, df = quick_fetch(mid, max_videos=max_videos)
        if df.empty:
            return None, pd.DataFrame()

        info_dict = {
            "mid": info.mid, "name": info.name,
            "face": info.face, "followers": info.followers,
            "video_count": info.video_count or len(df),
        }
        return info_dict, df
    except Exception as e:
        raise RuntimeError(f"实时 API 获取失败 / Live API failed: {e}")


def _build_kpi_cards(info: dict, df: pd.DataFrame) -> list[dict]:
    """构建 KPI 卡片。"""
    if df.empty:
        return []

    total_views = int(df["views"].sum())
    total_comments = int(df["comments"].sum())
    avg_views = int(df["views"].mean())
    max_video_views = int(df["views"].max())
    engagement_rate = round(df["engagement_rate"].mean(), 2)
    recent_30 = df[df["date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)]
    recent_views = int(recent_30["views"].sum()) if len(recent_30) > 0 else 0

    total_videos = info.get("video_count", len(df))
    followers = info.get("followers", 0)

    return [
        {"label": "总播放量 / Total Views", "value": _fmt_num(total_views), "sub": f"{total_views:,}"},
        {"label": "粉丝数 / Followers", "value": _fmt_num(followers), "sub": f"{followers:,}"},
        {"label": "视频总数 / Total Videos", "value": str(total_videos), "sub": f"近期抓取 {len(df)} 条"},
        {"label": "总评论数 / Total Comments", "value": _fmt_num(total_comments), "sub": f"{total_comments:,}"},
        {"label": "平均播放 / Avg Views", "value": _fmt_num(avg_views), "sub": f"{avg_views:,}"},
        {"label": "最高单作 / Top Video", "value": _fmt_num(max_video_views), "sub": f"{max_video_views:,}"},
        {"label": "互动率 / Engagement Rate", "value": f"{engagement_rate}%", "sub": "平均互动率"},
        {"label": "近30天播放 / 30d Views", "value": _fmt_num(recent_views), "sub": f"{recent_views:,}"},
    ]


def _plot_trend(df: pd.DataFrame) -> go.Figure:
    """趋势图。"""
    daily = df.groupby(df["date"].dt.date)["views"].sum().sort_index()
    if len(daily) == 0:
        return go.Figure()
    ma7 = daily.rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily.index.astype(str), y=daily.values,
        name="日播放量 / Daily Views",
        marker_color=COLOR_PRIMARY, opacity=0.6,
        hovertemplate="日期: %{x}<br>播放: %{y:,}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily.index.astype(str), y=ma7.values,
        mode="lines", name="7日均线 / 7-day MA",
        line=dict(color=COLOR_SECONDARY, width=3),
        hovertemplate="日期: %{x}<br>均线: %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="播放量趋势 / View Trend", font=dict(size=16)),
        height=380, margin=dict(l=50, r=30, t=60, b=40),
        template="plotly_white",
        xaxis_title="日期 / Date", yaxis_title="播放量 / Views",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    return fig


def _plot_top_videos(df: pd.DataFrame) -> go.Figure:
    """Top 10 视频。"""
    top10 = df.nlargest(10, "views").sort_values("views")
    if top10.empty:
        return go.Figure()
    titles = [t[:30] + "..." if len(t) > 30 else t for t in top10["title"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top10["views"].values, y=titles, orientation="h",
        marker_color=COLOR_PRIMARY,
        hovertemplate="<b>%{y}</b><br>播放: %{x:,}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Top 10 视频 / Top Videos", font=dict(size=16)),
        height=400, margin=dict(l=150, r=30, t=60, b=40),
        template="plotly_white",
        xaxis_title="播放量 / Views",
    )
    return fig


def _plot_monthly(df: pd.DataFrame) -> go.Figure:
    """月度分布图。"""
    df_copy = df.copy()
    df_copy["month"] = df_copy["date"].dt.to_period("M")
    monthly = df_copy.groupby("month").agg(
        count=("title", "count"), views=("views", "sum"),
    ).sort_index()
    if monthly.empty:
        return go.Figure()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=[str(m) for m in monthly.index], y=monthly["count"].values,
        name="发布数量 / Video Count", marker_color=COLOR_PRIMARY, opacity=0.7,
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=[str(m) for m in monthly.index], y=monthly["views"].values,
        name="播放量 / Views", mode="lines+markers",
        line=dict(color=COLOR_SECONDARY, width=3), marker=dict(size=8),
    ), secondary_y=True)
    fig.update_layout(
        title=dict(text="月度分布 / Monthly Distribution", font=dict(size=16)),
        height=380, margin=dict(l=50, r=50, t=60, b=40),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_yaxes(title_text="发布数量 / Count", secondary_y=False)
    fig.update_yaxes(title_text="播放量 / Views", secondary_y=True)
    fig.update_xaxes(title_text="月份 / Month")
    return fig


def _plot_heatmap(df: pd.DataFrame) -> go.Figure:
    """发布时间热力图。"""
    df_copy = df.copy()
    df_copy["weekday"] = df_copy["date"].dt.dayofweek
    df_copy["hour"] = df_copy["date"].dt.hour

    pivot = df_copy.pivot_table(
        index="weekday", columns="hour", values="title",
        aggfunc="count", fill_value=0,
    )
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=list(range(24)),
        y=[weekdays[i] for i in pivot.index],
        colorscale=[[0, "#f1f2f3"], [0.5, COLOR_PRIMARY], [1.0, COLOR_SECONDARY]],
        hovertemplate="星期: %{y}<br>小时: %{x}:00<br>数量: %{z}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="发布时间热力图 / Upload Time Heatmap", font=dict(size=16)),
        height=380, margin=dict(l=50, r=30, t=60, b=40),
        template="plotly_white",
        xaxis_title="小时 / Hour", yaxis_title="星期 / Weekday",
    )
    return fig


def _generate_insights(df: pd.DataFrame, info: dict) -> list[str]:
    """生成洞察。"""
    if df.empty:
        return ["暂无数据 / No data"]

    insights: list[str] = []
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    en_weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    df_copy = df.copy()
    df_copy["weekday"] = df_copy["date"].dt.dayofweek
    df_copy["hour"] = df_copy["date"].dt.hour

    best_w = df_copy.groupby("weekday")["views"].sum().idxmax()
    best_h = df_copy.groupby("hour")["views"].sum().idxmax()
    insights.append(
        f"🗓️ 最佳发布时间 / Best Upload Time: "
        f"{weekday_names[best_w]} {best_h}:00 ({en_weekdays[best_w]} {best_h}:00)"
    )

    total = df["views"].sum()
    top5 = df.nlargest(5, "views")["views"].sum()
    ratio = round(top5 / total * 100, 1) if total > 0 else 0
    insights.append(
        f"📊 头部集中度 / Top Concentration: "
        f"Top 5 视频贡献 {ratio}% 总播放量"
    )

    avg_er = round(df["engagement_rate"].mean(), 2)
    level = "高 / High" if avg_er >= 5 else ("中等 / Medium" if avg_er >= 2 else "低 / Low")
    insights.append(f"💬 平均互动率 / Avg Engagement Rate: {avg_er}% ({level})")

    df_copy["month"] = df_copy["date"].dt.to_period("M")
    monthly_count = df_copy.groupby("month").size()
    avg_monthly = round(monthly_count.mean(), 1) if len(monthly_count) > 0 else 0
    insights.append(
        f"📈 更新频率 / Upload Frequency: 平均每月 {avg_monthly} 条视频"
    )

    recent = df[df["date"] >= pd.Timestamp.now() - pd.Timedelta(days=90)]
    older = df[df["date"] < pd.Timestamp.now() - pd.Timedelta(days=90)]
    if len(recent) > 0 and len(older) > 0:
        recent_avg = recent["views"].mean()
        older_avg = older["views"].mean()
        if recent_avg > older_avg * 1.2:
            trend = "上升 / ↑ Rising"
        elif recent_avg < older_avg * 0.8:
            trend = "下降 / ↓ Declining"
        else:
            trend = "稳定 / → Stable"
        insights.append(
            f"📉 近期趋势 / Recent Trend: {trend}"
        )

    return insights


def load_up(mid: int, max_videos: int = 30, live: bool = False):
    """加载 UP 主数据。返回 9 个值匹配 outputs (含 status)。"""
    try:
        # 优先从 JSON 加载
        info, df = _load_from_json(mid)

        # 如果 JSON 没有，尝试实时 API
        if info is None or df.empty:
            if live:
                info, df = _fetch_live(mid, max_videos)
            else:
                raise ValueError(
                    f"UID {mid} 无预取数据。请点击「实时获取」或选择其他 UP 主。\n"
                    f"No pre-fetched data for UID {mid}. Click 'Live Fetch' or select another creator."
                )

        if df.empty:
            raise ValueError("未找到视频数据 / No videos found")

        # 确保数值列正确转换（双重保险）
        numeric_cols = ["views", "likes", "favorites", "comments", "shares", "engagement"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        if "engagement_rate" in df.columns:
            df["engagement_rate"] = pd.to_numeric(df["engagement_rate"], errors="coerce").fillna(0.0).astype(float)

        cards = _build_kpi_cards(info, df)

        # 构建 KPI HTML
        kpi_html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:12px 0;">'
        for c in cards:
            kpi_html += f'''
            <div style="background:linear-gradient(135deg,#f8f9fa,#e9ecef);border-radius:12px;padding:16px;
                        border-left:4px solid {COLOR_PRIMARY};box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                <div style="color:#666;font-size:12px;margin-bottom:6px;">{c['label']}</div>
                <div style="font-size:24px;font-weight:700;color:{COLOR_PRIMARY};">{c['value']}</div>
                <div style="color:#999;font-size:11px;margin-top:4px;">{c['sub']}</div>
            </div>'''
        kpi_html += "</div>"

        # UP 主信息卡
        name = info.get("name", "Unknown")
        followers = info.get("followers", 0)
        video_count = info.get("video_count", len(df))
        up_html = f'''
        <div style="background:linear-gradient(90deg,{COLOR_PRIMARY},{COLOR_SECONDARY});
                    border-radius:16px;padding:24px;color:white;margin-bottom:16px;
                    display:flex;align-items:center;gap:20px;box-shadow:0 4px 20px rgba(0,174,236,0.3);">
            <div style="width:72px;height:72px;border-radius:50%;background:rgba(255,255,255,0.3);
                        display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:700;">
                {name[0] if name else "?"}
            </div>
            <div style="flex:1;">
                <div style="font-size:22px;font-weight:700;">{name}</div>
                <div style="font-size:13px;opacity:0.95;margin-top:4px;">
                    UID: {mid} · 粉丝 / Followers: {_fmt_num(followers)} · 
                    视频 / Videos: {video_count}
                </div>
            </div>
        </div>'''

        # 生成图表
        fig_trend = _plot_trend(df)
        fig_top = _plot_top_videos(df)
        fig_monthly = _plot_monthly(df)
        fig_heatmap = _plot_heatmap(df)

        # 洞察
        insights = _generate_insights(df, info)
        insights_html = "<div style='padding:8px 0;'>" + "</div><div style='padding:8px 0;'>".join(insights) + "</div>"

        # 数据表
        table_df = df.head(50)[["title", "date", "views", "likes", "favorites", "comments", "engagement_rate"]].copy()
        table_df.columns = ["标题 / Title", "日期 / Date", "播放 / Views", "点赞 / Likes",
                           "投币 / Favorites", "评论 / Comments", "互动率 / ER%"]

        status_msg = "✅ 已加载（缓存）/ Loaded (Cached)"
        if live:
            status_msg = "✅ 已加载（实时）/ Loaded (Live)"

        return (
            up_html, kpi_html, fig_trend, fig_top, fig_monthly, fig_heatmap,
            insights_html, table_df, status_msg,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_html = f'<div style="background:#ffebee;color:#c62828;padding:16px;border-radius:8px;margin:12px 0;white-space:pre-wrap;">'
        error_html += f"❌ 错误 / Error: {str(e)}"
        error_html += "</div>"
        return (error_html, "", None, None, None, None, "", pd.DataFrame(), "❌ 加载失败 / Failed")


def build_app():
    """构建 Gradio 应用。"""
    with gr.Blocks(title="B站 UP 主数据分析器 / Bilibili Creator Data Analyzer") as app:

        gr.HTML("""
        <div style="background:linear-gradient(90deg,#00AEEC,#FB7299);color:white;padding:20px;border-radius:16px;margin-bottom:20px;text-align:center;">
            <h1 style="margin:0;font-size:28px;">📺 B站 UP 主数据分析器</h1>
            <p style="margin:4px 0 0 0;opacity:0.95;font-size:14px;">
                Bilibili Creator Data Analyzer · 实时 API 数据 · 智能洞察仪表盘
            </p>
        </div>
        """)

        with gr.Row(equal_height=False):
            # 左侧控制
            with gr.Column(scale=1):
                gr.Markdown("### 🔍 选择 UP 主 / Select Creator")

                preset = gr.Radio(
                    choices=[f"{n} ({uid})" for n, uid in PRESET_UPS],
                    value=f"{PRESET_UPS[0][0]} ({PRESET_UPS[0][1]})",
                    label="预设 / Presets",
                )
                uid_input = gr.Number(
                    label="或输入 UID / Or enter UID",
                    value=946974, precision=0,
                )
                fetch_btn = gr.Button("🚀 分析 (本地缓存) / Analyze (Cached)", variant="primary")
                live_btn = gr.Button("🌐 实时获取 / Live Fetch", variant="secondary")

                status = gr.Textbox(label="状态 / Status", interactive=False, value="就绪 / Ready")

                gr.Markdown("---")
                gr.Markdown("### 📦 导出 / Export")
                export_btn = gr.Button("⬇️ 导出 CSV / Export CSV")
                csv_file = gr.File(label="下载 / Download", file_types=[".csv"])

            # 右侧仪表板
            with gr.Column(scale=3):
                up_header = gr.HTML()
                kpi_html = gr.HTML()

                with gr.Row():
                    fig_trend = gr.Plot()
                    fig_top = gr.Plot()

                with gr.Row():
                    fig_monthly = gr.Plot()
                    fig_heatmap = gr.Plot()

                gr.Markdown("### 💡 数据洞察 / Insights")
                insights_html = gr.HTML()

                gr.Markdown("### 📋 视频数据表 / Video Data Table")
                table = gr.Dataframe(wrap=True)

        # ── 事件绑定 ──────────────────────────────────────────────────
        def on_preset_change(preset_str, current_uid):
            for name, uid in PRESET_UPS:
                if f"{name} ({uid})" == preset_str:
                    return uid
            return current_uid

        def on_fetch(uid):
            return load_up(int(uid), live=False)

        def on_live(uid):
            return load_up(int(uid), live=True)

        preset.change(on_preset_change, [preset, uid_input], uid_input)
        outputs = [up_header, kpi_html, fig_trend, fig_top, fig_monthly, fig_heatmap,
                   insights_html, table, status]

        fetch_btn.click(on_fetch, [uid_input], outputs)
        live_btn.click(on_live, [uid_input], outputs)

        def on_export(table_df):
            if table_df is None or table_df.empty:
                return None
            path = "bilibili_data.csv"
            table_df.to_csv(path, index=False, encoding="utf-8-sig")
            return path

        export_btn.click(on_export, [table], csv_file)

        # 启动时自动加载示例
        def _load_demo():
            try:
                # 写调试日志到文件
                debug_path = os.path.join(os.path.dirname(__file__), "debug.log")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write("_load_demo called\n")
                    f.write(f"DATA_DIR: {DATA_DIR}\n")
                    f.write(f"JSON exists: {os.path.exists(os.path.join(DATA_DIR, 'up_946974.json'))}\n")
                res = load_up(946974, live=False)
                with open(debug_path, "a", encoding="utf-8") as f:
                    f.write(f"load_up returned {len(res)} values\n")
                    f.write(f"status: {res[8] if len(res) > 8 else 'N/A'}\n")
                return res
            except Exception as e:
                import traceback
                debug_path = os.path.join(os.path.dirname(__file__), "debug.log")
                with open(debug_path, "a", encoding="utf-8") as f:
                    f.write(f"ERROR: {e}\n")
                    f.write(traceback.format_exc())
                raise

        app.load(fn=_load_demo, outputs=outputs)

    return app


if __name__ == "__main__":
    app = build_app()
    app.launch(
        server_name="127.0.0.1", server_port=7861, share=False,
        theme=gr.themes.Soft(),
    )
