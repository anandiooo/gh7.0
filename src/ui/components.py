import streamlit as st

from src.config import DB_PATH
from src.i18n.translator import get_language, set_language, t
from src.services.workspace_service import WorkspaceSummary


def sync_language() -> None:
    lang = st.session_state.get("lang", "id")
    set_language(lang)


def render_language_switcher() -> None:
    current = get_language()
    new_lang = st.radio(
        t("app.language"),
        options=["id", "en"],
        format_func=lambda x: "ID" if x == "id" else "EN",
        index=0 if current == "id" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="_lang_radio",
    )
    if new_lang and new_lang != current:
        st.session_state["lang"] = new_lang
        set_language(new_lang)
        st.rerun()


def render_header() -> None:
    sync_language()
    # Header is now mostly handled by the sidebar for navigation, but we keep this for page titles
    pass


def render_page_intro(*, icon: str, title: str, description: str, eyebrow: str) -> None:
    st.markdown(
        '<div class="mt-page-intro">'
        f'<div class="mt-eyebrow">{eyebrow}</div>'
        f"<h2>{material_icon(icon)} {title}</h2><p>{description}</p></div>",
        unsafe_allow_html=True,
    )


def material_icon(name: str) -> str:
    """Return a decorative Material Symbol for trusted UI markup."""
    return f'<span class="stIconMaterial mt-material-icon" aria-hidden="true">{name}</span>'


def render_prototype_banner() -> None:
    st.markdown(
        '<div style="background:var(--mt-yellow);color:var(--mt-ink);padding:12px 16px;'
        "margin-bottom:16px;border-radius:12px;border-left:6px solid var(--mt-dark-green);"
        'font-weight:600;box-shadow:0 4px 12px rgba(31, 110, 42, 0.1);">'
        f"{material_icon('warning')} {t('app.data_banner')} "
        '<span style="margin-left:10px;padding:4px 10px;'
        'background:var(--mt-dark-green);color:var(--mt-cream);border-radius:999px;font-size:0.85rem">'
        f"{t('app.prototype_badge')}</span></div>",
        unsafe_allow_html=True,
    )


def is_workspace_initialized() -> bool:
    return bool(st.session_state.get("workspace_initialized", False))


def active_database_path() -> str:
    return str(st.session_state.get("database_path", DB_PATH))


def render_workspace_required() -> None:
    sync_language()
    st.warning(t("state.workspace_required"), icon=":material/lock:")
    st.info(
        f"{t('welcome.load_demo')} / {t('welcome.start_empty')}",
        icon=":material/arrow_forward:",
    )


def render_page_placeholder(page_title_key: str) -> None:
    sync_language()
    if not is_workspace_initialized():
        render_workspace_required()
        st.stop()
    render_header()
    render_prototype_banner()
    st.subheader(t(page_title_key))
    st.info(t("state.coming_soon"))


def render_sidebar(summary: WorkspaceSummary = None, reset_callback=None) -> None:
    """Render the global sidebar with brand, navigation, workspace status, and reset."""

    with st.sidebar:
        st.markdown(
            '<div style="margin-bottom:2rem;">'
            '<h1 style="color:var(--mt-lime);font-size:2.5rem;margin:0;line-height:1;">'
            f"{material_icon('eco')} {t('app.title')}</h1>"
            "</div>",
            unsafe_allow_html=True,
        )

        # Navigation is now at the bottom (render_bottom_navbar)

        st.divider()

        # Workspace Status
        if summary:
            st.markdown(
                '<div class="mt-eyebrow" style="margin-bottom:0.5rem">'
                f"{t('workspace.summary_title')}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div style="background-color:rgba(255,255,255,0.1);padding:1rem;'
                'border-radius:12px;margin-bottom:1rem;">'
                '<p style="margin:0;font-weight:bold;color:var(--mt-cream);">'
                f"{summary.profile.name}</p>"
                '<p style="margin:0;font-size:0.85rem;color:var(--mt-lime);">'
                f"{summary.profile.pilot_region}</p>"
                '<p style="margin:0;font-size:0.85rem;color:var(--mt-cream);opacity:0.8;">'
                f"{t('workspace.mode')}: {summary.profile.workspace_mode.value}</p></div>",
                unsafe_allow_html=True,
            )

            st.caption(
                f":material/agriculture: {t('workspace.harvest_batches')}: "
                f"**{summary.planned_harvest_batches}**"
            )
            st.caption(
                f":material/storefront: {t('workspace.buyers')}: **{summary.active_buyers}**"
            )
            st.caption(
                f":material/inventory_2: {t('workspace.demands')}: **{summary.open_demands}**"
            )
            st.caption(
                f":material/local_shipping: {t('workspace.capacity_days')}: "
                f"**{summary.capacity_days}**"
            )

            st.divider()

        # Language Switcher
        st.markdown(
            f'<div class="mt-eyebrow" style="margin-bottom:0.5rem">{t("app.language")}</div>',
            unsafe_allow_html=True,
        )
        render_language_switcher()

        st.divider()

        # Reset Control
        if reset_callback:
            with st.expander(t("workspace.reset_title")):
                st.caption(t("workspace.reset_description"))
                confirmed = st.checkbox(
                    t("workspace.reset_confirmation"),
                    key="confirm_workspace_reset",
                )
                if st.button(
                    t("workspace.reset_action"),
                    key="btn_reset_workspace",
                    disabled=not confirmed,
                    use_container_width=True,
                ):
                    reset_callback()


