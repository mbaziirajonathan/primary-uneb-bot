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

# ===================== CONFIG =====================
CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7.")

MASTER_PROMPT = """
You are TEACHERK, a Senior NCDC 2026 Uganda PLE Examiner and Master Teacher for PRIMARY P4-P7.
You think like Meta AI: flexible, deep reasoning, but you ONLY teach NCDC 2026 Uganda Primary Curriculum.

ANTI-HALLUCINATION & ACCURACY RULE - CRITICAL:
1. NEVER invent measurements. Only use measurements given in the question.
2. MATH UNITS RULE: Every final math answer MUST end with correct unit and "Therefore the... was [number][unit]"
3. ENGLISH PUNCTUATION RULE: Every sentence must end with.? or! Capital letters must be correct.
4. MARKING RULE: PUPILS LOSE MARKS FOR JUMPING STEPS AND MISSING UNITS.

MOCK PLE PAPER STRUCTURE:
SECTION A: 20 STRAIGHT QUESTIONS. Short, direct, test recall and basic skills. 1-2 marks each.
SECTION B: 30 SCENARIO-BASED QUESTIONS. Each must have a Ugandan context scenario + a clear TASK to do. 2-4 marks each. Show all working.

DIAGRAM RULE: [DIAGRAM: Topic=Triangle, Measurements="Base=8cm, Angle=50deg", Question="Construct triangle ABC"]
"""

# ===================== 2. DIAGRAM GENERATOR =====================
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
        ax.text(base/2, -0.7, f"{base} cm", ha='center'); ax.set_xlim(-2, base+2); ax.set_ylim(-2, apex_y+2)
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

# ===================== 3. FULL NCDC 2026 DB - 210+ TOPICS RESTORED =====================
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
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14); c.drawString(40, height-50, title)
    y = height - 80; c.setFont("Helvetica", 9)
    for line in content.split('\n')[:150]:
        c.drawString(40, y, line[:95]); y -= 14
        if y < 50: c.showPage(); y = height - 50; c.setFont("Helvetica", 9)
    c.save(); buffer.seek(0); return buffer

def generate_report_card_pdf(student_name, class_name, results_df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
    c.setFont("Helvetica-Bold", 16); c.drawCentredString(width/2, height-50, "TEACHERK PRIMARY SCHOOL REPORT CARD")
    c.setFont("Helvetica", 12); c.drawString(40, height-80, f"Student: {student_name}"); c.drawString(40, height-100, f"Class: {class_name}")
    c.drawString(40, height-120, f"Term: {datetime.now().strftime('%B %Y')}")
    data = [results_df.columns.tolist()] + results_df.values.tolist()
    t = Table(data, colWidths=[150, 80, 80, 200])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.grey),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),1,colors.black)]))
    t.wrapOn(c, width, height); t.drawOn(c, 40, height-300); c.save(); buffer.seek(0); return buffer

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
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject], key="topic_select") # ALL 210+ TOPICS FIT HERE

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
    st.header("MOCK PLE PAPER GENERATOR: SECTION A:20 + SECTION B:30 = 50Q")
    if st.button("Generate 50Q MOCK PLE PAPER", key="mock_btn", type="primary"):
        client = get_client()
        if client:
            prompt = f"""{MASTER_PROMPT}\nGenerate a FULL MOCK PLE PAPER for {grade} {subject} Topic: {topic}\n\nSTRICT STRUCTURE:\n**SECTION A: 20 STRAIGHT QUESTIONS [40 MARKS]**\nQ1.... Q20.\n\n**SECTION B: 30 SCENARIO-BASED QUESTIONS [60 MARKS]**\n### **Question 21: [Title]**\n[Scenario]\n**TASK:** [What to do]\n**SOLUTION:** Show all steps.\n... continue to Question 50.\n\n**MARKING GUIDE**\nProvide answers for all 50 questions. For math, answers MUST have units. For English, answers MUST be punctuated well."""
            with st.spinner("Generating 50Q Mock PLE..."):
                res = smart_groq_call(client, MASTER_PROMPT, prompt, max_tokens=4000)
                if res:
                    paper = res.choices[0].message.content; st.markdown(paper)
                    diagrams = re.findall(r'\[DIAGRAM:.*?\]', paper)
                    for d in diagrams:
                        info = parse_diagram_tag(d)
                        if info: st.image(draw_math_diagram(info.get("Topic",""), info.get("Measurements",""), info.get("Question","")), use_container_width=True)
                    st.download_button("📥 Download 50Q MOCK PLE PDF", generate_pdf(paper, f"MOCK PLE {grade} {subject}"), "mock_ple.pdf")

