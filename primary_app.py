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

SYSTEM_PROMPT = """
You are TEACHERK, a Senior NCDC 2026 Uganda PLE Examiner and Master Teacher for PRIMARY P4-P7.
You teach like a real classroom teacher in Uganda using Competency-Based Curriculum CBC.

CRITICAL UNEB 2026 MARKING RULE: PUPILS LOSE MARKS IF THEY JUMP STEPS.
YOU MUST SHOW EVERY SINGLE CALCULATION STEP LIKE A PUPIL WRITING IN PLE EXAM.

TONE: Friendly, patient, Ugandan. Use local examples: boda boda, market, shamba, school, posho, beans.

MANDATORY MATH WORKING FORMAT - USE FOR ALL 7 SCENARIOS:

### **SCENARIO 1: [Ugandan Title]**
Write a 3-4 sentence Ugandan scenario with real numbers.

**COMPETENCY TASK:** What the learner must be able to DO by the end.

**QUESTION 1:** [2 marks]

**FULL WORKING METHOD 1: FORMULA/CONCEPT METHOD - SHOW ALL STEPS**
Step 1: Write down what is given
        Given:...
Step 2: Write the formula/concept to use
        Formula:...
Step 3: Substitute the values into the formula
        Therefore:...
Step 4: Do the calculation step by step. DO NOT JUMP.
        =...
        =...
Step 5: State the answer WITH CORRECT UNITS AND UNEB CLOSING
        Answer: 3kg or 3m or 3cm or 3L
        Therefore the budget needed was ugsh300,000

**FULL WORKING METHOD 2: LOGICAL/STORY METHOD - SHOW ALL STEPS**
Step 1: Explain the problem in words
Step 2: Break it down step by step
Step 3: Calculate each part
Step 4: Combine to get final answer WITH UNITS AND UNEB CLOSING
        Final Answer: 3kg
        Therefore the budget needed was ugsh300,000

---
REPEAT FOR SCENARIO 2, 3, 4, 5, 6, 7. ALL DIFFERENT UGANDA CONTEXTS.

### **PART 8: COMMON MISTAKES & UNEB EXAM TIPS**
1. Mistake 1: Forgetting to write units. PLE penalty: -1 mark
2. Mistake 2: Jumping steps. PLE penalty: -1 mark per missing step
3. Mistake 3: Wrong units e.g writing m instead of cm
4. TRICK: "Always end with 'Therefore the...' and box your final answer with units"

### **PART 9: QUICK PRACTICE FOR PUPILS**
Give 3 more questions. Tell them "Show all working and units. End with Therefore the..."

UNIT RULES - CRITICAL FOR PLE:
Money=ugsh, Mass=kg/g, Length=cm/m/km, Capacity=L/ml, Time=s/min/hr, Area=m2/cm2, Volume=m3/cm3, Speed=km/h
CLOSING RULE: End each scenario with "Therefore the [answer] was [number][unit]".

NEW: CONSTRUCTION & ACCURATE DIAGRAM RULES FOR UNEB NCDC 2026 - MANDATORY
When the question involves Geometry, Angles, Area, Triangle, Circle, Sector, Square, Rectangle, Rhombus, Kite, Trapezium, Polygon, Hexagon, Cube, Cone, Cylinder, Construction, you MUST do 3 things:

A. LIST UNEB CONSTRUCTION SET REQUIREMENTS FIRST:
1. A well calibrated 30cm ruler
2. A pair of compasses
3. A pair of dividers
4. A protractor 0-180 degrees
5. A sharp HB pencil and eraser
6. Plain paper

B. STEP BY STEP CONSTRUCTION GUIDE:
Teach exactly like in class:
Step 1: Sketch: Draw a rough freehand sketch and label all parts.
Step 2: Construction: Using ruler, draw base line AB =...cm
Step 3: Using compass, place at A, radius =...cm, draw arc.
Step 4: Using protractor, measure... degrees from AB. For angles: 45deg, 60deg, 90deg, 80deg, 120deg
Step 5: Join points. Label all sides, angles with arcs and measurements.

C. DIAGRAM TAG: Output this exact tag at the end of the response:
[DIAGRAM: Topic=Triangle, Measurements="Base=8cm, Angle=50deg", Question="Construct isosceles triangle"]
[DIAGRAM: Topic=Square, Measurements="Width=5cm", Question="Construct square"]
[DIAGRAM: Topic=Rectangle, Measurements="Length=8cm, Height=4cm", Question="Draw rectangle"]
[DIAGRAM: Topic=Rhombus, Measurements="Width=6cm, Height=5cm", Question="Construct rhombus"]
[DIAGRAM: Topic=Kite, Measurements="Width=8cm, Height=6cm", Question="Draw kite"]
[DIAGRAM: Topic=Trapezium, Measurements="Base1=10cm, Base2=6cm, Height=4cm", Question="Draw trapezium"]
[DIAGRAM: Topic=Polygon, Measurements="Sides=6, Radius=4cm", Question="Construct regular hexagon"]
[DIAGRAM: Topic=Circle, Measurements="Radius=3cm", Question="Draw circle"]
[DIAGRAM: Topic=Cone, Measurements="Radius=2cm, Height=5cm", Question="Draw net of cone"]
[DIAGRAM: Topic=Cylinder, Measurements="Radius=2cm, Height=6cm", Question="Draw net of cylinder"]
[DIAGRAM: Topic=Cube, Measurements="Side=3cm", Question="Draw net of cube"]
[DIAGRAM: Topic=Angle, Measurements="Angle=60deg", Question="Construct 60 degree angle"]
[DIAGRAM: Topic=Venn, Measurements="A=20, B=15, AB=5", Question="Venn diagram"]
[DIAGRAM: Topic=Bar, Measurements="Apples:10, Oranges:15", Question="Bar graph"]

Your job is to teach, not just answer. Always follow NCDC 2026 Competency-Based approach.
"""

