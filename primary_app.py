import streamlit as st
import io, re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib_venn import venn2, venn3
import hashlib
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7.")

# ===================== MASTER PROMPT =====================
MASTER_PROMPT = """
You are an OFFICIAL UNEB PLE EXAMINER for Uganda P4-P7. Be SMART, DIRECT, and ACCURATE like ChatGPT.
RULE 1: SECTION A = 20Q, 1 line, 8-12 words. SECTION B = 40Q, 3-4 lines scenario task, with a), b), c).
RULE 2: DIFFICULTY: P4=0Q, P5=6Q, P6=16Q, P7=18Q. Total 60Q.
RULE 3: IF SUBJECT=SST THEN SECTION B MUST BE: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE
RULE 4: FOR MATH ONLY: If question needs a diagram, START with [DIAGRAM: Topic="Triangle", Measurements="base=8cm,height=6cm"] on its own line BEFORE the question text.
RULE 5: FOR SETS: Use [DIAGRAM: Topic="venn2", Measurements="a=10,b=15,ab=5"] or [DIAGRAM: Topic="venn3", Measurements="..."]
RULE 6: NEVER put diagram tags for English, Science, SST, CRE, IRE.
RULE 7: ANSWER DIRECTLY. If user asks 1 question, answer that 1 question. If user asks for Mock, generate full Mock.
"""

# ===================== FULL DB RESTORED =====================
PRIMARY_DB = {
  "PRIMARY_4": {"Mathematics": [{"topic": "Set Concepts"}, {"topic": "Whole Numbers"}, {"topic": "Fractions"}, {"topic": "Measures"}], "English Language": [{"topic": "Comprehension"}], "Integrated Science": [{"topic": "Plant Life"}, {"topic": "Human Body"}], "Social Studies (SST)": [{"topic": "Our Sub-County"}], "Christian Religious Education (CRE)": [{"topic": "God's Creation"}], "Islamic Religious Education (IRE)": [{"topic": "Pillars of Islam"}]},
  "PRIMARY_5": {"Mathematics": [{"topic": "Sets Venn"}, {"topic": "LCM GCF"}, {"topic": "Decimals"}], "English Language": [{"topic": "Grammar Tenses"}], "Integrated Science": [{"topic": "Soil"}, {"topic": "Human Body Systems"}], "Social Studies (SST)": [{"topic": "Uganda Geography"}], "Christian Religious Education (CRE)": [{"topic": "Birth of Jesus"}], "Islamic Religious Education (IRE)": [{"topic": "Pillars of Iman"}]},
  "PRIMARY_6": {"Mathematics": [{"topic": "Ratios"}, {"topic": "Speed"}, {"topic": "Volume"}], "English Language": [{"topic": "Passive Voice"}], "Integrated Science": [{"topic": "Energy"}, {"topic": "Diseases"}], "Social Studies (SST)": [{"topic": "East Africa"}], "Christian Religious Education (CRE)": [{"topic": "Holy Spirit"}], "Islamic Religious Education (IRE)": [{"topic": "Hajj"}]},
  "PRIMARY_7": {"Mathematics": [{"topic": "Sets 3 Categories"}, {"topic": "Business Math"}, {"topic": "Graphs"}], "English Language": [{"topic": "Letter Writing"}], "Integrated Science": [{"topic": "Machines"}, {"topic": "Environment"}], "Social Studies (SST)": [{"topic": "Africa"}], "Christian Religious Education (CRE)": [{"topic": "Marriage"}], "Islamic Religious Education (IRE)": [{"topic": "Shariah"}]}
}
PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}
def get_all_topics(grade): return [t["topic"] for sub in PRIMARY_DB[f"PRIMARY_{grade[1:]}"].values() for t in sub]

