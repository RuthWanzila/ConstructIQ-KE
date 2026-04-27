import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import plotly.graph_objects as go
from fpdf import FPDF
import requests

# 🔗 Render API
API_URL = "https://construction-risk-api-2.onrender.com/predict"

st.set_page_config(
    page_title="ConstructIQ-KE",
    page_icon="🏗️",
    layout="wide"
)

# ---------- STYLE ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(rgba(10,12,16,0.85), rgba(10,12,16,0.85)),
    url("https://images.unsplash.com/photo-1504307651254-35680f356dfd") center/cover fixed;
}

.block-container {
    padding: 2rem 3rem;
}

h1, h2, h3 {
    color: #ffffff;
}

div[data-testid="stForm"], .stDataFrame, .stMetric {
    background: rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.2rem;
    border: 1px solid rgba(255,255,255,0.15);
    backdrop-filter: blur(10px);
}

.stButton>button {
    background: linear-gradient(135deg, #FF6B00, #ff8c42);
    color: white;
    border-radius: 10px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)

# ---------- HERO ----------
st.markdown("""
# 🏗️ ConstructIQ-KE  
### *AI-Powered Construction Risk Intelligence*
---
""")

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)')
    conn.execute('''CREATE TABLE IF NOT EXISTS predictions 
        (id INTEGER PRIMARY KEY, email TEXT, project_name TEXT, county TEXT,
         probability REAL, risk TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def signup(e,p):
    try:
        conn = sqlite3.connect('users.db')
        conn.execute("INSERT INTO users VALUES (?,?)", (e, hash_pw(p)))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def login(e,p):
    conn = sqlite3.connect('users.db')
    r = conn.execute(
        "SELECT 1 FROM users WHERE email=? AND password=?",
        (e, hash_pw(p))
    ).fetchone()
    conn.close()
    return r

# ---------- API PREDICTION ----------
def predict(d):

    payload = {
        "project_type": d['ptype'],
        "county": d['county'],
        "planned_cost_kes": d['cost'],
        "planned_duration_days": d['dur'],
        "weather_condition": d['weather'],

        # defaults required by backend
        "temperature": 25,
        "humidity": 60,
        "accident_count": 0,
        "labor_hours": 5000,
        "equipment_utilization": d['equip'],
        "material_usage": 1000,
        "safety_risk_score": 5,
        "site_activity": "Medium",
        "visible_defects": d['defects'],
        "structural_concern": "Pass",
        "photo_progress_score": 50,
        "unusual_event_reported": d['unusual']
    }

    try:
        r = requests.post(API_URL, json=payload, timeout=30)

        if r.status_code == 200:
            res = r.json()
            return res["probability"], res["risk_level"], res["reasons"]

        return 0, "Error", [r.text]

    except Exception as e:
        return 0, "Error", [str(e)]

# ---------- PDF ----------
def pdf_report(name,county,prob,risk,reasons):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial",'B',16)
    pdf.cell(0,10,"ConstructIQ-KE Risk Report",ln=True,align='C')
    pdf.ln(5)

    pdf.set_font("Arial",'',12)
    pdf.cell(0,8,f"Project: {name}",ln=True)
    pdf.cell(0,8,f"County: {county}",ln=True)
    pdf.cell(0,8,f"Risk: {risk} ({prob:.1%})",ln=True)
    pdf.ln(5)

    for r in reasons:
        pdf.multi_cell(0,7,f"- {r}")

    return pdf.output(dest='S').encode('latin1')

# ---------- INIT ----------
init_db()

if 'user' not in st.session_state:
    st.session_state.user = None

# ---------- LOGIN ----------
if not st.session_state.user:

    col1,col2,col3 = st.columns([1,2,1])

    with col2:
        st.markdown("## 🏗️ ConstructIQ-KE Login")

        t1,t2 = st.tabs(["Login","Sign Up"])

        with t1:
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")

            if st.button("Sign In"):
                if login(e,p):
                    st.session_state.user = e
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        with t2:
            e2 = st.text_input("Email", key="e2")
            p2 = st.text_input("Password", type="password", key="p2")

            if st.button("Create Account"):
                if signup(e2,p2):
                    st.success("Account created")
                else:
                    st.error("User exists")

    st.stop()

# ---------- HEADER ----------
colA,colB,colC = st.columns([1,6,1])

with colB:
    st.markdown("## ConstructIQ-KE Dashboard")

with colC:
    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

st.divider()

# ---------- FORM ----------
st.subheader("📊 New Project Assessment")

with st.form("f"):

    c1,c2 = st.columns(2)

    name = c1.text_input("Project Name")
    county = c2.selectbox("County",['Nairobi','Mombasa','Kisumu','Nakuru','Kiambu','Machakos','Kajiado'])

    ptype = c1.selectbox("Project Type",["Building","Bridge","Dam","Road","Tunnel"])
    cost = c2.number_input("Planned Cost (KES)",1_000_000,value=500_000_000,step=1_000_000)
    dur = c1.slider("Duration (days)",90,1200,365)
    weather = c2.selectbox("Weather",["Sunny","Rainy","Cloudy","Stormy"])
    equip = c1.slider("Equipment Utilization %",0,100,70)
    defects = c2.selectbox("Visible Defects",["None","Minor","Major"])
    unusual = c1.selectbox("Unusual Event",["No","Yes"])

    submitted = st.form_submit_button("🚀 Analyze Project")

# ---------- RESULT ----------
if submitted and name:

    prob, risk, reasons = predict({
        "ptype": ptype,
        "county": county,
        "cost": cost,
        "dur": dur,
        "weather": weather,
        "equip": equip,
        "defects": defects,
        "unusual": unusual
    })

    conn = sqlite3.connect('users.db')
    conn.execute(
        "INSERT INTO predictions VALUES (NULL,?,?,?,?,?,?)",
        (st.session_state.user, name, county, prob, risk, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    colA,colB = st.columns(2)

    with colA:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prob*100,
            title={'text':"Risk %"},
            gauge={'axis':{'range':[0,100]},'bar':{'color':"#FF6B00"}}
        ))
        st.plotly_chart(fig, use_container_width=True)

    with colB:
        st.metric("Risk Level", risk)
        st.metric("Probability", f"{prob:.1%}")

        st.write("**Drivers**")
        for r in reasons:
            st.write("•", r)

    pdf = pdf_report(name,county,prob,risk,reasons)
    st.download_button("📄 Download Report", pdf, f"{name}_ConstructIQ.pdf", "application/pdf")

# ---------- HISTORY ----------
st.divider()
st.subheader("📁 Recent Assessments")

conn = sqlite3.connect('users.db')
df = pd.read_sql(
    "SELECT project_name,county,risk,probability,created_at FROM predictions WHERE email=? ORDER BY id DESC LIMIT 10",
    conn,
    params=(st.session_state.user,)
)
conn.close()

if not df.empty:
    df['probability'] = (df['probability']*100).round(1).astype(str)+'%'
    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d %b %Y')
    st.dataframe(df, use_container_width=True, hide_index=True)
