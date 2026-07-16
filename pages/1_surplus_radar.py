import streamlit as st

from src.errors import MimpiTaniError
from src.i18n.translator import t
from src.services.workspace_service import get_workspace_summary
from src.ui.components import (
    active_database_path,
    is_workspace_initialized,
    render_header,
    render_prototype_banner,
    render_workspace_required,
    render_workspace_summary,
    sync_language,
)
from src.ui.messages import user_safe_error_message

sync_language()
if not is_workspace_initialized():
    render_workspace_required()
    st.stop()

render_header()
render_prototype_banner()
st.subheader(t("nav.radar"))
try:
    render_workspace_summary(get_workspace_summary(active_database_path()))
except MimpiTaniError as error:
    st.error(user_safe_error_message(error))
st.info(t("state.coming_soon"))
