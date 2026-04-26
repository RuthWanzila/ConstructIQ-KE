import streamlit as st
import pandas as pd
import joblib
import sqlite3
import hashlib
from datetime import datetime
import plotly.graph_objects as go
from fpdf import FPDF
import requests   


API_URL = https://construction-risk-api-2.onrender.com

st.set_page_config(
    page_title="ConstructIQ-KE",
    page_icon="🏗️",
    layout="wide"
)

# ---------- MODERN STYLE ----------
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

/* Background */
.stApp {
    background: linear-gradient(rgba(10,12,16,0.85), rgba(10,12,16,0.85)),
    url("https://images.unsplash.com/photo-1504307651254-35680f356dfd") center/cover fixed;
}

/* Main container */
.block-container {
    padding: 2rem 3rem;
}

/* Headings */
h1, h2, h3 {
    color: #ffffff;
}

/* Glass cards */
div[data-testid="stForm"], .stDataFrame, .stMetric {
    background: rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.2rem;
    border: 1px solid rgba(255,255,255,0.15);
    backdrop-filter: blur(10px);
}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #FF6B00, #ff8c42);
    color: white;
    border-radius: 10px;
    font-weight: 700;
    padding: 0.6rem 1.2rem;
    border: none;
    transition: 0.3s;
}

