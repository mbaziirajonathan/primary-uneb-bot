import streamlit as st
import os, io, json, random, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib_venn import venn2, venn3
import math
import time
import hashlib
from datetime import datetime
from groq import Groq, RateLimitError, APIError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ===================== CONFIG =====================
CONTACT = "256751040731"
DEBUG_MODE = True
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7.")

# ===================== MASTER PROMPT =====================
MASTER_PROMPT = """
You are an OFFICIAL UNEB PLE EXAMINER for Mathematics, Integrated Science, Social Studies (SST), and English Language.
Set HARD exams for P6-P7 with UNEB accuracy.

RULE 1: SECTION A = 20Q, 1 line, 8-12 words. SECTION B = 40Q, 3-4 lines scenario, a,b,c.
RULE 2: DIFFICULTY: P4=0Q, P5=6Q, P6=16Q, P7=18Q. Total 60Q.
RULE 3: IF SST THEN SECTION B: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE
RULE 4: MARKING: Math=M/A/B. Science=Keywords. SST=Facts. English=Layout/Content.
RULE 5: DIAGRAMS: Use [DIAGRAM: Topic="Triangle", Measurements="base=8cm"] tag BEFORE question.
Always output questions first, then "MARKING GUIDE:" section.
"""

# ===================== 2. DIAGRAM GENERATOR =====================
def draw_math_diagram(d_type, measurements, question_text):
    try:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        plt.axis('off'); ax.set_title(f"{question_text}", fontsize=10, fontweight='bold', pad=10)
        data = measurements.lower() if measurements else ""
        def safe_float(s, default):
            try: return float(re.findall(r"[\d.]+", s)[0])
            except: return default
        def get_unit(s):
            if "cm" in s: return "cm"
            if "m" in s: return "m"
            return ""

        if d_type and "venn2" in d_type.lower():
            A = safe_float(data.split("a=")[1], 10) if "a=" in data else 10
            B = safe_float(data.split("b=")[1], 15) if "b=" in data else 15
            AB = safe_float(data.split("ab=")[1], 5) if "ab=" in data else 5
            v = venn2(subsets = (A-AB, B-AB, AB), set_labels = ('Set A', 'Set B'))
            v.get_patch_by_id('10').set_color('skyblue'); v.get_patch_by_id('01').set_color('lightgreen')
        elif d_type and "triangle" in d_type.lower():
            base = safe_float(data.split("base=")[1], 8.0) if "base=" in data else 8.0
            unit = get_unit(data); height = safe_float(data.split("height=")[1], base*0.7) if "height=" in data else base*0.7
            triangle = patches.Polygon([(0, 0), (base, 0), (base/2, height)], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(triangle)
            ax.text(base/2, -0.5, f"Base = {base}{unit}", ha='center'); ax.text(-1, height/2, f"Height = {height}{unit}", va='center', rotation=90)
            ax.set_xlim(-2, base+2); ax.set_ylim(-2, height+2)
        elif d_type and "rectangle" in d_type.lower():
            w = safe_float(data.split("length=")[1], 6.0) if "length=" in data else 6.0
            h = safe_float(data.split("width=")[1], 4.0) if "width=" in data else 4.0
            unit = get_unit(data)
            poly = patches.Polygon([(0,0),(w,0),(w,h),(0,h)], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(poly)
            ax.text(w/2, -0.5, f"L = {w}{unit}", ha='center'); ax.set_xlim(-2, w+2); ax.set_ylim(-2, h+2)
        else:
            ax.text(0.5,0.5,"Diagram: " + d_type, ha='center', transform=ax.transAxes)

        plt.tight_layout(); buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight'); buf.seek(0); plt.close(fig); return buf
    except Exception as e:
        if DEBUG_MODE: st.error(f"Diagram Error: {e}")
        return None

def parse_diagram_tag(text):
    if "[DIAGRAM:" not in text: return None
    try:
        tag = text.split("[DIAGRAM:")[1].split("]")[0]; parts = {}
        for item in tag.split(","):
            if "=" in item: k,v = item.split("=",1); parts[k.strip()] = v.strip().strip('"')
        return parts if parts.get("Topic") else None
    except: return None

# ===================== 3. FULL DB RESTORED =====================
PRIMARY_DB = {
  "PRIMARY_4": {"Mathematics": [{"topic": "Set Concepts"}, {"topic": "Whole Numbers"}, {"topic": "Fractions"}, {"topic": "Measures"}], "English Language": [{"topic": "Comprehension"}, {"topic": "Describing People"}], "Integrated Science": [{"topic": "Plant Life"}, {"topic": "Weather"}, {"topic": "Human Body"}], "Social Studies (SST)": [{"topic": "Our Sub-County"}, {"topic": "Economic Activities"}], "Christian Religious Education (CRE)": [{"topic": "God's Creation"}], "Islamic Religious Education (IRE)": [{"topic": "Pillars of Islam"}]},
  "PRIMARY_5": {"Mathematics": [{"topic": "Sets Venn"}, {"topic": "LCM GCF"}, {"topic": "Decimals"}], "English Language": [{"topic": "Grammar Tenses"}, {"topic": "Comprehension"}], "Integrated Science": [{"topic": "Soil"}, {"topic": "Human Body Systems"}], "Social Studies (SST)": [{"topic": "Uganda Geography"}, {"topic": "People of Uganda"}], "Christian Religious Education (CRE)": [{"topic": "Birth of Jesus"}], "Islamic Religious Education (IRE)": [{"topic": "Pillars of Iman"}]},
  "PRIMARY_6": {"Mathematics": [{"topic": "Ratios"}, {"topic": "Speed"}, {"topic": "Volume"}], "English Language": [{"topic": "Passive Voice"}, {"topic": "Media"}], "Integrated Science": [{"topic": "Energy"}, {"topic": "Diseases"}], "Social Studies (SST)": [{"topic": "East Africa"}, {"topic": "EAC"}], "Christian Religious Education (CRE)": [{"topic": "Holy Spirit"}], "Islamic Religious Education (IRE)": [{"topic": "Hajj"}]},
  "PRIMARY_7": {"Mathematics": [{"topic": "Sets 3 Categories"}, {"topic": "Business Math"}, {"topic": "Graphs"}], "English Language": [{"topic": "Letter Writing"}, {"topic": "Direct Indirect Speech"}], "Integrated Science": [{"topic": "Machines"}, {"topic": "Environment"}], "Social Studies (SST)": [{"topic": "Africa"}, {"topic": "UN AU"}], "Christian Religious Education (CRE)": [{"topic": "Marriage"}], "Islamic Religious Education (IRE)": [{"topic": "Shariah"}]}
}
PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}
def get_all_topics(grade): return [t["topic"] for sub in PRIMARY_DB[f"PRIMARY_{grade[1:]}"].values() for t in sub]

# ===================== 4. SMART GROQ CALL WITH FULL DEBUG =====================
if "cache" not in st.session_state: st.session_state.cache = {}
if "last_response" not in st.session_state: st.session_state.last_response = ""

def smart_groq_call(client, system_prompt, user_prompt, max_tokens=2500):
    cache_key = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
    if cache_key in st.session_state.cache:
        if DEBUG_MODE: st.success("✅ Loaded from cache")
        return st.session_state.cache[cache_key]

    models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
    if len(user_prompt) > 3500: user_prompt = user_prompt[:3500] + "\n\n[Trimmed for length]"

    for model in models_to_try:
        try:
            if DEBUG_MODE: st.info(f"🔄 Calling Groq model: {model}")
            res = client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
                temperature=0.4,
                max_tokens=max_tokens,
                timeout=60
            )
            if res and res.choices and res.choices[0].message.content:
                st.session_state.cache[cache_key] = res
                if DEBUG_MODE: st.success(f"✅ Response received from {model}")
                return res
            else:
                if DEBUG_MODE: st.warning(f"⚠️ Empty response from {model}")
        except RateLimitError:
            if DEBUG_MODE: st.warning("⚠️ Rate limited. Trying next model...")
            time.sleep(3)
            continue
        except APIError as e:
            if DEBUG_MODE: st.error(f"❌ API Error with {model}: {e}")
            continue
        except Exception as e:
            if DEBUG_MODE: st.error(f"❌ General Error with {model}: {e}")
            continue

    st.error("❌ ALL MODELS FAILED. Check 1: GROQ_API_KEY in Secrets. 2: Billing at console.groq.com")
    return None

