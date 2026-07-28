import streamlit as st
import os, io, json, random, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
import time
import hashlib
from datetime import datetime
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ===================== CONFIG =====================
CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7.")

# ===================== MASTER PROMPT: UNEB PLE 2026 FORMAT =====================
MASTER_PROMPT = """
You are TEACHERK, a Senior NCDC 2026 Uganda PLE Examiner and Master Teacher for PRIMARY P4-P7.

YOUR CORE MISSION:
Set questions exactly like UNEB PLE 2026. Use simple English, Ugandan examples.

===================== RULE 1: UNEB PLE PAPER STRUCTURE =====================
**SECTION A: 20 STRAIGHT QUESTIONS [40 MARKS]**
Short 1-line questions. 2 marks each. No scenarios.
Q1. What is 3/4 of 20?
Q2. Name one vector of malaria.

**SECTION B: 15 SCENARIO QUESTIONS [60 MARKS]**
Each question numbered 21-35. Each has sub-parts a, b, c. 4 marks each.
Format:
### **Question 21: Buying Beans in Owino Market**
Auntie Nalongo bought 5kg of beans at ugx 4,000 per kg. She paid with a ugx 50,000 note.
a) How much did she pay for the beans?
b) How much balance did she get?
c) If she shared the balance equally among her 5 children, how much did each get?

===================== RULE 2: DIAGRAM RULE - ONLY WHEN NEEDED =====================
If question mentions: triangle, rectangle, square, circle, angle, radius, length, width, base, height.
THEN you MUST add tag right after that question:
[DIAGRAM: Topic=Triangle, Measurements="Base=8cm, Height=5cm", Question="Find area of triangle ABC"]
The measurements in tag MUST match the numbers and units in the question exactly.

===================== RULE 3: MATH RULES =====================
1. **UNITS RULE**: Every final answer MUST end with unit. "Therefore the area was 20cm2."
2. **STEPS RULE**: For section B, show Step 1, Step 2 for a, b, c.
3. **UGX CONTEXT**: Use ugx, kg, cm, m, litres, minutes.

===================== RULE 4: MARKING RULE =====================
DEDUCT 1 MARK FOR: No units, No steps in section B.
"""

