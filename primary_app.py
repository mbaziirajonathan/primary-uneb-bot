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
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ===================== CONFIG =====================
CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7.")

# ===================== MASTER PROMPT: UNEB PLE EXAMINER + LENGTH RULES =====================
MASTER_PROMPT = """
You are an OFFICIAL UNEB PLE EXAMINER for Mathematics, Integrated Science, Social Studies (SST), and English Language.
You set HARD exams for P6-P7 with UNEB accuracy and exact length.

===================== RULE 1: UNEB QUESTION LENGTH RULES - STRICT =====================
**SECTION A: 20 STRAIGHT QUESTIONS [40 MARKS]** Q1-Q20
UNEB LENGTH RULE: 1 line only. 8-12 words maximum. No story, no scenario.
Start with: Define, Calculate, Name, State, What is, List.
Example: Q1. Calculate 3/4 of 48kg. [2]

**SECTION B: 40 SCENARIO QUESTIONS [60 MARKS]** Q21-Q60
UNEB LENGTH RULE: 3-4 lines scenario. 25-40 words total per question. Must have real Ugandan context.
Then: a), b), c) each 1 line.
Example:
### **Question 21:** A trader bought 50kg of maize at ugx 1,500 per kg. He sold all of it at ugx 2,200 per kg.
a) How much did he spend on maize? [2]
b) How much money did he get from selling? [2]
c) Calculate his profit. [2]

===================== RULE 2: PAPER STRUCTURE =====================
**SECTION A: 20Q**
**SECTION B: 40Q**
DIFFICULTY DISTRIBUTION: P4=0Q, P5=6Q, P6=16Q, P7=18Q. Total 60Q.

===================== RULE 3: SST RELIGIOUS INTEGRATION RULE =====================
IF SUBJECT = "Social Studies (SST)" THEN:
**SECTION A: 20 SST STRAIGHT QUESTIONS**
**SECTION B: 40 QUESTIONS**
Q21-Q40 = SST SCENARIOS [20Q]
Q41-Q50 = CRE SCENARIOS [10Q] Label: "### **Question 41: CRE - **"
Q51-Q60 = IRE SCENARIOS [10Q] Label: "### **Question 51: IRE - **"

===================== RULE 4: UNEB MARKING GUIDE LOGIC =====================
When asked to mark, use these 4 subject criteria:

1. MATHEMATICS: Use M=Method, A=Accuracy, B=Statement. Show manual steps. Flag missing units.
2. SCIENCE: Exact keywords. Distinguish full vs partial. List wrong terms = 0.
3. SST: Facts, dates, locations. Separate "List" vs "Explain". Note regional confusion.
4. ENGLISH: Grammar rules. Penalties for spelling/punctuation. Compo: Layout, Content, Expression, Mechanics.

Output: Subject, Answer Key, Mark Allocation M/A/B, Common Candidate Mistakes.

===================== RULE 5: DIAGRAM FIRST RULE =====================
For shapes/sets: FIRST [DIAGRAM:] tag, then question a,b,c.
"""

