import streamlit as st


def render_global_styles() -> None:
    """Apply the shared visual language without coupling pages to CSS details."""
    st.markdown(
        """
        <style>
        :root {
            --mt-forest: #145319;
            --mt-leaf: #388E3C;
            --mt-lime: #8BC34A;
            --mt-amber: #D97706;
            --mt-chili: #C7392F;
            --mt-ink: #183019;
            --mt-muted: #657466;
            --mt-canvas: #F4F7F2;
            --mt-surface: rgba(255, 255, 255, 0.94);
            --mt-line: rgba(20, 83, 25, 0.12);
        }

        .stApp {
            background:
                radial-gradient(circle at 92% 4%, rgba(217, 119, 6, 0.10), transparent 24rem),
                radial-gradient(circle at 5% 30%, rgba(56, 142, 60, 0.08), transparent 28rem),
                var(--mt-canvas);
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1320px;
            padding-top: 1.4rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #F7FAF5 0%, #EDF4E9 100%);
            border-right: 1px solid var(--mt-line);
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 12px;
            margin: 0.18rem 0.5rem;
            transition: background 140ms ease, transform 140ms ease;
        }

        [data-testid="stSidebarNav"] a:hover {
            background: rgba(56, 142, 60, 0.10);
            transform: translateX(2px);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(90deg, rgba(56, 142, 60, 0.18), rgba(139, 195, 74, 0.10));
            color: var(--mt-forest);
            font-weight: 700;
        }

        h1, h2, h3 {
            color: var(--mt-ink);
            letter-spacing: -0.025em;
        }

        [data-testid="stMetric"] {
            min-height: 116px;
            padding: 1rem 1.05rem;
            background: var(--mt-surface);
            border: 1px solid var(--mt-line);
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(25, 63, 28, 0.055);
        }

        [data-testid="stMetricLabel"] {
            color: var(--mt-muted);
            font-weight: 650;
        }

        [data-testid="stMetricValue"] {
            color: var(--mt-ink);
            font-weight: 760;
            font-size: clamp(1.35rem, 2vw, 1.9rem);
        }

        [data-testid="stPlotlyChart"],
        [data-testid="stDataFrame"] {
            overflow: hidden;
            background: var(--mt-surface);
            border: 1px solid var(--mt-line);
            border-radius: 18px;
            box-shadow: 0 12px 34px rgba(25, 63, 28, 0.055);
        }

        .stButton > button,
        [data-testid="stPageLink-NavLink"] {
            border-radius: 11px;
            min-height: 2.75rem;
            font-weight: 700;
            transition: transform 130ms ease, box-shadow 130ms ease;
        }

        .stButton > button:hover,
        [data-testid="stPageLink-NavLink"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 18px rgba(20, 83, 25, 0.12);
        }

        [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid var(--mt-line);
            border-radius: 16px;
            padding: 1.05rem;
        }

        [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.74);
            border-color: var(--mt-line);
            border-radius: 14px;
        }

        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.45rem;
            border-bottom: 0;
        }

        [data-testid="stTabs"] button[role="tab"] {
            border-radius: 999px;
            background: rgba(56, 142, 60, 0.08);
            padding: 0.5rem 1rem;
        }

        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            background: var(--mt-forest);
            color: white;
        }

        .mt-brand-row {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            min-height: 58px;
        }

        .mt-brand-mark {
            display: grid;
            place-items: center;
            width: 48px;
            height: 48px;
            border-radius: 15px;
            background: linear-gradient(145deg, #145319, #388E3C);
            box-shadow: 0 10px 24px rgba(20, 83, 25, 0.19);
            font-size: 1.55rem;
        }

        .mt-brand-title {
            margin: 0;
            color: var(--mt-forest);
            font-size: clamp(1.75rem, 3vw, 2.45rem);
            line-height: 1;
        }

        .mt-brand-tagline {
            margin: 0.32rem 0 0;
            color: var(--mt-muted);
            font-size: 0.92rem;
        }

        .mt-eyebrow {
            color: var(--mt-leaf);
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .mt-page-intro {
            margin: 0.25rem 0 1rem;
            padding: 0.82rem 1.15rem;
            background: linear-gradient(120deg, rgba(255,255,255,0.96), rgba(235,244,230,0.88));
            border: 1px solid var(--mt-line);
            border-radius: 18px;
        }

        .mt-page-intro h2 {
            margin: 0.12rem 0 0.18rem;
            font-size: clamp(1.45rem, 2.6vw, 1.95rem);
        }

        .mt-page-intro p {
            margin: 0;
            color: var(--mt-muted);
        }

        .mt-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.35rem 0.72rem;
            border-radius: 999px;
            background: rgba(56, 142, 60, 0.10);
            color: var(--mt-forest);
            font-size: 0.78rem;
            font-weight: 750;
        }

        .mt-hero-copy {
            padding: clamp(1rem, 3vw, 2.8rem) 0.3rem;
        }

        .mt-hero-copy h1 {
            margin: 0.55rem 0 0.9rem;
            font-size: clamp(2.55rem, 5.7vw, 4.8rem);
            line-height: 0.98;
            color: var(--mt-forest);
        }

        .mt-hero-copy .mt-lead {
            max-width: 34rem;
            color: #506451;
            font-size: clamp(1rem, 1.65vw, 1.22rem);
            line-height: 1.65;
        }

        [data-testid="stImage"] img {
            border-radius: 24px;
            box-shadow: 0 24px 55px rgba(25, 63, 28, 0.18);
            border: 1px solid rgba(255,255,255,0.8);
            aspect-ratio: 16 / 9;
            object-fit: cover;
        }

        .mt-section-label {
            margin: 1.4rem 0 0.4rem;
            color: var(--mt-muted);
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.10em;
            text-transform: uppercase;
        }

        @media (max-width: 700px) {
            [data-testid="stMainBlockContainer"] {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            [data-testid="stMetric"] {
                min-height: 96px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["render_global_styles"]