# ===================== 2. DIAGRAM GENERATOR - AUTO LABELS =====================
def draw_math_diagram(d_type, measurements, question_text):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal'); plt.axis('off'); ax.set_title(f"{d_type}\n{question_text}", fontsize=12, fontweight='bold', pad=15)
    data = measurements.lower() if measurements else ""
    def safe_float(s, default):
        try: return float(re.findall(r"[\d.]+", s)[0])
        except: return default
    def get_unit(s):
        if "cm" in s: return "cm"
        if "m" in s: return "m"
        return "units"

    if d_type and "triangle" in d_type.lower():
        base = safe_float(data.split("base=")[1], 8.0) if "base=" in data else 8.0
        unit = get_unit(data)
        height = safe_float(data.split("height=")[1], base*0.8) if "height=" in data else base*0.8
        A, B, C = (0, 0), (base, 0), (base/2, height)
        triangle = patches.Polygon([A, B, C], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(triangle)
        ax.plot([A[0],B[0]],[A[1],B[1]],'ko', markersize=5); ax.plot([B[0],C[0]],[B[1],C[1]],'ko', markersize=5); ax.plot([C[0],A[0]],[C[1],A[1]],'ko', markersize=5)
        ax.text(A[0]-0.3, A[1]-0.3, "A", fontsize=11, fontweight='bold'); ax.text(B[0]+0.1, B[1]-0.3, "B", fontsize=11, fontweight='bold'); ax.text(C[0], C[1]+0.3, "C", fontsize=11, fontweight='bold')
        ax.text(base/2, -0.5, f"Base = {base}{unit}", ha='center', fontsize=10); ax.text(-1, height/2, f"Height = {height}{unit}", va='center', rotation=90, fontsize=10)
        ax.set_xlim(-2, base+2); ax.set_ylim(-2, height+2)

    elif d_type and "rectangle" in d_type.lower():
        w = safe_float(data.split("length=")[1], 6.0) if "length=" in data else 6.0
        h = safe_float(data.split("width=")[1], 4.0) if "width=" in data else 4.0
        unit = get_unit(data)
        A, B, C, D = (0, 0), (w, 0), (w, h), (0, h)
        poly = patches.Polygon([A, B, C, D], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(poly)
        for pt, label in zip([A,B,C,D], ['A','B','C','D']): ax.plot(pt[0],pt[1],'ko', markersize=5); ax.text(pt[0]-0.3, pt[1]-0.3, label, fontsize=11, fontweight='bold')
        ax.text(w/2, -0.5, f"Length = {w}{unit}", ha='center', fontsize=10); ax.text(-0.8, h/2, f"Width = {h}{unit}", va='center', rotation=90, fontsize=10)
        ax.set_xlim(-2, w+2); ax.set_ylim(-2, h+2)

    elif d_type and "square" in d_type.lower():
        s = safe_float(data.split("side=")[1], 5.0) if "side=" in data else 5.0
        unit = get_unit(data)
        A, B, C, D = (0, 0), (s, 0), (s, s), (0, s)
        poly = patches.Polygon([A, B, C, D], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(poly)
        for pt, label in zip([A,B,C,D], ['A','B','C','D']): ax.plot(pt[0],pt[1],'ko', markersize=5); ax.text(pt[0]-0.3, pt[1]-0.3, label, fontsize=11, fontweight='bold')
        ax.text(s/2, -0.5, f"Side = {s}{unit}", ha='center', fontsize=10); ax.text(-0.8, s/2, f"Side = {s}{unit}", va='center', rotation=90, fontsize=10)
        ax.set_xlim(-2, s+2); ax.set_ylim(-2, s+2)

    elif d_type and "circle" in d_type.lower():
        r = safe_float(data.split("radius=")[1], 3.0) if "radius=" in data else 3.0
        unit = get_unit(data)
        circle = patches.Circle((0, 0), r, fill=False, edgecolor='black', lw=2.5); ax.add_patch(circle)
        ax.plot(0,0,'ko', markersize=5); ax.text(-0.4, -0.4, 'O', fontsize=11, fontweight='bold'); ax.plot([0,r],[0,0],'r--', lw=1.5); ax.text(r/2, -0.4, f'Radius = {r}{unit}', ha='center', color='red', fontsize=10)
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

# ===================== 3. FULL NCDC 2026 DB =====================
PRIMARY_DB = {
  "PRIMARY_4": {"Mathematics": [{"topic": "Set Concepts"}, {"topic": "Whole Numbers (Up to 99,999)"}, {"topic": "Operations on Whole Numbers"}, {"topic": "Fractions"}, {"topic": "Geometric Shapes and Symmetry"}, {"topic": "Measures (Time, Length, Mass, Capacity)"}, {"topic": "Money and Financial Literacy"}, {"topic": "Patterns and Sequences"}, {"topic": "Basic Data Handling (Pictographs and Bar Graphs)"}],
    "English Language": [{"topic": "Describing People and Objects"}, {"topic": "Giving Directions"}, {"topic": "Feelings and Preferences"}, {"topic": "Comprehension: Descriptive Paragraphs"}, {"topic": "Comprehension: Simple Dialogues"}, {"topic": "Comprehension: Picture Interpretation"}],
    "Integrated Science": [{"topic": "Plant Life and Flowering Plants"}, {"topic": "Crop Husbandry and Basic Farming Tools"}, {"topic": "Weather and Its Elements"}, {"topic": "Human Body (External Parts and Cleanliness)"}, {"topic": "Personal Hygiene and Sanitation"}, {"topic": "Vectors and Pests (Houseflies, Mosquitoes)"}, {"topic": "First Aid (Common Accidents)"}, {"topic": "Air and Its Properties"}, {"topic": "Water and Its Uses"}, {"topic": "Introduction to Indigenous Crafts"}],
    "Social Studies (SST)": [{"topic": "Location of Our Sub-County/Division"}, {"topic": "Physical Features and Environment of Our Sub-County"}, {"topic": "Vegetation and Animals in Our Locality"}, {"topic": "People and Culture in Our Sub-County"}, {"topic": "Economic Activities (Farming, Trade, Crafting)"}, {"topic": "Social Services and Infrastructure"}, {"topic": "Leadership and Governance in Our Locality"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Creation and Our Talents"}, {"topic": "Knowing Jesus Christ and His Early Life"}, {"topic": "Christian Values (Honesty, Forgiveness, Love)"}, {"topic": "The Bible as God's Holy Word"}, {"topic": "Prayer and Fellowship"}, {"topic": "Relationships in the Family and School"}, {"topic": "Serving Others in the Community"}],
    "Islamic Religious Education (IRE)": [{"topic": "Selected Surahs from the Holy Qur'an"}, {"topic": "Pillars of Islam (Shahadah and Salat)"}, {"topic": "Pillars of Iman (Faith in Allah and His Angels)"}, {"topic": "The Life of Prophet Muhammad (PBUH) - Early Childhood"}, {"topic": "Islamic Manners and Akhlaq"}, {"topic": "Introduction to Wudhu and Adhan"}]},
  "PRIMARY_5": {"Mathematics": [{"topic": "Set Theory (Union, Intersection, Venn Diagrams)"}, {"topic": "Whole Numbers (Up to 999,999)"}, {"topic": "Operations on Whole Numbers"}, {"topic": "Number Patterns and Sequences (LCM, GCF)"}, {"topic": "Fractions"}, {"topic": "Decimals"}, {"topic": "Geometry (Lines, Angles, and Construction)"}, {"topic": "Measures (Perimeter, Area, and Volume)"}, {"topic": "Graphs and Data Interpretation"}, {"topic": "Business Mathematics (Profit, Loss)"}],
    "English Language": [{"topic": "Thematic Integration: Sanitation and Health"}, {"topic": "Thematic Integration: Local Culture"}, {"topic": "Grammar: Simple Past Tense"}, {"topic": "Grammar: Present Continuous Tense"}, {"topic": "Grammar: Conjunctions"}, {"topic": "Grammar: Wh- Question Formation"}, {"topic": "Comprehension: Interpreting Notices"}, {"topic": "Comprehension: Public Announcements"}, {"topic": "Comprehension: Informational Texts"}],
    "Integrated Science": [{"topic": "Soil Science (Composition, Erosion, and Conservation)"}, {"topic": "Non-Flowering Plants and Fungi"}, {"topic": "Matter and Its States"}, {"topic": "Poultry Keeping and Management"}, {"topic": "Bee Keeping (Apiculture)"}, {"topic": "Human Body Systems (Digestive and Respiratory)"}, {"topic": "Immunization and Child Health"}, {"topic": "Sanitation and Waste Management"}, {"topic": "Primary Health Care (PHC)"}, {"topic": "First Aid for Fractures, Burns, and Poisoning"}],
    "Social Studies (SST)": [{"topic": "Location and Geography of Uganda"}, {"topic": "Physical Features of Uganda"}, {"topic": "Climate and Weather Patterns in Uganda"}, {"topic": "Vegetation Zones of Uganda"}, {"topic": "Natural Resources and Economic Activities"}, {"topic": "The People of Uganda (Ethnic Groups)"}, {"topic": "Cultural Governance and Kingdom Structures"}, {"topic": "Pre-Colonial and Colonial History of Uganda"}, {"topic": "Road to Independence"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Covenant with His People"}, {"topic": "The Birth and Ministry of Jesus Christ"}, {"topic": "The Miracles and Parables of Jesus"}, {"topic": "Christian Responses to Suffering"}, {"topic": "The Church as a Family"}, {"topic": "Christian Holy Days"}, {"topic": "Developing Positive Moral Values"}],
    "Islamic Religious Education (IRE)": [{"topic": "Advanced Recitation and Meanings of Selected Surahs"}, {"topic": "Surat Al-Fatiha Deep Study"}, {"topic": "The Pillars of Islam (Zakat and Sawm)"}, {"topic": "The Pillars of Iman (Faith in Holy Books)"}, {"topic": "The Life of Prophet Muhammad - The Call"}, {"topic": "Islamic Etiquette"}, {"topic": "Historical Mosques and Holy Sites"}]},
  "PRIMARY_6": {"Mathematics": [{"topic": "Advanced Set Operations"}, {"topic": "Whole Numbers (Integers, Bases)"}, {"topic": "Operations on Fractions and Decimals"}, {"topic": "Ratios, Proportions, and Percentages"}, {"topic": "Sequences and Number Patterns"}, {"topic": "Geometry (Angles in Polygons, Circle)"}, {"topic": "Speed, Distance, and Time"}, {"topic": "Area, Volume, and Capacity"}, {"topic": "Business Math (Simple Interest)"}, {"topic": "Algebraic Expressions and Equations"}, {"topic": "Basic Probability"}],
    "English Language": [{"topic": "Media and Technology: Electronic Media"}, {"topic": "Media and Technology: Messaging"}, {"topic": "Grammar: Future Tenses"}, {"topic": "Grammar: If-Conditionals"}, {"topic": "Grammar: Relative Pronouns"}, {"topic": "Grammar: Passive Voice"}, {"topic": "Comprehension: Short Stories"}, {"topic": "Comprehension: Newspaper Excerpts"}, {"topic": "Comprehension: Dialogue Exchanges"}],
    "Integrated Science": [{"topic": "Plant Classification and Reproduction"}, {"topic": "Invertebrates"}, {"topic": "Vertebrates"}, {"topic": "Domestic Animals"}, {"topic": "Sound Energy"}, {"topic": "Classification of Matter"}, {"topic": "Human Body Systems (Circulatory)"}, {"topic": "Contagious and Communicable Diseases"}, {"topic": "Indigenous Technology"}, {"topic": "Basic Digital Tech and Coding"}],
    "Social Studies (SST)": [{"topic": "East Africa (Location, Neighbors)"}, {"topic": "Physical Features and Climate of East Africa"}, {"topic": "Vegetation and Wildlife Conservation"}, {"topic": "The People of East Africa"}, {"topic": "Historic Milestones and Colonialism"}, {"topic": "Main Inventions"}, {"topic": "Democratic Elections and Human Rights"}, {"topic": "Regional Economic Blocs (EAC)"}, {"topic": "Social Services and Security"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Guidance and the Prophets"}, {"topic": "The Death and Resurrection of Jesus"}, {"topic": "The Holy Spirit and His Gifts"}, {"topic": "The Early Church and Missionaries"}, {"topic": "Christian Witness"}, {"topic": "Respect for Authority"}, {"topic": "Preparing for the Future"}],
    "Islamic Religious Education (IRE)": [{"topic": "Advanced Recitation and Memorization"}, {"topic": "The Pillars of Islam (Hajj)"}, {"topic": "The Pillars of Iman (Day of Judgment)"}, {"topic": "Stories of Prophets"}, {"topic": "Islamic Social Values"}, {"topic": "Islamic Festivals"}]},
  "PRIMARY_7": {"Mathematics": [{"topic": "Advanced Sets (Three Categories)"}, {"topic": "Whole Numbers and Bases"}, {"topic": "Number Theory"}, {"topic": "Fractions, Decimals, and Percentages"}, {"topic": "Ratios and Proportion"}, {"topic": "Integers"}, {"topic": "Business Mathematics"}, {"topic": "Graphs and Data Handling"}, {"topic": "Geometry (Constructions)"}, {"topic": "Speed, Velocity"}, {"topic": "Area, Surface Area, and Volume"}, {"topic": "Equations and Inequalities"}],
    "English Language": [{"topic": "Formal and Informal Writing: Friendly Letters"}, {"topic": "Formal and Informal Writing: Official Letters"}, {"topic": "Formal and Informal Writing: School Timetables"}, {"topic": "Advanced Grammar: Apostrophes"}, {"topic": "Advanced Grammar: Semicolons and Colons"}, {"topic": "Advanced Grammar: Direct and Indirect Speech"}, {"topic": "Advanced Grammar: Perfect Tenses"}, {"topic": "Comprehension: Complex Continuous Prose"}, {"topic": "Comprehension: Poetry Analysis"}, {"topic": "Comprehension: Graphic Data"}, {"topic": "Comprehension: Answering in Full Sentences"}],
    "Integrated Science": [{"topic": "Plant Life and Advanced Crop Husbandry"}, {"topic": "Animal Management and Animal Breeding"}, {"topic": "Energy (Light, Heat, Electricity)"}, {"topic": "Simple Machines and Mechanics"}, {"topic": "Human Body Systems (Excretory, Nervous)"}, {"topic": "Human Health and Public Health"}, {"topic": "Environmental Management"}, {"topic": "Interdependence of Living Things"}, {"topic": "Scientific Innovation"}],
    "Social Studies (SST)": [{"topic": "Africa (Location, Size, Boundaries)"}, {"topic": "Major Drainage Systems, Climate"}, {"topic": "Economic Resources and Trade"}, {"topic": "The People of Africa"}, {"topic": "Foreign Influence, Slave Trade"}, {"topic": "The Struggle for Independence"}, {"topic": "Major Regional and Global Bodies (AU, UN)"}, {"topic": "Post-Independence Achievements"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Ultimate Plan for Salvation"}, {"topic": "The Teachings of Jesus Christ"}, {"topic": "Christian Service, Leadership"}, {"topic": "Contemporary Moral Challenges"}, {"topic": "Marriage, Family Life"}, {"topic": "Death, Resurrection, and Hope"}, {"topic": "Living Peacefully in a Multi-Faith Society"}],
    "Islamic Religious Education (IRE)": [{"topic": "Advanced Qur'anic Studies and Tafsir"}, {"topic": "The Pillars of Iman (Faith in Divine Decree)"}, {"topic": "Islamic Law (Shariah) and Social Justice"}, {"topic": "The Life of the Prophet's Companions"}, {"topic": "Islamic Economic System"}, {"topic": "Contemporary Issues in Islam"}]}
}

PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}
def get_all_topics_for_subject(grade, subject):
    return [t["topic"] for t in PRIMARY_DB[f"PRIMARY_{grade[1:]}"][subject]]

# ===================== 4. SMART GROQ CALL =====================
if "cache" not in st.session_state: st.session_state.cache = {}

def smart_groq_call(client, system_prompt, user_prompt, max_tokens=4000):
    cache_key = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
    if cache_key in st.session_state.cache: return st.session_state.cache[cache_key]
    models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
    if len(user_prompt) > 4000: user_prompt = user_prompt[:4000] + "\n\n[Context trimmed]"
    for attempt in range(3):
        for model in models_to_try:
            try:
                res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.3, max_tokens=max_tokens)
                st.session_state.cache[cache_key] = res; return res
            except RateLimitError: time.sleep(2 ** attempt); continue
            except Exception: continue
    st.error("All Groq models busy. Please wait 30s and try again."); return None

def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("Add GROQ_API_KEY in Streamlit Secrets"); return None

def generate_pdf(content, title):
    buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
    c.setFont("Helvetica-Bold", 14); c.drawString(40, height-50, title)
    y = height - 80; c.setFont("Helvetica", 9)
    for line in content.split('\n')[:250]: c.drawString(40, y, line[:95]); y -= 14
    if y < 50: c.showPage(); y = height - 50; c.setFont("Helvetica", 9)
    c.save(); buffer.seek(0); return buffer

# ===================== 5. PASSWORD =====================
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

# ===================== 6. HELPER: RENDER WITH INLINE DIAGRAMS =====================
def render_with_inline_diagrams(text):
    chunks = re.split(r'(### \*\*Question \d+:)', text)
    for i in range(0, len(chunks), 2):
        part = chunks[i]
        if i+1 < len(chunks): part += chunks[i+1]
        if part.strip():
            st.markdown(part)
            diagram_info = parse_diagram_tag(part)
            if diagram_info:
                st.image(draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question","")), use_container_width=True, caption="Diagram")
            st.markdown("---")

# ===================== 7. MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026 NCDC")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"], key="grade_select")
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()), key="subject_select")
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject], key="topic_select_scroll")

ALL_SUBJECT_TOPICS = get_all_topics_for_subject(grade, subject)
tabs = st.tabs(["🔍 General Search", "📖 Theory", "📝 MOCK PLE 35Q PAPER", "➗ Math Work", "👩‍🏫 Teacher Tools"])

def ask_ai(prompt, dl_name):
    client = get_client()
    if client:
        with st.spinner("Thinking like PLE Examiner..."):
            res = smart_groq_call(client, MASTER_PROMPT, prompt)
            if res:
                answer = res.choices[0].message.content
                render_with_inline_diagrams(answer)
                st.download_button("📥 Download PDF", generate_pdf(answer, dl_name), f"{dl_name}.pdf", key=f"dl_{dl_name}")

with tabs[0]:
    st.header("🔍 General Search")
    q = st.text_input("Ask Anything", key="ask_general")
    if st.button("Ask", key="btn_general") and q: ask_ai(f"User Context: {grade} {subject} Topic: {topic}\nUSER REQUEST: {q}", "answer_general")

with tabs[1]:
    st.header(f"📖 Theory: {grade} {subject}")
    if st.button("Generate Full Theory Notes", key="theory_btn"):
        ask_ai(f"Generate detailed NCDC 2026 theory notes for {grade} {subject} Topic: {topic}. Include Definition, Key Competency, 3 Examples, Ugandan Example, Life Skill.", f"Theory_{topic}")
    q = st.text_input("Ask about Theory", key="ask_theory")
    if st.button("Ask Theory", key="btn_theory") and q: ask_ai(f"User Context: {grade} {subject} Topic: {topic}\nUSER REQUEST: {q}", "answer_theory")

with tabs[2]:
    st.header("📝 MOCK PLE PAPER: UNEB 2026 FORMAT")
    if st.button("Generate MOCK PLE From WHOLE SUBJECT", key="mock_btn", type="primary"):
        prompt = f"{MASTER_PROMPT}\nGenerate a FULL MOCK PLE PAPER for {grade} {subject}. ROTATE ACROSS ALL TOPICS: {ALL_SUBJECT_TOPICS}.\n\n**SECTION A: 20 STRAIGHT QUESTIONS [40 MARKS]**\nQ1 to Q20.\n\n**SECTION B: 15 SCENARIO QUESTIONS [60 MARKS]**\nQuestion 21 to 35. Each must have a), b), c).\nIf math/shape is involved add [DIAGRAM:] tag with correct units."
        ask_ai(prompt, f"MOCK_PLE_{grade}_{subject}")

with tabs[3]:
    st.header("➗ Mathematics Worked Examples")
    if subject == "Mathematics":
        if st.button("Generate 7 Worked Examples From WHOLE SUBJECT", key="mathwork_btn"):
            prompt = f"{MASTER_PROMPT}\nGenerate 7 fully worked scenario-based math questions for {grade} {subject}. ROTATE ACROSS ALL TOPICS: {ALL_SUBJECT_TOPICS}. EACH QUESTION MUST HAVE a), b). SHOW ALL STEPS WITH UNITS. ADD [DIAGRAM:] IF SHAPE IS MENTIONED."
            ask_ai(prompt, f"Math_Work_{grade}")
    else: st.info("Select Mathematics subject to use.")

with tabs[4]:
    st.header("👩‍🏫 Teacher Tools")
    if st.button("Generate Test Paper 50Q", key="exam_btn"):
        prompt = f"{MASTER_PROMPT}\nGenerate a Test for {grade} {subject}. ROTATE ACROSS ALL TOPICS: {ALL_SUBJECT_TOPICS}. 20 Straight Qs + 10 Scenario Qs with a,b,c."
        ask_ai(prompt, f"Test_{grade}_{subject}")
    st.markdown("---")
    marking_scheme = st.text_area("Paste Marking Scheme", key="mark_scheme")
    student_answers = st.text_area("Paste Student Answers", key="mark_paste")
    if st.button("Mark Work Now", key="mark_btn") and student_answers:
        prompt = f"You are a UNEB PLE Examiner. Mark this {grade} {subject} work. Deduct 1 mark for missing units.\nMARKING SCHEME:\n{marking_scheme}\nSTUDENT WORK:\n{student_answers}\nProvide: Total, Breakdown, Comments."
        ask_ai(prompt, "Marked_Work")

st.sidebar.caption("NCDC 2026 | UNEB Format | Contact: " + CONTACT)