# ===================== DIAGRAM GENERATOR - FIXED =====================
def draw_math_diagram(d_type, measurements, q_text):
    try:
        fig, ax = plt.subplots(figsize=(5, 4.5)); plt.axis('off')
        ax.set_title(f"{q_text}", fontsize=10, fontweight='bold', pad=10, wrap=True) # LABEL ON TOP
        data = measurements.lower() if measurements else ""
        def sf(s, d):
            try: return float(re.findall(r"[\d.]+", s)[0])
            except: return d
        unit = "cm" if "cm" in data else "m" if "m" in data else ""

        if d_type and "venn2" in d_type.lower():
            A = sf(data.split("a=")[1], 10) if "a=" in data else 10
            B = sf(data.split("b=")[1], 15) if "b=" in data else 15
            AB = sf(data.split("ab=")[1], 5) if "ab=" in data else 5
            v = venn2(subsets = (A-AB, B-AB, AB), set_labels = ('Set A', 'Set B'))
            v.get_patch_by_id('10').set_color('lightblue'); v.get_patch_by_id('01').set_color('lightgreen')
            ax.set_title(f"{q_text}\nA={A}{unit}, B={B}{unit}, A∩B={AB}{unit}", fontsize=9)

        elif d_type and "venn3" in d_type.lower():
            v = venn3(subsets = (4,4,2,3,2,2,1), set_labels = ('Set A', 'Set B', 'Set C'))
            ax.set_title(f"{q_text}\n3-Set Venn Diagram", fontsize=9)

        elif d_type and "triangle" in d_type.lower():
            base = sf(data.split("base=")[1], 8.0) if "base=" in data else 8.0
            height = sf(data.split("height=")[1], base*0.7) if "height=" in data else base*0.7
            triangle = patches.Polygon([(0, 0), (base, 0), (base/2, height)], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(triangle)
            ax.text(base/2, -0.5, f"Base = {base}{unit}", ha='center', fontweight='bold')
            ax.text(-1, height/2, f"Height = {height}{unit}", va='center', rotation=90, fontweight='bold')
            ax.set_xlim(-2, base+2); ax.set_ylim(-2, height+2)

        elif d_type and "rectangle" in d_type.lower():
            w = sf(data.split("length=")[1], 6.0) if "length=" in data else 6.0
            h = sf(data.split("width=")[1], 4.0) if "width=" in data else 4.0
            rect = patches.Polygon([(0,0),(w,0),(w,h),(0,h)], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(rect)
            ax.text(w/2, -0.5, f"L = {w}{unit}", ha='center', fontweight='bold'); ax.set_xlim(-2, w+2); ax.set_ylim(-2, h+2)

        plt.tight_layout(); buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight'); buf.seek(0); plt.close(fig); return buf
    except: return None

def render_with_diagrams(text):
    if not text: st.error("No response. Try again."); return
    # Split by question and check for diagram tag before each question
    parts = re.split(r'(### \*\*Question \d+:)', text)
    for i in range(0, len(parts), 2):
        header = parts[i] if i < len(parts) else ""
        question = parts[i+1] if i+1 < len(parts) else ""
        full_part = header + question

        diagram_info = None
        if "[DIAGRAM:" in header:
            try: diagram_info = eval("{" + header.split("[DIAGRAM:")[1].split("]")[0].replace('=',':').replace('"',"'") + "}")
            except: pass

        if diagram_info and diagram_info.get("Topic"):
            img = draw_math_diagram(diagram_info["Topic"], diagram_info.get("Measurements",""), diagram_info.get("Question","Q"))
            if img: st.image(img, use_container_width=True)

        st.markdown(full_part.replace(header.split("[DIAGRAM:")[0], "")) # print question without tag

# ===================== GROQ CALL =====================
if "cache" not in st.session_state: st.session_state.cache = {}
def smart_groq_call(client, system_prompt, user_prompt):
    cache_key = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
    if cache_key in st.session_state.cache: return st.session_state.cache[cache_key]
    if len(user_prompt) > 2500: user_prompt = user_prompt[:2500] + "\n[Trimmed]"
    models_to_try = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    for model in models_to_try:
        try:
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.3, max_tokens=1600, timeout=45)
            if res and res.choices[0].message.content:
                st.session_state.cache[cache_key] = res; return res
        except RateLimitError: continue
        except: continue
    return None
def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("GROQ_API_KEY missing in Secrets"); return None
def generate_pdf(content, title):
    try:
        buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
        c.setFont("Helvetica-Bold", 14); c.drawString(40, height-50, title); y = height - 80; c.setFont("Helvetica", 10)
        for line in content.split('\n')[:350]:
            if y < 50: c.showPage(); y = height - 50
            c.drawString(40, y, line[:100]); y -= 16
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
        render_with_diagrams(answer) # NEW RENDERER
        pdf = generate_pdf(answer, dl_name)
        if pdf: st.download_button("📥 Download PDF", pdf, f"{dl_name}.pdf")
    else:
        st.error("AI Busy. Wait 1 min.")
    st.markdown("---")
    st.file_uploader("Upload student work for marking", type=["txt","pdf"], key=f"upload_{dl_name}")

with tabs[0]: # SMART SEARCH LIKE CHATGPT
    st.header("🔍 General Search - Ask Anything")
    q = st.text_input("Ask Anything", placeholder="e.g. What is the capital of Kenya? Explain photosynthesis")
    if st.button("Ask", type="primary") and q:
        ask_ai(f"You are a smart tutor. The student is in {grade} studying {subject}. Answer this question directly and clearly with Ugandan examples: {q}", "answer_general")

with tabs[1]:
    st.header(f"📖 Theory: {grade} {subject}")
    if st.button("Generate Full Theory Notes", type="primary"):
        ask_ai(f"Generate detailed NCDC 2026 theory notes for {grade} {subject} Topic: {topic}. Include Definition, 3 Examples, Ugandan Example.", f"Theory_{topic}")

with tabs[2]: # SST COMBINED
    st.header("📝 HARD COMBINED MOCK PLE")
    st.info("If Subject=SST, Section B will auto include CRE and IRE")
    if st.button("Generate HARD COMBINED MOCK PLE", type="primary"):
        sst_rule = "IMPORTANT: Because subject is Social Studies, SECTION B must be: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE" if subject == "Social Studies (SST)" else ""
        prompt = f"{MASTER_PROMPT}\nGenerate HARD MOCK PLE for {grade} {subject}. ROTATE TOPICS: {get_all_topics(grade)}. DIFFICULTY: P4=0,P5=6,P6=16,P7=18. {sst_rule}"
        ask_ai(prompt, f"HARD_MOCK_{subject}")

with tabs[3]:
    st.header("➗ Mathematics Worked Examples")
    if subject == "Mathematics":
        if st.button("Generate 7 Hard Worked Examples With Diagrams", type="primary"):
            prompt = f"{MASTER_PROMPT}\nGenerate 7 HARD P6-P7 math questions for {grade}. ROTATE TOPICS: {get_all_topics(grade)}. For 3 of them use [DIAGRAM: Topic=...] tag. Each question must have a), b). Then give UNEB MARKING GUIDE."
            ask_ai(prompt, f"Math_Work_{grade}")
    else: st.info("Select Mathematics subject.")

with tabs[4]:
    st.header("👩‍🏫 Teacher Tools")
    st.subheader("1. Test Paper Generator")
    if st.button("Generate Test Paper"):
        sst_rule = "FOR SST: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE" if subject == "Social Studies (SST)" else ""
        ask_ai(f"{MASTER_PROMPT}\nGenerate a Test for {grade} {subject} Topic: {topic}. 60 questions. {sst_rule}", "Test_Paper")
    st.subheader("2. UNEB Marking Guide Generator")
    questions = st.text_area("Paste PLE Question(s) Here", height=150)
    if st.button("Generate UNEB Marking Guide"):
        ask_ai(f"Act as UNEB Examiner for {subject}. Q: {questions}\nOutput: Answer Key, M/A/B, Common Mistakes.", "Marking_Guide")
    st.subheader("3. Marking / Grading Assistant")
    marking_scheme = st.text_area("Paste Marking Scheme", height=100)
    student_answers = st.text_area("Paste Student Answers", height=150)
    if st.button("Mark Work Now"):
        ask_ai(f"Act as UNEB Examiner for {subject}. Mark this.\nSCHEME:\n{marking_scheme}\nSTUDENT:\n{student_answers}", "Marked_Work")
    st.subheader("4. Report Card Generator")
    pupil_name = st.text_input("Pupil Name")
    scores = st.text_area("Paste scores: Subject: Score")
    if st.button("Generate Report Card"):
        ask_ai(f"Generate Report Card for {pupil_name} Class {grade}. Scores:\n{scores}", "Report_Card")
    st.subheader("5. Lesson Plan Generator")
    if st.button("Generate Lesson Plan"):
        ask_ai(f"Generate NCDC 2026 Lesson Plan for {grade} {subject} Topic: {topic}. 40 minutes.", "Lesson_Plan")
    st.subheader("6. Scheme of Work Generator")
    if st.button("Generate Scheme of Work"):
        ask_ai(f"Create 1-week scheme of work for {grade} {subject} Topic: {topic}. NCDC 2026 format.", "Scheme_of_Work")

st.sidebar.caption(f"NCDC 2026 | Contact: {CONTACT}")
