import logging
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from src.config import APP_TIMEZONE, PILOT_LATITUDE, PILOT_LONGITUDE
from src.errors import MimpiTaniError
from src.i18n.translator import t
from src.services.analysis_service import AnalysisService
from src.services.radar_service import RadarService
from src.services.workspace_service import get_workspace_summary
from src.ui.components import (
    active_database_path,
    is_workspace_initialized,
    render_header,
    render_page_intro,
    render_prototype_banner,
    render_workspace_required,
    render_workspace_summary,
    sync_language,
)
from src.ui.messages import user_safe_error_message
from src.ui.theme import ACCENT_WARNING_ORANGE

logger = logging.getLogger(__name__)
sync_language()
if not is_workspace_initialized():
    render_workspace_required()
    st.stop()

render_header()
render_prototype_banner()
database_path = active_database_path()
try:
    workspace = get_workspace_summary(database_path)
except MimpiTaniError as error:
    st.error(user_safe_error_message(error))
    st.stop()

render_page_intro(
    icon="📡",
    title=t("nav.radar"),
    description=(
        f"{workspace.profile.name} · {workspace.profile.pilot_region} · "
        f"{t('workspace.commodity_name')} · {workspace.profile.workspace_mode.value}"
    ),
    eyebrow=t("radar.eyebrow"),
)
with st.sidebar:
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
status_columns = st.columns([1, 2])
status_columns[0].info(f"🌦️ {weather_label}")
status_columns[1].caption(t("radar.weather_continues"))
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
    st.markdown(f"### {t('radar.setup_title')}")
    setup_steps = (
        (
            workspace.planned_harvest_batches > 0,
            "radar.setup_harvest",
            "radar.setup_harvest_help",
            "pages/2_harvest_plans.py",
            "🌾",
        ),
        (
            workspace.active_buyers > 0 and workspace.open_demands > 0,
            "radar.setup_buyer",
            "radar.setup_buyer_help",
            "pages/3_buyers_and_capacity.py",
            "🏢",
        ),
        (
            workspace.capacity_days > 0,
            "radar.setup_capacity",
            "radar.setup_capacity_help",
            "pages/3_buyers_and_capacity.py",
            "🚚",
        ),
        (
            False,
            "radar.setup_analysis",
            "radar.setup_analysis_help",
            "pages/4_analysis_and_simulation.py",
            "📊",
        ),
    )
    for index, (complete, title_key, help_key, page, icon) in enumerate(setup_steps):
        status = f"✅ {t('radar.setup_done')}" if complete else f"○ {t('radar.setup_pending')}"
        step_columns = st.columns([1.6, 3, 1.6], vertical_alignment="center")
        step_columns[0].markdown(f"**{status} — {t(title_key)}**")
        step_columns[1].caption(t(help_key))
        if step_columns[2].button(
            t(title_key), key=f"setup_step_{index}", icon=icon, width="stretch"
        ):
            st.switch_page(page)
    with st.expander(t("workspace.summary_title")):
        render_workspace_summary(workspace)
    st.stop()

st.markdown(
    '<div class="mt-status-card">'
    f'<div class="mt-eyebrow">{t("risk.label")}</div>'
    f"<h2>{t(f'risk.level.{radar.risk.level.value.lower()}').upper()} · "
    f"{radar.risk.score:.1f}/100</h2><p>{t('radar.status_summary')}</p>"
    f"<p><strong>{t('radar.critical_date')}:</strong> "
    f"{radar.risk.critical_date.strftime('%d %b %Y')}</p></div>",
    unsafe_allow_html=True,
)
action_columns = st.columns([1.5, 1, 2])
if action_columns[0].button(
    t("action.run_analysis"), type="primary", key="radar_run_analysis", width="stretch"
):
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
action_columns[1].page_link(
    "pages/3_buyers_and_capacity.py", label=t("radar.open_buyers"), icon="🏢"
)

