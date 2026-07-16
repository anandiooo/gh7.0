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
from src.ui.theme import ACCENT_WARNING_ORANGE, PRIMARY_DARK_GREEN, RISK_COLORS

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
status_columns[0].markdown(
    f'<span class="mt-pill">🌦️ {weather_label}</span>', unsafe_allow_html=True
)
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
    with st.expander(t("workspace.summary_title"), expanded=True):
        render_workspace_summary(workspace)
    st.page_link("pages/2_harvest_plans.py", label=t("radar.open_harvest"), icon="🌾")
    st.stop()

st.markdown(
    f'<div class="mt-section-label">{t("radar.chart_title")}</div>',
    unsafe_allow_html=True,
)
figure = go.Figure()
figure.add_trace(
    go.Scatter(
        x=[item.date for item in radar.analysis.daily_supply],
        y=[item.quantity_kg for item in radar.analysis.daily_supply],
        name=t("common.supply"),
        mode="lines+markers",
        fill="tozeroy",
        fillcolor="rgba(199,57,47,0.10)",
        line=dict(color="#C7392F", width=3),
        marker=dict(size=8, color="#C7392F", line=dict(color="white", width=2)),
    )
)
figure.add_trace(
    go.Scatter(
        x=[item.date for item in radar.analysis.daily_compatible_demand],
        y=[item.quantity_kg for item in radar.analysis.daily_compatible_demand],
        name=t("radar.compatible_demand"),
        mode="lines+markers",
        line=dict(color="#388E3C", width=3),
        marker=dict(size=8, color="#388E3C", line=dict(color="white", width=2)),
    )
)
figure.add_trace(
    go.Scatter(
        x=[item.date for item in radar.analysis.daily_capacity],
        y=[item.quantity_kg for item in radar.analysis.daily_capacity],
        name=t("common.capacity"),
        mode="lines+markers",
        line=dict(color=ACCENT_WARNING_ORANGE, width=3, dash="dot"),
        marker=dict(size=8, color=ACCENT_WARNING_ORANGE, line=dict(color="white", width=2)),
    )
)
figure.add_vline(
    x=radar.risk.critical_date.isoformat(),
    line_width=1.5,
    line_dash="dash",
    line_color="rgba(199,57,47,0.55)",
)
figure.update_layout(
    xaxis_title=t("common.date"),
    yaxis_title=t("radar.quantity_kg"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(l=20, r=20, t=42, b=20),
    height=410,
    hovermode="x unified",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(247,250,245,0.78)",
    font=dict(color="#334B35"),
    xaxis=dict(showgrid=False, tickformat="%d %b"),
    yaxis=dict(gridcolor="rgba(20,83,25,0.09)", zeroline=False),
)
chart_column, pulse_column = st.columns([2.15, 1], gap="medium")
with chart_column:
    st.caption(t("radar.chart_subtitle"))
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
with pulse_column:
    st.markdown(f"### {t('radar.decision_pulse')}")
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=radar.risk.score,
            number={"suffix": "/100", "font": {"size": 34, "color": PRIMARY_DARK_GREEN}},
            title={
                "text": t(f"risk.level.{radar.risk.level.value.lower()}"),
                "font": {"size": 17, "color": RISK_COLORS[radar.risk.level.value]},
            },
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "white"},
                "bar": {"color": RISK_COLORS[radar.risk.level.value], "thickness": 0.32},
                "bgcolor": "rgba(56,142,60,0.08)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 25], "color": "rgba(22,163,74,0.08)"},
                    {"range": [25, 50], "color": "rgba(217,119,6,0.08)"},
                    {"range": [50, 75], "color": "rgba(234,88,12,0.08)"},
                    {"range": [75, 100], "color": "rgba(220,38,38,0.08)"},
                ],
            },
        )
    )
    gauge.update_layout(
        height=275,
        margin=dict(l=22, r=22, t=52, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(gauge, width="stretch", config={"displayModeBar": False})
    st.metric(t("radar.critical_date"), radar.risk.critical_date.strftime("%d %b %Y"))

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

location_column, explanation_column = st.columns([1, 2], gap="medium")
with location_column:
    st.markdown(f"### {t('radar.pilot_map_title')}")
    pilot_map = go.Figure(
        go.Scattermap(
            lat=[PILOT_LATITUDE],
            lon=[PILOT_LONGITUDE],
            mode="markers",
            marker={"size": 18, "color": "#C7392F"},
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
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(pilot_map, width="stretch", config={"displayModeBar": False})
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
with st.expander(t("workspace.summary_title")):
    render_workspace_summary(workspace)
st.caption(t("analysis.advisory_disclaimer"))
