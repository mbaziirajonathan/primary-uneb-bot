import streamlit as st
import io, re, json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib_venn import venn2, venn3
import hashlib
from datetime import datetime
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7.")

# ===================== MASTER PROMPT =====================
MASTER_PROMPT = """
You are an OFFICIAL UNEB PLE EXAMINER for Uganda P4-P7. Be direct and accurate.

FORMAT RULES:
A. ENGLISH: TIME 2hr15min. SEC A: 30Q Grammar + 20Q Comprehension. SEC B: 5Q Composition 10marks each. TOTAL 100
B. SCIENCE: TIME 2hr15min. SEC A: 40Q 1mark. SEC B: 15Q 4marks with a),b). TOTAL 100
C. MATH/SST/CRE/IRE: SEC A: 20Q. SEC B: 40Q a,b,c. TOTAL 60Q. IF SST THEN Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE

DIFFICULTY: P4=0Q, P5=6Q, P6=16Q, P7=18Q.
FOR MATH ONLY: If question needs a diagram, START the question with exactly: [DIAGRAM: Topic="venn2", Measurements="a=10,b=15,ab=5", Question="In a class of 40 pupils"]
SUPPORTED DIAGRAMS: Triangle, Rectangle, venn2, venn3
NO DIAGRAMS FOR OTHER SUBJECTS.
IF GENERAL QUESTION: Answer directly in 3-5 paragraphs with examples. Do not use question format.
"""

# ===================== FULL DB =====================
PRIMARY_DB = {
  "PRIMARY_4": {"Mathematics": [{"topic": "Set Concepts"}, {"topic": "Whole Numbers"}], "English Language": [{"topic": "Comprehension"}], "Integrated Science": [{"topic": "Plant Life"}], "Social Studies (SST)": [{"topic": "Our Sub-County"}], "Christian Religious Education (CRE)": [{"topic": "God's Creation"}], "Islamic Religious Education (IRE)": [{"topic": "Pillars of Islam"}]},
  "PRIMARY_5": {"Mathematics": [{"topic": "Sets Venn"}, {"topic": "Decimals"}], "English Language": [{"topic": "Grammar"}], "Integrated Science": [{"topic": "Soil"}], "Social Studies (SST)": [{"topic": "Uganda Geography"}], "Christian Religious Education (CRE)": [{"topic": "Birth of Jesus"}], "Islamic Religious Education (IRE)": [{"topic": "Pillars of Iman"}]},
  "PRIMARY_6": {"Mathematics": [{"topic": "Ratios"}, {"topic": "Speed"}], "English Language": [{"topic": "Passive Voice"}], "Integrated Science": [{"topic": "Energy"}], "Social Studies (SST)": [{"topic": "East Africa"}], "Christian Religious Education (CRE)": [{"topic": "Holy Spirit"}], "Islamic Religious Education (IRE)": [{"topic": "Hajj"}]},
  "PRIMARY_7": {"Mathematics": [{"topic": "Sets 3 Categories"}, {"topic": "Business Math"}], "English Language": [{"topic": "Letter Writing"}, {"topic": "Composition"}], "Integrated Science": [{"topic": "Machines"}, {"topic": "Environment"}], "Social Studies (SST)": [{"topic": "Africa"}], "Christian Religious Education (CRE)": [{"topic": "Marriage"}], "Islamic Religious Education (IRE)": [{"topic": "Shariah"}]}
}
PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}
def get_all_topics(grade): return [t["topic"] for sub in PRIMARY_DB[f"PRIMARY_{grade[1:]}"].values() for t in sub]