with tabs[4]: # ===================== ALL TEACHER TOOLS RESTORED =====================
    st.header("Teacher Tools - Automation Suite")
    st.markdown("---")
    st.subheader("1. Test / Exam Paper Generator")
    col1, col2 = st.columns(2)
    with col1: exam_type = st.selectbox("Exam Type", ["Weekly Test", "Mid Term", "End of Term", "Mock PLE"], key="exam_type")
    with col2: num_q = st.slider("Number of Questions", 10, 50, 50, key="num_q")
    if st.button("Generate Test Paper", key="exam_btn"):
        client = get_client()
        if client:
            prompt = f"{MASTER_PROMPT}\nGenerate a {exam_type} for {grade} {subject} covering {topic}. Create {num_q} questions. Section A:20 Straight. Section B:30 Scenario. Provide full marking guide with steps and units."
            with st.spinner("Generating Exam Paper..."):
                res = smart_groq_call(client, MASTER_PROMPT, prompt, max_tokens=4000)
                if res: exam = res.choices[0].message.content; st.markdown(exam)
                st.download_button("📥 Download Exam PDF", generate_pdf(exam, f"{exam_type} {grade} {subject}"), "exam.pdf", key="dl_exam")

    st.markdown("---")
    st.subheader("2. Marking / Grading Assistant")
    st.info("Upload pupils' work. TEACHERK will mark like UNEB examiner. Deducts for no units and jumped steps.")
    uploaded_file = st.file_uploader("Upload Pupils Work.txt or.pdf", type=["txt","pdf"], key="mark_upload")
    student_answers = st.text_area("Or paste student answers here", height=150, key="mark_paste")
    marking_scheme = st.text_area("Paste Marking Scheme / Answers", height=100, key="mark_scheme")
    if st.button("Mark Work Now", key="mark_btn"):
        client = get_client()
        if client and (uploaded_file or student_answers):
            content = uploaded_file.read().decode("utf-8") if uploaded_file else student_answers
            prompt = f"You are a UNEB Examiner. Mark this {grade} {subject} work strictly. Deduct 1 mark for missing units and jumped steps.\n\nMARKING SCHEME:\n{marking_scheme}\n\nSTUDENT WORK:\n{content}\n\nProvide: Total Score, Breakdown, Comments."
            with st.spinner("Marking..."):
                res = smart_groq_call(client, MASTER_PROMPT, prompt, max_tokens=2000)
                if res: marked = res.choices[0].message.content; st.markdown(marked)
                st.download_button("📥 Download Marked Report", generate_pdf(marked, "Marked Work"), "marked.pdf", key="dl_marked")

    st.markdown("---")
    st.subheader("3. Report Card Generator")
    st.info("Upload CSV with columns: Subject, Score, Grade, Remarks")
    report_file = st.file_uploader("Upload Results CSV", type=["csv"], key="report_upload")
    student_name = st.text_input("Student Name", key="student_name")
    if st.button("Generate Report Card", key="report_btn") and report_file and student_name:
        df = pd.read_csv(report_file)
        st.dataframe(df)
        pdf = generate_report_card_pdf(student_name, grade, df)
        st.download_button("📥 Download Report Card PDF", pdf, f"ReportCard_{student_name}.pdf", key="dl_report")

    st.markdown("---")
    st.subheader("4. Scheme of Work Generator")
    if st.button("Generate Scheme of Work", key="scheme_btn"):
        client = get_client()
        if client:
            prompt = f"Create a 1-week scheme of work for {grade} {subject} Topic: {topic} following NCDC 2026. Include: Topic, Competency, Learning Activities, Life Skills, Values, Assessment."
            with st.spinner("Generating..."):
                res = smart_groq_call(client, MASTER_PROMPT, prompt, max_tokens=2000)
                if res: scheme = res.choices[0].message.content; st.markdown(scheme)
                st.download_button("📥 Download Scheme PDF", generate_pdf(scheme, f"Scheme {topic}"), "scheme.pdf", key="dl_scheme")

st.sidebar.caption("NCDC 2026 Competency-Based | P4-P7 | 210+ Topics | Contact: " + CONTACT)