def get_client():
    try:
        key = st.secrets["GROQ_API_KEY"]
        if DEBUG_MODE: st.success("✅ API Key Found in Secrets")
        return Groq(api_key=key)
    except KeyError:
        st.error("❌ CRITICAL: GROQ_API_KEY missing. Go to App Settings > Secrets > Add GROQ_API_KEY")
        return None

def generate_pdf(content, title):
    try:
        buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
        c.setFont("Helvetica-Bold", 14); c.drawString(40, height-50, title)
        y = height - 80; c.setFont("Helvetica", 9)
        for line in content.split('\n')[:400]:
            if y < 50: c.showPage(); y = height - 50
            c.drawString(40, y, line[:100]); y -= 14
        c.save(); buffer.seek(0); return buffer
    except Exception as e:
        st.error(f"PDF Error: {e}")
        return None

# ===================== 5. HELPER: RENDER WITH FALLBACK =====================
def render_response(text):
    st.session_state.last_response = text
    if not text or text.strip() == "":
        st.error("❌ Model returned empty. This is usually API key or rate limit issue.")
        return

    # 1. ALWAYS SHOW TEXT FIRST
    st.markdown("### 📄 Generated Response")
    st.write(text)

    # 2. THEN TRY DIAGRAMS
    chunks = re.split(r'(### \*\*Question \d+:)', text)
    for i in range(0, len(chunks), 2):
        diagram_part = chunks[i]
        diagram_info = parse_diagram_tag(diagram_part)
        if diagram_info:
            img_buf = draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question",""))
            if img_buf: st.image(img_buf, use_container_width=True)

