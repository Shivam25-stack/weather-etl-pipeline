"""Dashboard:  streamlit run dashboard.py"""
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pipeline import config

st.set_page_config(page_title="Air & Weather Monitor", page_icon="🌤️", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {padding-top: 2rem;}
.hero {padding: 1.4rem 1.8rem; border-radius: 16px; margin-bottom: 1rem;
       background: linear-gradient(135deg, #1e3a8a 0%, #0ea5e9 60%, #22d3ee 100%);}
.hero h1 {margin: 0; color: white; font-size: 2rem;}
.hero p {margin: .3rem 0 0; color: #e0f2fe;}
.card {background: #161b26; border: 1px solid #263045; border-radius: 14px;
       padding: 1rem 1.2rem; height: 100%;}
.card .label {color: #94a3b8; font-size: .8rem; text-transform: uppercase; letter-spacing: .05em;}
.card .value {color: #f8fafc; font-size: 2rem; font-weight: 700; line-height: 1.3;}
.card .sub {font-size: .85rem;}
.badge {display: inline-block; padding: 2px 10px; border-radius: 999px;
        font-size: .8rem; font-weight: 600; color: #0b0f19;}
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
AQI_LEVELS = [  # (upper limit, label, color)
    (50, "Good", "#22c55e"),
    (100, "Moderate", "#eab308"),
    (150, "Unhealthy for sensitive", "#f97316"),
    (200, "Unhealthy", "#ef4444"),
    (300, "Very unhealthy", "#a855f7"),
    (10_000, "Hazardous", "#9f1239"),
]


def aqi_level(value):
    if value is None or value != value:
        return "No data", "#64748b"
    for limit, label, color in AQI_LEVELS:
        if value <= limit:
            return label, color


def card(label, value, sub=""):
    return f'<div class="card"><div class="label">{label}</div>' \
           f'<div class="value">{value}</div><div class="sub">{sub}</div></div>'


def style(fig, height=320):
    fig.update_layout(template="plotly_dark", height=height, margin=dict(l=10, r=10, t=30, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.12))
    return fig


# ---------- Data ----------
if not config.DB_PATH.exists():
    st.warning("No data yet. Run `python run_pipeline.py` first.")
    st.stop()

con = duckdb.connect(str(config.DB_PATH), read_only=True)
all_df = con.execute("SELECT * FROM readings ORDER BY city, observed_at").df()
con.close()

now = pd.Timestamp.now("UTC").tz_localize(None)
cities = sorted(all_df["city"].unique())

st.sidebar.header("Filters")
city = st.sidebar.selectbox("City", cities)
compare = st.sidebar.multiselect("Compare cities", cities, default=cities[:3])
st.sidebar.caption(f"{len(all_df):,} rows · {len(cities)} cities")

df = all_df[all_df["city"] == city]
past = df[df["observed_at"] <= now].dropna(subset=["temperature_c"])
latest = past.iloc[-1]
prev = past.iloc[-2] if len(past) > 1 else latest

# ---------- Header ----------
st.markdown(f"""<div class="hero"><h1>🌤️ Air & Weather Monitor</h1>
<p>{city} · latest reading {latest.observed_at:%d %b %Y, %H:%M} UTC</p></div>""",
            unsafe_allow_html=True)

# ---------- KPI cards ----------
label, color = aqi_level(latest.aqi)
dt = latest.temperature_c - prev.temperature_c
arrow = "▲" if dt > 0 else "▼" if dt < 0 else "–"

k1, k2, k3, k4 = st.columns(4)
k1.markdown(card("Temperature", f"{latest.temperature_c:.1f}°C",
                 f"{arrow} {abs(dt):.1f}° vs previous hour"), unsafe_allow_html=True)
k2.markdown(card("Humidity", f"{latest.humidity_pct:.0f}%",
                 f"Wind {latest.wind_kmh:.0f} km/h"), unsafe_allow_html=True)
k3.markdown(card("Air quality (US AQI)",
                 "n/a" if latest.aqi != latest.aqi else f"{latest.aqi:.0f}",
                 f'<span class="badge" style="background:{color}">{label}</span>'),
            unsafe_allow_html=True)
k4.markdown(card("PM2.5", f"{latest.pm25:.1f}", "µg/m³ · fine particles"),
            unsafe_allow_html=True)

st.write("")

# ---------- Row 1: gauge + temperature/humidity ----------
g, t = st.columns([1, 2])
with g:
    st.subheader("Air quality now")
    gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=0 if latest.aqi != latest.aqi else latest.aqi,
        gauge={"axis": {"range": [0, 300]}, "bar": {"color": color},
               "steps": [{"range": [0, 50], "color": "#14532d"},
                         {"range": [50, 100], "color": "#713f12"},
                         {"range": [100, 150], "color": "#7c2d12"},
                         {"range": [150, 200], "color": "#7f1d1d"},
                         {"range": [200, 300], "color": "#581c87"}]}))
    st.plotly_chart(style(gauge, 300), width="stretch")

with t:
    st.subheader("Temperature & humidity")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.observed_at, y=df.temperature_c, name="Temperature (°C)",
                             line=dict(color="#f97316", width=3), fill="tozeroy",
                             fillcolor="rgba(249,115,22,0.10)"))
    fig.add_trace(go.Scatter(x=df.observed_at, y=df.humidity_pct, name="Humidity (%)",
                             line=dict(color="#38bdf8", width=2), yaxis="y2"))
    fig.update_layout(yaxis=dict(title="°C", rangemode="normal"),
                      yaxis2=dict(title="%", overlaying="y", side="right", showgrid=False))
    fig.add_vline(x=now, line_dash="dot", line_color="#94a3b8")
    st.plotly_chart(style(fig, 300), width="stretch")

# ---------- Row 2: PM2.5 + precipitation ----------
p, r = st.columns(2)
with p:
    st.subheader("PM2.5 (fine particles)")
    fig = px.area(df, x="observed_at", y="pm25", labels={"observed_at": "", "pm25": "µg/m³"})
    fig.update_traces(line_color="#a78bfa", fillcolor="rgba(167,139,250,0.25)")
    fig.add_hline(y=15, line_dash="dash", line_color="#22c55e",
                  annotation_text="WHO 24h guideline (15)")
    st.plotly_chart(style(fig), width="stretch")
with r:
    st.subheader("Wind & rainfall")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df.observed_at, y=df.precipitation_mm, name="Rain (mm)",
                         marker_color="#38bdf8"))
    fig.add_trace(go.Scatter(x=df.observed_at, y=df.wind_kmh, name="Wind (km/h)",
                             line=dict(color="#facc15"), yaxis="y2"))
    fig.update_layout(yaxis=dict(title="mm"),
                      yaxis2=dict(title="km/h", overlaying="y", side="right", showgrid=False))
    st.plotly_chart(style(fig), width="stretch")

# ---------- Row 3: city comparison ----------
st.subheader("City comparison")
c1, c2 = st.columns(2)
with c1:
    avg = (all_df.groupby("city", as_index=False)["aqi"].mean()
           .sort_values("aqi", ascending=False))
    avg["color"] = avg["aqi"].apply(lambda v: aqi_level(v)[1])
    fig = go.Figure(go.Bar(x=avg.city, y=avg.aqi, marker_color=avg.color,
                           text=avg.aqi.round(0), textposition="outside"))
    fig.update_layout(title="Average AQI (colored by health level)", yaxis_title="AQI")
    st.plotly_chart(style(fig), width="stretch")
with c2:
    if compare:
        cmp_df = all_df[all_df["city"].isin(compare)]
        fig = px.line(cmp_df, x="observed_at", y="aqi", color="city",
                      labels={"observed_at": "", "aqi": "AQI"}, title="AQI over time")
        st.plotly_chart(style(fig), width="stretch")
    else:
        st.info("Pick cities in the sidebar to compare.")

# ---------- Heatmap ----------
st.subheader("Temperature heatmap (city × hour of day)")
heat = all_df.assign(hour=all_df.observed_at.dt.hour).pivot_table(
    index="city", columns="hour", values="temperature_c", aggfunc="mean")
fig = px.imshow(heat, aspect="auto", color_continuous_scale="Turbo",
                labels=dict(x="Hour (UTC)", y="", color="°C"))
st.plotly_chart(style(fig, 300), width="stretch")

with st.expander("View raw data"):
    st.dataframe(df.sort_values("observed_at", ascending=False), width="stretch")