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
            '<div class="mt-brand-row"><div class="mt-brand-mark">🌶️</div><div>'
            f'<h1 class="mt-brand-title">{t("app.title")}</h1>'
            f'<p class="mt-brand-tagline">{t("app.tagline")}</p>'
            "</div></div>",
            unsafe_allow_html=True,
        )
    with col_lang:
        render_language_switcher()


def render_page_intro(*, icon: str, title: str, description: str, eyebrow: str) -> None:
    st.markdown(
        '<div class="mt-page-intro">'
        f'<div class="mt-eyebrow">{eyebrow}</div>'
        f"<h2>{icon}&nbsp; {title}</h2><p>{description}</p></div>",
        unsafe_allow_html=True,
    )


def render_prototype_banner() -> None:
    st.markdown(
        '<div style="background:#F7DC27;color:#214916;padding:8px 12px;'
        'margin-bottom:16px;border-radius:6px;border-left:4px solid #214916">'
        f'⚠️ {t("app.data_banner")} <span style="margin-left:10px;padding:2px 8px;'
        'background:#214916;color:#FAF8EF;border-radius:4px;font-size:.85em">'
        f"{t('app.prototype_badge')}</span></div>",
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


def render_workspace_summary(
    summary: WorkspaceSummary,
) -> None:
    st.subheader(t("workspace.summary_title"))
    st.caption(
        f"{t('workspace.mode')}: "
        f"{summary.profile.workspace_mode.value} · "
        f"{summary.profile.name} · "
        f"{summary.profile.pilot_region}"
    )
    st.caption(f"{t('workspace.commodity')}: {t('workspace.commodity_name')}")
    columns = st.columns(5)
    metrics = (
        ("workspace.farmers", summary.active_farmers),
        (
            "workspace.harvest_batches",
            summary.planned_harvest_batches,
        ),
        ("workspace.buyers", summary.active_buyers),
        ("workspace.demands", summary.open_demands),
        ("workspace.capacity_days", summary.capacity_days),
    )
    for column, (label_key, value) in zip(columns, metrics, strict=True):
        column.metric(t(label_key), value)