# ===================== 2. DIAGRAM GENERATOR =====================
def draw_math_diagram(d_type, measurements, question_text):
    fig, ax = plt.subplots(figsize=(6, 6))
    plt.axis('off'); ax.set_title(f"{question_text}", fontsize=11, fontweight='bold', pad=15)
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

    elif d_type and "venn3" in d_type.lower():
        A = safe_float(data.split("a=")[1], 10) if "a=" in data else 10
        B = safe_float(data.split("b=")[1], 12) if "b=" in data else 12
        C = safe_float(data.split("c=")[1], 8) if "c=" in data else 8
        AB = safe_float(data.split("ab=")[1], 3) if "ab=" in data else 3
        AC = safe_float(data.split("ac=")[1], 2) if "ac=" in data else 2
        BC = safe_float(data.split("bc=")[1], 4) if "bc=" in data else 4
        ABC = safe_float(data.split("abc=")[1], 1) if "abc=" in data else 1
        v = venn3(subsets = (A-AB-AC+ABC, B-AB-BC+ABC, AB-ABC, C-AC-BC+ABC, AC-ABC, BC-ABC, ABC), set_labels = ('A', 'B', 'C'))

    elif d_type and "triangle" in d_type.lower():
        base = safe_float(data.split("base=")[1], 8.0) if "base=" in data else 8.0
        unit = get_unit(data); height = safe_float(data.split("height=")[1], base*0.8) if "height=" in data else base*0.8
        A, B, C = (0, 0), (base, 0), (base/2, height)
        triangle = patches.Polygon([A, B, C], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(triangle)
        ax.text(base/2, -0.5, f"Base = {base}{unit}", ha='center'); ax.text(-1, height/2, f"Height = {height}{unit}", va='center', rotation=90)
        ax.set_xlim(-2, base+2); ax.set_ylim(-2, height+2)

    elif d_type and "rectangle" in d_type.lower():
        w = safe_float(data.split("length=")[1], 6.0) if "length=" in data else 6.0
        h = safe_float(data.split("width=")[1], 4.0) if "width=" in data else 4.0
        unit = get_unit(data)
        poly = patches.Polygon([(0,0),(w,0),(w,h),(0,h)], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(poly)
        ax.text(w/2, -0.5, f"L = {w}{unit}", ha='center'); ax.text(-0.8, h/2, f"W = {h}{unit}", va='center', rotation=90)
        ax.set_xlim(-2, w+2); ax.set_ylim(-2, h+2)

    elif d_type and "square" in d_type.lower():
        s = safe_float(data.split("side=")[1], 5.0) if "side=" in data else 5.0
        unit = get_unit(data)
        poly = patches.Polygon([(0,0),(s,0),(s,s),(0,s)], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(poly)
        ax.text(s/2, -0.5, f"Side = {s}{unit}", ha='center'); ax.text(-0.8, s/2, f"Side = {s}{unit}", va='center', rotation=90)
        ax.set_xlim(-2, s+2); ax.set_ylim(-2, s+2)

    elif d_type and "circle" in d_type.lower():
        r = safe_float(data.split("radius=")[1], 3.0) if "radius=" in data else 3.0
        unit = get_unit(data)
        circle = patches.Circle((0, 0), r, fill=False, edgecolor='black', lw=2.5); ax.add_patch(circle)
        ax.plot([0,r],[0,0],'r--', lw=1.5); ax.text(r/2, -0.4, f'R = {r}{unit}', ha='center', color='red')
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

# ===================== 3. FULL NCDC 2026 DB - FULLY RESTORED =====================
PRIMARY_DB = {
  "PRIMARY_4": {
    "Mathematics": [{"topic": "Set Concepts"}, {"topic": "Whole Numbers (Up to 99,999)"}, {"topic": "Operations on Whole Numbers"}, {"topic": "Fractions"}, {"topic": "Geometric Shapes and Symmetry"}, {"topic": "Measures (Time, Length, Mass, Capacity)"}, {"topic": "Money and Financial Literacy"}, {"topic": "Patterns and Sequences"}, {"topic": "Basic Data Handling (Pictographs and Bar Graphs)"}],
    "English Language": [{"topic": "Describing People and Objects"}, {"topic": "Giving Directions"}, {"topic": "Feelings and Preferences"}, {"topic": "Comprehension: Descriptive Paragraphs"}, {"topic": "Comprehension: Simple Dialogues"}, {"topic": "Comprehension: Picture Interpretation"}],
    "Integrated Science": [{"topic": "Plant Life and Flowering Plants"}, {"topic": "Crop Husbandry and Basic Farming Tools"}, {"topic": "Weather and Its Elements"}, {"topic": "Human Body (External Parts and Cleanliness)"}, {"topic": "Personal Hygiene and Sanitation"}, {"topic": "Vectors and Pests (Houseflies, Mosquitoes)"}, {"topic": "First Aid (Common Accidents)"}, {"topic": "Air and Its Properties"}, {"topic": "Water and Its Uses"}, {"topic": "Introduction to Indigenous Crafts"}],
    "Social Studies (SST)": [{"topic": "Location of Our Sub-County/Division"}, {"topic": "Physical Features and Environment of Our Sub-County"}, {"topic": "Vegetation and Animals in Our Locality"}, {"topic": "People and Culture in Our Sub-County"}, {"topic": "Economic Activities (Farming, Trade, Crafting)"}, {"topic": "Social Services and Infrastructure"}, {"topic": "Leadership and Governance in Our Locality"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Creation and Our Talents"}, {"topic": "Knowing Jesus Christ and His Early Life"}, {"topic": "Christian Values (Honesty, Forgiveness, Love)"}, {"topic": "The Bible as God's Holy Word"}, {"topic": "Prayer and Fellowship"}, {"topic": "Relationships in the Family and School"}, {"topic": "Serving Others in the Community"}],
    "Islamic Religious Education (IRE)": [{"topic": "Selected Surahs from the Holy Qur'an"}, {"topic": "Pillars of Islam (Shahadah and Salat)"}, {"topic": "Pillars of Iman (Faith in Allah and His Angels)"}, {"topic": "The Life of Prophet Muhammad (PBUH) - Early Childhood"}, {"topic": "Islamic Manners and Akhlaq"}, {"topic": "Introduction to Wudhu and Adhan"}]
  },
  "PRIMARY_5": {
    "Mathematics": [{"topic": "Set Theory (Union, Intersection, Venn Diagrams)"}, {"topic": "Whole Numbers (Up to 999,999)"}, {"topic": "Operations on Whole Numbers"}, {"topic": "Number Patterns and Sequences (LCM, GCF)"}, {"topic": "Fractions"}, {"topic": "Decimals"}, {"topic": "Geometry (Lines, Angles, and Construction)"}, {"topic": "Measures (Perimeter, Area, and Volume)"}, {"topic": "Graphs and Data Interpretation"}, {"topic": "Business Mathematics (Profit, Loss)"}],
    "English Language": [{"topic": "Thematic Integration: Sanitation and Health"}, {"topic": "Thematic Integration: Local Culture"}, {"topic": "Grammar: Simple Past Tense"}, {"topic": "Grammar: Present Continuous Tense"}, {"topic": "Grammar: Conjunctions"}, {"topic": "Grammar: Wh- Question Formation"}, {"topic": "Comprehension: Interpreting Notices"}, {"topic": "Comprehension: Public Announcements"}, {"topic": "Comprehension: Informational Texts"}],
    "Integrated Science": [{"topic": "Soil Science (Composition, Erosion, and Conservation)"}, {"topic": "Non-Flowering Plants and Fungi"}, {"topic": "Matter and Its States"}, {"topic": "Poultry Keeping and Management"}, {"topic": "Bee Keeping (Apiculture)"}, {"topic": "Human Body Systems (Digestive and Respiratory)"}, {"topic": "Immunization and Child Health"}, {"topic": "Sanitation and Waste Management"}, {"topic": "Primary Health Care (PHC)"}, {"topic": "First Aid for Fractures, Burns, and Poisoning"}],
    "Social Studies (SST)": [{"topic": "Location and Geography of Uganda"}, {"topic": "Physical Features of Uganda"}, {"topic": "Climate and Weather Patterns in Uganda"}, {"topic": "Vegetation Zones of Uganda"}, {"topic": "Natural Resources and Economic Activities"}, {"topic": "The People of Uganda (Ethnic Groups)"}, {"topic": "Cultural Governance and Kingdom Structures"}, {"topic": "Pre-Colonial and Colonial History of Uganda"}, {"topic": "Road to Independence"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Covenant with His People"}, {"topic": "The Birth and Ministry of Jesus Christ"}, {"topic": "The Miracles and Parables of Jesus"}, {"topic": "Christian Responses to Suffering"}, {"topic": "The Church as a Family"}, {"topic": "Christian Holy Days"}, {"topic": "Developing Positive Moral Values"}],
    "Islamic Religious Education (IRE)": [{"topic": "Advanced Recitation and Meanings of Selected Surahs"}, {"topic": "Surat Al-Fatiha Deep Study"}, {"topic": "The Pillars of Islam (Zakat and Sawm)"}, {"topic": "The Pillars of Iman (Faith in Holy Books)"}, {"topic": "The Life of Prophet Muhammad - The Call"}, {"topic": "Islamic Etiquette"}, {"topic": "Historical Mosques and Holy Sites"}]
  },
  "PRIMARY_6": {
    "Mathematics": [{"topic": "Advanced Set Operations"}, {"topic": "Whole Numbers (Integers, Bases)"}, {"topic": "Operations on Fractions and Decimals"}, {"topic": "Ratios, Proportions, and Percentages"}, {"topic": "Sequences and Number Patterns"}, {"topic": "Geometry (Angles in Polygons, Circle)"}, {"topic": "Speed, Distance, and Time"}, {"topic": "Area, Volume, and Capacity"}, {"topic": "Business Math (Simple Interest)"}, {"topic": "Algebraic Expressions and Equations"}, {"topic": "Basic Probability"}],
    "English Language": [{"topic": "Media and Technology: Electronic Media"}, {"topic": "Media and Technology: Messaging"}, {"topic": "Grammar: Future Tenses"}, {"topic": "Grammar: If-Conditionals"}, {"topic": "Grammar: Relative Pronouns"}, {"topic": "Grammar: Passive Voice"}, {"topic": "Comprehension: Short Stories"}, {"topic": "Comprehension: Newspaper Excerpts"}, {"topic": "Comprehension: Dialogue Exchanges"}],
    "Integrated Science": [{"topic": "Plant Classification and Reproduction"}, {"topic": "Invertebrates"}, {"topic": "Vertebrates"}, {"topic": "Domestic Animals"}, {"topic": "Sound Energy"}, {"topic": "Classification of Matter"}, {"topic": "Human Body Systems (Circulatory)"}, {"topic": "Contagious and Communicable Diseases"}, {"topic": "Indigenous Technology"}, {"topic": "Basic Digital Tech and Coding"}],
    "Social Studies (SST)": [{"topic": "East Africa (Location, Neighbors)"}, {"topic": "Physical Features and Climate of East Africa"}, {"topic": "Vegetation and Wildlife Conservation"}, {"topic": "The People of East Africa"}, {"topic": "Historic Milestones and Colonialism"}, {"topic": "Main Inventions"}, {"topic": "Democratic Elections and Human Rights"}, {"topic": "Regional Economic Blocs (EAC)"}, {"topic": "Social Services and Security"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Guidance and the Prophets"}, {"topic": "The Death and Resurrection of Jesus"}, {"topic": "The Holy Spirit and His Gifts"}, {"topic": "The Early Church and Missionaries"}, {"topic": "Christian Witness"}, {"topic": "Respect for Authority"}, {"topic": "Preparing for the Future"}],
    "Islamic Religious Education (IRE)": [{"topic": "Advanced Recitation and Memorization"}, {"topic": "The Pillars of Islam (Hajj)"}, {"topic": "The Pillars of Iman (Day of Judgment)"}, {"topic": "Stories of Prophets"}, {"topic": "Islamic Social Values"}, {"topic": "Islamic Festivals"}]
  },
  "PRIMARY_7": {
    "Mathematics": [{"topic": "Advanced Sets (Three Categories)"}, {"topic": "Whole Numbers and Bases"}, {"topic": "Number Theory"}, {"topic": "Fractions, Decimals, and Percentages"}, {"topic": "Ratios and Proportion"}, {"topic": "Integers"}, {"topic": "Business Mathematics"}, {"topic": "Graphs and Data Handling"}, {"topic": "Geometry (Constructions)"}, {"topic": "Speed, Velocity"}, {"topic": "Area, Surface Area, and Volume"}, {"topic": "Equations and Inequalities"}],
    "English Language": [{"topic": "Formal and Informal Writing: Friendly Letters"}, {"topic": "Formal and Informal Writing: Official Letters"}, {"topic": "Formal and Informal Writing: School Timetables"}, {"topic": "Advanced Grammar: Apostrophes"}, {"topic": "Advanced Grammar: Semicolons and Colons"}, {"topic": "Advanced Grammar: Direct and Indirect Speech"}, {"topic": "Advanced Grammar: Perfect Tenses"}, {"topic": "Comprehension: Complex Continuous Prose"}, {"topic": "Comprehension: Poetry Analysis"}, {"topic": "Comprehension: Graphic Data"}, {"topic": "Comprehension: Answering in Full Sentences"}],
    "Integrated Science": [{"topic": "Plant Life and Advanced Crop Husbandry"}, {"topic": "Animal Management and Animal Breeding"}, {"topic": "Energy (Light, Heat, Electricity)"}, {"topic": "Simple Machines and Mechanics"}, {"topic": "Human Body Systems (Excretory, Nervous)"}, {"topic": "Human Health and Public Health"}, {"topic": "Environmental Management"}, {"topic": "Interdependence of Living Things"}, {"topic": "Scientific Innovation"}],
    "Social Studies (SST)": [{"topic": "Africa (Location, Size, Boundaries)"}, {"topic": "Major Drainage Systems, Climate"}, {"topic": "Economic Resources and Trade"}, {"topic": "The People of Africa"}, {"topic": "Foreign Influence, Slave Trade"}, {"topic": "The Struggle for Independence"}, {"topic": "Major Regional and Global Bodies (AU, UN)"}, {"topic": "Post-Independence Achievements"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Ultimate Plan for Salvation"}, {"topic": "The Teachings of Jesus Christ"}, {"topic": "Christian Service, Leadership"}, {"topic": "Contemporary Moral Challenges"}, {"topic": "Marriage, Family Life"}, {"topic": "Death, Resurrection, and Hope"}, {"topic": "Living Peacefully in a Multi-Faith Society"}],
    "Islamic Religious Education (IRE)": [{"topic": "Advanced Qur'anic Studies and Tafsir"}, {"topic": "The Pillars of Iman (Faith in Divine Decree)"}, {"topic": "Islamic Law (Shariah) and Social Justice"}, {"topic": "The Life of the Prophet's Companions"}, {"topic": "Islamic Economic System"}, {"topic": "Contemporary Issues in Islam"}]
  }
}
PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}
def get_all_topics(grade): return [t["topic"] for sub in PRIMARY_DB[f"PRIMARY_{grade[1:]}"].values() for t in sub]

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
    st.error("All Groq models busy."); return None
def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("Add GROQ_API_KEY in Streamlit Secrets"); return None
def generate_pdf(content, title):
    buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
    c.setFont("Helvetica-Bold", 14); c.drawString(40, height-50, title)
    y = height - 80; c.setFont("Helvetica", 9)
    for line in content.split('\n')[:350]: c.drawString(40, y, line[:95]); y -= 14
    if y < 50: c.showPage(); y = height - 50; c.setFont("Helvetica", 9)
    c.save(); buffer.seek(0); return buffer

# ===================== 5. HELPER: RENDER DIAGRAM FIRST =====================
def render_diagram_first(text):
    chunks = re.split(r'(### \*\*Question \d+:)', text)
    for i in range(0, len(chunks), 2):
        diagram_part = chunks[i]
        question_part = chunks[i+1] if i+1 < len(chunks) else ""
        diagram_info = parse_diagram_tag(diagram_part)
        if diagram_info:
            st.image(draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question","")), use_container_width=True)
        if question_part.strip(): st.markdown("### **Question" + question_part)
        st.markdown("---")

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
st.title("🐢 TEACHERK PRIMARY 2026 NCDC - FULL RESTORE")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"])
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])

tabs = st.tabs(["🔍 General Search", "📖 Theory", "📝 HARD COMBINED MOCK PLE", "➗ Math Work", "👩‍🏫 Teacher Tools"])

def ask_ai(prompt, dl_name):
    client = get_client()
    if client:
        with st.spinner("UNEB Examiner is Setting Paper..."):
            res = smart_groq_call(client, MASTER_PROMPT, prompt)
            if res:
                answer = res.choices[0].message.content
                render_diagram_first(answer)
                st.download_button("📥 Download PDF", generate_pdf(answer, dl_name), f"{dl_name}.pdf", key=f"dl_{dl_name}")
        st.markdown("---")
        st.subheader("Upload & Download")
        upload = st.file_uploader("Upload student work txt/pdf", type=["txt","pdf"], key=f"upload_{dl_name}")

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
    st.header("📝 HARD COMBINED MOCK PLE: UNEB LENGTH")
    st.info("Section A: 1 line, 8-12 words. Section B: 3-4 lines scenario, 25-40 words. Total 60Q. SST=20+10+10")
    if st.button("Generate HARD COMBINED MOCK PLE", key="mock_btn", type="primary"):
        sst_rule = "FOR SST: SECTION A=20 SST. SECTION B=20 SST Q21-Q40, 10 CRE Q41-Q50, 10 IRE Q51-Q60." if subject == "Social Studies (SST)" else ""
        prompt = f"{MASTER_PROMPT}\nGenerate a HARD COMBINED MOCK PLE PAPER for {grade} {subject}. FOLLOW UNEB LENGTH RULES STRICTLY.\nROTATE DIFFICULTY: P4=0Q, P5=6Q, P6=16Q, P7=18Q. Total 60Q. ROTATE TOPICS: {get_all_topics(grade)}\n\n**SECTION A: 20 STRAIGHT QUESTIONS [40 MARKS]** 1 line each, 8-12 words.\nQ1 to Q20.\n\n**SECTION B: 40 SCENARIO QUESTIONS [60 MARKS]** 3-4 lines each, 25-40 words.\nQuestion 21 to 60. Each must have a), b), c). {sst_rule}\nFOR SETS AND SHAPES, PUT [DIAGRAM:] TAG FIRST.\nAfter the paper, generate the UNEB MARKING GUIDE using RULE 4."
        ask_ai(prompt, f"HARD_MOCK_PLE_{subject}")

with tabs[3]:
    st.header("➗ Mathematics Worked Examples + UNEB Marking")
    if subject == "Mathematics":
        if st.button("Generate 7 Hard Worked Examples With M/A/B", key="mathwork_btn"):
            prompt = f"{MASTER_PROMPT}\nGenerate 7 HARD P6-P7 math questions. ROTATE TOPICS: {get_all_topics(grade)}. EACH SCENARIO MUST BE 3-4 LINES. EACH MUST HAVE a), b). THEN GENERATE UNEB MARKING GUIDE: Show M, A, B. Flag missing units."
            ask_ai(prompt, f"Math_Work_{grade}")
    else: st.info("Select Mathematics subject.")

with tabs[4]:
    st.header("👩‍🏫 Teacher Tools - UNEB EXAMINER SUITE")
    st.subheader("1. Test Paper Generator")
    if st.button("Generate Test Paper", key="exam_btn"):
        ask_ai(f"{MASTER_PROMPT}\nGenerate a Test for {grade} {subject} Topic: {topic}. 60 questions. FOLLOW UNEB LENGTH RULES. ROTATE TOPICS: {get_all_topics(grade)}. Then generate marking guide.", "Test_Paper")

    st.subheader("2. UNEB Marking Guide Generator")
    questions = st.text_area("Paste PLE Question(s) Here", height=150)
    if st.button("Generate UNEB Marking Guide", key="marking_btn"):
        prompt = f"Act as an official UNEB PLE Examiner for {subject}. Question: {questions}\nGenerate marking guide using RULE 4. Output: Subject, Answer Key, M/A/B, Common Mistakes."
        ask_ai(prompt, "UNEB_Marking_Guide")

    st.subheader("3. Marking / Grading Assistant")
    marking_scheme = st.text_area("Paste Marking Scheme", height=100, key="mark_scheme")
    student_answers = st.text_area("Paste Student Answers", height=150, key="mark_paste")
    upload_mark = st.file_uploader("Or Upload student work", type=["txt","pdf"], key="mark_upload")
    if st.button("Mark Work Now - UNEB Style", key="mark_btn"):
        content = upload_mark.read().decode("utf-8") if upload_mark else student_answers
        prompt = f"Act as UNEB PLE Examiner for {subject}. Mark this work using RULE 4.\nSCHEME:\n{marking_scheme}\nSTUDENT:\n{content}\nOutput: Total, M/A/B Breakdown, Common Mistakes."
        ask_ai(prompt, "Marked_Work_UNEB")

    st.subheader("4. Report Card Generator")
    pupil_name = st.text_input("Pupil Name")
    scores = st.text_area("Paste scores: Subject: Score", height=100)
    if st.button("Generate Report Card", key="report_btn"):
        ask_ai(f"Generate Report Card for {pupil_name} Class {grade}. Term 2 2026. Scores:\n{scores}", "Report_Card")

    st.subheader("5. Lesson Plan Generator")
    duration = st.selectbox("Duration", ["40 minutes", "80 minutes"])
    if st.button("Generate Lesson Plan", key="lesson_btn"):
        ask_ai(f"{MASTER_PROMPT}\nGenerate NCDC 2026 Lesson Plan for {grade} {subject} Topic: {topic}. Duration: {duration}.", "Lesson_Plan")

    st.subheader("6. Scheme of Work Generator")
    if st.button("Generate Scheme of Work", key="scheme_btn"):
        ask_ai(f"Create 1-week scheme of work for {grade} {subject} Topic: {topic}. NCDC 2026 format.", "Scheme_of_Work")

st.sidebar.caption("NCDC 2026 | FULL DB RESTORED | Contact: " + CONTACT)
