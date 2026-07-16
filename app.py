import streamlit as st

from src.i18n.translator import t
from src.ui.components import (
    render_language_switcher,
    sync_language,
)
from src.ui.theme import (
    ACCENT_WARNING_ORANGE,
    PRIMARY_DARK_GREEN,
    PRIMARY_TEXT,
    SECONDARY_LIGHT_GREEN,
    SURFACE_BACKGROUND,
)

st.set_page_config(
    page_title="MimpiTani",
    page_icon="🌶️",
    layout="wide",
    initial_sidebar_state="expanded",
)
if "lang" not in st.session_state:
    st.session_state["lang"] = "id"
sync_language()


def _render_welcome() -> None:
    _left, center, _right = st.columns([1, 2, 1])
    with center:
        st.markdown(
            f'<div style="text-align: center; padding: 2rem 0;">'
            f'<h1 style="color: {PRIMARY_DARK_GREEN}; font-size: 2.5rem;">{t("app.title")}</h1>'
            f'<p style="color: {SECONDARY_LIGHT_GREEN}; font-size: 1.15rem; margin-top: -0.5rem;">'
            f"{t('app.tagline')}</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="text-align: center; color: {PRIMARY_TEXT};">{t("welcome.description")}</p>',
            unsafe_allow_html=True,
        )
        st.divider()
        col_demo, col_empty = st.columns(2)
        with col_demo:
            st.markdown(
                f'<div style="background: {SURFACE_BACKGROUND}; padding: 1.5rem; '
                f"border-radius: 8px; border: 2px solid {SECONDARY_LIGHT_GREEN}; "
                f'text-align: center; min-height: 140px;">'
                f'<h3 style="color: {PRIMARY_DARK_GREEN};">{t("welcome.load_demo")}</h3>'
                f'<p style="color: {PRIMARY_TEXT}; font-size: 0.9rem;">'
                f"{t('welcome.load_demo_desc')}</p></div>",
                unsafe_allow_html=True,
            )
            if st.button(
                t("welcome.load_demo"),
                key="btn_load_demo",
                type="primary",
                use_container_width=True,
                icon="📦",
            ):
                st.session_state["workspace_mode"] = "DEMO"
                st.session_state["workspace_initialized"] = True
                st.rerun()
        with col_empty:
            st.markdown(
                f'<div style="background: {SURFACE_BACKGROUND}; padding: 1.5rem; '
                f"border-radius: 8px; border: 2px solid {ACCENT_WARNING_ORANGE}; "
                f'text-align: center; min-height: 140px;">'
                f'<h3 style="color: {PRIMARY_DARK_GREEN};">{t("welcome.start_empty")}</h3>'
                f'<p style="color: {PRIMARY_TEXT}; font-size: 0.9rem;">'
                f"{t('welcome.start_empty_desc')}</p></div>",
                unsafe_allow_html=True,
            )
            if st.button(
                t("welcome.start_empty"),
                key="btn_start_empty",
                use_container_width=True,
                icon="📝",
            ):
                st.session_state["workspace_mode"] = "EMPTY"
                st.session_state["workspace_initialized"] = True
                st.rerun()
        st.divider()
        st.caption(f"{t('welcome.disclaimer')}")
        st.markdown("")
        render_language_switcher()


if not st.session_state.get("workspace_initialized", False):
    _render_welcome()
else:
    mode = st.session_state.get("workspace_mode", "UNKNOWN")
    msg_key = "welcome.workspace_demo_ready" if mode == "DEMO" else "welcome.workspace_empty_ready"
    if not st.session_state.get("_toast_shown"):
        st.toast(t(msg_key), icon="ℹ️")
        st.session_state["_toast_shown"] = True

    pg = st.navigation(
        [
            st.Page("pages/1_surplus_radar.py", title=t("nav.radar"), icon="🌶️"),
            st.Page("pages/2_harvest_plans.py", title=t("nav.harvest_plans"), icon="🌾"),
            st.Page(
                "pages/3_buyers_and_capacity.py",
                title=t("nav.buyers_capacity"),
                icon="🏢",
            ),
            st.Page(
                "pages/4_analysis_and_simulation.py",
                title=t("nav.analysis_simulation"),
                icon="📊",
            ),
        ]
    )
    pg.run()
