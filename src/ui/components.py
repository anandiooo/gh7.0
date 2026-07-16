import streamlit as st

from src.config import DB_PATH
from src.i18n.translator import get_language, set_language, t
from src.services.workspace_service import WorkspaceSummary
from src.ui.theme import ACCENT_WARNING_ORANGE, PRIMARY_DARK_GREEN, PRIMARY_TEXT


def sync_language() -> None:
    lang = st.session_state.get("lang", "id")
    set_language(lang)


def render_language_switcher() -> None:
    current = get_language()
    new_lang = st.radio(
        "🌐",
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
    col_title, col_lang = st.columns([4, 1])
    with col_title:
        st.markdown(
            f'<h1 style="color: {PRIMARY_DARK_GREEN}; margin-bottom: 0;">🌶️ {t("app.title")}</h1>',
            unsafe_allow_html=True,
        )
        st.caption(t("app.tagline"))
    with col_lang:
        render_language_switcher()


def render_prototype_banner() -> None:
    st.markdown(
        f'<div style="background-color: {ACCENT_WARNING_ORANGE}15; '
        f"border-left: 4px solid {ACCENT_WARNING_ORANGE}; "
        f"padding: 8px 12px; margin-bottom: 16px; border-radius: 4px; "
        f'color: {PRIMARY_TEXT};">⚠️ {t("app.data_banner")}'
        f'<span style="margin-left: 12px; padding: 2px 8px; '
        f"background-color: {ACCENT_WARNING_ORANGE}30; border-radius: 4px; "
        f'font-size: 0.85em;">{t("app.prototype_badge")}</span></div>',
        unsafe_allow_html=True,
    )


def is_workspace_initialized() -> bool:
    return bool(st.session_state.get("workspace_initialized", False))


def active_database_path() -> str:
    return str(st.session_state.get("database_path", DB_PATH))


def render_workspace_required() -> None:
    sync_language()
    st.warning(t("state.workspace_required"))
    st.info(
        f"👉 {t('welcome.load_demo')} / {t('welcome.start_empty')}  —  {t('welcome.description')}"
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


def render_workspace_summary(summary: WorkspaceSummary) -> None:
    st.subheader(t("workspace.summary_title"))
    st.caption(
        f"{t('workspace.mode')}: {summary.profile.workspace_mode.value} · "
        f"{summary.profile.name} · {summary.profile.pilot_region}"
    )
    st.caption(f"{t('workspace.commodity')}: {t('workspace.commodity_name')}")
    columns = st.columns(5)
    metrics = (
        ("workspace.farmers", summary.active_farmers),
        ("workspace.harvest_batches", summary.planned_harvest_batches),
        ("workspace.buyers", summary.active_buyers),
        ("workspace.demands", summary.open_demands),
        ("workspace.capacity_days", summary.capacity_days),
    )
    for column, (label_key, value) in zip(columns, metrics, strict=True):
        column.metric(t(label_key), value)
