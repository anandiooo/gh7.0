import logging

import streamlit as st

from src.config import DB_PATH
from src.enums import WorkspaceMode
from src.errors import MimpiTaniError
from src.i18n.translator import t
from src.services.workspace_service import WorkspaceSummary, initialize_workspace, reset_workspace
from src.ui.components import (
    render_language_switcher,
    render_prototype_banner,
    sync_language,
)
from src.ui.messages import user_safe_error_message
from src.ui.styles import render_global_styles
from src.ui.theme import (
    PRIMARY_DARK_GREEN,
    PRIMARY_TEXT,
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
render_global_styles()
logger = logging.getLogger(__name__)


def _database_path() -> str:
    return str(st.session_state.get("database_path", DB_PATH))


def _store_workspace(summary: WorkspaceSummary) -> None:
    st.session_state["workspace_initialized"] = True
    st.session_state["workspace_mode"] = summary.profile.workspace_mode.value
    st.session_state["workspace_metadata"] = summary.session_metadata()
    st.session_state["database_path"] = _database_path()


def _run_initialization(mode: WorkspaceMode, *, reset: bool = False) -> None:
    try:
        with st.spinner(t("welcome.initializing"), show_time=True):
            initializer = reset_workspace if reset else initialize_workspace
            summary = initializer(mode, _database_path())
    except MimpiTaniError as error:
        st.error(user_safe_error_message(error))
        return
    except Exception:
        logger.exception("Unexpected workspace initialization failure")
        st.error(t("error.system"))
        return
    _store_workspace(summary)
    st.session_state["workspace_notice"] = (
        "welcome.workspace_demo_ready"
        if mode is WorkspaceMode.DEMO
        else "welcome.workspace_empty_ready"
    )
    st.rerun()


def _render_welcome() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    hero_copy, hero_image = st.columns([1.02, 1], gap="large", vertical_alignment="center")
    with hero_copy:
        st.markdown(
            '<div class="mt-hero-copy">'
            f'<div class="mt-eyebrow">{t("welcome.eyebrow")}</div>'
            f"<h1>{t('app.title')}</h1>"
            f'<p class="mt-lead">{t("app.tagline")} {t("welcome.description")}</p>'
            "</div>",
            unsafe_allow_html=True,
        )
        render_prototype_banner()
        st.markdown(
            f'<span class="mt-pill">✓ {t("welcome.local_first")}</span>',
            unsafe_allow_html=True,
        )
    with hero_image:
        st.markdown('<div class="mt-hero-image">', unsafe_allow_html=True)
        st.image(
            "assets/mimpitani-hero.webp",
            width="stretch",
            caption=t("welcome.hero_caption"),
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f'<div class="mt-section-label">{t("welcome.choose_workspace")}</div>',
        unsafe_allow_html=True,
    )
    col_demo, col_empty = st.columns(2, gap="medium")
    with col_demo:
        st.markdown(
            f'<div style="background: {SURFACE_BACKGROUND}; padding: 1.5rem; '
            f"border-radius: 16px; border: 1px solid rgba(169,235,53,.72); "
            f'box-shadow: 0 12px 30px rgba(33,73,22,.20); min-height: 150px;">'
            f'<span class="mt-pill">{t("welcome.recommended")}</span>'
            f'<h3 style="color: {PRIMARY_DARK_GREEN};">📦 {t("welcome.load_demo")}</h3>'
            f'<p style="color: {PRIMARY_TEXT}; font-size: 0.92rem;">'
            f"{t('welcome.load_demo_desc')}</p></div>",
            unsafe_allow_html=True,
        )
        if st.button(
            t("welcome.load_demo"),
            key="btn_load_demo",
            type="primary",
            width="stretch",
            icon="📦",
        ):
            _run_initialization(WorkspaceMode.DEMO)
    with col_empty:
        st.markdown(
            f'<div style="background: {SURFACE_BACKGROUND}; padding: 1.5rem; '
            f"border-radius: 16px; border: 1px solid rgba(247,220,39,.72); "
            f'box-shadow: 0 12px 30px rgba(33,73,22,.20); min-height: 150px;">'
            f'<span class="mt-pill">{t("welcome.blank_canvas")}</span>'
            f'<h3 style="color: {PRIMARY_DARK_GREEN};">📝 {t("welcome.start_empty")}</h3>'
            f'<p style="color: {PRIMARY_TEXT}; font-size: 0.92rem;">'
            f"{t('welcome.start_empty_desc')}</p></div>",
            unsafe_allow_html=True,
        )
        if st.button(
            t("welcome.start_empty"),
            key="btn_start_empty",
            width="stretch",
            icon="📝",
        ):
            _run_initialization(WorkspaceMode.EMPTY)
    st.divider()
    footer_copy, footer_lang = st.columns([4, 1])
    footer_copy.caption(t("welcome.disclaimer"))
    with footer_lang:
        render_language_switcher()


def _render_reset_control() -> None:
    with st.sidebar.expander(t("workspace.reset_title")):
        st.caption(t("workspace.reset_description"))
        confirmed = st.checkbox(t("workspace.reset_confirmation"), key="confirm_workspace_reset")
        if st.button(
            t("workspace.reset_action"),
            key="btn_reset_workspace",
            disabled=not confirmed,
            width="stretch",
        ):
            mode = WorkspaceMode(st.session_state["workspace_mode"])
            _run_initialization(mode, reset=True)


def _workspace_pages() -> list[st.Page]:
    return [
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


if not st.session_state.get("workspace_initialized", False):
    _render_welcome()
else:
    if notice := st.session_state.pop("workspace_notice", None):
        st.success(t(notice), icon="✅")
    _render_reset_control()

    pg = st.navigation(_workspace_pages())
    try:
        pg.run()
    except MimpiTaniError as error:
        st.error(user_safe_error_message(error))
    except Exception:
        logger.exception("Unexpected workspace page failure")
        st.error(t("error.system"))
