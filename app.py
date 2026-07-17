# Force Streamlit reload 2
import logging

import streamlit as st

from src.config import DB_PATH
from src.enums import WorkspaceMode
from src.errors import TetaniError
from src.i18n.translator import t
from src.services.workspace_service import (
    WorkspaceSummary,
    get_workspace_summary,
    initialize_workspace,
    reset_workspace,
)
from src.ui.components import (
    material_icon,
    render_bottom_navbar,
    render_language_switcher,
    render_prototype_banner,
    render_sidebar,
    sync_language,
)
from src.ui.messages import user_safe_error_message
from src.ui.styles import render_global_styles

st.set_page_config(
    page_title="tetani",
    page_icon=":material/agriculture:",
    layout="wide",
    initial_sidebar_state="auto",
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
    except TetaniError as error:
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
    # Hide sidebar and header purely for the welcome screen to maintain focus
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
        .stAppHeader, header, [data-testid="stHeader"] {
            display: none !important;
        }
        .mt-welcome-container {
            position: relative;
            z-index: 1;
            padding: 2rem 0;
        }
        .mt-shape-1 {
            top: -20px; left: -20px; width: 60px; height: 60px;
            background: var(--mt-yellow);
        }
        .mt-shape-2 {
            bottom: -10px; right: 10%; width: 40px; height: 40px;
            background: var(--mt-lime);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Decorative background shapes
    st.markdown(
        '<div class="mt-floating-shape mt-shape-circle mt-shape-1"></div>'
        '<div class="mt-floating-shape mt-shape-circle mt-shape-2"></div>'
        '<div class="mt-floating-shape mt-shape-plus" style="top:20%;right:5%;">+</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="mt-welcome-container">', unsafe_allow_html=True)
    hero_copy, hero_image = st.columns([1.1, 1], gap="large", vertical_alignment="center")
    with hero_copy:
        st.markdown(
            '<div class="mt-hero-copy">'
            '<h1 class="mt-brand-title" '
            'style="font-size:clamp(3rem,6vw,5.5rem);margin-bottom:1.5rem;">'
            f"{t('app.title')}</h1>"
            '<p class="mt-lead" '
            'style="font-size:1.4rem;color:var(--mt-cream);font-weight:500;">'
            f"{t('welcome.purpose')}</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        render_prototype_banner()
    with hero_image:
        st.image(
            "assets/tetani-hero.webp",
            caption=t("welcome.hero_caption"),
            width="stretch",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="mt-section-label" '
        'style="text-align:center;margin:3rem 0 1rem;font-size:1rem;">'
        f"{t('welcome.choose_workspace')}</div>",
        unsafe_allow_html=True,
    )
    col_demo, col_empty = st.columns(2, gap="medium")
    with col_demo:
        st.markdown(
            f'<div style="background-color:var(--mt-cream);padding:2rem;border-radius:24px;'
            "border:none;box-shadow:0 12px 32px rgba(31,110,42,0.2);min-height:180px;"
            'position:relative;overflow:hidden;">'
            '<div style="position:absolute;top:0;left:0;width:8px;height:100%;'
            'background-color:var(--mt-lime);"></div>'
            f'<span class="mt-pill" style="margin-bottom:1rem;">{t("welcome.recommended")}</span>'
            '<h3 style="color:var(--mt-ink);margin:0 0 0.5rem;font-size:1.8rem;">'
            f"{material_icon('inventory_2')} {t('welcome.load_demo')}</h3>"
            '<p style="color:var(--mt-dark-green);margin:0;font-size:1.1rem;">'
            f"{t('welcome.load_demo_desc')}</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            t("welcome.load_demo"),
            key="btn_load_demo",
            type="primary",
            use_container_width=True,
            icon=":material/inventory_2:",
        ):
            _run_initialization(WorkspaceMode.DEMO)

    with col_empty:
        st.markdown(
            f'<div style="background-color:var(--mt-cream);padding:2rem;border-radius:24px;'
            "border:none;box-shadow:0 12px 32px rgba(31,110,42,0.2);min-height:180px;"
            'position:relative;overflow:hidden;">'
            '<div style="position:absolute;top:0;left:0;width:8px;height:100%;'
            'background-color:var(--mt-yellow);"></div>'
            '<span class="mt-pill" '
            'style="margin-bottom:1rem;background-color:var(--mt-yellow);">'
            f"{t('welcome.blank_canvas')}</span>"
            '<h3 style="color:var(--mt-ink);margin:0 0 0.5rem;font-size:1.8rem;">'
            f"{material_icon('note_add')} {t('welcome.start_empty')}</h3>"
            '<p style="color:var(--mt-dark-green);margin:0;font-size:1.1rem;">'
            f"{t('welcome.start_empty_desc')}</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            t("welcome.start_empty"),
            key="btn_start_empty",
            use_container_width=True,
            icon=":material/note_add:",
        ):
            _run_initialization(WorkspaceMode.EMPTY)

    st.divider()
    _, footer_lang = st.columns([4, 1])
    with footer_lang:
        render_language_switcher()


def _reset_callback() -> None:
    mode = WorkspaceMode(st.session_state["workspace_mode"])
    _run_initialization(mode, reset=True)


def _workspace_pages() -> list[st.Page]:
    return [
        st.Page(
            "pages/1_surplus_radar.py",
            title=t("nav.radar"),
            icon=":material/radar:",
        ),
        st.Page(
            "pages/2_harvest_plans.py",
            title=t("nav.harvest_plans"),
            icon=":material/agriculture:",
        ),
        st.Page(
            "pages/3_buyers_and_capacity.py",
            title=t("nav.buyers_capacity"),
            icon=":material/storefront:",
        ),
        st.Page(
            "pages/4_analysis_and_simulation.py",
            title=t("nav.analysis_simulation"),
            icon=":material/monitoring:",
        ),
    ]


if not st.session_state.get("workspace_initialized", False):
    _render_welcome()
else:
    # Ensure sidebar is visible and expanded when workspace is active
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: flex !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if notice := st.session_state.pop("workspace_notice", None):
        st.success(t(notice), icon=":material/check_circle:")

    pg = st.navigation(_workspace_pages(), position="hidden")

    # Render Sidebar with Summary and Reset Callback
    try:
        summary = get_workspace_summary(_database_path())
        render_sidebar(summary=summary, reset_callback=_reset_callback)
    except TetaniError:
        render_sidebar(reset_callback=_reset_callback)

    try:
        pg.run()
    except TetaniError as error:
        st.error(user_safe_error_message(error))
    except Exception:
        logger.exception("Unexpected workspace page failure")
        st.error(t("error.system"))

    render_bottom_navbar()
