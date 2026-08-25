"""
B站 UP 主数据分析器 — Streamlit 毛玻璃仪表板
Bilibili Creator Data Analyzer — Streamlit Glassmorphism Dashboard

数据来源：
- 默认：预取 JSON 文件（data/ 目录，稳定可靠）
- 可选：实时 B站 API（dm_img_* + WBI 签名）
"""
from __future__ import annotations

import os
import sys
import json
import tempfile

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 本地依赖路径（requests 等）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".packages"))

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# 预设 UP 主
PRESET_UPS = [
    ("影视飓风 / Stormstorm", 946974),
    ("老番茄 / OldTomato", 546195),
    ("半佛仙人 / Bafo", 37663924),
]

# B站配色
C_PRIMARY = "#00AEEC"
C_SECONDARY = "#FB7299"


# ═══════════════════════════════════════════════════════════════════
# 毛玻璃设计系统
# ═══════════════════════════════════════════════════════════════════
GLASS_CSS = """
<style>
:root {
    --bg: #0a0e14;
    --txt: #ffffff;
    --txt-2: #d4d8e0;
    --muted: #a8afba;
    --accent: #00AEEC;
    --accent-2: #FB7299;
    --glass-bg: rgba(255,255,255,0.04);
    --glass-border: rgba(255,255,255,0.08);
    --r: 16px;
}

.stApp {
    background:
        radial-gradient(900px 600px at 5% -5%, rgba(0,174,236,0.12) 0%, transparent 50%),
        radial-gradient(800px 500px at 95% 5%, rgba(251,114,153,0.10) 0%, transparent 50%),
        radial-gradient(700px 500px at 50% 100%, rgba(139,92,246,0.06) 0%, transparent 50%),
        #0a0e14;
}

header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, 'Segoe UI', system-ui, sans-serif;
    color: var(--txt);
    -webkit-font-smoothing: antialiased;
}
h1, h2, h3, h4 { color: var(--txt) !important; letter-spacing: -0.02em; }

/* 毛玻璃卡片 */
.glass {
    background: var(--glass-bg);
    backdrop-filter: blur(20px) saturate(150%);
    -webkit-backdrop-filter: blur(20px) saturate(150%);
    border: 1px solid var(--glass-border);
    border-radius: var(--r);
    box-shadow: 0 8px 32px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.05);
    padding: 1.2rem;
    margin-bottom: 1rem;
    animation: fadeUp 0.5s ease both;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: none; }
}

/* 渐变标题 */
.gradient-title {
    background: linear-gradient(90deg, #00AEEC, #FB7299);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
}

/* KPI 卡片网格 */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.7rem;
    margin-bottom: 1rem;
}
.kpi-card {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 3px solid var(--accent);
    border-radius: 12px;
    padding: 0.9rem;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,174,236,0.15);
}
.kpi-card .label { font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.kpi-card .value { font-size: 1.5rem; font-weight: 800; color: var(--accent); margin-top: 0.25rem; line-height: 1.1; }
.kpi-card .sub { font-size: 0.68rem; color: var(--muted); margin-top: 0.2rem; }

/* UP 主头部 */
.up-header {
    background: linear-gradient(90deg, rgba(0,174,236,0.15), rgba(251,114,153,0.12));
    backdrop-filter: blur(20px) saturate(150%);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.up-avatar {
    width: 64px; height: 64px; border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    display: flex; align-items: center; justify-content: center;
    font-size: 1.8rem; font-weight: 800; color: white; flex: none;
    box-shadow: 0 4px 16px rgba(0,174,236,0.3);
}
.up-name { font-size: 1.4rem; font-weight: 700; color: var(--txt); }
.up-meta { font-size: 0.8rem; color: var(--txt-2); margin-top: 0.2rem; }

/* 洞察列表 */
.insight-item {
    background: rgba(255,255,255,0.02);
    border-left: 3px solid var(--accent-2);
    padding: 0.6rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    font-size: 0.88rem;
    color: var(--txt-2);
}

/* Streamlit 组件覆盖 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: var(--txt) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(0,174,236,0.12) !important;
}
.stSelectbox > div > div > div[data-baseweb="select"] {
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    background: rgba(255,255,255,0.04) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #00AEEC, #FB7299) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 16px rgba(0,174,236,0.25) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(0,174,236,0.35) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: var(--txt) !important;
}

/* 侧边栏 */
section[data-testid="stSidebar"] {
    background: rgba(10,14,20,0.8) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}

/* 数据表 */
.dataframe {
    background: rgba(255,255,255,0.02) !important;
    border-radius: 10px !important;
}
.dataframe th { background: rgba(0,174,236,0.1) !important; color: var(--accent) !important; }
.dataframe td { color: var(--txt-2) !important; }

/* 分割线 */
hr {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.06) !important;
    margin: 1rem 0 !important;
}

/* Streamlit 组件覆盖 — 标签文字统一亮色 */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, .stRadio label, .stCheckbox label {
    color: var(--txt-2) !important;
    font-weight: 600 !important;
}
.stMarkdown, .stMarkdown p, .stMarkdown li { color: var(--txt-2) !important; }
.stMetric label { color: var(--muted) !important; }
.caption, .st-emotion-cache-10trblm, div[data-testid="stCaptionContainer"] {
    color: var(--muted) !important;
}

/* 标签 */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--txt-2);
    margin: 0.8rem 0 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.section-label .num {
    width: 1.1rem; height: 1.1rem; border-radius: 6px;
    display: grid; place-items: center;
    font-size: 0.6rem; color: white;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
}
</style>
"""


def inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# 数据处理
# ═══════════════════════════════════════════════════════════════════
def _fmt_num(n: int | float) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(int(n))


def _load_from_json(mid: int) -> tuple[dict | None, pd.DataFrame]:
    """从预取 JSON 加载数据。"""
    filepath = os.path.join(DATA_DIR, f"up_{mid}.json")
    if not os.path.exists(filepath):
        return None, pd.DataFrame()

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    info = data["info"]
    df = pd.DataFrame(data["videos"])

    # 转换日期
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # 转换数值列（JSON 中都是字符串）
    for col in ["views", "likes", "favorites", "comments", "shares", "engagement"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    if "engagement_rate" in df.columns:
        df["engagement_rate"] = pd.to_numeric(df["engagement_rate"], errors="coerce").fillna(0.0).astype(float)

    # 补充列
    if "engagement" not in df.columns:
        df["engagement"] = df["likes"] + df["favorites"] + df["comments"] + df["shares"]
    if "engagement_rate" not in df.columns:
        df["engagement_rate"] = df.apply(
            lambda r: round(r["engagement"] / r["views"] * 100, 2) if r["views"] > 0 else 0.0,
            axis=1,
        )

    df = df.sort_values("date", ascending=False, na_position="last").reset_index(drop=True)
    return info, df


def _fetch_live(mid: int, max_videos: int = 30) -> tuple[dict | None, pd.DataFrame]:
    """从 B站 API 实时获取。"""
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
        error_msg = str(e)
        # 友好化错误信息
        if "412" in error_msg or "banned" in error_msg.lower():
            st.error(
                f"❌ B站反爬拦截 (412) / Bilibili anti-bot blocked request.\n\n"
                f"原因：B站检测到自动化请求。请稍后重试，或使用「缓存分析」加载已有数据。\n\n"
                f"Reason: B站 detected automated requests. Try again later or use cached data.\n\n"
                f"详细错误 / Detail: {error_msg}"
            )
        elif "404" in error_msg:
            st.error(f"❌ UID {mid} 不存在 / UID {mid} not found")
        elif "超时" in error_msg or "timeout" in error_msg.lower():
            st.error(f"❌ 请求超时 / Request timeout: {error_msg}")
        else:
            st.error(f"❌ 实时 API 获取失败 / Live API failed: {error_msg}")
        return None, pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════
# 图表生成
# ═══════════════════════════════════════════════════════════════════
PLOT_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e8eaed", family="Inter, sans-serif"),
    margin=dict(l=40, r=30, t=50, b=35),
)


def _plot_trend(df: pd.DataFrame) -> go.Figure:
    """播放量趋势 + 7日均线。"""
    daily = df.groupby(df["date"].dt.date)["views"].sum().sort_index()
    if daily.empty:
        return go.Figure()
    ma7 = daily.rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily.index.astype(str), y=daily.values,
        name="日播放 / Daily", marker_color=C_PRIMARY, opacity=0.5,
        hovertemplate="📅 %{x}<br>▶️ %{y:,}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily.index.astype(str), y=ma7.values,
        name="7日均线 / 7-day MA", mode="lines",
        line=dict(color=C_SECONDARY, width=3),
        hovertemplate="📅 %{x}<br>📈 %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        title="播放量趋势 / View Trend", height=350,
        xaxis_title="日期 / Date", yaxis_title="播放量 / Views",
        legend=dict(orientation="h", y=1.06, x=0),
        hovermode="x unified", **PLOT_LAYOUT,
    )
    return fig


