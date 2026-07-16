import streamlit as st


def render_global_styles() -> None:
    """Apply the shared visual language without coupling pages to CSS details."""
    st.markdown(
        """
        <style>
        :root {
            --mt-background: #297F39;
            --mt-cream: #FAF8EF;
            --mt-neon: #A9EB35;
            --mt-ink: #214916;
            --mt-yellow: #F7DC27;
            --mt-muted: rgba(33, 73, 22, 0.72);
            --mt-surface: rgba(250, 248, 239, 0.97);
            --mt-line: rgba(169, 235, 53, 0.42);
            --mt-display-font: "Agrandir Tight", "Arial Narrow",
                "Helvetica Neue Condensed", sans-serif;
            --mt-body-font: "Helvetica World", "Helvetica Neue", Helvetica, Arial, sans-serif;
        }

        html, body, .stApp, button, input, textarea, select {
            font-family: var(--mt-body-font);
        }

        h1, h2, h3, .mt-brand-title, .mt-eyebrow, .mt-section-label {
            font-family: var(--mt-display-font);
        }

        .stApp {
            background:
                radial-gradient(circle at 92% 4%, rgba(247, 220, 39, 0.18), transparent 24rem),
                radial-gradient(circle at 5% 35%, rgba(169, 235, 53, 0.14), transparent 30rem),
                var(--mt-background);
            color: var(--mt-cream);
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1320px;
            padding-top: 1.4rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #214916 0%, #183B11 100%);
            border-right: 1px solid var(--mt-line);
        }

        [data-testid="stSidebar"] * {
            color: var(--mt-cream);
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 12px;
            margin: 0.18rem 0.5rem;
            transition: background 140ms ease, transform 140ms ease;
        }

        [data-testid="stSidebarNav"] a:hover {
            background: rgba(169, 235, 53, 0.14);
            transform: translateX(2px);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(90deg, var(--mt-neon), #C9F47E);
            color: var(--mt-ink);
            font-weight: 700;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] * {
            color: var(--mt-ink);
        }

        h1, h2, h3 {
            color: var(--mt-cream);
            letter-spacing: -0.025em;
        }

        [data-testid="stMetric"] {
            min-height: 116px;
            padding: 1rem 1.05rem;
            background: var(--mt-surface);
            border: 1px solid var(--mt-line);
            border-radius: 16px;
            box-shadow: 0 12px 30px rgba(33, 73, 22, 0.24);
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
            box-shadow: 0 14px 34px rgba(33, 73, 22, 0.24);
        }

        .stButton > button,
        [data-testid="stPageLink-NavLink"] {
            border-radius: 11px;
            min-height: 2.75rem;
            font-weight: 700;
            transition: transform 130ms ease, box-shadow 130ms ease;
        }

        .stButton > button[kind="primary"] {
            background: var(--mt-neon);
            border-color: var(--mt-neon);
            color: var(--mt-ink);
        }

        .stButton > button:hover,
        [data-testid="stPageLink-NavLink"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 18px rgba(33, 73, 22, 0.28);
        }

        [data-testid="stForm"] {
            background: rgba(33, 73, 22, 0.78);
            border: 1px solid var(--mt-line);
            border-radius: 16px;
            padding: 1.05rem;
        }

        [data-testid="stExpander"] {
            background: rgba(33, 73, 22, 0.66);
            border-color: var(--mt-line);
            border-radius: 14px;
        }

        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.45rem;
            border-bottom: 0;
        }

        [data-testid="stTabs"] button[role="tab"] {
            border-radius: 999px;
            background: rgba(250, 248, 239, 0.12);
            padding: 0.5rem 1rem;
        }

        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            background: var(--mt-neon);
            color: var(--mt-ink);
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
            background: linear-gradient(145deg, var(--mt-neon), var(--mt-yellow));
            box-shadow: 0 10px 24px rgba(33, 73, 22, 0.28);
            font-size: 1.55rem;
        }

        .mt-brand-title {
            margin: 0;
            color: var(--mt-cream);
            font-size: clamp(1.75rem, 3vw, 2.45rem);
            line-height: 1;
        }

        .mt-brand-tagline {
            margin: 0.32rem 0 0;
            color: rgba(250, 248, 239, 0.78);
            font-size: 0.92rem;
        }

        .mt-eyebrow {
            color: var(--mt-neon);
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .mt-page-intro {
            margin: 0.25rem 0 1rem;
            padding: 0.82rem 1.15rem;
            background: linear-gradient(120deg, rgba(250,248,239,0.98), rgba(169,235,53,0.88));
            border: 1px solid var(--mt-line);
            border-radius: 18px;
        }

        .mt-page-intro h2 {
            margin: 0.12rem 0 0.18rem;
            font-size: clamp(1.45rem, 2.6vw, 1.95rem);
            color: var(--mt-ink);
        }

        .mt-page-intro p {
            margin: 0;
            color: var(--mt-muted);
        }

        .mt-page-intro .mt-eyebrow {
            color: var(--mt-background);
        }

        .mt-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.35rem 0.72rem;
            border-radius: 999px;
            background: var(--mt-neon);
            color: var(--mt-ink);
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
            color: var(--mt-cream);
        }

        .mt-hero-copy .mt-lead {
            max-width: 34rem;
            color: rgba(250, 248, 239, 0.88);
            font-size: clamp(1rem, 1.65vw, 1.22rem);
            line-height: 1.65;
        }

        [data-testid="stImage"] img {
            border-radius: 24px;
            box-shadow: 0 24px 55px rgba(33, 73, 22, 0.34);
            border: 2px solid var(--mt-yellow);
            aspect-ratio: 16 / 9;
            object-fit: cover;
        }

        .mt-section-label {
            margin: 1.4rem 0 0.4rem;
            color: var(--mt-neon);
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