# ===================== DIAGRAM GENERATOR =====================
def draw_math_diagram(d_type, measurements, q_text):
    try:
        fig, ax = plt.subplots(figsize=(5.5, 4.5)); plt.axis('off')
        ax.set_title(f"{q_text}", fontsize=10, fontweight='bold', pad=10, wrap=True)
        data = measurements.lower() if measurements else ""
        def sf(s, d):
            try: return float(re.findall(r"[\d.]+", s)[0])
            except: return d
        unit = "cm" if "cm" in data else ""

        if "venn2" in d_type.lower():
            A = sf(data.split("a=")[1], 10) if "a=" in data else 10
            B = sf(data.split("b=")[1], 15) if "b=" in data else 15
            AB = sf(data.split("ab=")[1], 5) if "ab=" in data else 5
            v = venn2(subsets = (A-AB, B-AB, AB), set_labels = ('Set A', 'Set B'))
            for txt in v.set_labels: txt.set_fontsize(9)
        elif "venn3" in d_type.lower():
            v = venn3(subsets = (4,4,2,3,2,2,1), set_labels = ('A', 'B', 'C'))
        elif "triangle" in d_type.lower():
            base = sf(data.split("base=")[1], 8.0) if "base=" in data else 8.0
            height = sf(data.split("height=")[1], base*0.7) if "height=" in data else base*0.7
            triangle = patches.Polygon([(0, 0), (base, 0), (base/2, height)], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(triangle)
            ax.text(base/2, -0.5, f"Base = {base}{unit}", ha='center', fontweight='bold')
            ax.set_xlim(-2, base+2); ax.set_ylim(-2, height+2)
        plt.tight_layout(); buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight'); buf.seek(0); plt.close(fig); return buf
    except Exception as e:
        st.warning(f"Diagram error: {e}")
        return None

def parse_tag(tag_str):
    try:
        tag_str = tag_str.replace("Topic=", '"Topic":').replace("Measurements=", '"Measurements":').replace("Question=", '"Question":')
        return json.loads("{" + tag_str + "}")
    except: return None

def render_with_diagrams(text, subject):
    if not text:
        st.error("No response from AI. Try again.")
        return

    # If no question format, just print as normal text - fixes General Search and Theory
    if "### **Question" not in text:
        st.markdown(text)
        return

    parts = re.split(r'(### \*\*Question \d+:)', text)
    for i in range(0, len(parts), 2):
        header = parts[i] if i < len(parts) else ""
        question = parts[i+1] if i+1 < len(parts) else ""

        diagram_info = None
        if "[DIAGRAM:" in header and subject == "Mathematics":
            tag = header.split("[DIAGRAM:")[1].split("]")[0]
            diagram_info = parse_tag(tag)

        if diagram_info and diagram_info.get("Topic"):
            img = draw_math_diagram(diagram_info["Topic"], diagram_info.get("Measurements",""), diagram_info.get("Question","Question"))
            if img: st.image(img, use_container_width=True)

        clean_header = header.split("[DIAGRAM:")[0]
        st.markdown(clean_header + question)

# ===================== GROQ CALL =====================
if "cache" not in st.session_state: st.session_state.cache = {}
def smart_groq_call(client, system_prompt, user_prompt):
    cache_key = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
    if cache_key in st.session_state.cache: return st.session_state.cache[cache_key]
    if len(user_prompt) > 2500: user_prompt = user_prompt[:2500]
    models_to_try = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    last_error = None
    for model in models_to_try:
        try:
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.4, max_tokens=1800, timeout=60)
            if res and res.choices[0].message.content:
                st.session_state.cache[cache_key] = res; return res
        except RateLimitError as e: last_error = e; continue
        except Exception as e: last_error = e; continue
    if last_error: st.error(f"AI Error: {last_error}")
    return None

def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("GROQ_API_KEY missing in Secrets"); return None

def generate_pdf(content, title, subject, grade):
    try:
        buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
        year = datetime.now().year
        c.setFont("Helvetica-Bold", 12); c.drawCentredString(width/2, height-40, f"UNEB PRIMARY {grade[1:]} {subject.upper()} {year}")
        c.setFont("Helvetica", 10); c.drawCentredString(width/2, height-55, "Time Allowed: 2 hours 15 minutes")
        c.setFont("Helvetica", 9)
        c.drawString(40, height-75, "Candidate's name: ________________________________")
        c.drawString(40, height-90, "School name: ____________________________________")
        y = height - 120; c.setFont("Helvetica", 9)
        for line in content.split('\n')[:500]:
            if y < 50: c.showPage(); y = height - 50
            c.drawString(40, y, line[:95]); y -= 14
        c.save(); buffer.seek(0); return buffer
    except: return None

# ===================== PASSWORD =====================
def check_password():
    APP_PW = st.secrets.get("PRIMARY_APP_PASSWORD", "PRIMARY2026")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "ADMIN256")
    if "password_correct" not in st.session_state:
        st.title("🔒 TEACHERK PRIMARY 2026 NCDC")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == APP_PW: st.session_state["user_type"] = "Pupil"; st.session_state["password_correct"] = True; st.rerun()
            elif pw == ADMIN_PW: st.session_state["user_type"] = "Teacher"; st.session_state["password_correct"] = True; st.rerun()
            else: st.error("Wrong password")
        st.stop()
check_password()

# ===================== MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026 NCDC")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"])
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])

tabs = st.tabs(["🔍 General Search", "📖 Theory", "📝 HARD MOCK", "➗ Math Work", "👩‍🏫 Teacher Tools"])

def ask_ai(prompt, dl_name):
    client = get_client()
    if not client: return
    with st.spinner("Generating..."):
        res = smart_groq_call(client, MASTER_PROMPT, prompt)
    if res:
        answer = res.choices[0].message.content
        render_with_diagrams(answer, subject) # FIXED RENDERER
        pdf = generate_pdf(answer, dl_name, subject, grade)
        if pdf: st.download_button("📥 Download PDF", pdf, f"{dl_name}.pdf")
    else:
        st.error("AI Busy. Please wait 1 minute and retry.")
    st.markdown("---")
    st.file_uploader("Upload student work for marking", type=["txt","pdf"], key=f"upload_{dl_name}")

with tabs[0]: # FIXED: Now answers directly
    st.header("🔍 General Search - Ask Anything")
    q = st.text_input("Ask Anything", placeholder="e.g. Explain the water cycle for P5")
    if st.button("Ask", type="primary") and q:
        ask_ai(f"You are a smart UNEB tutor for {grade} {subject}. The student asks: {q}. Answer directly in simple language with 2 Ugandan examples.", "answer_general")