def _plot_top_videos(df: pd.DataFrame) -> go.Figure:
    """Top 10 视频水平柱状图。"""
    top10 = df.nlargest(10, "views").sort_values("views")
    if top10.empty:
        return go.Figure()
    titles = [t[:25] + "…" if len(t) > 25 else t for t in top10["title"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top10["views"].values, y=titles, orientation="h",
        marker=dict(
            color=top10["views"].values,
            colorscale=[[0, C_PRIMARY], [1, C_SECONDARY]],
        ),
        hovertemplate="<b>%{y}</b><br>▶️ %{x:,}<extra></extra>",
    ))
    fig.update_layout(
        title="Top 10 视频 / Top Videos", height=380,
        xaxis_title="播放量 / Views",
        margin=dict(l=180, r=30, t=50, b=35),
        **{k: v for k, v in PLOT_LAYOUT.items() if k != "margin"},
    )
    return fig


def _plot_monthly(df: pd.DataFrame) -> go.Figure:
    """月度分布双轴图。"""
    df_c = df.copy()
    df_c["month"] = df_c["date"].dt.to_period("M")
    monthly = df_c.groupby("month").agg(
        count=("title", "count"), views=("views", "sum"),
    ).sort_index()
    if monthly.empty:
        return go.Figure()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=[str(m) for m in monthly.index], y=monthly["count"].values,
        name="发布数 / Count", marker_color=C_PRIMARY, opacity=0.6,
        hovertemplate="📅 %{x}<br>🎬 %{y} 条<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=[str(m) for m in monthly.index], y=monthly["views"].values,
        name="播放量 / Views", mode="lines+markers",
        line=dict(color=C_SECONDARY, width=3), marker=dict(size=7),
        hovertemplate="📅 %{x}<br>▶️ %{y:,}<extra></extra>",
    ), secondary_y=True)
    fig.update_layout(
        title="月度发布分布 / Monthly Distribution", height=320,
        legend=dict(orientation="h", y=1.06, x=0),
        hovermode="x unified", **PLOT_LAYOUT,
    )
    fig.update_yaxes(title_text="发布数 / Count", secondary_y=False, gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(title_text="播放量 / Views", secondary_y=True, gridcolor="rgba(255,255,255,0.05)")
    return fig


def _plot_heatmap(df: pd.DataFrame) -> go.Figure:
    """发布时间热力图。"""
    df_c = df.copy()
    df_c["weekday"] = df_c["date"].dt.dayofweek
    df_c["hour"] = df_c["date"].dt.hour

    pivot = df_c.pivot_table(index="weekday", columns="hour", values="title", aggfunc="count", fill_value=0)
    weekdays_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekdays_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"{h}:00" for h in range(24)],
        y=[f"{weekdays_cn[i]} {weekdays_en[i]}" for i in pivot.index],
        colorscale=[[0, "rgba(15,20,30,0.3)"], [0.5, C_PRIMARY], [1, C_SECONDARY]],
        hovertemplate="📅 %{y}<br>🕐 %{x}<br>🎬 %{z} 条<extra></extra>",
    ))
    fig.update_layout(
        title="发布时间热力图 / Upload Heatmap", height=300,
        xaxis_title="小时 / Hour", yaxis_title="星期 / Weekday",
        xaxis_nticks=24, **PLOT_LAYOUT,
    )
    return fig


def _plot_engagement(df: pd.DataFrame) -> go.Figure:
    """互动构成饼图。"""
    total_likes = int(df["likes"].sum())
    total_favs = int(df["favorites"].sum())
    total_comments = int(df["comments"].sum())
    total_shares = int(df["shares"].sum())

    fig = go.Figure(data=go.Pie(
        labels=["点赞 / Likes", "投币 / Favorites", "评论 / Comments", "分享 / Shares"],
        values=[total_likes, total_favs, total_comments, total_shares],
        hole=0.55,
        marker=dict(colors=[C_PRIMARY, C_SECONDARY, "#8b5cf6", "#10b981"]),
        textinfo="label+percent",
        textfont_size=11,
        hovertemplate="<b>%{label}</b><br>数量: %{value:,}<extra></extra>",
    ))
    fig.update_layout(
        title="互动构成 / Engagement Breakdown", height=300,
        showlegend=False, **PLOT_LAYOUT,
    )
    return fig


