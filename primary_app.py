import streamlit as st
import os, io, json, random, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from datetime import datetime
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import streamlit.components.v1 as components

# ===================== CONFIG =====================
CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7. Confirm with Class Teacher.")

MASTER_PROMPT = """
You are TEACHERK, a Senior NCDC 2026 Uganda PLE Examiner and Master Teacher for PRIMARY P4-P7.
You think like Meta AI: flexible, deep reasoning, but you ONLY teach NCDC 2026 Uganda Primary Curriculum.

ANTI-HALLUCINATION & ACCURACY RULE - CRITICAL:
1. NEVER invent measurements. Only use measurements given in the question.
2. If question says "Base=8cm", diagram MUST show "Base=8cm".
3. MATH UNITS RULE: Every final math answer MUST end with correct unit and "Therefore the... was [number][unit]"
4. ENGLISH PUNCTUATION RULE: Every sentence must end with.? or! Capital letters must be correct.
5. MARKING RULE: PUPILS LOSE MARKS FOR JUMPING STEPS AND MISSING UNITS.

MOCK PLE PAPER STRUCTURE:
SECTION A: 20 STRAIGHT QUESTIONS. Short, direct, test recall and basic skills. 1-2 marks each.
SECTION B: 30 SCENARIO-BASED QUESTIONS. Each must have a Ugandan context scenario + a clear TASK to do. 2-4 marks each. Show all working.

FOR MATH:
SCENARIO FORMAT:
### **Question X: [Ugandan Title]**
[3-4 sentence scenario with real numbers. e.g. Mama bought 3kg of beans at ugsh4,000 per kg]
**TASK:** [What the learner must DO]
**SOLUTION METHOD 1: FORMULA METHOD**
Step 1: Given:...
Step 2: Formula:...
Step 3: Substitute:...
Step 4: =...
Step 5: Answer: 12kg. Therefore the total cost was ugsh48,000
**SOLUTION METHOD 2: LOGICAL METHOD**
Step 1-4:...
Step 5: Answer: 12kg. Therefore the total cost was ugsh48,000

FOR ENGLISH:
All answers must be in full, punctuated sentences. Start with capital letter. End with.? or!
Example: "The girl is happy because she passed her exams."

DIAGRAM RULE: FOR ALL GEOMETRY. LIST CONSTRUCTION STEPS. THEN ADD TAG:
[DIAGRAM: Topic=Triangle, Measurements="Base=8cm, Angle=50deg", Question="Construct triangle ABC"]
"""

