import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

st.set_page_config(page_title="AI Industrial Predictive Maintenance",
                   page_icon="🏭",
                   layout="wide")

st_autorefresh(interval=2000, key="refresh")

st.markdown("""
<style>
.main {background-color:#0e1117;}
div[data-testid="stMetric"]{
    background:#1b263b;
    border-radius:10px;
    padding:10px;
    border:1px solid #33415c;
}
.status-ok{
    background:#0f5132;
    color:white;
    padding:12px;
    border-radius:10px;
    font-size:22px;
    font-weight:bold;
    text-align:center;
}
.status-bad{
    background:#842029;
    color:white;
    padding:12px;
    border-radius:10px;
    font-size:22px;
    font-weight:bold;
    text-align:center;
}
</style>
""", unsafe_allow_html=True)

st.title("🏭 AI Industrial Predictive Maintenance Dashboard")
st.caption("Live Machine Monitoring System")

try:
    df = pd.read_csv("dataset/machine_log.csv")
except FileNotFoundError:
    st.error("dataset/machine_log.csv not found.")
    st.stop()

df["Time"] = pd.to_datetime(df["Time"])
df = df.sort_values("Time").tail(30)

latest = df.iloc[-1]

temp = latest["Temperature"]
vib = latest["Vibration"]
rpm = latest["RPM"]
failure = int(latest["Failure"])

health = max(0, 100 - ((max(temp-40,0)*0.5)+(max(vib-5,0)*3)+(max(rpm-1500,0)/80)))
health = round(min(100, health),1)

status = "🟢 HEALTHY" if failure==0 else "🔴 MAINTENANCE REQUIRED"

col1,col2 = st.columns([3,1])
with col1:
    st.subheader("Factory Live Status")
with col2:
    st.write(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

if failure==0:
    st.markdown(f'<div class="status-ok">{status}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-bad">{status}</div>', unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)
c1.metric("🌡 Temperature", f"{temp} °C")
c2.metric("📳 Vibration", vib)
c3.metric("⚙ RPM", rpm)
c4.metric("❤️ Health Score", f"{health}%")

left,right = st.columns(2)

with left:
    fig=px.line(df,x="Time",y="Temperature",markers=True,
                title="Temperature Trend")
    st.plotly_chart(fig,use_container_width=True)

    fig=px.line(df,x="Time",y="RPM",markers=True,
                title="RPM Trend")
    st.plotly_chart(fig,use_container_width=True)

with right:
    fig=px.line(df,x="Time",y="Vibration",markers=True,
                title="Vibration Trend")
    st.plotly_chart(fig,use_container_width=True)

    st.subheader("🤖 AI Recommendation")
    if failure==0:
        st.success("Machine is operating normally.\n\nContinue production.")
    else:
        reasons=[]
        if temp>80:
            reasons.append("High Temperature")
        if vib>10:
            reasons.append("High Vibration")
        if rpm>2800:
            reasons.append("High RPM")
        st.error("Maintenance Required")
        st.write("Reasons:")
        for r in reasons:
            st.write("•",r)

st.subheader("📊 Statistics")
a,b,c,d = st.columns(4)
a.metric("Total Readings", len(df))
b.metric("Max Temp", df["Temperature"].max())
c.metric("Max Vib", df["Vibration"].max())
d.metric("Max RPM", df["RPM"].max())

st.subheader("📋 Latest Sensor History")
st.dataframe(df.tail(20), use_container_width=True)