def _generate_insights(df: pd.DataFrame, info: dict) -> list[str]:
    """生成数据洞察。"""
    if df.empty:
        return ["暂无数据 / No data"]

    insights = []
    cn_wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    en_wd = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    df_c = df.copy()
    df_c["weekday"] = df_c["date"].dt.dayofweek
    df_c["hour"] = df_c["date"].dt.hour

    best_w = int(df_c.groupby("weekday")["views"].sum().idxmax())
    best_h = int(df_c.groupby("hour")["views"].sum().idxmax())
    insights.append(
        f"🗓️ 最佳发布时间 / Best Upload Time: "
        f"{cn_wd[best_w]} {best_h}:00 ({en_wd[best_w]} {best_h}:00)"
    )

    total = df["views"].sum()
    top5 = df.nlargest(5, "views")["views"].sum()
    ratio = round(top5 / total * 100, 1) if total > 0 else 0
    insights.append(f"📊 头部集中度 / Top 5 Contribution: Top 5 视频贡献 {ratio}% 总播放")

    avg_er = round(df["engagement_rate"].mean(), 2)
    level = "高 / High" if avg_er >= 5 else ("中等 / Medium" if avg_er >= 2 else "低 / Low")
    insights.append(f"💬 平均互动率 / Avg Engagement Rate: {avg_er}% ({level})")

    df_c["month"] = df_c["date"].dt.to_period("M")
    monthly_count = df_c.groupby("month").size()
    avg_monthly = round(monthly_count.mean(), 1) if len(monthly_count) > 0 else 0
    insights.append(f"📈 更新频率 / Upload Frequency: 平均每月 {avg_monthly} 条")

    recent = df[df["date"] >= pd.Timestamp.now() - pd.Timedelta(days=90)]
    older = df[df["date"] < pd.Timestamp.now() - pd.Timedelta(days=90)]
    if len(recent) > 0 and len(older) > 0:
        r_avg = recent["views"].mean()
        o_avg = older["views"].mean()
        if r_avg > o_avg * 1.2:
            trend = "↑ 上升 / Rising"
        elif r_avg < o_avg * 0.8:
            trend = "↓ 下降 / Declining"
        else:
            trend = "→ 稳定 / Stable"
        insights.append(f"📉 近期趋势 / Recent Trend: {trend}")

    return insights


# ═══════════════════════════════════════════════════════════════════
# Streamlit UI
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="B站 UP 主数据分析器", page_icon="📺", layout="wide")
inject_css()

# ── 标题 ──────────────────────────────────────────────────────────
st.markdown("""
<div class="glass" style="text-align:center; padding:1.5rem;">
    <div style="font-size:2rem; margin-bottom:0.3rem;">📺</div>
    <div class="gradient-title">B站 UP 主数据分析器</div>
    <div style="font-size:0.85rem; color:var(--txt-2); margin-top:0.2rem;">
        Bilibili Creator Data Analyzer · 智能洞察仪表盘 · Glassmorphism UI
    </div>
</div>
""", unsafe_allow_html=True)