# ===================== 2. DIAGRAM GENERATOR - WELL DRAWN & LABELED =====================
def draw_math_diagram(d_type, measurements, question_text):
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_aspect('equal'); plt.axis('off'); ax.set_title(f"{d_type}\n{question_text}", fontsize=13, fontweight='bold', pad=20)
    data = measurements.lower() if measurements else ""
    def safe_float(s, default):
        try: return float(re.findall(r"[\d.]+", s)[0])
        except: return default

    if d_type and "triangle" in d_type.lower():
        base = safe_float(data.split("base=")[1], 8.0) if "base=" in data else 8.0
        angle_deg = safe_float(data.split("angle=")[1], 50.0) if "angle=" in data else 50.0
        angle_rad = math.radians(angle_deg); apex_x = base / 2; apex_y = (base / 2) * math.tan(angle_rad) if angle_deg < 90 else base
        side_len = math.sqrt(apex_x**2 + apex_y**2); A, B, C = (0, 0), (base, 0), (apex_x, apex_y)
        triangle = patches.Polygon([A, B, C], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(triangle)
        ax.plot([A[0],B[0]],[A[1],B[1]],'ko', markersize=6); ax.plot([B[0],C[0]],[B[1],C[1]],'ko', markersize=6); ax.plot([C[0],A[0]],[C[1],A[1]],'ko', markersize=6)
        ax.text(A[0]-0.5, A[1]-0.5, "A", fontsize=12, fontweight='bold'); ax.text(B[0]+0.2, B[1]-0.5, "B", fontsize=12, fontweight='bold'); ax.text(C[0], C[1]+0.5, "C", fontsize=12, fontweight='bold')
        ax.text(base/2, -0.7, f"{base} cm", ha='center', fontsize=11); ax.text(apex_x/2 - 0.5, apex_y/2, f"{side_len:.1f} cm", ha='right', fontsize=11); ax.text((apex_x+base)/2 + 0.5, apex_y/2, f"{side_len:.1f} cm", ha='left', fontsize=11)
        arc = patches.Arc(A, 2, 2, theta1=0, theta2=angle_deg, color='red', linewidth=2); ax.add_patch(arc); ax.text(1.2, 0.4, f"{angle_deg}°", color='red', fontsize=12)
        ax.set_xlim(-2, base+2); ax.set_ylim(-2, apex_y+2)

    elif d_type and "square" in d_type.lower():
        s = safe_float(data.split("side=")[1], 5.0) if "side=" in data else 5.0
        A, B, C, D = (0, 0), (s, 0), (s, s), (0, s)
        poly = patches.Polygon([A, B, C, D], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(poly)
        for pt, label in zip([A,B,C,D], ['A','B','C','D']): ax.plot(pt[0],pt[1],'ko', markersize=6); ax.text(pt[0]-0.3, pt[1]-0.3, label, fontsize=12, fontweight='bold')
        ax.text(s/2, -0.7, f"{s} cm", ha='center'); ax.text(-0.9, s/2, f"{s} cm", va='center', rotation=90)
        ax.set_xlim(-2, s+2); ax.set_ylim(-2, s+2)

    elif d_type and "rectangle" in d_type.lower():
        w = safe_float(data.split("length=")[1], 6.0) if "length=" in data else 6.0
        h = safe_float(data.split("width=")[1], 4.0) if "width=" in data else 4.0
        A, B, C, D = (0, 0), (w, 0), (w, h), (0, h)
        poly = patches.Polygon([A, B, C, D], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(poly)
        for pt, label in zip([A,B,C,D], ['A','B','C','D']): ax.plot(pt[0],pt[1],'ko', markersize=6); ax.text(pt[0]-0.3, pt[1]-0.3, label, fontsize=12, fontweight='bold')
        ax.text(w/2, -0.7, f"{w} cm", ha='center'); ax.text(-0.9, h/2, f"{h} cm", va='center', rotation=90)
        ax.set_xlim(-2, w+2); ax.set_ylim(-2, h+2)

    elif d_type and "circle" in d_type.lower():
        r = safe_float(data.split("radius=")[1], 3.0) if "radius=" in data else 3.0
        circle = patches.Circle((0, 0), r, fill=False, edgecolor='black', lw=2.5); ax.add_patch(circle)
        ax.plot(0,0,'ko', markersize=6); ax.text(-0.4, -0.4, 'O', fontsize=12, fontweight='bold'); ax.plot([0,r],[0,0],'r--', lw=1.5); ax.text(r/2, -0.5, f'{r} cm', ha='center', color='red')
        ax.set_xlim(-r-1.5, r+1.5); ax.set_ylim(-r-1.5, r+1.5)

    plt.tight_layout(); buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=200, bbox_inches='tight'); buf.seek(0); plt.close(fig); return buf

def parse_diagram_tag(text):
    if "[DIAGRAM:" not in text: return None
    try:
        tag = text.split("[DIAGRAM:")[1].split("]")[0]; parts = {}
        for item in tag.split(","):
            if "=" in item: k,v = item.split("=",1); parts[k.strip()] = v.strip().strip('"')
        return parts if parts.get("Topic") else None
    except: return None

# ===================== 3. FULL NCDC 2026 DB - NO DATA LOSS =====================
PRIMARY_DB = {
  "PRIMARY_4": {
    "Mathematics": [{"topic": "Set Concepts", "competency": "Identify sets"}, {"topic": "Whole Numbers", "competency": "Up to 99,999"}, {"topic": "Operations", "competency": "Add, subtract, multiply, divide"}, {"topic": "Fractions", "competency": "Add fractions"}, {"topic": "Geometric Shapes", "competency": "Identify shapes"}, {"topic": "Measures", "competency": "Convert units"}, {"topic": "Money", "competency": "Budgets"}, {"topic": "Patterns", "competency": "Complete patterns"}, {"topic": "Data Handling", "competency": "Bar graphs"}],
    "English Language": [{"topic": "Describing People and Objects", "competency": "Use adjectives"}, {"topic": "Giving Directions", "competency": "Use prepositions"}, {"topic": "Feelings and Preferences", "competency": "Express likes"}, {"topic": "Comprehension: Descriptive Paragraphs", "competency": "Answer from paragraphs"}, {"topic": "Comprehension: Simple Dialogues", "competency": "Interpret dialogues"}, {"topic": "Comprehension: Picture Interpretation", "competency": "Describe picture"}],
    "Integrated Science": [{"topic": "Plant Life"}, {"topic": "Crop Husbandry"}, {"topic": "Weather"}, {"topic": "Human Body"}, {"topic": "Personal Hygiene"}, {"topic": "Vectors"}, {"topic": "First Aid"}, {"topic": "Air"}, {"topic": "Water"}, {"topic": "Indigenous Crafts"}],
    "Social Studies (SST)": [{"topic": "Location of Sub-County"}, {"topic": "Physical Features"}, {"topic": "Vegetation"}, {"topic": "People and Culture"}, {"topic": "Economic Activities"}, {"topic": "Social Services"}, {"topic": "Leadership"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Creation"}, {"topic": "Knowing Jesus"}, {"topic": "Christian Values"}, {"topic": "The Bible"}, {"topic": "Prayer"}, {"topic": "Relationships"}, {"topic": "Serving Others"}],
    "Islamic Religious Education (IRE)": [{"topic": "Selected Surahs"}, {"topic": "Pillars of Islam"}, {"topic": "Pillars of Iman"}, {"topic": "Life of Prophet"}, {"topic": "Islamic Manners"}, {"topic": "Wudhu"}]
  },
  "PRIMARY_5": {
    "Mathematics": [{"topic": "Set Theory"}, {"topic": "Whole Numbers"}, {"topic": "BODMAS"}, {"topic": "LCM and GCF"}, {"topic": "Fractions"}, {"topic": "Decimals"}, {"topic": "Geometry"}, {"topic": "Measures"}, {"topic": "Graphs"}, {"topic": "Business Math"}],
    "English Language": [{"topic": "Sanitation and Health"}, {"topic": "Local Culture"}, {"topic": "Simple Past Tense"}, {"topic": "Present Continuous"}, {"topic": "Conjunctions"}, {"topic": "Wh- Questions"}, {"topic": "Interpreting Notices"}, {"topic": "Public Announcements"}, {"topic": "Informational Texts"}],
    "Integrated Science": [{"topic": "Soil Science"}, {"topic": "Non-Flowering Plants"}, {"topic": "Matter"}, {"topic": "Poultry"}, {"topic": "Bee Keeping"}, {"topic": "Body Systems"}, {"topic": "Immunization"}, {"topic": "Waste Management"}, {"topic": "PHC"}, {"topic": "First Aid"}],
    "Social Studies (SST)": [{"topic": "Geography of Uganda"}, {"topic": "Physical Features"}, {"topic": "Climate"}, {"topic": "Vegetation Zones"}, {"topic": "Natural Resources"}, {"topic": "People of Uganda"}, {"topic": "Kingdoms"}, {"topic": "Colonial History"}, {"topic": "Independence"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Covenant"}, {"topic": "Ministry of Jesus"}, {"topic": "Parables"}, {"topic": "Christian Responses"}, {"topic": "The Church"}, {"topic": "Holy Days"}, {"topic": "Integrity"}],
    "Islamic Religious Education (IRE)": [{"topic": "Recitation"}, {"topic": "Surat Al-Fatiha"}, {"topic": "Zakat and Fasting"}, {"topic": "Faith in Books"}, {"topic": "Call to Prophethood"}, {"topic": "Islamic Etiquette"}, {"topic": "Holy Sites"}]
  },
  "PRIMARY_6": {
    "Mathematics": [{"topic": "Advanced Sets"}, {"topic": "Integers"}, {"topic": "Fractions and Decimals"}, {"topic": "Ratios"}, {"topic": "Sequences"}, {"topic": "Geometry"}, {"topic": "Speed"}, {"topic": "Area and Volume"}, {"topic": "Simple Interest"}, {"topic": "Algebra"}, {"topic": "Probability"}],
    "English Language": [{"topic": "Electronic Media"}, {"topic": "Messaging"}, {"topic": "Future Tenses"}, {"topic": "If-Conditionals"}, {"topic": "Relative Pronouns"}, {"topic": "Passive Voice"}, {"topic": "Short Stories"}, {"topic": "Newspaper"}, {"topic": "Dialogue"}],
    "Integrated Science": [{"topic": "Plant Classification"}, {"topic": "Invertebrates"}, {"topic": "Vertebrates"}, {"topic": "Domestic Animals"}, {"topic": "Sound"}, {"topic": "Matter"}, {"topic": "Body Systems"}, {"topic": "Diseases"}, {"topic": "Indigenous Tech"}, {"topic": "Digital Tech"}],
    "Social Studies (SST)": [{"topic": "East Africa"}, {"topic": "Physical Features"}, {"topic": "Wildlife"}, {"topic": "People of EA"}, {"topic": "Colonialism"}, {"topic": "Inventions"}, {"topic": "Democracy"}, {"topic": "EAC"}, {"topic": "Social Services"}],
    "Christian Religious Education (CRE)": [{"topic": "Prophets"}, {"topic": "Resurrection"}, {"topic": "Holy Spirit"}, {"topic": "Early Church"}, {"topic": "Witness"}, {"topic": "Authority"}, {"topic": "Future"}],
    "Islamic Religious Education (IRE)": [{"topic": "Memorization"}, {"topic": "Hajj"}, {"topic": "Day of Judgment"}, {"topic": "Prophets"}, {"topic": "Social Values"}, {"topic": "Festivals"}]
  },
  "PRIMARY_7": {
    "Mathematics": [{"topic": "Advanced Sets"}, {"topic": "Bases"}, {"topic": "Number Theory"}, {"topic": "Fractions"}, {"topic": "Ratios"}, {"topic": "Integers"}, {"topic": "Business Math"}, {"topic": "Graphs"}, {"topic": "Geometry"}, {"topic": "Speed"}, {"topic": "Surface Area"}, {"topic": "Inequalities"}],
    "English Language": [{"topic": "Friendly Letters"}, {"topic": "Official Letters"}, {"topic": "Timetables"}, {"topic": "Apostrophes"}, {"topic": "Semicolons and Colons"}, {"topic": "Direct Indirect Speech"}, {"topic": "Perfect Tenses"}, {"topic": "Complex Prose"}, {"topic": "Poetry"}, {"topic": "Graphic Data"}, {"topic": "Full Sentences"}],
    "Integrated Science": [{"topic": "Crop Husbandry"}, {"topic": "Animal Breeding"}, {"topic": "Energy"}, {"topic": "Simple Machines"}, {"topic": "Body Systems"}, {"topic": "Public Health"}, {"topic": "Environment"}, {"topic": "Interdependence"}, {"topic": "Innovation"}],
    "Social Studies (SST)": [{"topic": "Africa"}, {"topic": "Drainage"}, {"topic": "Trade"}, {"topic": "People of Africa"}, {"topic": "Slave Trade"}, {"topic": "Independence"}, {"topic": "AU and UN"}, {"topic": "Challenges"}],
    "Christian Religious Education (CRE)": [{"topic": "Salvation"}, {"topic": "Kingdom of God"}, {"topic": "Leadership"}, {"topic": "Moral Challenges"}, {"topic": "Marriage"}, {"topic": "Christian Hope"}, {"topic": "Multi-Faith"}],
    "Islamic Religious Education (IRE)": [{"topic": "Tafsir"}, {"topic": "Divine Decree"}, {"topic": "Shariah"}, {"topic": "Sahaba"}, {"topic": "Islamic Economics"}, {"topic": "Contemporary Issues"}]
  }
}

PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}
def get_all_topics_text():
    all_topics = []
    for grade, subjects in PRIMARY_DB.items():
        for subject, topics in subjects.items():
            for t in topics: all_topics.append(f"{grade} {subject}: {t['topic']}")
    return "\n".join(all_topics)

def smart_groq_call(client, system_prompt, user_prompt, max_tokens=4000):
    models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant"]
    for model in models_to_try:
        try:
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.3, max_tokens=max_tokens)
            return res
        except RateLimitError: continue
        except Exception: continue
    st.error("All Groq models busy."); return None

def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("Add GROQ_API_KEY in Streamlit Secrets"); return None

def generate_pdf(content, title):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
    c.setFont("Helvetica-Bold", 14); c.drawString(40, height-50, title); y = height - 80; c.setFont("Helvetica", 9)
    for line in content.split('\n')[:150]: c.drawString(40, y, line[:95]); y -= 14; if y < 50: c.showPage(); y = height - 50
    c.save(); buffer.seek(0); return buffer

# ===================== 4. PASSWORD =====================
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

# ===================== 5. MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026 NCDC - MOCK PLE GENERATOR")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"], key="grade_select")
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()), key="subject_select")
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject], key="topic_select")

