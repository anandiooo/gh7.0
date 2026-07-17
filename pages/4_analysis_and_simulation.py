import logging
from datetime import datetime

import streamlit as st
from pydantic import ValidationError as PydanticValidationError

from src.analysis_models import (
    ScenarioOverrides,
    ScenarioResult,
    TemporaryBuyerDemandOverride,
    TemporaryCapacityOverride,
)
from src.config import APP_TIMEZONE
from src.enums import QualityGrade
from src.errors import TetaniError
from src.i18n.translator import t
from src.services.analysis_service import AnalysisOutcome, AnalysisService
from src.services.scenario_service import ScenarioService
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

logger = logging.getLogger(__name__)
sync_language()
if not is_workspace_initialized():
    render_workspace_required()
    st.stop()


def render_outcome(outcome: AnalysisOutcome) -> None:
    with st.container(border=True):
        st.markdown(f"### :material/monitoring: {t('scenario.before')}")
        metric_columns = st.columns(4)
        metric_columns[0].metric(t("analysis.risk_score"), f"{outcome.risk.score:.1f}/100")
        metric_columns[1].metric(
            t("risk.label"), t(f"risk.level.{outcome.risk.level.value.lower()}")
        )
        metric_columns[2].metric(
            t("analysis.allocated_kg"), f"{outcome.optimization.allocated_kg:,.1f} kg"
        )
        metric_columns[3].metric(
            t("analysis.fulfillment_rate"),
            f"{outcome.optimization.demand_fulfillment_rate:.1%}",
        )
        st.info(
            t("analysis.interpretation").format(
                allocated=outcome.optimization.allocated_kg,
                unallocated=outcome.optimization.unallocated_kg,
            )
        )

    with st.container(border=True):
        harvests = {item.batch_id: item for item in outcome.analysis.harvests}
        demands = {item.demand_id: item for item in outcome.analysis.demands}
        st.markdown(f"### :material/assignment: {t('analysis.allocation_table')}")
        if outcome.optimization.allocations:
            st.dataframe(
                [
                    {
                        t("common.farmer"): harvests[item.harvest_batch_id].farmer_name,
                        t("common.grade"): harvests[item.harvest_batch_id].grade.value,
                        t("common.buyer"): demands[item.buyer_demand_id].buyer_name,
                        t("buyers.channel"): t(
                            f"channel.{demands[item.buyer_demand_id].channel.lower()}"
                        ),
                        t("analysis.delivery_date"): item.delivery_date.isoformat(),
                        t("common.quantity"): f"{item.quantity_kg:,.1f} kg",
                        t("analysis.reason"): ", ".join(
                            t(f"allocation_reason.{code.value.lower()}")
                            for code in item.reason_codes
                        ),
                    }
                    for item in outcome.optimization.allocations
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.info(t("analysis.no_allocations"))

    detail_columns = st.columns(2, gap="large")
    with detail_columns[0], st.container(border=True):
        st.markdown(
            f"<h3 style='margin-top:0;'>{t('analysis.unallocated_batches')}</h3>",
            unsafe_allow_html=True,
        )
        if outcome.optimization.unallocated_batches:
            st.dataframe(
                [
                    {
                        t("common.farmer"): harvests[item.harvest_batch_id].farmer_name,
                        t("common.date"): item.harvest_date.isoformat(),
                        t("common.grade"): item.grade.value,
                        t("common.quantity"): f"{item.quantity_kg:,.1f} kg",
                    }
                    for item in outcome.optimization.unallocated_batches
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.success(t("analysis.all_supply_allocated"))
    with detail_columns[1], st.container(border=True):
        st.markdown(
            f"<h3 style='margin-top:0;'>{t('analysis.unmet_demands')}</h3>",
            unsafe_allow_html=True,
        )
        if outcome.optimization.unmet_demands:
            st.dataframe(
                [
                    {
                        t("common.buyer"): demands[item.buyer_demand_id].buyer_name,
                        t("demand.deadline"): item.deadline.isoformat(),
                        t("common.quantity"): f"{item.quantity_kg:,.1f} kg",
                    }
                    for item in outcome.optimization.unmet_demands
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.success(t("analysis.all_demand_fulfilled"))


def render_scenario_comparison(base: AnalysisOutcome, scenario: ScenarioResult) -> None:
    with st.container(border=True):
        st.markdown(f"### :material/compare_arrows: {t('scenario.comparison_title')}")
        st.success(
            t("scenario.improvement_kg").format(
                quantity=scenario.comparison.allocated_kg_delta,
                rate=-scenario.comparison.unallocated_supply_rate_delta,
            )
        )
        comparison_columns = st.columns(4)
        comparison_columns[0].metric(
            t("analysis.risk_score"),
            f"{scenario.risk.score:.1f}/100",
            f"{scenario.comparison.risk_score_delta:+.1f}",
        )
        comparison_columns[1].metric(
            t("analysis.allocated_kg"),
            f"{scenario.optimization.allocated_kg:,.1f} kg",
            f"{scenario.comparison.allocated_kg_delta:+,.1f} kg",
        )
        comparison_columns[2].metric(
            t("analysis.unallocated_kg"),
            f"{scenario.optimization.unallocated_kg:,.1f} kg",
            f"{scenario.comparison.unallocated_kg_delta:+,.1f} kg",
            delta_color="inverse",
        )
        comparison_columns[3].metric(
            t("analysis.fulfillment_rate"),
            f"{scenario.optimization.demand_fulfillment_rate:.1%}",
            f"{scenario.comparison.demand_fulfillment_rate_delta:+.1%}",
        )
        rows = (
            (
                t("analysis.risk_score"),
                base.risk.score,
                scenario.risk.score,
                scenario.comparison.risk_score_delta,
            ),
            (
                t("analysis.allocated_kg"),
                base.optimization.allocated_kg,
                scenario.optimization.allocated_kg,
                scenario.comparison.allocated_kg_delta,
            ),
            (
                t("analysis.unallocated_kg"),
                base.optimization.unallocated_kg,
                scenario.optimization.unallocated_kg,
                scenario.comparison.unallocated_kg_delta,
            ),
            (
                t("analysis.unmet_demand_kg"),
                base.optimization.unmet_demand_kg,
                scenario.optimization.unmet_demand_kg,
                scenario.comparison.unmet_demand_kg_delta,
            ),
        )
        st.dataframe(
            [
                {
                    t("scenario.metric"): label,
                    t("scenario.before"): f"{before:,.2f}",
                    t("scenario.after"): f"{after:,.2f}",
                    t("scenario.delta"): f"{delta:+,.2f}",
                }
                for label, before, after, delta in rows
            ],
            hide_index=True,
            width="stretch",
        )
        st.caption(t("scenario.temporary_notice"))


render_header()
render_prototype_banner()
render_page_intro(
    icon="monitoring",
    title=t("nav.analysis_simulation"),
    description=t("analysis.provenance"),
    eyebrow=t("analysis.eyebrow"),
)
if notice := st.session_state.pop("analysis_notice", None):
    st.success(t(notice), icon=":material/check_circle:")

database_path = active_database_path()
service = AnalysisService(database_path)

with st.container(border=True):
    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    horizon_start = col1.date_input(
        t("analysis.horizon_start"), value=datetime.now(APP_TIMEZONE).date(), key="analysis_horizon"
    )
    if col2.button(
        t("action.run_analysis"),
        type="primary",
        key="analysis_run_button",
        use_container_width=True,
    ):
        try:
            with st.spinner(t("analysis.running")):
                outcome = service.run_base(horizon_start)
        except TetaniError as error:
            st.error(user_safe_error_message(error))
        except Exception:
            logger.exception("Analysis execution failed")
            st.error(t("error.system"))
        else:
            st.session_state["active_analysis_run_id"] = outcome.run.id
            st.session_state.pop("scenario_result_json", None)
            st.session_state["analysis_notice"] = "analysis.completed"
            st.rerun()

try:
    base = service.latest_successful_base()
except TetaniError as error:
    st.error(user_safe_error_message(error))
    st.stop()

if base is None:
    st.info(t("state.empty.analysis"))
    link_columns = st.columns(2)
    if link_columns[0].button(
        t("radar.open_harvest"), icon=":material/agriculture:", use_container_width=True
    ):
        st.switch_page("pages/2_harvest_plans.py")
    if link_columns[1].button(
        t("radar.open_buyers"), icon=":material/storefront:", use_container_width=True
    ):
        st.switch_page("pages/3_buyers_and_capacity.py")
    st.stop()

st.caption(t("analysis.last_run").format(timestamp=base.run.created_at.strftime("%Y-%m-%d %H:%M")))
stale = service.is_stale(base)
if stale:
    st.warning(t("analysis.stale_warning"), icon=":material/warning:")
render_outcome(base)
for warning in base.risk.warnings + base.optimization.warnings:
    st.warning(t(f"analysis.warning.{warning.lower()}"))
st.caption(t("analysis.advisory_disclaimer"))


st.markdown(f"## :material/science: {t('scenario.title')}")
with st.container(border=True):
    st.caption(t("scenario.description"))
    buyer_contexts = list({item.buyer_id: item for item in base.analysis.demands}.values())
    scenario_name = st.text_input(t("scenario.name"), value=t("scenario.default_name"))

    sc_cols = st.columns(2, gap="large")

    with sc_cols[0]:
        use_demand = st.checkbox(t("scenario.add_demand"), value=True)
        selected_buyer = None
        scenario_quantity = 1000.0
        scenario_grades = list(QualityGrade)
        scenario_deadline = base.analysis.horizon_end
        scenario_priority = 3
        if use_demand and buyer_contexts:
            selected_buyer = st.selectbox(
                t("scenario.existing_buyer"),
                buyer_contexts,
                format_func=lambda item: item.buyer_name,
            )
            scenario_quantity = st.number_input(
                t("demand.quantity_kg"), min_value=0.0, value=1000.0, step=100.0
            )
            scenario_deadline = st.date_input(
                t("demand.deadline"), value=base.analysis.horizon_end, key="scenario_deadline"
            )
            scenario_priority = st.selectbox(
                t("demand.priority"), [1, 2, 3], index=2, key="scenario_priority"
            )
            scenario_grades = st.multiselect(
                t("demand.accepted_grades"),
                list(QualityGrade),
                default=list(QualityGrade),
                key="scenario_grades",
            )

    with sc_cols[1]:
        use_capacity = st.checkbox(t("scenario.replace_capacity"), value=True)
        capacity_date = base.risk.critical_date or base.analysis.horizon_end
        capacity_value = 1500.0
        if use_capacity:
            capacity_date = st.selectbox(
                t("common.date"), [item.date for item in base.analysis.daily_capacity]
            )
            current_capacity = next(
                item.quantity_kg
                for item in base.analysis.daily_capacity
                if item.date == capacity_date
            )
            capacity_value = st.number_input(
                t("scenario.effective_capacity"),
                min_value=0.0,
                value=max(1500.0, float(current_capacity)),
                step=100.0,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(
        t("scenario.run_action"),
        type="primary",
        disabled=stale,
        key="scenario_run_button",
        use_container_width=True,
    ):
        try:
            demand_override = (
                TemporaryBuyerDemandOverride(
                    buyer_id=selected_buyer.buyer_id,
                    buyer_name=selected_buyer.buyer_name,
                    channel=selected_buyer.channel,
                    distance_km=selected_buyer.distance_km,
                    quantity_kg=scenario_quantity,
                    accepted_grades=tuple(scenario_grades),
                    deadline=scenario_deadline,
                    priority=scenario_priority,
                )
                if use_demand and selected_buyer
                else None
            )
            capacity_overrides = (
                (
                    TemporaryCapacityOverride(
                        date=capacity_date, effective_capacity_kg=capacity_value
                    ),
                )
                if use_capacity
                else ()
            )
            overrides = ScenarioOverrides(
                scenario_name=scenario_name,
                buyer_demand=demand_override,
                capacities=capacity_overrides,
            )
            scenario = ScenarioService().run(base, overrides)
        except (TetaniError, PydanticValidationError) as error:
            st.error(
                user_safe_error_message(error)
                if isinstance(error, TetaniError)
                else t("error.validation")
            )
        except Exception:
            logger.exception("Scenario execution failed")
            st.error(t("error.system"))
        else:
            st.session_state["scenario_result_json"] = scenario.model_dump_json()
            st.session_state["scenario_base_run_id"] = base.run.id
            st.success(t("scenario.completed"), icon=":material/check_circle:")

if (
    not stale
    and st.session_state.get("scenario_base_run_id") == base.run.id
    and (scenario_json := st.session_state.get("scenario_result_json"))
):
    render_scenario_comparison(base, ScenarioResult.model_validate_json(scenario_json))

st.markdown("<br>", unsafe_allow_html=True)
with st.expander(t("analysis.technical_details"), icon=":material/settings:"):
    st.write(
        f"{t('analysis.solver_status')}: "
        f"{t(f'solver_status.{base.optimization.status.value.lower()}')}"
    )
    st.markdown(f"#### {t('analysis.factor_breakdown')}")
    st.dataframe(
        [
            {
                t("analysis.factor"): t(f"risk.factor_name.{factor.code.value.lower()}"),
                t("analysis.raw_factor"): f"{factor.raw_value:.3f}",
                t("analysis.weight"): f"{factor.weight:.1f}",
                t("analysis.points"): f"{factor.weighted_points:.2f}",
            }
            for factor in base.risk.factors
        ],
        hide_index=True,
        width="stretch",
    )
    st.code(base.run.id)
    st.write(f"{t('analysis.data_version')}: {base.run.data_version}")
    st.dataframe(
        [
            {
                t("analysis.run_id"): run.id,
                t("analysis.run_type"): run.run_type.value,
                t("common.date"): run.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for run in service.list_recent_runs()
        ],
        hide_index=True,
        width="stretch",
    )
