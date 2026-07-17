import streamlit as st
from src.i18n.translator import t
import logging

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Navbar Test", layout="wide")

def render_bottom_navbar():
    st.markdown("""
        <style>
        /* We target the outermost container */
        div[data-testid="stVerticalBlock"]:has(> div > div > div > div > .mt-bottom-nav-marker),
        div[data-testid="stVerticalBlock"]:has(.mt-bottom-nav-marker) {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 99999;
            background-color: var(--mt-ink, #1A2E1A);
            padding: 8px 16px;
            box-shadow: 0 -8px 24px rgba(0,0,0, 0.2);
            border-top-left-radius: 24px;
            border-top-right-radius: 24px;
            margin: 0;
        }

        /* override st.page_link default button styles inside this nav */
        div[data-testid="stVerticalBlock"]:has(.mt-bottom-nav-marker) [data-testid="stPageLink-NavLink"] {
            background-color: transparent !important;
            border: none !important;
            color: var(--mt-cream, #F2EFE8) !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 4px !important;
            min-height: auto !important;
            height: auto !important;
            gap: 4px !important;
        }

        /* Make active links yellow */
        div[data-testid="stVerticalBlock"]:has(.mt-bottom-nav-marker) [data-testid="stPageLink-NavLink"][data-active="true"],
        div[data-testid="stVerticalBlock"]:has(.mt-bottom-nav-marker) [data-testid="stPageLink-NavLink"]:hover {
            background-color: rgba(255,255,255,0.1) !important;
            color: var(--mt-yellow, #F2DB1D) !important;
        }
        
        div[data-testid="stVerticalBlock"]:has(.mt-bottom-nav-marker) p {
            font-size: 0.75rem !important;
            margin: 0 !important;
            line-height: 1.1 !important;
        }
        
        /* Ensure emojis are bigger */
        div[data-testid="stVerticalBlock"]:has(.mt-bottom-nav-marker) .st-emotion-cache-1ghhxcv {
            font-size: 1.25rem !important;
        }
        
        /* Ensure the main container has enough padding */
        .block-container {
            padding-bottom: 120px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="mt-bottom-nav-marker"></div>', unsafe_allow_html=True)
        cols = st.columns(4, gap="small")
        with cols[0]:
            st.page_link("app.py", label="Radar", icon="🌶️")
        with cols[1]:
            st.page_link("app.py", label="Harvest", icon="🌾")
        with cols[2]:
            st.page_link("app.py", label="Buyers", icon="🏢")
        with cols[3]:
            st.page_link("app.py", label="Analysis", icon="📊")

st.title("Main Content")
for i in range(20):
    st.write(f"Line {i}")

render_bottom_navbar()