SYLLABUS_CONTEXT = get_all_topics_text()

tabs = st.tabs(["AI Chat", "Theory", "MOCK PLE 50Q PAPER", "Math Work", "Teacher Tools"])

with tabs[0]:
    st.header("Ask TeacherK Anything")
    q = st.text_input("🔍 Ask your question", key="chat_q")
    if st.button("Ask", key="ask_btn") and q:
        client = get_client()
        if client:
            prompt = f"{MASTER_PROMPT}\n\nSYLLABUS:\n{SYLLABUS_CONTEXT}\n\nContext: {grade} {subject}\nQUESTION: {q}\n\nAnswer directly. Use units for math. Use full punctuation for English."
            with st.spinner("Reasoning..."):
                res = smart_groq_call(client, MASTER_PROMPT, prompt)
                if res:
                    answer = res.choices[0].message.content; st.markdown(answer)
                    diagram_info = parse_diagram_tag(answer)
                    if diagram_info: st.image(draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question","")), use_container_width=True)
                    st.download_button("📥 Download PDF", generate_pdf(answer, "Answer"), "answer.pdf")

with tabs[2]:
    st.header("MOCK PLE PAPER GENERATOR: SECTION A + SECTION B")
    if st.button("Generate 50Q MOCK PLE PAPER", key="mock_btn", type="primary"):
        client = get_client()
        if client:
            prompt = f"""{MASTER_PROMPT}

            Generate a FULL MOCK PLE PAPER for {grade} {subject} Topic: {topic}

            STRICT STRUCTURE:
            **SECTION A: 20 STRAIGHT QUESTIONS [40 MARKS]**
            Instructions: Answer all questions. Short answers.
            Q1....
            Q2....
           ... up to Q20.

            **SECTION B: 30 SCENARIO-BASED QUESTIONS [60 MARKS]**
            Instructions: Answer all questions. Show all working. Use Ugandan contexts.
            ### **Question 21: [Title]**
            [Scenario 3-4 sentences]
            **TASK:** [What to do]
            [Provide full solution with steps and units]

           ... continue to Question 50.

            **MARKING GUIDE**
            Provide answers for all 50 questions. For math, answers MUST have units. For English, answers MUST be punctuated well.
            """
            with st.spinner("Generating 50Q Mock PLE... This takes 1 minute"):
                res = smart_groq_call(client, MASTER_PROMPT, prompt, max_tokens=4000)
                if res:
                    paper = res.choices[0].message.content; st.markdown(paper)
                    diagrams = re.findall(r'\[DIAGRAM:.*?\]', paper)
                    for d in diagrams:
                        info = parse_diagram_tag(d)
                        if info: st.image(draw_math_diagram(info.get("Topic",""), info.get("Measurements",""), info.get("Question","")), use_container_width=True)
                    st.download_button("📥 Download 50Q MOCK PLE PDF", generate_pdf(paper, f"MOCK PLE {grade} {subject}"), "mock_ple.pdf")

with tabs[4]:
    st.header("Teacher Tools")
    if st.button("Generate Scheme of Work", key="scheme_btn"):
        client = get_client()
        if client:
            prompt = f"Create a 1-week scheme of work for {grade} {subject} Topic: {topic} following NCDC 2026."
            res = smart_groq_call(client, MASTER_PROMPT, prompt, max_tokens=2000)
            if res: st.markdown(res.choices[0].message.content)

st.sidebar.caption("NCDC 2026 | Section A:20 + Section B:30 | Contact: " + CONTACT)
