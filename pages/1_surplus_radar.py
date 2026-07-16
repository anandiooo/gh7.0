import logging
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from src.config import APP_TIMEZONE
from src.errors import MimpiTaniError
from src.i18n.translator import t
from src.services.analysis_service import AnalysisService
from src.services.radar_service import RadarService
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

logger = logging.getLogger(__name__)
sync_language()
if not is_workspace_initialized():
    render_workspace_required()
    st.stop()

render_header()
render_prototype_banner()
st.subheader(t("nav.radar"))
database_path = active_database_path()
try:
    workspace = get_workspace_summary(database_path)
except MimpiTaniError as error:
    st.error(user_safe_error_message(error))
    st.stop()

st.caption(f"{workspace.profile.name} · {workspace.profile.pilot_region}")
st.caption(t("radar.provenance"))
render_workspace_summary(workspace)
horizon_start = st.date_input(
    t("radar.horizon_start"), value=datetime.now(APP_TIMEZONE).date(), key="radar_horizon"
)
analysis_service = AnalysisService(database_path)
try:
    radar = RadarService(database_path).calculate(horizon_start)
    latest = analysis_service.latest_successful_base()
except MimpiTaniError as error:
    st.error(user_safe_error_message(error))
    st.stop()
except Exception:
    logger.exception("Radar calculation failed")
    st.error(t("error.system"))
    st.stop()

weather_label = t(f"weather.{radar.risk.weather_status.value.lower()}")
st.info(f"{weather_label} · {t('radar.weather_continues')}", icon="🌦️")
if latest:
    if analysis_service.is_stale(latest):
        st.warning(t("analysis.stale_warning"), icon="⚠️")
    else:
        st.caption(
            t("analysis.last_run").format(
                timestamp=latest.run.created_at.strftime("%Y-%m-%d %H:%M")
            )
        )

if not radar.risk.has_data:
    st.info(t("state.empty.radar"))
    st.page_link("pages/2_harvest_plans.py", label=t("radar.open_harvest"), icon="🌾")
    st.stop()

kpi_columns = st.columns(5)
kpis = (
    ("radar.expected_harvest", radar.analysis.total_supply_kg),
    ("radar.compatible_demand", radar.analysis.compatible_demand_kg),
    ("radar.potential_surplus", radar.potential_surplus_kg),
    ("radar.operational_surplus", radar.operationally_constrained_surplus_kg),
)
for column, (label, value) in zip(kpi_columns[:4], kpis, strict=True):
    column.metric(t(label), f"{value:,.1f} kg")
kpi_columns[4].metric(
    t("risk.label"),
    t(f"risk.level.{radar.risk.level.value.lower()}"),
    f"{radar.risk.score:.1f}/100",
)

figure = go.Figure()
figure.add_trace(
    go.Scatter(
        x=[item.date for item in radar.analysis.daily_supply],
        y=[item.quantity_kg for item in radar.analysis.daily_supply],
        name=t("common.supply"),
        mode="lines+markers",
    )
)
figure.add_trace(
    go.Scatter(
        x=[item.date for item in radar.analysis.daily_compatible_demand],
        y=[item.quantity_kg for item in radar.analysis.daily_compatible_demand],
        name=t("radar.compatible_demand"),
        mode="lines+markers",
    )
)
figure.add_trace(
    go.Scatter(
        x=[item.date for item in radar.analysis.daily_capacity],
        y=[item.quantity_kg for item in radar.analysis.daily_capacity],
        name=t("common.capacity"),
        mode="lines+markers",
    )
)
figure.update_layout(
    title=t("radar.chart_title"),
    xaxis_title=t("common.date"),
    yaxis_title=t("radar.quantity_kg"),
    legend_title_text=t("radar.series"),
    margin=dict(l=20, r=20, t=55, b=20),
    height=360,
)
st.plotly_chart(figure, width="stretch")

risk_column, date_column = st.columns(2)
risk_column.markdown(f"### {t('radar.risk_score')}: {radar.risk.score:.1f}/100")
risk_column.write(t(f"risk.level.{radar.risk.level.value.lower()}"))
date_column.markdown(f"### {t('radar.critical_date')}")
date_column.write(radar.risk.critical_date.isoformat())

factor_column, action_column = st.columns(2)
with factor_column:
    st.markdown(f"### {t('radar.top_factors')}")
    factor_by_code = {factor.code: factor for factor in radar.risk.factors}
    for code in radar.risk.top_factors:
        factor = factor_by_code[code]
        explanation = t(f"risk.factor.{code.value.lower()}").format(
            value=factor.raw_value,
            points=factor.weighted_points,
        )
        st.write(f"- {explanation}")
with action_column:
    st.markdown(f"### {t('radar.recommended_actions')}")
    for action in radar.risk.recommended_actions:
        st.write(f"- {t(f'action_code.{action.value.lower()}')}")

for warning in radar.risk.warnings:
    st.warning(t(f"analysis.warning.{warning.lower()}"))

if st.button(t("action.run_analysis"), type="primary", key="radar_run_analysis"):
    try:
        with st.spinner(t("analysis.running")):
            outcome = analysis_service.run_base(horizon_start)
    except MimpiTaniError as error:
        st.error(user_safe_error_message(error))
    except Exception:
        logger.exception("Base analysis failed")
        st.error(t("error.system"))
    else:
        st.session_state["active_analysis_run_id"] = outcome.run.id
        st.session_state["analysis_notice"] = "analysis.completed"
        st.rerun()

guidance_columns = st.columns(2)
with guidance_columns[0]:
    st.page_link("pages/2_harvest_plans.py", label=t("radar.open_harvest"), icon="🌾")
with guidance_columns[1]:
    st.page_link("pages/3_buyers_and_capacity.py", label=t("radar.open_buyers"), icon="🏢")
st.caption(t("analysis.advisory_disclaimer"))