def render_bottom_navbar() -> None:
    """Render a floating bottom navigation bar."""
    sync_language()
    st.markdown(
        """
        <style>
        /* Target the specific bordered container via its key class */
        .st-key-bottom_nav {
            position: fixed !important;
            bottom: 24px !important;
            left: 0 !important;
            right: 0 !important;
            z-index: 99999 !important;
            background-color: var(--mt-ink, #1A2E1A) !important;
            padding: 12px 24px !important;
            box-shadow: 0 12px 32px rgba(0,0,0, 0.5) !important;
            border-radius: 32px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            margin: 0 auto !important;
            max-width: 800px !important;
            width: 90% !important;
        }

        /* Override st.page_link default button styles inside this nav */
        .st-key-bottom_nav [data-testid="stPageLink-NavLink"] {
            background-color: transparent !important;
            border: none !important;
            color: rgba(242, 239, 232, 0.6) !important; /* dimmed cream */
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 6px 8px !important;
            min-height: auto !important;
            height: auto !important;
            gap: 6px !important;
            border-radius: 12px !important;
        }

        /* Active/hover state for the links */
        .st-key-bottom_nav [data-testid="stPageLink-NavLink"][data-active="true"],
        .st-key-bottom_nav [data-testid="stPageLink-NavLink"]:hover {
            color: var(--mt-yellow, #F2DB1D) !important;
            background-color: rgba(255,255,255,0.05) !important;
        }
        /* Style the text label */
        .st-key-bottom_nav p, .st-key-bottom_nav span {
            color: rgba(242, 239, 232, 0.8) !important; /* dimmed cream */
            font-size: 0.75rem !important;
            margin: 0 !important;
            font-weight: 600 !important;
            line-height: 1.1 !important;
            white-space: nowrap !important;
        }

        .st-key-bottom_nav [data-testid="stPageLink-NavLink"][data-active="true"] p,
        .st-key-bottom_nav [data-testid="stPageLink-NavLink"]:hover p {
            color: var(--mt-yellow, #F2DB1D) !important;
        }

        .st-key-bottom_nav .stIconMaterial,
        .st-key-bottom_nav .st-emotion-cache-1ghhxcv,
        .st-key-bottom_nav [data-testid="stIconMaterial"] {
            font-size: 1.4rem !important;
            margin: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True, key="bottom_nav"):
        cols = st.columns(4, gap="small")
        with cols[0]:
            st.page_link("pages/1_surplus_radar.py", label=t("nav.radar"), icon=":material/radar:")
        with cols[1]:
            st.page_link(
                "pages/2_harvest_plans.py",
                label=t("nav.harvest_plans"),
                icon=":material/agriculture:",
            )
        with cols[2]:
            st.page_link(
                "pages/3_buyers_and_capacity.py",
                label=t("nav.buyers_capacity"),
                icon=":material/storefront:",
            )
        with cols[3]:
            st.page_link(
                "pages/4_analysis_and_simulation.py",
                label=t("nav.analysis_simulation"),
                icon=":material/monitoring:",
            )
