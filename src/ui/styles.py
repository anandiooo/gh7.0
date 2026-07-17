import streamlit as st


def render_global_styles() -> None:
    """Apply the approved cooperative visual identity consistently."""
    st.markdown(
        """
        <style>
        :root {
            --mt-green: #297f39;
            --mt-cream: #faf8ef;
            --mt-neon: #a9eb35;
            --mt-ink: #214916;
            --mt-yellow: #f7dc27;
            --mt-display: "Agrandir Tight", "Arial Narrow", "Helvetica Neue Condensed", sans-serif;
            --mt-body: "Helvetica World", "Helvetica Neue", Helvetica, Arial, sans-serif;
        }
        html, body, .stApp, button, input, textarea, select {
            font-family: var(--mt-body);
        }
        h1, h2, h3, .mt-title, .mt-eyebrow, .mt-section-label {
            font-family: var(--mt-display);
        }
        .stApp {
            background:
                radial-gradient(circle at 92% 4%, rgba(247,220,39,.16), transparent 24rem),
                var(--mt-green);
            color: var(--mt-cream);
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 1320px;
            padding-top: 1.25rem;
            padding-bottom: 4rem;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--mt-ink), #173b10);
            border-right: 1px solid rgba(169,235,53,.38);
        }
        [data-testid="stSidebar"] * { color: var(--mt-cream); }
        [data-testid="stSidebarNav"] a {
            border-radius: 12px;
            margin: .16rem .5rem;
        }
        [data-testid="stSidebarNav"] a:hover { background: rgba(169,235,53,.14); }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(90deg, var(--mt-neon), #cdf681);
            color: var(--mt-ink);
            font-weight: 750;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] * { color: var(--mt-ink); }
        h1, h2, h3 { color: var(--mt-cream); letter-spacing: -.025em; }
        [data-testid="stMetric"],
        [data-testid="stPlotlyChart"],
        [data-testid="stDataFrame"] {
            background: rgba(250,248,239,.98);
            border: 1px solid rgba(169,235,53,.45);
            border-radius: 16px;
            box-shadow: 0 12px 30px rgba(33,73,22,.22);
            overflow: hidden;
        }
        [data-testid="stMetric"] { min-height: 108px; padding: .9rem 1rem; }
        [data-testid="stMetricLabel"] { color: rgba(33,73,22,.72); font-weight: 650; }
        [data-testid="stMetricValue"] { color: var(--mt-ink); font-weight: 780; }
        .stButton > button, [data-testid="stPageLink-NavLink"] {
            border-radius: 11px;
            min-height: 2.65rem;
            font-weight: 720;
        }
        .stButton > button[kind="primary"] {
            background: var(--mt-neon);
            border-color: var(--mt-neon);
            color: var(--mt-ink);
        }
        [data-testid="stForm"], [data-testid="stExpander"] {
            background: rgba(33,73,22,.62);
            border: 1px solid rgba(169,235,53,.36);
            border-radius: 15px;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            background: var(--mt-neon);
            color: var(--mt-ink);
            border-radius: 999px;
        }
        .mt-brand-row { display:flex; align-items:center; gap:.75rem; min-height:58px; }
        .mt-brand-mark {
            display:grid; place-items:center; width:48px; height:48px; border-radius:15px;
            background:linear-gradient(145deg,var(--mt-neon),var(--mt-yellow)); font-size:1.55rem;
        }
        .mt-brand-title { margin:0; color:var(--mt-cream); font-size:clamp(1.8rem,3vw,2.45rem); }
        .mt-brand-tagline { margin:.28rem 0 0; color:rgba(250,248,239,.8); }
        .mt-eyebrow, .mt-section-label {
            color:var(--mt-neon); font-size:.76rem; font-weight:800;
            letter-spacing:.11em; text-transform:uppercase;
        }
        .mt-page-intro {
            margin:.25rem 0 1rem; padding:.9rem 1.15rem;
            background:linear-gradient(120deg,var(--mt-cream),rgba(169,235,53,.9));
            border-radius:18px;
        }
        .mt-page-intro h2 { margin:.12rem 0 .18rem; color:var(--mt-ink); }
        .mt-page-intro p { margin:0; color:rgba(33,73,22,.76); }
        .mt-page-intro .mt-eyebrow { color:var(--mt-green); }
        .mt-pill {
            display:inline-flex; align-items:center; gap:.3rem; padding:.34rem .7rem;
            border-radius:999px; background:var(--mt-neon); color:var(--mt-ink);
            font-size:.78rem; font-weight:760;
        }
        .mt-hero-copy { padding:clamp(1rem,3vw,2.7rem) .25rem; }
        .mt-hero-copy h1 {
            margin:.5rem 0 .85rem; color:var(--mt-cream);
            font-size:clamp(2.6rem,5.7vw,4.8rem); line-height:.98;
        }
        .mt-lead {
            color:rgba(250,248,239,.9); font-size:clamp(1rem,1.6vw,1.22rem);
            line-height:1.6;
        }
        [data-testid="stImage"] img {
            border-radius:24px; border:2px solid var(--mt-yellow);
            box-shadow:0 24px 55px rgba(33,73,22,.34); aspect-ratio:16/9; object-fit:cover;
        }
        .mt-status-card {
            padding:1.1rem 1.25rem; margin:.35rem 0 1rem; border-radius:18px;
            background:var(--mt-cream); border-left:8px solid var(--mt-yellow); color:var(--mt-ink);
        }
        .mt-status-card h2 { color:var(--mt-ink); margin:.15rem 0 .35rem; }
        .mt-status-card p { margin:.2rem 0; color:rgba(33,73,22,.8); }
        @media (max-width:700px) {
            [data-testid="stMainBlockContainer"] { padding-left:1rem; padding-right:1rem; }
            [data-testid="stMetric"] { min-height:92px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["render_global_styles"]