# ===================== 2. DIAGRAM GENERATOR =====================
def draw_math_diagram(d_type, measurements, question_text):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    plt.axis('off')
    ax.set_title(f"{d_type}\n{question_text}", fontsize=12, pad=20)
    data = measurements.lower() if measurements else ""

    def safe_float(s, default):
        try: return float(re.findall(r"[\d.]+", s)[0])
        except: return default
    def safe_int(s, default):
        try: return int(re.findall(r"\d+", s)[0])
        except: return default

    if d_type and "triangle" in d_type.lower():
        base = 8.0
        if "base=" in data: base = safe_float(data, 8.0)
        angle_deg = 50.0
        if "angle=" in data: angle_deg = safe_float(data, 50.0)
        angle_rad = math.radians(angle_deg); apex_x = base / 2; apex_y = (base / 2) * math.tan(angle_rad) if angle_deg < 90 else base
        side_len = math.sqrt(apex_x**2 + apex_y**2); A, B, C = (0, 0), (base, 0), (apex_x, apex_y)
        triangle = patches.Polygon([A, B, C], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(triangle)
        ax.text(A[0]-0.5, A[1]-0.5, "A"); ax.text(B[0]+0.5, B[1]-0.5, "B"); ax.text(C[0], C[1]+0.5, "C")
        ax.text(base/2, -0.5, f"{base}cm", ha='center'); ax.text(apex_x/2 - 0.3, apex_y/2, f"{side_len:.1f}cm", ha='right'); ax.text((apex_x+base)/2 + 0.3, apex_y/2, f"{side_len:.1f}cm", ha='left')
        arc = patches.Arc(A, 1.5, 1.5, theta1=0, theta2=angle_deg, color='red', linewidth=1.5); ax.add_patch(arc); ax.text(1, 0.3, f"{angle_deg}°", color='red')
        ax.set_xlim(-2, base+2); ax.set_ylim(-2, apex_y+2)
    elif d_type and any(x in d_type.lower() for x in ["square", "rectangle", "rhombus", "kite"]):
        w = 6.0; h = 4.0
        if "width=" in data: w = safe_float(data, 6.0)
        if "length=" in data: w = safe_float(data, 6.0)
        if "height=" in data: h = safe_float(data, 4.0)
        if "square" in d_type.lower(): h = w
        if "rhombus" in d_type.lower(): offset = w * 0.3; A, B, C, D = (offset, 0), (w+offset, 0), (w, h), (0, h)
        elif "kite" in d_type.lower(): A, B, C, D = (w/2, 0), (w, h/2), (w/2, h), (0, h/2)
        else: A, B, C, D = (0, 0), (w, 0), (w, h), (0, h)
        if "square" in d_type.lower() or "rectangle" in d_type.lower(): A, B, C, D = (0, 0), (w, 0), (w, h), (0, h)
        poly = patches.Polygon([A, B, C, D], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(poly)
        ax.text(A[0]-0.5, A[1]-0.5, "A"); ax.text(B[0]+0.2, B[1]-0.5, "B"); ax.text(C[0]+0.2, C[1]+0.2, "C"); ax.text(D[0]-0.5, D[1]+0.2, "D")
        ax.text(w/2, -0.5, f"{w}cm", ha='center'); ax.text(-0.8, h/2, f"{h}cm", va='center', rotation=90)
        ax.set_xlim(-2, w+2); ax.set_ylim(-2, h+2)
    elif d_type and "circle" in d_type.lower():
        r = 3.0
        if "radius=" in data: r = safe_float(data, 3.0)
        circle = patches.Circle((0, 0), r, fill=False, edgecolor='black', lw=2); ax.add_patch(circle)
        ax.text(-0.4, -0.4, 'O'); ax.text(r/2, -0.5, f'{r} cm', ha='center'); ax.set_xlim(-r-1, r+1); ax.set_ylim(-r-1, r+1)
    elif d_type and "angle" in d_type.lower():
        angle = 60
        if "angle=" in data: angle = safe_float(data, 60)
        ax.plot([0, 4], [0, 0], 'k-', lw=2)
        end_x = 3 * math.cos(math.radians(angle)); end_y = 3 * math.sin(math.radians(angle))
        ax.plot([0, end_x], [0, end_y], 'k-', lw=2)
        arc = patches.Arc((0,0), 1.5, 1.5, theta1=0, theta2=angle, color='red', lw=2); ax.add_patch(arc)
        ax.text(0.8, 0.2, f"{angle}°", color='red', fontsize=12); ax.set_xlim(-1, 4); ax.set_ylim(-1, 4)
    elif d_type and "bar" in d_type.lower():
        labels = []; values = []
        for item in data.split(","):
            if ":" in item:
                k,v = item.split(":"); labels.append(k.strip().title()); values.append(safe_int(v, 0))
        if labels:
            ax.bar(labels, values, color='teal'); ax.set_ylabel("Frequency")
            for i,v in enumerate(values): ax.text(i, v+0.5, str(v), ha='center'); plt.xticks(rotation=15)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

def parse_diagram_tag(text):
    if "[DIAGRAM:" not in text: return None
    try:
        tag = text.split("[DIAGRAM:")[1].split("]")[0]; parts = {}
        for item in tag.split(","):
            if "=" in item:
                k,v = item.split("=",1); parts[k.strip()] = v.strip().strip('"')
        return parts if parts.get("Topic") else None
    except: return None

# ===================== 3. FULL NCDC 2026 DB =====================
PRIMARY_DB = {
  "PRIMARY_4": {"Mathematics": [{"topic": "Set Concepts", "competency": "Identify, name and form sets", "scenario": "Grouping pupils in class"}], "English Language": [], "Integrated Science": [], "Social Studies (SST)": [], "Christian Religious Education (CRE)": [], "Islamic Religious Education (IRE)": []},
  "PRIMARY_5": {"Mathematics": [{"topic": "Set Theory (Union, Intersection, Venn Diagrams)", "competency": "Solve problems using Venn diagrams", "scenario": "Pupils who like math and english"}], "English Language": [], "Integrated Science": [], "Social Studies (SST)": [], "Christian Religious Education (CRE)": [], "Islamic Religious Education (IRE)": []},
  "PRIMARY_6": {"Mathematics": [{"topic": "Advanced Set Operations", "competency": "Solve 3-set problems", "scenario": "Pupils in sports"}], "English Language": [], "Integrated Science": [], "Social Studies (SST)": [], "Christian Religious Education (CRE)": [], "Islamic Religious Education (IRE)": []},
  "PRIMARY_7": {"Mathematics": [{"topic": "Advanced Sets (Three Categories/Word Problems)", "competency": "Solve 3-set word problems", "scenario": "Pupils in 3 subjects"}], "English Language": [], "Integrated Science": [], "Social Studies (SST)": [], "Christian Religious Education (CRE)": [], "Islamic Religious Education (IRE)": []}
}
PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}

def get_topic_data(grade, subject, topic_name):
    grade_num = grade.replace("P","")
    grade_key = f"PRIMARY_{grade_num}"
    if grade_key in PRIMARY_DB and subject in PRIMARY_DB[grade_key]:
        for t in PRIMARY_DB[grade_key][subject]:
            if t["topic"] == topic_name: return t
    return {"topic": topic_name, "competency": "NCDC Competency", "scenario": "Ugandan Context"}

def smart_groq_call(client, system_prompt, user_prompt, max_tokens=2000):
    models_to_try = [MODEL_CHOICE, "llama-3.1-8b-instant", "llama-3.1-70b-versatile"]
    models_to_try = list(dict.fromkeys(models_to_try))
    for model in models_to_try:
        try:
            tokens = max_tokens if "70b" in model else 1024
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.2, max_tokens=tokens)
            if model!= MODEL_CHOICE: st.warning(f"⚠️ Switched to {model} because {MODEL_CHOICE} was busy.")
            return res
        except RateLimitError: continue
        except Exception: continue
    st.error("All Groq models busy. Wait 1 minute."); return None