.stButton>button:hover {
    transform: scale(1.03);
    background: linear-gradient(135deg, #e55f00, #ff6b00);
}

/* Metric styling */
[data-testid="stMetricValue"] {
    font-size: 1.6rem;
    font-weight: 700;
    color: #FFB36B;
}

/* Dataframe */
thead tr th {
    background-color: rgba(255,107,0,0.2);
    color: white;
}

</style>
""", unsafe_allow_html=True)

# ---------- HERO ----------
st.markdown("""
# 🏗️ ConstructIQ-KE  
### *AI-Powered Construction Risk Intelligence for Kenya*

---
""")

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY, email TEXT, project_name TEXT, county TEXT, probability REAL, risk TEXT, created_at TEXT)''')
    conn.commit(); conn.close()

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def signup(e,p):
    try:
        c=sqlite3.connect('users.db')
        c.execute("INSERT INTO users VALUES (?,?)",(e,hash_pw(p)))
        c.commit()
        return True
    except:
        return False
    finally:
        c.close()

def login(e,p): 
    c=sqlite3.connect('users.db')
    r=c.execute("SELECT 1 FROM users WHERE email=? AND password=?",(e,hash_pw(p))).fetchone()
    c.close()
    return r

@st.cache_resource
def load_model():
    return joblib.load('abandonment_model.joblib'), joblib.load('model_features.joblib')

model, FEATURES = load_model()

ARCHETYPE = {'Nairobi':'Nairobi','Kiambu':'Nairobi','Mombasa':'Mombasa','Kisumu':'Kisumu','Nakuru':'Nakuru','Uasin Gishu':'Eldoret'}
for c in ['Kwale','Kilifi','Siaya','Kakamega','Machakos','Kajiado','Turkana','Kitui']:
    ARCHETYPE.setdefault(c,'Nairobi')

def predict(d):
    arch = ARCHETYPE.get(d['county'],'Nairobi')
    row = pd.DataFrame([{
        'Project_Type':d['ptype'],'County':arch,'Planned_Cost_KES':d['cost'],'Planned_Duration':d['dur'],
        'Weather_Condition':d['weather'],'Temperature':25,'Humidity':60,'Accident_Count':0,'Labor_Hours':5000,
        'Equipment_Utilization':d['equip'],'Material_Usage':1000,'Safety_Risk_Score':5,'Site_Activity':'Medium',
        'Visible_Defects':d['defects'],'Structural_Concern':'Pass','Photo_Progress_Score':50,'Unusual_Event_Reported':d['unusual']
    }])

    X = pd.get_dummies(row).reindex(columns=FEATURES, fill_value=0)
    prob = float(model.predict_proba(X)[0,1])
    risk = "High" if prob>0.7 else "Medium" if prob>0.4 else "Low"

    reasons=[]
    if d['equip']<50: reasons.append("Low equipment utilization")
    if d['defects']=="Major": reasons.append("Major structural defects")
    if d['unusual']=="Yes": reasons.append("Unusual site event")
    if not reasons: reasons=["Stable progress conditions"]

    return prob,risk,reasons[:3]

def pdf_report(name,county,ptype,prob,risk,reasons):
    pdf=FPDF()
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

# ---------- AUTH ----------
init_db()
if 'user' not in st.session_state:
    st.session_state.user=None

if not st.session_state.user:
    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        st.markdown("## 🏗️ ConstructIQ-KE Login")

        st.caption("Secure access to AI-powered construction risk intelligence")

        t1,t2 = st.tabs(["Login","Sign Up"])

        with t1:
            e=st.text_input("Email")
            p=st.text_input("Password",type="password")
            if st.button("Sign In",use_container_width=True):
                if login(e,p):
                    st.session_state.user=e
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        with t2:
            e2=st.text_input("Email",key="e2")
            p2=st.text_input("Password",type="password",key="p2")
            if st.button("Create Account",use_container_width=True):
                if signup(e2,p2):
                    st.success("Account created successfully")
                else:
                    st.error("Account already exists")

    st.stop()

# ---------- HEADER ----------
colA,colB,colC = st.columns([1,6,1])
with colA:
    st.markdown("### 🏗️")
with colB:
    st.markdown("## ConstructIQ-KE Dashboard")
with colC:
    if st.button("Logout"):
        st.session_state.user=None
        st.rerun()

st.divider()

# ---------- FORM ----------
st.subheader("📊 New Project Assessment")

with st.form("f"):
    c1,c2 = st.columns(2)

    name=c1.text_input("Project Name")
    county=c2.selectbox("County",['Nairobi','Mombasa','Kisumu','Nakuru','Uasin Gishu','Kiambu','Machakos','Kajiado'])
    ptype=c1.selectbox("Project Type",["Building","Bridge","Dam","Road","Tunnel"])
    cost=c2.number_input("Planned Cost (KES)",1_000_000,value=500_000_000,step=1_000_000)
    dur=c1.slider("Duration (days)",90,1200,365)
    weather=c2.selectbox("Weather",["Sunny","Rainy","Cloudy","Stormy"])
    equip=c1.slider("Equipment Utilization %",0,100,70)
    defects=c2.selectbox("Visible Defects",["None","Minor","Major"])
    unusual=c1.selectbox("Unusual Event",["No","Yes"])

    submitted = st.form_submit_button("🚀 Analyze Project",use_container_width=True)

if submitted and name:
    prob,risk,reasons = predict(dict(
        ptype=ptype,county=county,cost=cost,dur=dur,
        weather=weather,equip=equip,defects=defects,unusual=unusual
    ))

    conn=sqlite3.connect('users.db')
    conn.execute(
        "INSERT INTO predictions VALUES (NULL,?,?,?,?,?,?)",
        (st.session_state.user,name,county,prob,risk,datetime.now().isoformat())
    )
    conn.commit(); conn.close()

    colA,colB = st.columns([1,1])

    with colA:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prob*100,
            title={'text':"Risk Level %"},
            gauge={'axis':{'range':[0,100]},'bar':{'color':"#FF6B00"}}
        ))
        fig.update_layout(height=260,margin=dict(t=40,b=0))
        st.plotly_chart(fig,use_container_width=True)

    with colB:
        st.metric("Risk Category",risk)
        st.metric("Probability",f"{prob:.1%}")

        st.markdown("**Key Risk Drivers**")
        for r in reasons:
            st.write("•",r)

    pdf = pdf_report(name,county,ptype,prob,risk,reasons)
    st.download_button("📄 Download Report",pdf,f"{name}_ConstructIQ.pdf","application/pdf",use_container_width=True)

st.divider()

# ---------- HISTORY ----------
st.subheader("📁 Recent Assessments")

conn=sqlite3.connect('users.db')
df=pd.read_sql(
    "SELECT project_name,county,risk,probability,created_at FROM predictions WHERE email=? ORDER BY id DESC LIMIT 10",
    conn,
    params=(st.session_state.user,)
)
conn.close()

if not df.empty:
    df['probability']=(df['probability']*100).round(1).astype(str)+'%'
    df['created_at']=pd.to_datetime(df['created_at']).dt.strftime('%d %b %Y')
    st.dataframe(df,use_container_width=True,hide_index=True)
