from datetime import datetime

import streamlit as st

from src.config import APP_TIMEZONE
from src.enums import BatchStatus, EstimateConfidence, QualityGrade
from src.errors import MimpiTaniError
from src.i18n.translator import t
from src.services.harvest_service import HarvestService
from src.ui.components import (
    active_database_path,
    is_workspace_initialized,
    render_header,
    render_prototype_banner,
    render_workspace_required,
    sync_language,
)
from src.ui.messages import user_safe_error_message

sync_language()
if not is_workspace_initialized():
    render_workspace_required()
    st.stop()

render_header()
render_prototype_banner()
st.subheader(t("nav.harvest_plans"))
st.caption(t("harvest.source_label"))
if notice := st.session_state.pop("harvest_notice", None):
    st.success(t(notice), icon="✅")

service = HarvestService(active_database_path())
try:
    farmers = service.list_active_farmers()
    all_batches = service.list_harvests()
except MimpiTaniError as error:
    st.error(user_safe_error_message(error))
    st.stop()

farmer_names = {farmer.id: farmer.name for farmer in farmers}
with st.expander(t("harvest.filters")):
    filter_columns = st.columns(4)
    selected_farmer = filter_columns[0].selectbox(
        t("common.farmer"),
        options=[None, *farmers],
        format_func=lambda item: t("common.all") if item is None else item.name,
        key="harvest_filter_farmer",
    )
    selected_grade = filter_columns[1].selectbox(
        t("common.grade"),
        options=[None, *QualityGrade],
        format_func=lambda item: t("common.all") if item is None else item.value,
        key="harvest_filter_grade",
    )
    selected_confidence = filter_columns[2].selectbox(
        t("harvest.confidence"),
        options=[None, *EstimateConfidence],
        format_func=lambda item: (
            t("common.all") if item is None else t(f"confidence.{item.value.lower()}")
        ),
        key="harvest_filter_confidence",
    )
    selected_status = filter_columns[3].selectbox(
        t("common.status"),
        options=[None, *BatchStatus],
        format_func=lambda item: (
            t("common.all") if item is None else t(f"batch_status.{item.value.lower()}")
        ),
        key="harvest_filter_status",
    )
    use_dates = st.checkbox(t("harvest.filter_dates"), key="harvest_filter_dates_enabled")
    start_date = end_date = None
    if use_dates:
        date_columns = st.columns(2)
        start_date = date_columns[0].date_input(t("harvest.start_date"), key="harvest_start_date")
        end_date = date_columns[1].date_input(t("harvest.end_date"), key="harvest_end_date")

filtered = service.list_harvests(
    farmer_id=selected_farmer.id if selected_farmer else None,
    start_date=start_date,
    end_date=end_date,
    grade=selected_grade,
    confidence=selected_confidence,
    status=selected_status,
)
st.metric(t("harvest.planned_quantity"), f"{service.planned_quantity_summary(filtered):,.1f} kg")
if filtered:
    st.dataframe(
        [
            {
                t("common.farmer"): farmer_names.get(batch.farmer_id, batch.farmer_id),
                t("common.date"): batch.estimated_harvest_date.isoformat(),
                t("common.quantity"): f"{batch.estimated_quantity_kg:,.1f} kg",
                t("common.grade"): batch.grade.value,
                t("harvest.confidence"): t(f"confidence.{batch.confidence.value.lower()}"),
                t("common.status"): t(f"batch_status.{batch.status.value.lower()}"),
            }
            for batch in filtered
        ],
        width="stretch",
        hide_index=True,
    )
else:
    st.info(t("state.empty.harvest"))

st.divider()
st.markdown(f"### {t('harvest.add_title')}")
if not farmers:
    st.warning(t("harvest.no_active_farmers"))