with tabs[1]: # FIXED: Now shows theory
    st.header(f"📖 Theory: {grade} {subject}")
    if st.button("Generate Full Theory Notes", type="primary"):
        ask_ai(f"Generate detailed NCDC 2026 theory notes for {grade} {subject} Topic: {topic}. Format: Definition, Key Points, 3 Examples, Ugandan Example.", f"Theory_{topic}")

with tabs[2]:
    st.header("📝 HARD COMBINED MOCK PLE")
    is_english = subject == "English Language"
    is_science = subject == "Integrated Science"
    if is_english: st.info("ENGLISH: Sec A 50Q, Sec B 5Q. Time: 2hr 15min")
    elif is_science: st.info("SCIENCE: Sec A 40Q, Sec B 15Q. Time: 2hr 15min")
    else: st.info("MATH/SST: Sec A 20Q, Sec B 40Q")

    if st.button("Generate HARD COMBINED MOCK PLE", type="primary"):
        if is_english:
            prompt = f"{MASTER_PROMPT}\nGenerate HARD UNEB PLE MOCK for {grade} ENGLISH. TIME: 2 hours 15 minutes. SECTION A: Sub-Section I 30Q. Sub-Section II 20Q. SECTION B: 5Q Composition. ROTATE TOPICS: {get_all_topics(grade)}."
        elif is_science:
            prompt = f"{MASTER_PROMPT}\nGenerate HARD UNEB PLE MOCK for {grade} INTEGRATED SCIENCE. TIME: 2 hours 15 minutes. SECTION A: 40Q. SECTION B: 15Q with a), b). ROTATE TOPICS: {get_all_topics(grade)}."
        else:
            sst_rule = "FOR SST: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE" if subject == "Social Studies (SST)" else ""
            force_venn = "For Mathematics Sets topic, you MUST include 2 questions with [DIAGRAM: Topic=\"venn2\"]" if subject=="Mathematics" else ""
            prompt = f"{MASTER_PROMPT}\nGenerate HARD MOCK for {grade} {subject}. SECTION A 20Q. SECTION B 40Q. {sst_rule} {force_venn} ROTATE TOPICS: {get_all_topics(grade)}."
        ask_ai(prompt, f"HARD_MOCK_{subject}")

with tabs[3]:
    st.header("➗ Mathematics Worked Examples")
    if subject == "Mathematics":
        if st.button("Generate 7 Hard Worked Examples With Diagrams", type="primary"):
            ask_ai(f"{MASTER_PROMPT}\nGenerate 7 HARD P6-P7 math questions for {grade}. For at least 2 questions on Sets, use [DIAGRAM: Topic=\"venn2\"] or [DIAGRAM: Topic=\"venn3\"]. For 1 question use Triangle. Each must have a),b). Then UNEB MARKING GUIDE.", f"Math_Work_{grade}")
    else: st.info("Select Mathematics subject.")

with tabs[4]: # FIXED: All 6 tools now work
    st.header("👩‍🏫 Teacher Tools")
    st.subheader("1. Test Paper Generator")
    if st.button("Generate Test Paper"):
        ask_ai(f"{MASTER_PROMPT}\nGenerate a full Test for {grade} {subject} Topic: {topic}. 60Q or per subject format.", "Test_Paper")

    st.subheader("2. UNEB Marking Guide Generator")
    questions = st.text_area("Paste PLE Question(s) Here", height=150)
    if st.button("Generate UNEB Marking Guide"):
        ask_ai(f"Act as UNEB Examiner for {subject}. Question: {questions}\nOutput: Answer Key, Marking Guide, Common Mistakes.", "Marking_Guide")

    st.subheader("3. Marking / Grading Assistant")
    marking_scheme = st.text_area("Paste Marking Scheme", height=100)
    student_answers = st.text_area("Paste Student Answers", height=150)
    if st.button("Mark Work Now"):
        ask_ai(f"Act as UNEB Examiner for {subject}. Mark this work.\nSCHEME:\n{marking_scheme}\nSTUDENT:\n{student_answers}\nGive total, breakdown, feedback.", "Marked_Work")

    st.subheader("4. Report Card Generator")
    pupil_name = st.text_input("Pupil Name")
    scores = st.text_area("Paste scores: Subject: Score")
    if st.button("Generate Report Card"):
        ask_ai(f"Generate Report Card for {pupil_name} Class {grade}. Term 2 {datetime.now().year}. Scores:\n{scores}", "Report_Card")

    st.subheader("5. Lesson Plan Generator")
    if st.button("Generate Lesson Plan"):
        ask_ai(f"Generate NCDC 2026 Lesson Plan for {grade} {subject} Topic: {topic}. Duration: 40 minutes. Include Objectives, Materials, Procedure.", "Lesson_Plan")

    st.subheader("6. Scheme of Work Generator")
    if st.button("Generate Scheme of Work"):
        ask_ai(f"Create 1-week scheme of work for {grade} {subject} Topic: {topic}. NCDC 2026 format with Competencies.", "Scheme_of_Work")

st.sidebar.caption(f"NCDC 2026 | Contact: {CONTACT}")
