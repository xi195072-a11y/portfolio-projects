"""
B站 UP 主数据分析器 — Streamlit 毛玻璃仪表板
Bilibili Creator Data Analyzer — Streamlit Glassmorphism Dashboard

数据来源：
- 默认：预取 JSON 文件（data/ 目录，稳定可靠）
- 可选：实时 B站 API（dm_img_* + WBI 签名 + Playwright）
"""
from __future__ import annotations

import os
import sys
import json
import tempfile

# ── 关键：确保 Streamlit Runtime 子进程也能找到 .packages 里的依赖 ──
# （Streamlit 会 fork 子进程执行用户代码，sys.path 不一定继承启动脚本的设置）
_here = os.path.dirname(os.path.abspath(__file__))
_pkgs = os.path.join(_here, ".packages")
if os.path.isdir(_pkgs) and _pkgs not in sys.path:
    sys.path.insert(0, _pkgs)
if _here not in sys.path:
    sys.path.insert(0, _here)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    --txt-2: #e0e4ec;
    --muted: #b8c0cc;
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
    background: rgba(10,14,20,0.92) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}
section[data-testid="stSidebar"] .block-container {
    color: #e0e4ec !important;
}
section[data-testid="stSidebar"] label {
    color: #e8ecf4 !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stMarkdownContainer {
    color: #d8dce6 !important;
}
section[data-testid="stSidebar"] .stCaptionContainer {
    color: #b8c0cc !important;
}
section[data-testid="stSidebar"] hr {
    border-top: 1px solid rgba(255,255,255,0.10) !important;
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
    color: #e4e8f0 !important;
    font-weight: 600 !important;
}
.stMarkdown, .stMarkdown p, .stMarkdown li { color: var(--txt-2) !important; }
.stMetric label { color: #c8d0dc !important; }
.caption, div[data-testid="stCaptionContainer"] {
    color: #c0c8d4 !important;
    opacity: 1 !important;
}
/* Streamlit 原生文字/提示/info box 对比度增强 */
div[data-testid="stAlert"] { color: var(--txt) !important; }
div[data-testid="stInfo"] { color: var(--txt) !important; }
div[data-testid="stSuccess"] { color: var(--txt) !important; }
div[data-testid="stWarning"] { color: var(--txt) !important; }
div[data-testid="stError"] { color: var(--txt) !important; }
div[data-testid="stMarkdownContainer"] p { color: var(--txt-2) !important; }
.st-emotion-cache-10trblm { color: #c0c8d4 !important; }

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


def _fetch_live(
    mid: int,
    max_videos: int = 30,
    user_cookie: str = "",
    use_playwright: bool | None = None,
) -> tuple[dict | None, pd.DataFrame]:
    """从 B站 API 实时获取。

    Args:
        use_playwright: None=自动（优先 Playwright）, True=Playwright, False=requests+Cookie
    """
    try:
        from bilibili_api import quick_fetch
        info, df = quick_fetch(
            mid,
            max_videos=max_videos,
            user_cookie=user_cookie,
            use_playwright=use_playwright,
        )
        if df.empty:
            return None, pd.DataFrame()
        info_dict = {
            "mid": info.mid, "name": info.name,
            "face": info.face, "followers": info.followers,
            "video_count": info.video_count or len(df),
        }
        return info_dict, df
    except Exception as e:
        # 错误信息存在 session_state 里，供上层决定如何显示
        st.session_state["_last_error"] = str(e)
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
    st.markdown(
        "<div style='font-size:0.7rem; color:var(--muted); margin-bottom:0.5rem;'>"
        "💡 侧边栏可折叠：点击左上角 › 按钮展开 / Sidebar collapsed? Click › to expand"
        "</div>",
        unsafe_allow_html=True,
    )

    # 预设列表 + 自定义选项（默认选中自定义，让输入框始终可见）
    preset_labels = [f"{n} ({uid})" for n, uid in PRESET_UPS]
    preset_labels.append("✏️ 自定义 UID / Custom UID")
    selected_preset = st.radio("预设 / Presets", preset_labels, index=len(preset_labels) - 1)

    # 根据选中的预设确定初始 UID
    is_custom = "自定义" in selected_preset
    if is_custom:
        # 自定义模式：保留用户上次输入的值，不要覆盖
        default_uid = st.session_state.get("custom_uid_input", 14476927)
    else:
        # 预设模式：强制使用预设 UID
        for name, uid in PRESET_UPS:
            if f"{name} ({uid})" == selected_preset:
                default_uid = uid
                break

    # 关键：如果预设切换了，删掉旧 session_state 让新 value 生效
    if "cached_preset" not in st.session_state:
        st.session_state.cached_preset = selected_preset
    if st.session_state.cached_preset != selected_preset:
        # 预设变了 → 删掉 custom_uid_input，让 number_input 的 value= 生效
        st.session_state.pop("custom_uid_input", None)
        st.session_state.cached_preset = selected_preset
        # 重新确定 default_uid（因为 pop 后需要用 value= 参数）
        if not is_custom:
            default_uid = next((uid for name, uid in PRESET_UPS if f"{name} ({uid})" == selected_preset), 14476927)
        else:
            default_uid = 14476927

    # 只有预设模式才强制同步 session_state → 防止预设切换时值不更新
    # 自定义模式保留用户输入，不要 pop
    if not is_custom:
        if "custom_uid_input" in st.session_state:
            if st.session_state.custom_uid_input != default_uid:
                st.session_state.pop("custom_uid_input", None)

    # 输入框始终可见，预设切换自动填充 UID
    uid_input = st.number_input(
        "输入 UID / Enter UID",
        min_value=1, step=1, format="%d",
        value=default_uid,
        key="custom_uid_input",
    )
    mid = int(uid_input)
    st.caption("💡 输入任意 B站 UID，点击下方按钮分析 / Enter any Bilibili UID")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        cached_btn = st.button("🚀 缓存分析", use_container_width=True)
    with col_btn2:
        live_btn = st.button("🌐 实时获取", use_container_width=True)

    st.markdown("---")
    st.markdown("### ⚙️ 抓取模式 / Fetch Mode")
    # 检测 Playwright 是否可用
    try:
        from bilibili_api import is_playwright_available
        _pw_avail = is_playwright_available()
    except Exception as _e:
        _pw_avail = False
        # 调试：显示具体错误原因
        st.warning(f"Playwright 检测异常: {_e}")
        st.caption(f"sys.path[:3] = {sys.path[:3]}")

    mode_opts = [
        ("🤖 自动（推荐）/ Auto (Recommended)", None),
    ]
    if _pw_avail:
        mode_opts.append(("🎭 Playwright 真实浏览器 / Playwright Browser", True))
    mode_opts.append(("🍪 Cookie 模式 / Cookie Mode (requests)", False))

    selected_mode_label = st.radio(
        "抓取模式 / Fetch Mode",
        [k for k, _ in mode_opts],
        index=0,
        help=(
            "Playwright = 不需要 Cookie，安装后直接搜；"
            "Cookie 模式 = 需要登录 B站 获得 Cookie 绕过反爬"
        ),
    )
    # 拿到对应的 use_playwright 值
    use_playwright: bool | None = next(
        (v for k, v in mode_opts if k == selected_mode_label), None
    )

    if _pw_avail:
        st.success("🎭 Playwright 已就绪 / Playwright ready — 无需 Cookie 即可搜索")
    else:
        if use_playwright is True:
            st.error(
                "❌ 选择了 Playwright 但未安装 / Playwright not installed.\n"
                "安装命令（无需下浏览器，会自动复用系统 Chrome）:\n"
                "```\n"
                "pip install playwright\n"
                "```\n"
                "（如系统未装 Chrome/Edge，再执行：playwright install chromium）"
            )
        else:
            st.info(
                "💡 想直接搜索（无需 Cookie）？安装 Playwright：\n"
                "```\n"
                "pip install playwright\n"
                "```\n"
                "（自动复用系统 Chrome/Edge，不用额外下载浏览器；装完重启应用）"
            )

    st.markdown("---")
    st.markdown("### 🔑 B站登录 / Bilibili Login")
    # Cookie 模式下显示更详细的引导；Playwright 模式下可以跳过
    if use_playwright is True or (use_playwright is None and _pw_avail):
        st.caption(
            "🎭 当前使用 Playwright，**不需要** Cookie 即可搜索任意 UID / "
            "Playwright mode: no cookie needed for public data"
        )
        # 依然允许用户填 cookie（有 cookie 可以看更多权限字段）
        with st.expander("🔑 可选：手动注入 Cookie / Optional: inject cookie"):
            manual_cookie = st.text_input(
                "粘贴 Cookie / Paste cookie",
                value="",
                type="password",
                key="pw_manual_cookie",
            )
        user_cookie = manual_cookie if manual_cookie else ""
    else:
        # ── Cookie 模式的完整流程（兼容之前的逻辑） ──
        # 自动从 Chrome 读取 Cookie
        if "auto_cookie" not in st.session_state:
            try:
                from bilibili_api import auto_read_chrome_cookie
                st.session_state.auto_cookie = auto_read_chrome_cookie()
            except Exception:
                st.session_state.auto_cookie = ""

        # 手动重新读取按钮
        if st.button("🔄 从 Chrome 重新读取 / Re-read from Chrome", use_container_width=True):
            try:
                from bilibili_api import auto_read_chrome_cookie
                st.session_state.auto_cookie = auto_read_chrome_cookie()
            except Exception as e:
                st.session_state.auto_cookie = ""
            st.rerun()

        auto_cookie = st.session_state.get("auto_cookie", "")

        if auto_cookie and "SESSDATA" in auto_cookie:
            st.success("✅ 已从 Chrome 读取登录态 / Login cookie found")
            user_cookie = auto_cookie
        elif auto_cookie:
            st.warning("⚠️ 读取到 Cookie 但未登录 / Cookie found but not logged in")
            st.caption("在 Chrome 中登录 bilibili.com 后重启 / Log into bilibili.com in Chrome then restart")
            user_cookie = auto_cookie  # 仍可用 buvid3 等
        else:
            st.warning("⚠️ 未读取到 Cookie / No Chrome cookie found")
            st.caption(
                "在 Chrome 登录 bilibili.com 后点上方按钮 / "
                "Login bilibili.com in Chrome then click above"
            )
            user_cookie = ""

        # 手动覆盖
        manual_cookie = st.text_input(
            "或手动粘贴 Cookie / Or paste manually",
            value="",
            type="password",
            help="覆盖自动读取的 Cookie / Override auto-read cookie",
        )
        if manual_cookie:
            user_cookie = manual_cookie
            st.success("✅ 手动 Cookie 已注入 / Manual cookie injected")

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
force_reload = cached_btn or live_btn
mid_changed = st.session_state.get("current_mid") != mid
error_state = st.session_state.get("error_state", False)

# 预设模式：切换时自动加载；自定义模式：必须点击按钮
should_load = force_reload or "df_cache" not in st.session_state or (not is_custom and mid_changed)

if should_load:
    info = None
    df = pd.DataFrame()
    # 搜索新 UID 时，清除旧缓存，避免显示旧数据
    if mid_changed or force_reload:
        st.session_state.pop("df_cache", None)
        st.session_state.pop("info_cache", None)
        error_state = False

    if live_btn:
        # ── 实时获取模式 ──
        with st.spinner("🌐 正在从 B站 实时获取... / Fetching live data from Bilibili..."):
            info, df = _fetch_live(mid, user_cookie=user_cookie, use_playwright=use_playwright)
            if info is None or df.empty:
                info, df = _load_from_json(mid)
    else:
        # ── 缓存分析模式（默认） ──
        # 1. 先尝试缓存
        info, df = _load_from_json(mid)

        # 2. 缓存不存在 → 自动尝试实时 API
        if info is None or df.empty:
            with st.spinner("🌐 缓存未找到，正在获取... / Cache miss, fetching..."):
                info, df = _fetch_live(mid, user_cookie=user_cookie, use_playwright=use_playwright)
                if info is not None and not df.empty:
                    # 实时成功 → 自动保存为缓存
                    try:
                        cache_path = os.path.join(DATA_DIR, f"up_{mid}.json")
                        info_dict = info if isinstance(info, dict) else vars(info)
                        videos_list = []
                        for _, row in df.iterrows():
                            record = {}
                            for col in df.columns:
                                val = row[col]
                                if pd.notna(val) and isinstance(val, (pd.Timestamp,)):
                                    record[col] = val.isoformat()
                                elif pd.isna(val):
                                    record[col] = None
                                else:
                                    record[col] = val if not isinstance(val, (pd.Timestamp,)) else str(val)
                            videos_list.append(record)
                        cache_data = {"info": info_dict, "videos": videos_list}
                        os.makedirs(DATA_DIR, exist_ok=True)
                        with open(cache_path, "w", encoding="utf-8") as f:
                            json.dump(cache_data, f, ensure_ascii=False, indent=2, default=str)
                        st.success(f"✅ 数据已缓存 / Data cached: {cache_path}")
                    except Exception as e:
                        st.warning(f"⚠️ 缓存保存失败（不影响展示）/ Cache save failed: {e}")

        # 3. 缓存和实时都失败
        if info is None or df.empty:
            error_state = True
            st.session_state["error_state"] = True
            st.session_state["error_mid"] = mid
        else:
            error_state = False
            st.session_state["error_state"] = False

    if not error_state:
        st.session_state["df_cache"] = df
        st.session_state["info_cache"] = info
        st.session_state["current_mid"] = mid
        st.session_state["error_state"] = False

# ── 条件渲染：错误页 / 数据页 / 空状态页 ────────────────────────
if error_state:
    err_mid = st.session_state.get("error_mid", mid)
    err_detail = st.session_state.get("_last_error", "未知错误")
    st.markdown(f"""
    <div class="glass" style="text-align:center; padding:2rem;">
        <div style="font-size:2rem; margin-bottom:0.5rem;">😵</div>
        <div style="color:var(--txt); font-size:1.1rem; margin-bottom:0.5rem;">
            UID {err_mid} 数据无法加载
        </div>
        <div style="color:var(--muted); font-size:0.9rem;">
            错误 / Error: {err_detail}<br><br>
            💡 建议：在侧边栏粘贴 B站 Cookie 后重试 / Paste Bilibili Cookie in sidebar and retry.
        </div>
    </div>
    """, unsafe_allow_html=True)

elif "df_cache" in st.session_state and not st.session_state["df_cache"].empty:
    df = st.session_state["df_cache"]
    info = st.session_state["info_cache"]

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

else:
    # 空状态：首次打开或没有数据
    st.markdown("""
    <div class="glass" style="text-align:center; padding:2rem;">
        <div style="color:var(--muted);">请选择 UP 主并点击分析按钮 / Please select a creator and click Analyze</div>
    </div>
    """, unsafe_allow_html=True)

# ── 页脚 ──────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:1rem 0; color:var(--muted); font-size:0.72rem;">
    Built by 小希 · Powered by B站 API + Streamlit + Plotly · Glassmorphism UI
</div>
""", unsafe_allow_html=True)
