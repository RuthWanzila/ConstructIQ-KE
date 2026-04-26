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
.stButton>button {
    background: linear-gradient(135deg,#FF6B00,#ff8c42);
    color:white;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# ---------- AUTH ----------
def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)")
    conn.execute("""CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY, email TEXT, project_name TEXT,
        county TEXT, probability REAL, risk TEXT, created_at TEXT)""")
    conn.commit(); conn.close()

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def signup(e,p):
    try:
        conn = sqlite3.connect('users.db')
        conn.execute("INSERT INTO users VALUES (?,?)",(e,hash_pw(p)))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def login(e,p):
    conn = sqlite3.connect('users.db')
    r = conn.execute("SELECT 1 FROM users WHERE email=? AND password=?",(e,hash_pw(p))).fetchone()
    conn.close(); return r

init_db()
if 'user' not in st.session_state:
    st.session_state.user = None

# ---------- LOGIN UI ----------
if not st.session_state.user:

    st.markdown("## 🔐 ConstructIQ-KE Access")
    st.caption("Login to access construction risk intelligence")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")

        if st.button("Sign In", use_container_width=True):
            if login(e,p):
                st.session_state.user = e
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        e2 = st.text_input("Email", key="e2")
        p2 = st.text_input("Password", type="password", key="p2")

        if st.button("Create Account", use_container_width=True):
            if signup(e2,p2):
                st.success("Account created")
            else:
                st.error("Account exists")

    st.stop()

# ---------- HEADER ----------
col1,col2 = st.columns([8,1])
with col1:
    st.markdown("# 🏗️ ConstructIQ-KE")
    st.caption("AI-Powered Construction Risk Intelligence for Kenya")
with col2:
    if st.button("Logout"):
        st.session_state.user=None
        st.rerun()

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

        if r.status_code == 200:
            res = r.json()
            return res["probability"], res["risk_level"], res["reasons"]

        return 0,"Error",[r.text]

    except Exception as e:
        return 0,"Error",[str(e)]

# ---------- PDF ----------
def pdf_report(name,county,prob,risk,reasons):

    recommendations = []
    if "equipment" in str(reasons).lower():
        recommendations.append("Improve equipment utilization and reduce idle time.")
    if "defects" in str(reasons).lower():
        recommendations.append("Conduct structural inspection and corrective works.")
    if "unusual" in str(reasons).lower():
        recommendations.append("Investigate site incidents and apply mitigation.")

    actions = [
        "Perform site audit",
        "Reassess resource allocation",
        "Improve supervision",
        "Track material usage closely"
    ]

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,"ConstructIQ-KE Risk Report",ln=True,align="C")

    pdf.set_font("Arial","",12)
    pdf.cell(0,8,f"Project: {name}",ln=True)
    pdf.cell(0,8,f"County: {county}",ln=True)
    pdf.cell(0,8,f"Risk: {risk} ({prob:.1%})",ln=True)

    pdf.ln(5)
    pdf.multi_cell(0,7,"This project shows a {} risk level based on current site conditions and operational efficiency.".format(risk.lower()))

    pdf.ln(3)
    pdf.cell(0,8,"Key Drivers:",ln=True)
    for r in reasons:
        pdf.multi_cell(0,6,f"- {r}")

    pdf.ln(3)
    pdf.cell(0,8,"Recommendations:",ln=True)
    for r in recommendations:
        pdf.multi_cell(0,6,f"- {r}")

    pdf.ln(3)
    pdf.cell(0,8,"Suggested Actions:",ln=True)
    for a in actions:
        pdf.multi_cell(0,6,f"- {a}")

    return pdf.output(dest='S').encode('latin1')

# ---------- FORM ----------
st.subheader("📊 Project Assessment")

with st.form("f"):
    c1,c2 = st.columns(2)

    name = c1.text_input("Project Name")
    county = c2.selectbox("County",['Nairobi','Mombasa','Kisumu','Nakuru','Kiambu','Machakos','Kajiado'])
    ptype = c1.selectbox("Project Type",["Building","Bridge","Road"])

    cost = c2.number_input("Planned Cost (KES)",1_000_000,500_000_000)
    st.caption(f"{format_currency(cost)}")

    dur = c1.slider("Planned Duration (Days)",90,1200,365)

    st.markdown("### ⚙️ Site Conditions")

    equip = c1.slider("Equipment Utilization (%)",0,100,70)
    defects = c2.selectbox("Visible Defects",["None","Minor","Major"])
    structure = c1.selectbox("Structural Concern",["Pass","Warning","Critical"])
    unusual = c2.selectbox("Unusual Event",["No","Yes"])
    material = c1.selectbox("Material Efficiency",["Efficient","Slight Overuse","Heavy Overuse"])
    weather = c2.selectbox("Weather",["Sunny","Rainy","Cloudy","Stormy"])

    submitted = st.form_submit_button("🚀 Analyze")

# ---------- RESULTS ----------
if submitted and name:

    prob,risk,reasons = predict({
        "ptype":ptype,"county":county,"cost":cost,"dur":dur,
        "weather":weather,"equip":equip,
        "defects":defects,"structure":structure,
        "unusual":unusual,"material":material
    })

    conn = sqlite3.connect('users.db')
    conn.execute("INSERT INTO predictions VALUES (NULL,?,?,?,?,?,?)",
        (st.session_state.user,name,county,prob,risk,datetime.now().isoformat()))
    conn.commit(); conn.close()

    col1,col2 = st.columns(2)

    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prob*100,
            title={'text':"Risk %"},
            gauge={'axis':{'range':[0,100]},'bar':{'color':"#FF6B00"}}
        ))
        st.plotly_chart(fig,use_container_width=True)

    with col2:
        st.metric("Risk Level", risk)
        st.metric("Probability", f"{prob:.1%}")

        for r in reasons:
            st.write("•", r)

    pdf = pdf_report(name,county,prob,risk,reasons)
    st.download_button("📄 Download Report",pdf,f"{name}_report.pdf")
