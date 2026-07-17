import streamlit as st


def render_global_styles() -> None:
    """Apply the approved cooperative visual identity consistently."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=block');

        :root {
            --mt-bg-green: #2F8B3A;
            --mt-dark-green: #1F6E2A;
            --mt-yellow: #F2DB1D;
            --mt-lime: #A8E629;
            --mt-cream: #F2EFE8;
            --mt-ink: #1A2E1A;
            --mt-border-gray: #D1D5DB;
            --mt-display: 'Outfit', sans-serif;
            --mt-body: 'Inter', sans-serif;
        }

        /* Base Typography & Background */
        html, body, .stApp, button, input, textarea, select, [class*="st-"] {
            font-family: var(--mt-body) !important;
        }
        
        /* Force Material Icons to use the correct font and overpower the base rule */
        .stIconMaterial, 
        .material-symbols-rounded, 
        [data-testid="stIconMaterial"],
        [data-testid="stAlertDynamicIcon"],
        [data-testid="stSidebarCollapsedControl"] i,
        [data-testid="stSidebarCollapsedControl"] span,
        [data-testid="stSidebarNav"] i,
        [data-testid="stSidebarNav"] span,
        [class*="st-"] .material-symbols-rounded,
        [class*="st-"] [data-testid="stIconMaterial"],
        [class*="st-"] [data-testid="stAlertDynamicIcon"],
        [class*="st-"] [data-testid*="Icon"],
        [class*="st-"] [translate="no"] {
            font-family: "Material Symbols Rounded" !important;
            font-feature-settings: "liga" !important;
            -webkit-font-feature-settings: "liga" !important;
            -webkit-font-smoothing: antialiased;
            font-style: normal;
            letter-spacing: normal;
            text-transform: none;
            white-space: nowrap;
        }
        h1, h2, h3, .mt-title, .mt-eyebrow, .mt-section-label {
            font-family: var(--mt-display) !important;
        }
        
        .stApp {
            background-color: var(--mt-bg-green);
            color: var(--mt-cream);
        }

        .mt-material-icon {
            display: inline-block;
            font-size: 1.1em;
            font-variation-settings: "FILL" 0, "wght" 600, "GRAD" 0, "opsz" 24;
            line-height: 1;
            vertical-align: -0.12em;
        }
        h1, h2, h3, .mt-title, .mt-eyebrow, .mt-section-label {
            font-family: var(--mt-display) !important;
        }

        .stApp {
            background-color: var(--mt-bg-green);
            color: var(--mt-cream);
        }

        /* Hide Streamlit Header ONLY, Keep Sidebar */
        [data-testid="stHeader"],
        .stAppHeader,
        header,
        .st-emotion-cache-114ix68,
        .e1yxiy6j1 {
            display: none !important;
            visibility: hidden !important;
            height: 0px !important;
            opacity: 0 !important;
        }

        /* Container Layout */
        [data-testid="stMainBlockContainer"],
        .stAppViewBlockContainer,
        .block-container,
        .main .block-container {
            max-width: 1366px !important;
            padding-top: 2rem !important;
            padding-bottom: 120px !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* Typography Styling */
        h1, h2, h3 {
            color: var(--mt-cream);
            letter-spacing: -0.02em;
            font-weight: 800 !important;
        }
        p, label, [data-testid="stCaptionContainer"], .stMarkdown {
            color: var(--mt-cream);
            font-weight: 500;
        }
        /* Cards / Metrics / Forms */
        [data-testid="stMetric"],
        [data-testid="stForm"],
        div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: var(--mt-cream) !important;
            border: none !important;
            border-radius: 24px !important;
            box-shadow: 0 8px 24px rgba(31, 110, 42, 0.15) !important;
            overflow: hidden;
            padding: 1rem;
        }

        /* Override st.container(border=True) and forms defaults */
        div[data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stForm"] {
            background-color: var(--mt-cream) !important;
            color: var(--mt-ink) !important;
            border-radius: 24px !important;
            border: none !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1) !important;
        }

        /* Re-color text inside cards/forms to dark ink (Streamlit default text is cream) */
        div[data-testid="stVerticalBlockBorderWrapper"] h1,
        div[data-testid="stVerticalBlockBorderWrapper"] h2,
        div[data-testid="stVerticalBlockBorderWrapper"] h3,
        div[data-testid="stVerticalBlockBorderWrapper"] p,
        div[data-testid="stVerticalBlockBorderWrapper"] label,
        div[data-testid="stVerticalBlockBorderWrapper"] span,
        div[data-testid="stVerticalBlockBorderWrapper"] li,
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stText"],
        div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown,
        [data-testid="stForm"] h1,
        [data-testid="stForm"] h2,
        [data-testid="stForm"] h3,
        [data-testid="stForm"] p,
        [data-testid="stForm"] label,
        [data-testid="stForm"] span,
        [data-testid="stForm"] li,
        [data-testid="stForm"] div[data-testid="stText"],
        [data-testid="stForm"] .stMarkdown {
            color: var(--mt-ink) !important;
        }

        [data-testid="stMetric"] {
            padding: 1.25rem 1.5rem;
        }
        [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
            color: var(--mt-dark-green) !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
        }
        [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
            color: var(--mt-ink) !important;
            font-weight: 900 !important;
            font-family: var(--mt-display) !important;
        }

        /* Buttons */
        .stButton > button,
        [data-testid="baseButton-primary"],
        [data-testid="baseButton-secondary"],
        [data-testid="stPageLink-NavLink"] {
            border-radius: 999px !important; /* Pill shape */
            min-height: 3rem;
            font-weight: 700 !important;
            font-family: var(--mt-display) !important;
            transition: all 0.2s ease-in-out;
        }
        .stButton > button[kind="primary"], [data-testid="baseButton-primary"] {
            background-color: var(--mt-yellow) !important;
            border-color: var(--mt-yellow) !important;
        }
        .stButton > button[kind="primary"] *, [data-testid="baseButton-primary"] * {
            color: var(--mt-ink) !important;
        }
        .stButton > button[kind="primary"]:hover, [data-testid="baseButton-primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(242, 219, 29, 0.4) !important;
        }
        .stButton > button:not([kind="primary"]), [data-testid="baseButton-secondary"] {
            background-color: var(--mt-cream) !important;
            border: 2px solid var(--mt-lime) !important;
        }
        .stButton > button:not([kind="primary"]) *, [data-testid="baseButton-secondary"] * {
            color: var(--mt-ink) !important;
        }
        .stButton > button:not([kind="primary"]):hover, [data-testid="baseButton-secondary"]:hover {
            background-color: var(--mt-lime) !important;
        }

        /* Inputs */
        [data-baseweb="input"], [data-baseweb="textarea"],
        [data-baseweb="select"] > div, [data-baseweb="base-input"] {
            background-color: #FFFFFF !important;
            color: var(--mt-ink) !important;
            border-radius: 12px !important;
            border: 1px solid var(--mt-border-gray) !important;
        }
        [data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
        [data-baseweb="select"] *, [data-baseweb="base-input"] input {
            color: var(--mt-ink) !important;
            -webkit-text-fill-color: var(--mt-ink) !important;
            font-weight: 500;
        }

        ::placeholder {
            color: #6B7280 !important;
            -webkit-text-fill-color: #6B7280 !important;
            opacity: 1 !important;
        }

        /* Alerts (st.info, st.error, etc) */
        [data-testid="stAlert"] * {
            color: var(--mt-ink) !important;
        }

        /* Tabs */
        [data-testid="stTabs"] button[role="tab"], [data-baseweb="tab"] {
            font-family: var(--mt-display) !important;
            font-weight: 700 !important;
            background-color: transparent !important;
        }
        [data-testid="stTabs"] button[role="tab"] *, [data-baseweb="tab"] * {
            color: var(--mt-cream) !important;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"],
        [data-baseweb="tab"][aria-selected="true"] {
            background-color: var(--mt-lime) !important;
            border-radius: 999px !important;
            padding: 0.5rem 1.5rem !important;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] *,
        [data-baseweb="tab"][aria-selected="true"] * {
            color: var(--mt-ink) !important;
        }

        /* Custom UI Classes */
        .mt-brand-title {
            font-family: var(--mt-display);
            margin:0;
            color: var(--mt-cream);
            font-size: clamp(2.5rem, 4vw, 4rem);
            font-weight: 900;
            line-height: 1.1;
        }
        .mt-brand-tagline {
            font-family: var(--mt-body);
            margin: 0.5rem 0 0;
            color: var(--mt-lime);
            font-size: 1.2rem;
            font-weight: 600;
        }
        .mt-eyebrow, .mt-section-label {
            color: var(--mt-lime);
            font-size: 0.85rem;
            font-weight: 800;
            letter-spacing: 0.15em;
            text-transform: uppercase;
        }
        .mt-page-intro {
            margin: 0.5rem 0 2rem;
            padding: 1.5rem 2rem;
            background-color: var(--mt-cream);
            border-radius: 24px;
            color: var(--mt-ink);
        }
        .mt-page-intro h2 { margin: 0 0 0.5rem 0; color: var(--mt-ink); font-weight: 800; }
        .mt-page-intro p { margin: 0; color: var(--mt-dark-green); font-size: 1.1rem; }
        .mt-page-intro .mt-eyebrow { color: var(--mt-dark-green); }

        .mt-pill {
            display: inline-flex; align-items: center; gap: 0.5rem;
            padding: 0.4rem 1rem;
            border-radius: 999px;
            background-color: var(--mt-lime);
            color: var(--mt-ink);
            font-size: 0.85rem;
            font-weight: 800;
        }

        /* Decorative shapes for Hero */
        .mt-floating-shape {
            position: absolute;
            z-index: -1;
            opacity: 0.8;
        }
        .mt-shape-circle {
            width: 40px; height: 40px;
            border-radius: 50%;
            background-color: var(--mt-cream);
        }
        .mt-shape-plus {
            color: var(--mt-lime);
            font-size: 2rem;
            font-weight: 900;
        }

        /* Status Card */
        .mt-status-card {
            padding: 2rem;
            margin: 1rem 0 2rem;
            border-radius: 24px;
            background-color: var(--mt-cream);
            border-left: 12px solid var(--mt-yellow);
            color: var(--mt-ink);
            box-shadow: 0 12px 32px rgba(31, 110, 42, 0.2);
        }
        .mt-status-card h2 {
            color: var(--mt-ink);
            font-size: 2.5rem;
            font-weight: 900;
            margin-bottom: 0.5rem;
        }
        .mt-status-card p { font-size: 1.2rem; color: var(--mt-dark-green); margin: 0; }

        /* Adjust bottom padding for mobile */
        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"] {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 1rem !important;
            }
            .mt-brand-title { font-size: 2.5rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["render_global_styles"]
