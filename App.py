import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import plotly.graph_objects as go
from fpdf import FPDF
import requests

API_URL = "https://construction-risk-api-2.onrender.com/predict"

st.set_page_config(page_title="ConstructIQ-KE", page_icon="🏗️", layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

html, body {font-family: 'Inter', sans-serif;}

.stApp {
    background: linear-gradient(rgba(10,12,16,0.9), rgba(10,12,16,0.9)),
    url("https://images.unsplash.com/photo-1504307651254-35680f356dfd") center/cover fixed;
}

.card {
    background: rgba(255,255,255,0.07);
    padding: 1.2rem;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.15);
    margin-bottom: 1rem;
}

.stButton>button {
    background: linear-gradient(135deg,#FF6B00,#ff8c42);
    color:white;
    border-radius:10px;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("# 🏗️ ConstructIQ-KE")
st.caption("AI-Powered Construction Risk Intelligence for Kenya")
st.divider()

# ---------- HELPERS ----------
def format_currency(x):
    return f"KES {int(x):,}"

def material_to_value(level):
    return {"Efficient":1000,"Slight Overuse":1200,"Heavy Overuse":1500}[level]

# ---------- API ----------
def predict(d):
    payload = {
        "project_type": d['ptype'],
        "county": d['county'],
        "planned_cost_kes": d['cost'],
        "planned_duration_days": d['dur'],
        "weather_condition": d['weather'],
        "temperature": 25,
        "humidity": 60,
        "accident_count": 0,
        "labor_hours": 5000,
        "equipment_utilization": d['equip'],
        "material_usage": material_to_value(d['material']),
        "safety_risk_score": 5,
        "site_activity": "Medium",
        "visible_defects": d['defects'],
        "structural_concern": d['structure'],
        "photo_progress_score": 50,
        "unusual_event_reported": d['unusual']
    }

    try:
        r = requests.post(API_URL, json=payload, timeout=30)
        res = r.json()
        return res["probability"], res["risk_level"], res["reasons"]
    except Exception as e:
        return 0,"Error",[str(e)]

# ---------- PDF ----------
def pdf_report(name,county,prob,risk,reasons):

    recommendations = []
    if "equipment" in str(reasons).lower():
        recommendations.append("Improve equipment allocation and scheduling efficiency.")
    if "defects" in str(reasons).lower():
        recommendations.append("Conduct structural inspection and corrective works immediately.")
    if "unusual" in str(reasons).lower():
        recommendations.append("Investigate reported site incidents and apply mitigation controls.")

    actions = [
        "Perform detailed site audit",
        "Reassess project schedule and resource allocation",
        "Improve on-site supervision and monitoring",
        "Strengthen material usage tracking"
    ]

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,"ConstructIQ-KE Risk Report",ln=True,align="C")

    pdf.ln(5)
    pdf.set_font("Arial","",12)

    pdf.cell(0,8,f"Project: {name}",ln=True)
    pdf.cell(0,8,f"County: {county}",ln=True)
    pdf.cell(0,8,f"Risk Level: {risk}",ln=True)
    pdf.cell(0,8,f"Probability: {prob:.1%}",ln=True)

    pdf.ln(5)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"Summary",ln=True)

    pdf.set_font("Arial","",11)
    pdf.multi_cell(0,7,
        f"This project shows a {risk.lower()} risk of abandonment. "
        "The risk level is influenced by operational efficiency, site conditions, and structural factors."
    )

    pdf.ln(3)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"Key Risk Drivers",ln=True)

    pdf.set_font("Arial","",11)
    for r in reasons:
        pdf.multi_cell(0,6,f"- {r}")

    pdf.ln(3)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"Recommendations",ln=True)

    pdf.set_font("Arial","",11)
    for r in recommendations:
        pdf.multi_cell(0,6,f"- {r}")

    pdf.ln(3)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"Suggested Actions",ln=True)

    pdf.set_font("Arial","",11)
    for a in actions:
        pdf.multi_cell(0,6,f"- {a}")

    return pdf.output(dest='S').encode('latin1')

# ---------- FORM ----------
st.subheader("📊 Project Assessment")

with st.form("f"):

    st.markdown("### 🏗️ Project Overview")
    c1,c2 = st.columns(2)

    name = c1.text_input("Project Name")
    county = c2.selectbox("County",['Nairobi','Mombasa','Kisumu','Nakuru','Kiambu','Machakos','Kajiado'])
    ptype = c1.selectbox("Project Type",["Building","Bridge","Road"])

    cost = c2.number_input("Planned Cost (KES)",1_000_000,500_000_000)
    st.caption(f"Formatted: {format_currency(cost)}")

    dur = c1.slider("Planned Duration (Days)",90,1200,365)

    st.markdown("### ⚙️ Site Intelligence")

    equip = c1.slider("Equipment Utilization (%)",0,100,70)
    defects = c2.selectbox("Visible Defects",["None","Minor","Major"])
    structure = c1.selectbox("Structural Concern",["Pass","Warning","Critical"])
    unusual = c2.selectbox("Unusual Event",["No","Yes"])
    material = c1.selectbox("Material Efficiency",["Efficient","Slight Overuse","Heavy Overuse"])
    weather = c2.selectbox("Weather",["Sunny","Rainy","Cloudy","Stormy"])

    submitted = st.form_submit_button("🚀 Analyze Project Risk")

# ---------- RESULTS ----------
if submitted and name:

    prob,risk,reasons = predict({
        "ptype":ptype,"county":county,"cost":cost,"dur":dur,
        "weather":weather,"equip":equip,
        "defects":defects,"structure":structure,
        "unusual":unusual,"material":material
    })

    col1,col2 = st.columns(2)

    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prob*100,
            title={'text':"Risk Level %"},
            gauge={'axis':{'range':[0,100]},'bar':{'color':"#FF6B00"}}
        ))
        st.plotly_chart(fig,use_container_width=True)

    with col2:
        st.metric("Risk Level", risk)
        st.metric("Probability", f"{prob:.1%}")

        st.markdown("**Key Drivers**")
        for r in reasons:
            st.write("•", r)

    pdf = pdf_report(name,county,prob,risk,reasons)
    st.download_button("📄 Download Full Report",pdf,f"{name}_ConstructIQ_Report.pdf")