else:
    with st.form("add_harvest_form"):
        add_farmer = st.selectbox(
            t("common.farmer"), farmers, format_func=lambda farmer: farmer.name
        )
        add_columns = st.columns(3)
        add_date = add_columns[0].date_input(
            t("common.date"), value=datetime.now(APP_TIMEZONE).date()
        )
        add_quantity = add_columns[1].number_input(
            t("harvest.quantity_kg"), min_value=0.0, value=100.0, step=10.0
        )
        add_grade = add_columns[2].selectbox(t("common.grade"), list(QualityGrade))
        add_confidence = st.selectbox(
            t("harvest.confidence"),
            list(EstimateConfidence),
            format_func=lambda item: t(f"confidence.{item.value.lower()}"),
        )
        add_note = st.text_input(t("harvest.maturity_note"))
        submitted = st.form_submit_button(t("action.add_harvest"), type="primary")
    if submitted:
        try:
            service.create_harvest(
                farmer_id=add_farmer.id,
                estimated_harvest_date=add_date,
                estimated_quantity_kg=add_quantity,
                grade=add_grade,
                confidence=add_confidence,
                maturity_note=add_note,
            )
        except MimpiTaniError as error:
            st.error(user_safe_error_message(error))
        else:
            st.session_state["harvest_notice"] = "harvest.created"
            st.rerun()

if all_batches:
    st.divider()
    st.markdown(f"### {t('harvest.manage_title')}")
    selected_batch = st.selectbox(
        t("harvest.select_batch"),
        all_batches,
        format_func=lambda batch: (
            f"{farmer_names.get(batch.farmer_id, batch.farmer_id)} · "
            f"{batch.estimated_harvest_date.isoformat()} · {batch.estimated_quantity_kg:,.1f} kg"
        ),
        key="manage_harvest_batch",
    )
    with st.form("edit_harvest_form"):
        edit_farmer = st.selectbox(
            t("common.farmer"),
            farmers,
            index=next(
                (
                    index
                    for index, farmer in enumerate(farmers)
                    if farmer.id == selected_batch.farmer_id
                ),
                0,
            ),
            format_func=lambda farmer: farmer.name,
        )
        edit_columns = st.columns(3)
        edit_date = edit_columns[0].date_input(
            t("common.date"), value=selected_batch.estimated_harvest_date, key="edit_harvest_date"
        )
        edit_quantity = edit_columns[1].number_input(
            t("harvest.quantity_kg"),
            min_value=0.0,
            value=float(selected_batch.estimated_quantity_kg),
            step=10.0,
            key="edit_harvest_quantity",
        )
        edit_grade = edit_columns[2].selectbox(
            t("common.grade"),
            list(QualityGrade),
            index=list(QualityGrade).index(selected_batch.grade),
            key="edit_harvest_grade",
        )
        edit_confidence = st.selectbox(
            t("harvest.confidence"),
            list(EstimateConfidence),
            index=list(EstimateConfidence).index(selected_batch.confidence),
            format_func=lambda item: t(f"confidence.{item.value.lower()}"),
            key="edit_harvest_confidence",
        )
        edit_note = st.text_input(
            t("harvest.maturity_note"), value=selected_batch.maturity_note or "", key="edit_note"
        )
        update_submitted = st.form_submit_button(t("harvest.update_action"))
    if update_submitted:
        try:
            service.update_harvest(
                selected_batch.id,
                farmer_id=edit_farmer.id,
                estimated_harvest_date=edit_date,
                estimated_quantity_kg=edit_quantity,
                grade=edit_grade,
                confidence=edit_confidence,
                maturity_note=edit_note,
            )
        except MimpiTaniError as error:
            st.error(user_safe_error_message(error))
        else:
            st.session_state["harvest_notice"] = "harvest.updated"
            st.rerun()

    if selected_batch.status is BatchStatus.PLANNED:
        confirmed = st.checkbox(t("harvest.cancel_confirmation"), key="cancel_harvest_confirm")
        if st.button(
            t("harvest.cancel_action"),
            disabled=not confirmed,
            type="secondary",
            key="cancel_harvest_button",
        ):
            try:
                service.cancel_harvest(selected_batch.id)
            except MimpiTaniError as error:
                st.error(user_safe_error_message(error))
            else:
                st.session_state["harvest_notice"] = "harvest.cancelled"
                st.rerun()