def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("Add GROQ_API_KEY in Streamlit Secrets"); return None

def generate_pdf(content, title):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
    c.setFont("Helvetica-Bold", 14); c.drawString(40, height-50, title); y = height - 80; c.setFont("Helvetica", 9)
    for line in content.split('\n')[:80]: c.drawString(40, y, line[:95]); y -= 14
    if y < 50: c.showPage(); y = height - 50
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
st.title("🐢 TEACHERK PRIMARY 2026 NCDC")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"], key="grade_select")
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()), key="subject_select")
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject], key="topic_select")

st.sidebar.header("⚙️ Settings")
MODEL_CHOICE = st.sidebar.selectbox("AI Brain", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama-3.1-70b-versatile"], index=0)

topic_data = get_topic_data(grade, subject, topic)
st.subheader(f"{grade} {subject}: {topic_data['topic']}")

tabs = st.tabs(["AI Chat + Voice", "Theory + Practicals", "Quiz + Evaluation", "Math Work", "Teacher Tools"])

with tabs[0]:
    st.header("Ask TeacherK NCDC - 7 Scenarios")
    q = st.text_input("Type question here", key="chat_q")
    if st.button("Ask", key="ask_btn") and q:
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\n\nLevel: {grade}, Subject: {subject}, Topic: {topic_data['topic']}\n\nStudent Request: {q}\n\nCRITICAL: SHOW EVERY SINGLE STEP."
            with st.spinner("TeacherK is thinking..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                if res: answer = res.choices[0].message.content; st.markdown(answer)
                diagram_info = parse_diagram_tag(answer)
                if diagram_info: st.image(draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question","")), use_container_width=True)
                st.download_button("📥 Download Lesson PDF", generate_pdf(answer, f"{grade} {subject} {topic_data['topic']}"), "lesson.pdf", key="dl_lesson")

with tabs[1]:
    st.header("Theory + Practical Activities")
    if st.button("Generate Theory + 7 Practicals", key="theory_btn"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nTeach {grade} {subject} Topic: {topic_data['topic']}. Give Theory + 7 Uganda practical activities. Show steps."
            with st.spinner("Generating..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                if res: theory = res.choices[0].message.content; st.markdown(theory)
                st.download_button("📥 Download Theory PDF", generate_pdf(theory, f"Theory {topic_data['topic']}"), "theory.pdf", key="dl_theory")

with tabs[2]:
    st.header("Quiz + Evaluation")
    if st.button("Generate 7 Scenario Quiz", key="quiz_btn"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nCreate 7 scenario-based quiz questions for {grade} {subject} Topic: {topic_data['topic']}. Provide answers with full steps and units."
            with st.spinner("Generating Quiz..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=2000)
                if res: quiz = res.choices[0].message.content; st.markdown(quiz)
                st.download_button("📥 Download Quiz PDF", generate_pdf(quiz, f"Quiz {topic_data['topic']}"), "quiz.pdf", key="dl_quiz")

with tabs[3]:
    st.header("Mathematics Work Page")
    if subject == "Mathematics":
        if st.button("Generate 7 Scenario Worked Examples", key="mathwork_btn", type="primary"):
            client = get_client()
            if client:
                prompt = f"{SYSTEM_PROMPT}\nGenerate 7 fully worked scenario-based math questions for {grade} {subject} Topic: {topic_data['topic']}. EACH QUESTION MUST SHOW EVERY STEP."
                with st.spinner("Generating Math Work..."):
                    res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                    if res: math_work = res.choices[0].message.content; st.markdown(math_work)
                    st.download_button("📥 Download Math Work PDF", generate_pdf(math_work, f"Math Work {topic_data['topic']}"), "math_work.pdf", key="dl_math")
    else: st.info("Select Mathematics subject to use.")

with tabs[4]:
    st.header("Teacher Tools - Automation Suite")
    st.markdown("---")

    st.subheader("1. Test / Exam Paper Generator")
    col1, col2 = st.columns(2)
    with col1: exam_type = st.selectbox("Exam Type", ["Weekly Test", "Mid Term", "End of Term", "Mock PLE"], key="exam_type")
    with col2: num_q = st.slider("Number of Questions", 5, 20, 10, key="num_q")
    if st.button("Generate Test Paper", key="exam_btn"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nGenerate a {exam_type} for {grade} {subject} covering {topic_data['topic']}. Create {num_q} questions. Provide full marking guide with steps and marks. Use UNEB format."
            with st.spinner("Generating Exam Paper..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                if res: exam = res.choices[0].message.content; st.markdown(exam)
                st.download_button("📥 Download Exam PDF", generate_pdf(exam, f"{exam_type} {grade} {subject}"), "exam.pdf", key="dl_exam")

    st.markdown("---")
    st.subheader("2. Marking / Grading Assistant")
    st.info("Upload pupils' scanned work or type answers. TEACHERK will mark like UNEB examiner.")
    uploaded_file = st.file_uploader("Upload Pupils Work.txt or.pdf", type=["txt","pdf"], key="mark_upload")
    student_answers = st.text_area("Or paste student answers here", height=150, key="mark_paste")
    marking_scheme = st.text_area("Paste Marking Scheme / Answers", height=100, key="mark_scheme")
    if st.button("Mark Work Now", key="mark_btn"):
        client = get_client()
        if client and (uploaded_file or student_answers):
            content = uploaded_file.read().decode("utf-8") if uploaded_file else student_answers
            prompt = f"You are a UNEB Examiner. Mark this {grade} {subject} work strictly. Deduct 1 mark for missing units and jumped steps.\n\nMARKING SCHEME:\n{marking_scheme}\n\nSTUDENT WORK:\n{content}\n\nProvide: Total Score, Breakdown per question, Comments, and What to improve."
            with st.spinner("Marking..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=2000)
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
            prompt = f"Create a 1-week scheme of work for {grade} {subject} Topic: {topic_data['topic']} following NCDC 2026. Include Competency, Activities, Assessment."
            with st.spinner("Generating..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=2000)
                if res: scheme = res.choices[0].message.content; st.markdown(scheme)
                st.download_button("📥 Download Scheme PDF", generate_pdf(scheme, f"Scheme {topic_data['topic']}"), "scheme.pdf", key="dl_scheme")

st.sidebar.caption("NCDC 2026 Competency-Based | P4-P7 | Contact: " + CONTACT)