kpi_columns = st.columns(4)
kpis = (
    ("radar.expected_harvest", radar.analysis.total_supply_kg),
    ("radar.compatible_demand", radar.analysis.compatible_demand_kg),
    ("common.capacity", sum(item.quantity_kg for item in radar.analysis.daily_capacity)),
    ("radar.operational_surplus", radar.operationally_constrained_surplus_kg),
)
for column, (label, value) in zip(kpi_columns, kpis, strict=True):
    column.metric(t(label), f"{value:,.1f} kg")

st.subheader(t("radar.chart_title"))
figure = go.Figure()
figure.add_trace(
    go.Scatter(
        x=[item.date for item in radar.analysis.daily_supply],
        y=[item.quantity_kg for item in radar.analysis.daily_supply],
        name=t("common.supply"),
        mode="lines+markers",
        fill="tozeroy",
        fillcolor="rgba(33,73,22,0.12)",
        line=dict(color="#214916", width=3),
        marker=dict(size=8, color="#214916", line=dict(color="#FAF8EF", width=2)),
    )
)
figure.add_trace(
    go.Scatter(
        x=[item.date for item in radar.analysis.daily_compatible_demand],
        y=[item.quantity_kg for item in radar.analysis.daily_compatible_demand],
        name=t("radar.compatible_demand"),
        mode="lines+markers",
        line=dict(color="#A9EB35", width=3),
        marker=dict(size=8, color="#A9EB35", line=dict(color="#214916", width=2)),
    )
)
figure.add_trace(
    go.Scatter(
        x=[item.date for item in radar.analysis.daily_capacity],
        y=[item.quantity_kg for item in radar.analysis.daily_capacity],
        name=t("common.capacity"),
        mode="lines+markers",
        line=dict(color=ACCENT_WARNING_ORANGE, width=3, dash="dot"),
        marker=dict(
            size=8,
            color=ACCENT_WARNING_ORANGE,
            line=dict(color="#214916", width=2),
        ),
    )
)
figure.add_vline(
    x=radar.risk.critical_date.isoformat(),
    line_width=1.5,
    line_dash="dash",
    line_color="rgba(247,220,39,0.82)",
)
figure.update_layout(
    xaxis_title=t("common.date"),
    yaxis_title=t("radar.quantity_kg"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(l=58, r=20, t=42, b=52),
    height=410,
    hovermode="x unified",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(250,248,239,0.92)",
    font=dict(color="#214916", family="Helvetica World, Helvetica Neue, Helvetica, Arial"),
    xaxis=dict(showgrid=False, tickformat="%d %b %Y"),
    yaxis=dict(gridcolor="rgba(41,127,57,0.14)", zeroline=False),
)
st.caption(t("radar.chart_subtitle"))
st.plotly_chart(
    figure,
    width="stretch",
    theme=None,
    config={"displayModeBar": False},
)

location_column, explanation_column = st.columns([1, 2], gap="medium")
with location_column:
    st.markdown(f"### {t('radar.pilot_map_title')}")
    pilot_map = go.Figure(
        go.Scattermap(
            lat=[PILOT_LATITUDE],
            lon=[PILOT_LONGITUDE],
            mode="markers",
            marker={"size": 18, "color": "#F7DC27"},
            text=[workspace.profile.name],
            hovertemplate="%{text}<extra></extra>",
        )
    )
    pilot_map.update_layout(
        map={
            "style": "carto-positron",
            "center": {"lat": PILOT_LATITUDE, "lon": PILOT_LONGITUDE},
            "zoom": 7.2,
        },
        height=310,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(
        pilot_map,
        width="stretch",
        theme=None,
        config={"displayModeBar": False},
    )
    st.caption(t("radar.pilot_map_caption"))
with explanation_column:
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

guidance_columns = st.columns(2)
with guidance_columns[0]:
    st.page_link("pages/2_harvest_plans.py", label=t("radar.open_harvest"), icon="🌾")
with guidance_columns[1]:
    st.page_link("pages/3_buyers_and_capacity.py", label=t("radar.open_buyers"), icon="🏢")
with st.expander(t("workspace.summary_title")):
    render_workspace_summary(workspace)
st.caption(t("analysis.advisory_disclaimer"))
