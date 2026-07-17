from datetime import datetime

import streamlit as st

from src.config import APP_TIMEZONE
from src.enums import ChannelType, DemandStatus, QualityGrade
from src.errors import MimpiTaniError
from src.i18n.translator import t
from src.services.buyer_service import BuyerService
from src.services.capacity_service import CapacityService
from src.ui.components import (
    active_database_path,
    is_workspace_initialized,
    render_header,
    render_page_intro,
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
render_page_intro(
    icon="🏢",
    title=t("nav.buyers_capacity"),
    description=t("buyers.provenance"),
    eyebrow=t("buyers.eyebrow"),
)
if notice := st.session_state.pop("buyer_notice", None):
    st.success(t(notice), icon="✅")

buyer_service = BuyerService(active_database_path())
capacity_service = CapacityService(active_database_path())
try:
    buyers = buyer_service.list_buyers()
    demands = buyer_service.list_demands()
except MimpiTaniError as error:
    st.error(user_safe_error_message(error))
    st.stop()

buyer_by_id = {buyer.id: buyer for buyer in buyers}


def priority_label(priority: int) -> str:
    keys = {1: "demand.priority_low", 2: "demand.priority_normal", 3: "demand.priority_high"}
    return t(keys[priority])


buyer_tab, demand_tab, capacity_tab = st.tabs(
    [t("buyers.section"), t("demand.section"), t("capacity.section")]
)

with buyer_tab:
    st.subheader(t("buyers.list_title"))
    st.caption(t("buyers.summary").format(count=sum(buyer.active for buyer in buyers)))
    if buyers:
        st.dataframe(
            [
                {
                    t("common.name"): buyer.name,
                    t("buyers.channel"): t(f"channel.{buyer.channel.value.lower()}"),
                    t("buyers.location"): buyer.location,
                    t("buyers.distance"): f"{buyer.distance_km:,.1f} km",
                    t("common.status"): (
                        t("buyers.active") if buyer.active else t("buyers.inactive")
                    ),
                }
                for buyer in buyers
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info(t("state.empty.buyers"))

    st.markdown(f"#### {t('buyers.add_title')}")
    with st.form("add_buyer_form"):
        buyer_name = st.text_input(t("common.name"), key="add_buyer_name")
        buyer_columns = st.columns(3)
        buyer_channel = buyer_columns[0].selectbox(t("buyers.channel"), list(ChannelType))
        buyer_location = buyer_columns[1].text_input(t("buyers.location"))
        buyer_distance = buyer_columns[2].number_input(
            t("buyers.distance"), min_value=0.0, value=0.0, step=1.0
        )
        add_buyer = st.form_submit_button(t("buyers.add_action"), type="primary")
    if add_buyer:
        try:
            buyer_service.create_buyer(
                name=buyer_name,
                channel=buyer_channel,
                location=buyer_location,
                distance_km=buyer_distance,
            )
        except MimpiTaniError as error:
            st.error(user_safe_error_message(error))
        else:
            st.session_state["buyer_notice"] = "buyers.created"
            st.rerun()

    if buyers:
        st.markdown(f"#### {t('buyers.manage_title')}")
        managed_buyer = st.selectbox(
            t("buyers.select"), buyers, format_func=lambda item: item.name, key="managed_buyer"
        )
        with st.form("edit_buyer_form"):
            edit_name = st.text_input(t("common.name"), value=managed_buyer.name)
            edit_columns = st.columns(3)
            edit_channel = edit_columns[0].selectbox(
                t("buyers.channel"),
                list(ChannelType),
                index=list(ChannelType).index(managed_buyer.channel),
            )
            edit_location = edit_columns[1].text_input(
                t("buyers.location"), value=managed_buyer.location
            )
            edit_distance = edit_columns[2].number_input(
                t("buyers.distance"),
                min_value=0.0,
                value=float(managed_buyer.distance_km),
                step=1.0,
            )
            update_buyer = st.form_submit_button(t("buyers.update_action"))
        if update_buyer:
            try:
                buyer_service.update_buyer(
                    managed_buyer.id,
                    name=edit_name,
                    channel=edit_channel,
                    location=edit_location,
                    distance_km=edit_distance,
                )
            except MimpiTaniError as error:
                st.error(user_safe_error_message(error))
            else:
                st.session_state["buyer_notice"] = "buyers.updated"
                st.rerun()
        if managed_buyer.active:
            confirm_deactivate = st.checkbox(
                t("buyers.deactivate_confirmation"), key="deactivate_buyer_confirm"
            )
            if st.button(
                t("buyers.deactivate_action"),
                disabled=not confirm_deactivate,
                key="deactivate_buyer_button",
            ):
                try:
                    buyer_service.deactivate_buyer(managed_buyer.id)
                except MimpiTaniError as error:
                    st.error(user_safe_error_message(error))
                else:
                    st.session_state["buyer_notice"] = "buyers.deactivated"
                    st.rerun()

with demand_tab:
    st.subheader(t("demand.section"))
    st.caption(t("demand.explanation"))
    if demands:
        st.dataframe(
            [
                {
                    t("common.buyer"): buyer_by_id.get(demand.buyer_id).name,
                    t("buyers.channel"): t(
                        f"channel.{buyer_by_id.get(demand.buyer_id).channel.value.lower()}"
                    ),
                    t("common.quantity"): f"{demand.quantity_kg:,.1f} kg",
                    t("demand.accepted_grades"): ", ".join(
                        grade.value for grade in demand.accepted_grades
                    ),
                    t("demand.deadline"): demand.deadline.strftime("%d %b %Y"),
                    t("demand.priority"): priority_label(demand.priority),
                    t("common.status"): t(f"demand_status.{demand.status.value.lower()}"),
                }
                for demand in demands
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info(t("demand.empty"))

    active_buyers = [buyer for buyer in buyers if buyer.active]
    st.markdown(f"#### {t('demand.add_title')}")
    if not active_buyers:
        st.warning(t("demand.no_active_buyers"))
    else:
        with st.form("add_demand_form"):
            demand_buyer = st.selectbox(
                t("common.buyer"), active_buyers, format_func=lambda item: item.name
            )
            demand_columns = st.columns(3)
            demand_quantity = demand_columns[0].number_input(
                t("demand.quantity_kg"), min_value=0.0, value=100.0, step=10.0
            )
            demand_deadline = demand_columns[1].date_input(
                t("demand.deadline"), value=datetime.now(APP_TIMEZONE).date()
            )
            demand_priority = demand_columns[2].selectbox(
                t("demand.priority"),
                [1, 2, 3],
                index=2,
                format_func=priority_label,
            )
            demand_grades = st.multiselect(t("demand.accepted_grades"), list(QualityGrade))
            add_demand = st.form_submit_button(t("demand.add_action"), type="primary")
        if add_demand:
            try:
                buyer_service.create_demand(
                    buyer_id=demand_buyer.id,
                    quantity_kg=demand_quantity,
                    accepted_grades=tuple(demand_grades),
                    deadline=demand_deadline,
                    priority=demand_priority,
                )
            except MimpiTaniError as error:
                st.error(user_safe_error_message(error))
            else:
                st.session_state["buyer_notice"] = "demand.created"
                st.rerun()

    if demands:
        st.markdown(f"#### {t('demand.manage_title')}")
        managed_demand = st.selectbox(
            t("demand.select"),
            demands,
            format_func=lambda item: (
                f"{buyer_by_id[item.buyer_id].name} · {item.deadline.isoformat()} · "
                f"{item.quantity_kg:,.1f} kg"
            ),
            key="managed_demand",
        )
        with st.form("edit_demand_form"):
            demand_edit_buyer = st.selectbox(
                t("common.buyer"),
                buyers,
                index=next(
                    index
                    for index, buyer in enumerate(buyers)
                    if buyer.id == managed_demand.buyer_id
                ),
                format_func=lambda item: item.name,
                key="edit_demand_buyer",
            )
            demand_edit_columns = st.columns(3)
            demand_edit_quantity = demand_edit_columns[0].number_input(
                t("demand.quantity_kg"),
                min_value=0.0,
                value=float(managed_demand.quantity_kg),
                step=10.0,
                key="edit_demand_quantity",
            )
            demand_edit_deadline = demand_edit_columns[1].date_input(
                t("demand.deadline"), value=managed_demand.deadline, key="edit_demand_deadline"
            )
            demand_edit_priority = demand_edit_columns[2].selectbox(
                t("demand.priority"),
                [1, 2, 3],
                index=managed_demand.priority - 1,
                key="edit_demand_priority",
                format_func=priority_label,
            )
            demand_edit_grades = st.multiselect(
                t("demand.accepted_grades"),
                list(QualityGrade),
                default=list(managed_demand.accepted_grades),
                key="edit_demand_grades",
            )
            update_demand = st.form_submit_button(t("demand.update_action"))
        if update_demand:
            try:
                buyer_service.update_demand(
                    managed_demand.id,
                    buyer_id=demand_edit_buyer.id,
                    quantity_kg=demand_edit_quantity,
                    accepted_grades=tuple(demand_edit_grades),
                    deadline=demand_edit_deadline,
                    priority=demand_edit_priority,
                )
            except MimpiTaniError as error:
                st.error(user_safe_error_message(error))
            else:
                st.session_state["buyer_notice"] = "demand.updated"
                st.rerun()
        if managed_demand.status is DemandStatus.OPEN:
            confirm_close = st.checkbox(t("demand.close_confirmation"), key="close_demand_confirm")
            if st.button(
                t("demand.close_action"), disabled=not confirm_close, key="close_demand_button"
            ):
                try:
                    buyer_service.close_demand(managed_demand.id)
                except MimpiTaniError as error:
                    st.error(user_safe_error_message(error))
                else:
                    st.session_state["buyer_notice"] = "demand.closed"
                    st.rerun()

with capacity_tab:
    st.subheader(t("capacity.section"))
    st.caption(t("capacity.explanation"))
    horizon_start = st.date_input(
        t("capacity.horizon_start"), value=datetime.now(APP_TIMEZONE).date()
    )
    try:
        capacity_days = capacity_service.seven_day_horizon(horizon_start)
    except MimpiTaniError as error:
        st.error(user_safe_error_message(error))
    else:
        missing_count = sum(day.missing for day in capacity_days)
        if missing_count:
            st.warning(t("capacity.missing_warning").format(count=missing_count))
        with st.form("capacity_form"):
            capacity_values = []
            for day in capacity_days:
                columns = st.columns([1, 1, 2])
                columns[0].text_input(
                    t("common.date"),
                    value=day.date.isoformat(),
                    disabled=True,
                    key=f"date_{day.date}",
                )
                quantity = columns[1].number_input(
                    t("capacity.quantity_kg"),
                    min_value=0.0,
                    value=float(day.available_capacity_kg),
                    step=50.0,
                    key=f"capacity_{day.date}",
                )
                note = columns[2].text_input(
                    t("capacity.note"), value=day.note or "", key=f"capacity_note_{day.date}"
                )
                if day.missing:
                    columns[0].caption(t("capacity.missing_status"))
                capacity_values.append((day.date, quantity, note))
            save_capacity = st.form_submit_button(t("capacity.save_action"), type="primary")
        if save_capacity:
            try:
                capacity_service.upsert_week(capacity_values)
            except MimpiTaniError as error:
                st.error(user_safe_error_message(error))
            else:
                st.session_state["buyer_notice"] = "capacity.saved"
                st.rerun()
