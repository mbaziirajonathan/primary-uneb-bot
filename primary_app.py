import streamlit as st
import io, re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib_venn import venn2, venn3
import time
import hashlib
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7.")

# ===================== MASTER PROMPT: UNEB EXAMINER =====================
MASTER_PROMPT = """
You are an OFFICIAL UNEB PLE EXAMINER for Mathematics, Integrated Science, Social Studies (SST), and English Language.
RULE 1: SECTION A = 20Q, 1 line, 8-12 words. SECTION B = 40Q, 3-4 lines scenario, a,b,c.
RULE 2: DIFFICULTY: P4=0Q, P5=6Q, P6=16Q, P7=18Q. Total 60Q.
RULE 3: IF SST THEN SECTION B: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE
RULE 4: MARKING: Math=M/A/B. Science=Keywords. SST=Facts. English=Layout/Content.
RULE 5: DIAGRAMS: Use [DIAGRAM: Topic="Triangle", Measurements="base=8cm"] tag BEFORE question.
Always output questions first, then "MARKING GUIDE:" section.
"""

# ===================== FULL NCDC 2026 DB RESTORED =====================
PRIMARY_DB = {
  "PRIMARY_4": {
    "Mathematics": [{"topic": "Set Concepts"}, {"topic": "Whole Numbers (Up to 99,999)"}, {"topic": "Operations on Whole Numbers"}, {"topic": "Fractions"}, {"topic": "Geometric Shapes and Symmetry"}, {"topic": "Measures (Time, Length, Mass, Capacity)"}, {"topic": "Money and Financial Literacy"}, {"topic": "Patterns and Sequences"}, {"topic": "Basic Data Handling"}],
    "English Language": [{"topic": "Describing People and Objects"}, {"topic": "Giving Directions"}, {"topic": "Feelings and Preferences"}, {"topic": "Comprehension: Descriptive Paragraphs"}, {"topic": "Comprehension: Simple Dialogues"}, {"topic": "Comprehension: Picture Interpretation"}],
    "Integrated Science": [{"topic": "Plant Life and Flowering Plants"}, {"topic": "Crop Husbandry"}, {"topic": "Weather and Its Elements"}, {"topic": "Human Body (External Parts)"}, {"topic": "Personal Hygiene"}, {"topic": "Vectors and Pests"}, {"topic": "First Aid"}, {"topic": "Air and Its Properties"}, {"topic": "Water and Its Uses"}, {"topic": "Indigenous Crafts"}],
    "Social Studies (SST)": [{"topic": "Location of Our Sub-County"}, {"topic": "Physical Features"}, {"topic": "Vegetation and Animals"}, {"topic": "People and Culture"}, {"topic": "Economic Activities"}, {"topic": "Social Services"}, {"topic": "Leadership and Governance"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Creation and Our Talents"}, {"topic": "Knowing Jesus Christ"}, {"topic": "Christian Values"}, {"topic": "The Bible"}, {"topic": "Prayer and Fellowship"}, {"topic": "Relationships"}, {"topic": "Serving Others"}],
    "Islamic Religious Education (IRE)": [{"topic": "Selected Surahs"}, {"topic": "Pillars of Islam"}, {"topic": "Pillars of Iman"}, {"topic": "Life of Prophet Muhammad"}, {"topic": "Islamic Manners"}, {"topic": "Wudhu and Adhan"}]
  },
  "PRIMARY_5": {
    "Mathematics": [{"topic": "Set Theory (Union, Intersection, Venn Diagrams)"}, {"topic": "Whole Numbers (Up to 999,999)"}, {"topic": "Operations on Whole Numbers"}, {"topic": "Number Patterns (LCM, GCF)"}, {"topic": "Fractions"}, {"topic": "Decimals"}, {"topic": "Geometry (Lines, Angles)"}, {"topic": "Measures (Perimeter, Area)"}, {"topic": "Graphs and Data"}, {"topic": "Business Mathematics"}],
    "English Language": [{"topic": "Sanitation and Health"}, {"topic": "Local Culture"}, {"topic": "Simple Past Tense"}, {"topic": "Present Continuous"}, {"topic": "Conjunctions"}, {"topic": "Wh- Questions"}, {"topic": "Interpreting Notices"}, {"topic": "Public Announcements"}, {"topic": "Informational Texts"}],
    "Integrated Science": [{"topic": "Soil Science"}, {"topic": "Non-Flowering Plants"}, {"topic": "Matter and Its States"}, {"topic": "Poultry Keeping"}, {"topic": "Bee Keeping"}, {"topic": "Human Body Systems"}, {"topic": "Immunization"}, {"topic": "Sanitation"}, {"topic": "Primary Health Care"}, {"topic": "First Aid"}],
    "Social Studies (SST)": [{"topic": "Location and Geography of Uganda"}, {"topic": "Physical Features"}, {"topic": "Climate and Weather"}, {"topic": "Vegetation Zones"}, {"topic": "Natural Resources"}, {"topic": "The People of Uganda"}, {"topic": "Cultural Governance"}, {"topic": "Pre-Colonial History"}, {"topic": "Road to Independence"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Covenant"}, {"topic": "Birth and Ministry of Jesus"}, {"topic": "Miracles and Parables"}, {"topic": "Christian Responses"}, {"topic": "The Church"}, {"topic": "Christian Holy Days"}, {"topic": "Moral Values"}],
    "Islamic Religious Education (IRE)": [{"topic": "Selected Surahs Deep Study"}, {"topic": "Surat Al-Fatiha"}, {"topic": "Pillars of Islam"}, {"topic": "Pillars of Iman"}, {"topic": "Life of Prophet"}, {"topic": "Islamic Etiquette"}, {"topic": "Holy Sites"}]
  },
  "PRIMARY_6": {
    "Mathematics": [{"topic": "Advanced Set Operations"}, {"topic": "Whole Numbers and Integers"}, {"topic": "Fractions and Decimals"}, {"topic": "Ratios, Proportions, Percentages"}, {"topic": "Sequences"}, {"topic": "Geometry (Angles, Circle)"}, {"topic": "Speed, Distance, Time"}, {"topic": "Area, Volume"}, {"topic": "Business Math"}, {"topic": "Algebra"}, {"topic": "Basic Probability"}],
    "English Language": [{"topic": "Electronic Media"}, {"topic": "Messaging"}, {"topic": "Future Tenses"}, {"topic": "If-Conditionals"}, {"topic": "Relative Pronouns"}, {"topic": "Passive Voice"}, {"topic": "Short Stories"}, {"topic": "Newspaper Excerpts"}, {"topic": "Dialogue Exchanges"}],
    "Integrated Science": [{"topic": "Plant Classification"}, {"topic": "Invertebrates"}, {"topic": "Vertebrates"}, {"topic": "Domestic Animals"}, {"topic": "Sound Energy"}, {"topic": "Classification of Matter"}, {"topic": "Circulatory System"}, {"topic": "Diseases"}, {"topic": "Indigenous Technology"}, {"topic": "Basic Digital Tech"}],
    "Social Studies (SST)": [{"topic": "East Africa"}, {"topic": "Physical Features"}, {"topic": "Climate"}, {"topic": "Vegetation and Wildlife"}, {"topic": "The People"}, {"topic": "Colonialism"}, {"topic": "Main Inventions"}, {"topic": "Democratic Elections"}, {"topic": "EAC"}, {"topic": "Social Services"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Guidance"}, {"topic": "Death and Resurrection"}, {"topic": "The Holy Spirit"}, {"topic": "The Early Church"}, {"topic": "Christian Witness"}, {"topic": "Respect for Authority"}, {"topic": "Preparing for Future"}],
    "Islamic Religious Education (IRE)": [{"topic": "Advanced Recitation"}, {"topic": "Pillars of Islam"}, {"topic": "Pillars of Iman"}, {"topic": "Stories of Prophets"}, {"topic": "Islamic Social Values"}, {"topic": "Islamic Festivals"}]
  },
  "PRIMARY_7": {
    "Mathematics": [{"topic": "Advanced Sets (Three Categories)"}, {"topic": "Whole Numbers and Bases"}, {"topic": "Number Theory"}, {"topic": "Fractions, Decimals, Percentages"}, {"topic": "Ratios and Proportion"}, {"topic": "Integers"}, {"topic": "Business Mathematics"}, {"topic": "Graphs and Data Handling"}, {"topic": "Geometry (Constructions)"}, {"topic": "Speed, Velocity"}, {"topic": "Area, Surface Area, Volume"}, {"topic": "Equations and Inequalities"}],
    "English Language": [{"topic": "Friendly Letters"}, {"topic": "Official Letters"}, {"topic": "School Timetables"}, {"topic": "Apostrophes"}, {"topic": "Semicolons and Colons"}, {"topic": "Direct and Indirect Speech"}, {"topic": "Perfect Tenses"}, {"topic": "Continuous Prose"}, {"topic": "Poetry Analysis"}, {"topic": "Graphic Data"}, {"topic": "Full Sentences"}],
    "Integrated Science": [{"topic": "Plant Life and Crop Husbandry"}, {"topic": "Animal Management"}, {"topic": "Energy (Light, Heat, Electricity)"}, {"topic": "Simple Machines"}, {"topic": "Human Body Systems"}, {"topic": "Human Health"}, {"topic": "Environmental Management"}, {"topic": "Interdependence"}, {"topic": "Scientific Innovation"}],
    "Social Studies (SST)": [{"topic": "Africa Location"}, {"topic": "Drainage Systems"}, {"topic": "Climate"}, {"topic": "Economic Resources"}, {"topic": "The People of Africa"}, {"topic": "Slave Trade"}, {"topic": "Struggle for Independence"}, {"topic": "AU, UN"}, {"topic": "Post-Independence"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Plan for Salvation"}, {"topic": "Teachings of Jesus"}, {"topic": "Christian Service"}, {"topic": "Moral Challenges"}, {"topic": "Marriage, Family"}, {"topic": "Death and Hope"}, {"topic": "Multi-Faith Society"}],
    "Islamic Religious Education (IRE)": [{"topic": "Advanced Qur'anic Studies"}, {"topic": "Pillars of Iman"}, {"topic": "Islamic Law"}, {"topic": "Life of Companions"}, {"topic": "Islamic Economic System"}, {"topic": "Contemporary Issues"}]
  }
}
PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}
def get_all_topics(grade): return [t["topic"] for sub in PRIMARY_DB[f"PRIMARY_{grade[1:]}"].values() for t in sub]

# ===================== DIAGRAM GENERATOR =====================
def draw_math_diagram(d_type, measurements):
    try:
        fig, ax = plt.subplots(figsize=(5, 4)); plt.axis('off')
        data = measurements.lower() if measurements else ""
        def safe_float(s, default):
            try: return float(re.findall(r"[\d.]+", s)[0])
            except: return default
        if d_type and "triangle" in d_type.lower():
            base = safe_float(data.split("base=")[1], 8.0) if "base=" in data else 8.0; height = base*0.7
            triangle = patches.Polygon([(0, 0), (base, 0), (base/2, height)], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(triangle)
            ax.set_xlim(-2, base+2); ax.set_ylim(-2, height+2)
        elif d_type and "venn2" in d_type.lower():
            A = safe_float(data.split("a=")[1], 10) if "a=" in data else 10; B = safe_float(data.split("b=")[1], 15) if "b=" in data else 15; AB = safe_float(data.split("ab=")[1], 5) if "ab=" in data else 5
            v = venn2(subsets = (A-AB, B-AB, AB), set_labels = ('Set A', 'Set B'))
        elif d_type and "venn3" in d_type.lower():
            v = venn3(subsets = (5,5,2,5,2,2,1), set_labels = ('A', 'B', 'C'))
        plt.tight_layout(); buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight'); buf.seek(0); plt.close(fig); return buf
    except: return None

def parse_diagram_tag(text):
    if "[DIAGRAM:" not in text: return None
    try:
        tag = text.split("[DIAGRAM:")[1].split("]")[0]; parts = {}
        for item in tag.split(","):
            if "=" in item: k,v = item.split("=",1); parts[k.strip()] = v.strip().strip('"')
        return parts
    except: return None

# ===================== GROQ CALL - STABLE =====================
if "cache" not in st.session_state: st.session_state.cache = {}
def smart_groq_call(client, system_prompt, user_prompt):
    cache_key = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
    if cache_key in st.session_state.cache: return st.session_state.cache[cache_key]
    if len(user_prompt) > 2500: user_prompt = user_prompt[:2500] + "\n[Trimmed]"
    models_to_try = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    for model in models_to_try:
        try:
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.4, max_tokens=1500, timeout=45)
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

def render_response(text):
    if not text: st.error("No response. Please try again."); return
    st.markdown(text)
    for part in text.split("[DIAGRAM:"):
        if "]" in part:
            info = parse_diagram_tag("[DIAGRAM:" + part.split("]")[0] + "]")
            if info:
                img = draw_math_diagram(info.get("Topic",""), info.get("Measurements",""))
                if img: st.image(img, use_container_width=True)

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

# ===================== MAIN APP - ALL 5 TABS RESTORED =====================
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
        render_response(answer)
        pdf = generate_pdf(answer, dl_name)
        if pdf: st.download_button("📥 Download PDF", pdf, f"{dl_name}.pdf")
    else:
        st.error("All AI models busy. Please wait 1-2 minutes.")
    st.markdown("---")
    st.subheader("Upload Student Work")
    st.file_uploader("Upload txt/pdf for marking", type=["txt","pdf"], key=f"upload_{dl_name}")

with tabs[0]:
    st.header("🔍 General Search")
    q = st.text_input("Ask Anything", placeholder="e.g. What are the functions of the liver")
    if st.button("Ask", type="primary") and q:
        ask_ai(f"For {grade} {subject}, Topic: {topic}. Answer clearly with Ugandan examples: {q}", "answer_general")

with tabs[1]:
    st.header(f"📖 Theory: {grade} {subject}")
    if st.button("Generate Full Theory Notes", type="primary"):
        ask_ai(f"Generate detailed NCDC 2026 theory notes for {grade} {subject} Topic: {topic}. Include Definition, Key Competency, 3 Examples, Ugandan Example, Life Skill.", f"Theory_{topic}")
    q = st.text_input("Ask about Theory", key="ask_theory")
    if st.button("Ask Theory") and q: ask_ai(f"User Context: {grade} {subject} Topic: {topic}\nQ: {q}", "answer_theory")

with tabs[2]:
    st.header("📝 HARD COMBINED MOCK PLE")
    st.info("Section A: 20Q 1-line. Section B: 40Q scenario a,b,c. SST=20+10+10")
    if st.button("Generate HARD COMBINED MOCK PLE", type="primary"):
        sst_rule = "FOR SST: SECTION A=20 SST. SECTION B=20 SST Q21-Q40, 10 CRE Q41-Q50, 10 IRE Q51-Q60." if subject == "Social Studies (SST)" else ""
        prompt = f"{MASTER_PROMPT}\nGenerate HARD MOCK for {grade} {subject}. ROTATE TOPICS: {get_all_topics(grade)}. DIFFICULTY: P4=0Q, P5=6Q, P6=16Q, P7=18Q. {sst_rule}"
        ask_ai(prompt, f"HARD_MOCK_{subject}")

with tabs[3]:
    st.header("➗ Mathematics Worked Examples + UNEB Marking")
    if subject == "Mathematics":
        if st.button("Generate 7 Hard Worked Examples With M/A/B", type="primary"):
            prompt = f"{MASTER_PROMPT}\nGenerate 7 HARD P6-P7 math questions for {grade}. ROTATE TOPICS: {get_all_topics(grade)}. Each 3-4 lines with a), b). Then UNEB MARKING GUIDE: Show M, A, B."
            ask_ai(prompt, f"Math_Work_{grade}")
    else: st.info("Select Mathematics subject.")

with tabs[4]:
    st.header("👩‍🏫 Teacher Tools - UNEB EXAMINER SUITE")
    st.subheader("1. Test Paper Generator")
    if st.button("Generate Test Paper"):
        ask_ai(f"{MASTER_PROMPT}\nGenerate a Test for {grade} {subject} Topic: {topic}. 60 questions. ROTATE TOPICS: {get_all_topics(grade)}. Then generate marking guide.", "Test_Paper")

    st.subheader("2. UNEB Marking Guide Generator")
    questions = st.text_area("Paste PLE Question(s) Here", height=150)
    if st.button("Generate UNEB Marking Guide"):
        prompt = f"Act as an official UNEB PLE Examiner for {subject}. Question: {questions}\nGenerate marking guide: Subject, Answer Key, M/A/B, Common Mistakes."
        ask_ai(prompt, "UNEB_Marking_Guide")

    st.subheader("3. Marking / Grading Assistant")
    marking_scheme = st.text_area("Paste Marking Scheme", height=100)
    student_answers = st.text_area("Paste Student Answers", height=150)
    upload_mark = st.file_uploader("Or Upload student work", type=["txt","pdf"], key="mark_upload")
    if st.button("Mark Work Now - UNEB Style"):
        content = upload_mark.read().decode("utf-8") if upload_mark else student_answers
        prompt = f"Act as UNEB PLE Examiner for {subject}. Mark this work.\nSCHEME:\n{marking_scheme}\nSTUDENT:\n{content}\nOutput: Total, M/A/B Breakdown, Common Mistakes."
        ask_ai(prompt, "Marked_Work")

    st.subheader("4. Report Card Generator")
    pupil_name = st.text_input("Pupil Name")
    scores = st.text_area("Paste scores: Subject: Score", height=100)
    if st.button("Generate Report Card"):
        ask_ai(f"Generate Report Card for {pupil_name} Class {grade}. Term 2 2026. Scores:\n{scores}", "Report_Card")

    st.subheader("5. Lesson Plan Generator")
    duration = st.selectbox("Duration", ["40 minutes", "80 minutes"])
    if st.button("Generate Lesson Plan"):
        ask_ai(f"{MASTER_PROMPT}\nGenerate NCDC 2026 Lesson Plan for {grade} {subject} Topic: {topic}. Duration: {duration}.", "Lesson_Plan")

    st.subheader("6. Scheme of Work Generator")
    if st.button("Generate Scheme of Work"):
        ask_ai(f"Create 1-week scheme of work for {grade} {subject} Topic: {topic}. NCDC 2026 format.", "Scheme_of_Work")

st.sidebar.caption(f"NCDC 2026 | Contact: {CONTACT}")