# ── 侧边栏 ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 选择 UP 主 / Select Creator")

    # 预设列表 + 自定义选项
    preset_labels = [f"{n} ({uid})" for n, uid in PRESET_UPS]
    preset_labels.append("✏️ 自定义 UID / Custom UID")
    selected_preset = st.radio("预设 / Presets", preset_labels, index=0, key="preset_radio")

    # 判断是否选了自定义
    is_custom = selected_preset == "✏️ 自定义 UID / Custom UID"

    # 预设 UID
    selected_uid = PRESET_UPS[0][1]
    if not is_custom:
        for name, uid in PRESET_UPS:
            if f"{name} ({uid})" == selected_preset:
                selected_uid = uid
                break

    # 关键修复：预设切换时，通过 widget 的 key 直接修改 session_state
    # Streamlit 有 key 的 widget 值存储在 session_state[key] 中
    if "last_preset" not in st.session_state:
        st.session_state["last_preset"] = selected_preset
        st.session_state["uid_input_widget"] = selected_uid

    if st.session_state["last_preset"] != selected_preset:
        st.session_state["last_preset"] = selected_preset
        if not is_custom:
            # 直接修改 widget 对应的 session_state key，下一次 rerun 就会用新值
            st.session_state["uid_input_widget"] = selected_uid

    # 自定义模式：初始化 uid_input_widget
    if "uid_input_widget" not in st.session_state:
        st.session_state["uid_input_widget"] = selected_uid

    uid_input = st.number_input(
        "或输入 UID / Or enter UID",
        step=1, format="%d",
        key="uid_input_widget",
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        cached_btn = st.button("🚀 缓存分析", use_container_width=True)
    with col_btn2:
        live_btn = st.button("🌐 实时获取", use_container_width=True)

    st.markdown("---")
    st.markdown("### 📦 导出 / Export")
    export_btn = st.button("⬇️ 导出 CSV / Export CSV", use_container_width=True)

    st.markdown("---")
    st.markdown("### ℹ️ About / 关于")
    st.markdown(
        "<div style='font-size:0.75rem; color:var(--muted); line-height:1.6;'>"
        "本工具从 B站 API 获取 UP 主视频数据，<br>"
        "通过可视化图表展示数据分析结果。<br><br>"
        "Built by 小希 · Streamlit + Plotly"
        "</div>",
        unsafe_allow_html=True,
    )

# ── 主内容区 ──────────────────────────────────────────────────────
mid = int(uid_input)
force_reload = cached_btn or live_btn

if force_reload or "df_cache" not in st.session_state or st.session_state.get("current_mid") != mid:
    if live_btn:
        # 实时获取模式：先尝试实时 API，失败再回退到缓存
        with st.spinner("🌐 实时获取中... / Fetching live data..."):
            info, df = _fetch_live(mid)
            if info is None or df.empty:
                # 实时失败，回退到缓存
                st.warning("⚠️ 实时获取失败，正在加载缓存数据... / Live fetch failed, loading cached data...")
                info, df = _load_from_json(mid)
                if info is not None and not df.empty:
                    st.info("💡 已回退到缓存数据 / Fallback to cached data")
    else:
        # 缓存分析模式：先尝试 JSON 缓存，没有就自动回退到实时 API
        with st.spinner("加载缓存数据... / Loading cached data..."):
            info, df = _load_from_json(mid)
            # 关键修复：任何 UID 缓存不存在都自动尝试实时获取，不限于预设
            if info is None or df.empty:
                st.warning("⚠️ 缓存不存在，正在从 B站 实时获取... / Cache not found, fetching from Bilibili API...")
                with st.spinner("🌐 实时获取中... / Fetching live data..."):
                    info, df = _fetch_live(mid)
                    if info is not None and not df.empty:
                        # 实时获取成功，自动保存为缓存
                        try:
                            cache_path = os.path.join(DATA_DIR, f"up_{mid}.json")
                            cache_data = {
                                "info": info if isinstance(info, dict) else vars(info),
                                "videos": df.to_dict(orient="records"),
                            }
                            with open(cache_path, "w", encoding="utf-8") as f:
                                json.dump(cache_data, f, ensure_ascii=False, indent=2, default=str)
                        except Exception:
                            pass  # 保存缓存失败不影响展示

    # 最终检查数据是否可用
    if info is None or df.empty:
        st.markdown(f"""
        <div class="glass" style="text-align:center; padding:2rem;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">🔍</div>
            <div style="color:var(--muted);">
                UID {mid} 无数据。请检查 UID 是否正确，或选择预设 UP 主。<br>
                No data for UID {mid}. Check UID or select a preset creator.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    st.session_state["df_cache"] = df
    st.session_state["info_cache"] = info
    st.session_state["current_mid"] = mid

df = st.session_state.get("df_cache")
info = st.session_state.get("info_cache")

if df is None or info is None or df.empty:
    st.markdown("""
    <div class="glass" style="text-align:center; padding:2rem;">
        <div style="color:var(--muted);">请选择 UP 主并点击分析按钮 / Please select a creator and click Analyze</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── UP 主头部 ─────────────────────────────────────────────────────
name = info.get("name", "Unknown")
followers = info.get("followers", 0)
video_count = info.get("video_count", len(df))

st.markdown(f"""
<div class="up-header">
    <div class="up-avatar">{name[0] if name else "?"}</div>
    <div style="flex:1;">
        <div class="up-name">{name}</div>
        <div class="up-meta">
            UID: {mid} · 📊 粉丝 / Followers: <b style="color:var(--accent)">{_fmt_num(followers)}</b> ·
            🎬 视频 / Videos: <b style="color:var(--accent-2)">{video_count}</b>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI 卡片 ─────────────────────────────────────────────────────
total_views = int(df["views"].sum())
total_comments = int(df["comments"].sum())
avg_views = int(df["views"].mean())
max_views = int(df["views"].max())
avg_er = round(df["engagement_rate"].mean(), 2)
recent_30 = df[df["date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)]
recent_views = int(recent_30["views"].sum()) if len(recent_30) > 0 else 0

kpi_data = [
    ("总播放量 / Total Views", _fmt_num(total_views), f"{total_views:,}"),
    ("粉丝数 / Followers", _fmt_num(followers), f"{followers:,}"),
    ("视频总数 / Total Videos", str(video_count), f"抓取 {len(df)} 条"),
    ("总评论 / Comments", _fmt_num(total_comments), f"{total_comments:,}"),
    ("平均播放 / Avg Views", _fmt_num(avg_views), f"{avg_views:,}"),
    ("最高单作 / Top Video", _fmt_num(max_views), f"{max_views:,}"),
    ("互动率 / Engagement", f"{avg_er}%", "平均互动率"),
    ("近30天 / 30d Views", _fmt_num(recent_views), f"{recent_views:,}"),
]

kpi_html = '<div class="kpi-grid">'
for label, value, sub in kpi_data:
    kpi_html += f"""
    <div class="kpi-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>"""
kpi_html += "</div>"
st.markdown(kpi_html, unsafe_allow_html=True)

# ── 图表区 ────────────────────────────────────────────────────────
st.markdown('<div class="section-label"><span class="num">1</span> 📈 数据可视化 / Visualizations</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    st.plotly_chart(_plot_trend(df), use_container_width=True)
with col_b:
    st.plotly_chart(_plot_top_videos(df), use_container_width=True)

col_c, col_d = st.columns(2)
with col_c:
    st.plotly_chart(_plot_monthly(df), use_container_width=True)
with col_d:
    st.plotly_chart(_plot_engagement(df), use_container_width=True)

st.plotly_chart(_plot_heatmap(df), use_container_width=True)

# ── 洞察 ─────────────────────────────────────────────────────────
st.markdown('<div class="section-label"><span class="num">2</span> 💡 数据洞察 / Insights</div>', unsafe_allow_html=True)

insights = _generate_insights(df, info)
insights_html = '<div class="glass" style="padding:1rem;">'
for ins in insights:
    insights_html += f'<div class="insight-item">{ins}</div>'
insights_html += '</div>'
st.markdown(insights_html, unsafe_allow_html=True)

# ── 数据表 ───────────────────────────────────────────────────────
st.markdown('<div class="section-label"><span class="num">3</span> 📋 视频数据表 / Video Data Table</div>', unsafe_allow_html=True)

table_df = df.head(50)[["title", "date", "views", "likes", "favorites", "comments", "engagement_rate"]].copy()
table_df.columns = ["标题 / Title", "日期 / Date", "播放 / Views", "点赞 / Likes",
                     "投币 / Favorites", "评论 / Comments", "互动率 / ER%"]
table_df["日期 / Date"] = table_df["日期 / Date"].dt.strftime("%Y-%m-%d")
st.dataframe(table_df, use_container_width=True, height=400)

# ── 导出 ─────────────────────────────────────────────────────────
if export_btn:
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as f:
        f.write(csv)
        tmp_path = f.name
    st.download_button(
        label="⬇️ 下载 CSV / Download CSV",
        data=csv.encode("utf-8-sig"),
        file_name=f"bilibili_{mid}_data.csv",
        mime="text/csv",
    )
    st.success("CSV 已生成，点击上方按钮下载 / CSV ready, click button above to download")

# ── 页脚 ──────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:1rem 0; color:var(--muted); font-size:0.72rem;">
    Built by 小希 · Powered by B站 API + Streamlit + Plotly · Glassmorphism UI
</div>
""", unsafe_allow_html=True)
