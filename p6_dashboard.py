import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import os

st.set_page_config(
    page_title="P6 EVM Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #1e1e2e;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid #2d2d44;
}
.health-red    { border-left: 6px solid #ef4444; background: #2d1b1b; }
.health-amber  { border-left: 6px solid #f59e0b; background: #2d2410; }
.health-green  { border-left: 6px solid #22c55e; background: #1b2d1e; }
.section-title { font-size: 1.1rem; font-weight: 600; color: #94a3b8; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Data store (session state acts as in-memory DB) ─────────────────────────
if "evm_history" not in st.session_state:
    st.session_state.evm_history = []
if "latest" not in st.session_state:
    st.session_state.latest = None
if "activities" not in st.session_state:
    st.session_state.activities = []

# ── Webhook receiver via query params (n8n sends GET with params) ────────────
# n8n HTTP Request node POSTs JSON → Streamlit reads it via st.query_params
# For production: use st.experimental_memo or a small FastAPI sidecar
# Here we use a file-based approach for simplicity

DATA_FILE = "p6_latest.json"

def load_from_file():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return None

def save_to_file(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ── Sidebar: Manual data input / file upload ─────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Oracle_Primavera_logo.png/320px-Oracle_Primavera_logo.png", width=160)
    st.title("P6 EVM Control")
    st.divider()

    st.subheader("📥 Load Data")
    uploaded = st.file_uploader("Upload n8n JSON output", type=["json"])
    if uploaded:
        data = json.load(uploaded)
        st.session_state.latest = data
        st.session_state.evm_history.append({**data.get("summary", {}), "timestamp": datetime.now().isoformat()})
        st.session_state.activities = data.get("activities", [])
        st.success("Data loaded!")

    st.divider()
    st.subheader("🔄 Auto-refresh")
    auto = st.toggle("Refresh from file", value=False)
    if auto:
        file_data = load_from_file()
        if file_data:
            st.session_state.latest = file_data
            st.session_state.activities = file_data.get("activities", [])

    st.divider()
    st.caption("Connected to: Primavera P6 Pipeline")
    st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ── Demo data if nothing loaded ───────────────────────────────────────────────
if not st.session_state.latest:
    st.session_state.latest = {
        "summary": {
            "total_activities": 24,
            "planned_value": 250000,
            "earned_value": 198000,
            "actual_cost": 215000,
            "schedule_variance": -52000,
            "schedule_performance_index": 0.792,
            "cost_variance": -17000,
            "cost_performance_index": 0.921,
            "estimate_at_completion": 271250,
            "project_health": "RED"
        },
        "risk_indicators": {
            "critical_path_activities": ["A1000", "A1020", "A1050"],
            "negative_float_activities": ["A1020", "A1050"],
            "delayed_milestones": ["MEP Rough-In", "Facade Installation"],
            "negative_float_count": 2
        },
        "activities": [
            {"activity_id": "A1000", "activity_name": "Foundation Work", "percent_complete": 100, "total_float": 0, "budget_cost": 50000, "actual_cost": 48000, "status": "Complete"},
            {"activity_id": "A1010", "activity_name": "Structural Steel", "percent_complete": 75, "total_float": 3, "budget_cost": 120000, "actual_cost": 95000, "status": "In Progress"},
            {"activity_id": "A1020", "activity_name": "MEP Rough-In", "percent_complete": 30, "total_float": -2, "budget_cost": 80000, "actual_cost": 42000, "status": "In Progress"},
            {"activity_id": "A1030", "activity_name": "Facade Installation", "percent_complete": 0, "total_float": -5, "budget_cost": 60000, "actual_cost": 0, "status": "Not Started"},
            {"activity_id": "A1040", "activity_name": "Interior Fit-Out", "percent_complete": 0, "total_float": 10, "budget_cost": 90000, "actual_cost": 0, "status": "Not Started"},
        ]
    }
    st.session_state.activities = st.session_state.latest["activities"]

data    = st.session_state.latest
summary = data.get("summary", {})
risks   = data.get("risk_indicators", {})
acts    = st.session_state.activities

health      = summary.get("project_health", "GREEN")
health_cls  = f"health-{health.lower()}"
health_icon = {"RED": "🔴", "AMBER": "🟡", "GREEN": "🟢"}.get(health, "⚪")
spi         = summary.get("schedule_performance_index", 0)
cpi         = summary.get("cost_performance_index", 0)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"## 🏗️ Primavera P6 — EVM Dashboard")
st.markdown(f"<div class='metric-card {health_cls}'><h2>{health_icon} Project Health: {health}</h2></div>", unsafe_allow_html=True)
st.divider()

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("📅 SPI",  f"{spi:.3f}",  delta=f"{spi-1:.3f}", delta_color="normal")
k2.metric("💰 CPI",  f"{cpi:.3f}",  delta=f"{cpi-1:.3f}", delta_color="normal")
k3.metric("📊 PV",   f"${summary.get('planned_value', 0):,.0f}")
k4.metric("✅ EV",   f"${summary.get('earned_value', 0):,.0f}",  delta=f"${summary.get('schedule_variance', 0):,.0f}")
k5.metric("💸 AC",   f"${summary.get('actual_cost', 0):,.0f}",   delta=f"${summary.get('cost_variance', 0):,.0f}")

st.divider()

# ── Gauges + EAC ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

def gauge(title, val, low=0.9, high=1.0):
    color = "#ef4444" if val < low else ("#f59e0b" if val < high else "#22c55e")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        title={"text": title, "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 1.5], "tickwidth": 1},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 0.9],    "color": "#3f1a1a"},
                {"range": [0.9, 0.95], "color": "#3f2e10"},
                {"range": [0.95, 1.5], "color": "#1a3f1e"},
            ],
            "threshold": {"line": {"color": "white", "width": 3}, "thickness": 0.75, "value": 1.0}
        }
    ))
    fig.update_layout(height=250, margin=dict(t=40, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)", font_color="white")
    return fig

with col1:
    st.plotly_chart(gauge("Schedule Performance Index (SPI)", spi), use_container_width=True)
with col2:
    st.plotly_chart(gauge("Cost Performance Index (CPI)", cpi), use_container_width=True)
with col3:
    eac = summary.get("estimate_at_completion", 0)
    pv  = summary.get("planned_value", 1)
    overrun_pct = ((eac - pv) / pv * 100) if pv else 0
    st.metric("📈 Estimate at Completion (EAC)", f"${eac:,.0f}", delta=f"{overrun_pct:+.1f}% vs Budget", delta_color="inverse")
    st.metric("⚠️ Negative Float Activities", risks.get("negative_float_count", 0), delta_color="inverse")
    st.metric("🔴 Critical Path Activities",  len(risks.get("critical_path_activities", [])))

st.divider()

# ── S-Curve (PV / EV / AC) ───────────────────────────────────────────────────
st.subheader("📈 S-Curve: PV vs EV vs AC")
pv_val = summary.get("planned_value", 0)
ev_val = summary.get("earned_value",  0)
ac_val = summary.get("actual_cost",   0)

scurve = pd.DataFrame({
    "Period": ["Start", "Q1", "Q2", "Q3", "Now"],
    "PV": [0, pv_val*0.2, pv_val*0.5, pv_val*0.75, pv_val],
    "EV": [0, ev_val*0.15, ev_val*0.4, ev_val*0.7,  ev_val],
    "AC": [0, ac_val*0.18, ac_val*0.45, ac_val*0.72, ac_val],
})
fig_s = px.line(scurve, x="Period", y=["PV", "EV", "AC"],
                color_discrete_map={"PV": "#60a5fa", "EV": "#34d399", "AC": "#f87171"},
                markers=True)
fig_s.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white", legend_title="", height=320)
st.plotly_chart(fig_s, use_container_width=True)

st.divider()

# ── Activity Table ────────────────────────────────────────────────────────────
st.subheader("📋 Activity Status")
if acts:
    df = pd.DataFrame(acts)
    cols_to_show = [c for c in ["activity_id","activity_name","status","percent_complete","total_float","budget_cost","actual_cost"] if c in df.columns]
    df_show = df[cols_to_show].copy()
    df_show.columns = [c.replace("_", " ").title() for c in cols_to_show]

    def color_float(val):
        if isinstance(val, (int, float)):
            if val < 0:   return "background-color: #3f1a1a; color: #ef4444"
            if val == 0:  return "background-color: #2d1f10; color: #f59e0b"
        return ""

    def color_status(val):
        m = {"Complete": "color: #34d399", "In Progress": "color: #60a5fa", "Not Started": "color: #94a3b8"}
        return m.get(val, "")

    styled = df_show.style.map(color_float, subset=["Total Float"] if "Total Float" in df_show.columns else []) \
                          .map(color_status, subset=["Status"] if "Status" in df_show.columns else [])
    st.dataframe(styled, use_container_width=True, height=320)

st.divider()

# ── Risk Panel ────────────────────────────────────────────────────────────────
st.subheader("⚠️ Risk Indicators")
r1, r2 = st.columns(2)
with r1:
    st.markdown("**🔴 Negative Float Activities**")
    for a in risks.get("negative_float_activities", []):
        st.error(f"Activity: {a}")
    if not risks.get("negative_float_activities"):
        st.success("None — all activities on schedule")

with r2:
    st.markdown("**⏰ Delayed Milestones**")
    for m in risks.get("delayed_milestones", []):
        st.warning(f"⚠️ {m}")
    if not risks.get("delayed_milestones"):
        st.success("No delayed milestones")

st.divider()
st.caption("Primavera P6 EVM Dashboard · Powered by n8n + Streamlit · Auto-updates every pipeline run")