# ===================== 6. PASSWORD =====================
def check_password():
    APP_PW = st.secrets.get("PRIMARY_APP_PASSWORD", "PRIMARY2026")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "ADMIN256")
    if "password_correct" not in st.session_state:
        st.title("🔒 TEACHERK PRIMARY 2026 NCDC")
        pw = st.text_input("Password", type="password", key="pw_input")
        if st.button("Login"):
            if pw == APP_PW: st.session_state["user_type"] = "Pupil"; st.session_state["password_correct"] = True; st.rerun()
            elif pw == ADMIN_PW: st.session_state["user_type"] = "Teacher"; st.session_state["password_correct"] = True; st.rerun()
            else: st.error("Wrong password")
        st.stop()
check_password()

# ===================== 7. MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026 NCDC - DEBUG v2.8")
if DEBUG_MODE: st.sidebar.warning("DEBUG MODE ON - You will see all errors")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"])
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])

tabs = st.tabs(["🔍 General Search", "📖 Theory", "📝 HARD MOCK", "➗ Math Work", "👩‍🏫 Teacher Tools"])

def ask_ai(prompt, dl_name):
    client = get_client()
    if not client: return

    with st.spinner("UNEB Examiner is Generating... Please wait 10-20s"):
        res = smart_groq_call(client, MASTER_PROMPT, prompt)

    if res and res.choices:
        answer = res.choices[0].message.content
        if DEBUG_MODE:
            with st.expander("Show Raw AI Response"):
                st.code(answer)
        render_response(answer)
        pdf = generate_pdf(answer, dl_name)
        if pdf: st.download_button("📥 Download PDF", pdf, f"{dl_name}.pdf", key=f"dl_{dl_name}")
    else:
        st.error("No response generated. Check debug messages above.")

    st.markdown("---")
    st.subheader("Upload & Download")
    st.file_uploader("Upload student work txt/pdf", type=["txt","pdf"], key=f"upload_{dl_name}")

with tabs[0]:
    st.header("🔍 General Search")
    q = st.text_input("Ask Anything", key="ask_general", placeholder="e.g. What is photosynthesis")
    if st.button("Ask", key="btn_general") and q:
        ask_ai(f"Answer this for {grade} {subject} Topic: {topic} in simple Ugandan English. Q: {q}", "answer_general")

with tabs[1]:
    st.header(f"📖 Theory: {grade} {subject}")
    if st.button("Generate Full Theory Notes", key="theory_btn"):
        ask_ai(f"Generate detailed NCDC 2026 theory notes for {grade} {subject} Topic: {topic}. Include Definition, 3 Examples, Ugandan Example.", f"Theory_{topic}")

with tabs[2]:
    st.header("📝 HARD COMBINED MOCK PLE")
    st.info("Section A: 20Q 1-line. Section B: 40Q scenario a,b,c. SST=20+10+10")
    if st.button("Generate HARD COMBINED MOCK PLE", key="mock_btn", type="primary"):
        sst_rule = "FOR SST: SECTION A=20 SST. SECTION B=20 SST Q21-Q40, 10 CRE Q41-Q50, 10 IRE Q51-Q60." if subject == "Social Studies (SST)" else ""
        prompt = f"{MASTER_PROMPT}\nGenerate HARD MOCK for {grade} {subject}. ROTATE TOPICS: {get_all_topics(grade)}. {sst_rule}"
        ask_ai(prompt, f"HARD_MOCK_{subject}")

with tabs[4]:
    st.header("👩‍🏫 Teacher Tools")
    questions = st.text_area("Paste Question for UNEB Marking Guide", height=150)
    if st.button("Generate UNEB Marking Guide", key="marking_btn"):
        prompt = f"Act as UNEB Examiner for {subject}. Q: {questions}. Output: Subject, Answer Key, M/A/B Marks, Common Mistakes."
        ask_ai(prompt, "Marking_Guide")

st.sidebar.caption("DEBUG: Read messages above | Contact: " + CONTACT)
