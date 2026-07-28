import streamlit as st
import io, re
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

# ===================== MASTER PROMPT - 3 UNEB FORMATS =====================
MASTER_PROMPT = """
You are an OFFICIAL UNEB PLE EXAMINER for Uganda P4-P7. Follow EXACT UNEB formatting and language.

FORMAT RULES:
A. IF SUBJECT = ENGLISH LANGUAGE:
   HEADER: UNEB PRIMARY SEVEN ENGLISH, TIME: 2 hours 15 minutes.
   SECTION A: Sub-Section I 30Q Grammar/Vocab 1mk each. Sub-Section II 20Q Comprehension 1mk each.
   SECTION B: 5Q Composition/Letter/Summary 10 marks each. TOTAL 100 MARKS.
B. IF SUBJECT = INTEGRATED SCIENCE:
   HEADER: UNEB PRIMARY SEVEN INTEGRATED SCIENCE, TIME: 2 hours 15 minutes.
   SECTION A: 40Q Short 1 mark each. SECTION B: 15Q Scenario 4 marks each with a), b). TOTAL 100 MARKS.
C. IF SUBJECT = MATHEMATICS OR SOCIAL STUDIES OR CRE OR IRE:
   SECTION A: 20Q 1-line. SECTION B: 40Q scenario a,b,c. TOTAL 60Q.
   IF SUBJECT = SOCIAL STUDIES (SST) THEN SECTION B: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE

DIFFICULTY DISTRIBUTION: P4=0Q, P5=6Q, P6=16Q, P7=18Q.
FOR MATH ONLY: Use [DIAGRAM: Topic="Triangle", Measurements="base=8cm,height=6cm"] BEFORE question.
NO DIAGRAMS FOR ENGLISH, SCIENCE, SST, CRE, IRE.
BE SMART: If user asks 1 question in General Search, answer directly like ChatGPT with Ugandan examples.
"""

# ===================== FULL NCDC 2026 DB RESTORED - NO TRUNCATION =====================
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
    "English Language": [{"topic": "Friendly Letters"}, {"topic": "Official Letters"}, {"topic": "School Timetables"}, {"topic": "Apostrophes"}, {"topic": "Semicolons and Colons"}, {"topic": "Direct and Indirect Speech"}, {"topic": "Perfect Tenses"}, {"topic": "Continuous Prose"}, {"topic": "Poetry Analysis"}, {"topic": "Graphic Data"}, {"topic": "Full Sentences"}, {"topic": "Composition Writing"}],
    "Integrated Science": [{"topic": "Plant Life and Crop Husbandry"}, {"topic": "Animal Management"}, {"topic": "Energy (Light, Heat, Electricity)"}, {"topic": "Simple Machines"}, {"topic": "Human Body Systems"}, {"topic": "Human Health"}, {"topic": "Environmental Management"}, {"topic": "Interdependence"}, {"topic": "Scientific Innovation"}],
    "Social Studies (SST)": [{"topic": "Africa Location"}, {"topic": "Drainage Systems"}, {"topic": "Climate"}, {"topic": "Economic Resources"}, {"topic": "The People of Africa"}, {"topic": "Slave Trade"}, {"topic": "Struggle for Independence"}, {"topic": "AU, UN"}, {"topic": "Post-Independence"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Plan for Salvation"}, {"topic": "Teachings of Jesus"}, {"topic": "Christian Service"}, {"topic": "Moral Challenges"}, {"topic": "Marriage, Family"}, {"topic": "Death and Hope"}, {"topic": "Multi-Faith Society"}],
    "Islamic Religious Education (IRE)": [{"topic": "Advanced Qur'anic Studies"}, {"topic": "Pillars of Iman"}, {"topic": "Islamic Law"}, {"topic": "Life of Companions"}, {"topic": "Islamic Economic System"}, {"topic": "Contemporary Issues"}]
  }
}
PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}
def get_all_topics(grade): return [t["topic"] for sub in PRIMARY_DB[f"PRIMARY_{grade[1:]}"].values() for t in sub]

# ===================== DIAGRAM GENERATOR - MATH ONLY =====================
def draw_math_diagram(d_type, measurements, q_text):
    try:
        fig, ax = plt.subplots(figsize=(5.5, 4.5)); plt.axis('off')
        ax.set_title(f"{q_text}", fontsize=10, fontweight='bold', pad=10, wrap=True)
        data = measurements.lower() if measurements else ""
        def sf(s, d):
            try: return float(re.findall(r"[\d.]+", s)[0])
            except: return d
        unit = "cm" if "cm" in data else "m" if "m" in data else ""

        if d_type and "venn2" in d_type.lower():
            A = sf(data.split("a=")[1], 10) if "a=" in data else 10; B = sf(data.split("b=")[1], 15) if "b=" in data else 15; AB = sf(data.split("ab=")[1], 5) if "ab=" in data else 5
            v = venn2(subsets = (A-AB, B-AB, AB), set_labels = ('Set A', 'Set B'))
            v.get_patch_by_id('10').set_color('lightblue'); v.get_patch_by_id('01').set_color('lightgreen')
        elif d_type and "venn3" in d_type.lower():
            v = venn3(subsets = (4,4,2,3,2,2,1), set_labels = ('A', 'B', 'C'))
        elif d_type and "triangle" in d_type.lower():
            base = sf(data.split("base=")[1], 8.0) if "base=" in data else 8.0; height = sf(data.split("height=")[1], base*0.7) if "height=" in data else base*0.7
            triangle = patches.Polygon([(0, 0), (base, 0), (base/2, height)], closed=True, fill=False, edgecolor='black', linewidth=2.5); ax.add_patch(triangle)
            ax.text(base/2, -0.5, f"Base = {base}{unit}", ha='center', fontweight='bold')
            ax.text(-1, height/2, f"Height = {height}{unit}", va='center', rotation=90, fontweight='bold')
            ax.set_xlim(-2, base+2); ax.set_ylim(-2, height+2)
        plt.tight_layout(); buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight'); buf.seek(0); plt.close(fig); return buf
    except: return None

def render_with_diagrams(text, subject):
    if not text: st.error("No response. Try again."); return
    parts = re.split(r'(### \*\*Question \d+:)', text)
    for i in range(0, len(parts), 2):
        header = parts[i] if i < len(parts) else ""
        question = parts[i+1] if i+1 < len(parts) else ""
        full_part = header + question
        diagram_info = None
        if "[DIAGRAM:" in header and subject == "Mathematics":
            try: diagram_info = eval("{" + header.split("[DIAGRAM:")[1].split("]")[0].replace('=',':').replace('"',"'") + "}")
            except: pass
        if diagram_info and diagram_info.get("Topic"):
            img = draw_math_diagram(diagram_info["Topic"], diagram_info.get("Measurements",""), diagram_info.get("Question","Q"))
            if img: st.image(img, use_container_width=True)
        st.markdown(full_part.replace(header.split("[DIAGRAM:")[0], ""))

# ===================== GROQ CALL =====================
if "cache" not in st.session_state: st.session_state.cache = {}
def smart_groq_call(client, system_prompt, user_prompt):
    cache_key = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
    if cache_key in st.session_state.cache: return st.session_state.cache[cache_key]
    if len(user_prompt) > 2500: user_prompt = user_prompt[:2500] + "\n[Trimmed]"
    models_to_try = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    for model in models_to_try:
        try:
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.3, max_tokens=1800, timeout=45)
            if res and res.choices[0].message.content:
                st.session_state.cache[cache_key] = res; return res
        except RateLimitError: continue
        except: continue
    return None
def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("GROQ_API_KEY missing in Secrets"); return None

# ===================== PDF WITH UNEB HEADER =====================
def generate_pdf(content, title, subject, grade):
    try:
        buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
        year = datetime.now().year

        # UNEB HEADER
        c.setFont("Helvetica-Bold", 12); c.drawCentredString(width/2, height-40, f"UNEB PRIMARY {grade[1:]} {subject.upper()} {year}")
        c.setFont("Helvetica", 10); c.drawCentredString(width/2, height-55, "Time Allowed: 2 hours 15 minutes")

        # Candidate details
        c.setFont("Helvetica", 9)
        c.drawString(40, height-75, "Candidate's name: ________________________________")
        c.drawString(40, height-90, "Candidate's signature: ____________________________")
        c.drawString(40, height-105, "School name: ____________________________________")
        c.drawString(300, height-105, "District name: ____________________")

        # Examiner table
        c.rect(400, height-130, 120, 80)
        c.drawString(405, height-115, "FOR EXAMINERS' USE")
        c.drawString(405, height-130, "Qn. No | MARKS")

        y = height - 150
        c.setFont("Helvetica", 9)
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

# ===================== MAIN APP - ALL 5 TABS =====================
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
        render_with_diagrams(answer, subject)
        pdf = generate_pdf(answer, dl_name, subject, grade)
        if pdf: st.download_button("📥 Download PDF", pdf, f"{dl_name}.pdf")
    else:
        st.error("AI Busy. Wait 1 min.")
    st.markdown("---")
    st.file_uploader("Upload student work for marking", type=["txt","pdf"], key=f"upload_{dl_name}")

with tabs[0]:
    st.header("🔍 General Search - Ask Anything")
    q = st.text_input("Ask Anything", placeholder="e.g. What are 3 functions of the heart")
    if st.button("Ask", type="primary") and q:
        ask_ai(f"You are a smart UNEB tutor. Student: {grade} {subject}. Answer directly and clearly with Ugandan examples: {q}", "answer_general")

with tabs[1]:
    st.header(f"📖 Theory: {grade} {subject}")
    if st.button("Generate Full Theory Notes", type="primary"):
        ask_ai(f"Generate detailed NCDC 2026 theory notes for {grade} {subject} Topic: {topic}. Include Definition, 3 Examples, Ugandan Example, Life Skill.", f"Theory_{topic}")

with tabs[2]:
    st.header("📝 HARD COMBINED MOCK PLE")
    is_english = subject == "English Language"
    is_science = subject == "Integrated Science"
    if is_english: st.info("ENGLISH FORMAT: Sec A 50Q, Sec B 5Q Composition. Time: 2hr 15min")
    elif is_science: st.info("SCIENCE FORMAT: Sec A 40Q, Sec B 15Q. Time: 2hr 15min")
    else: st.info("MATH/SST FORMAT: Sec A 20Q, Sec B 40Q")

    if st.button("Generate HARD COMBINED MOCK PLE", type="primary"):
        if is_english:
            prompt = f"{MASTER_PROMPT}\nGenerate HARD UNEB PLE MOCK for {grade} ENGLISH. TIME: 2 hours 15 minutes. SECTION A: Sub-Section I 30Q Grammar/Vocab. Sub-Section II 20Q Comprehension. SECTION B: 5Q Composition/Letter/Summary 10 marks each. ROTATE TOPICS: {get_all_topics(grade)}."
        elif is_science:
            prompt = f"{MASTER_PROMPT}\nGenerate HARD UNEB PLE MOCK for {grade} INTEGRATED SCIENCE. TIME: 2 hours 15 minutes. SECTION A: 40Q Short 1 mark each. SECTION B: 15Q Scenario 4 marks each with a), b). ROTATE TOPICS: {get_all_topics(grade)}."
        else:
            sst_rule = "FOR SST: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE" if subject == "Social Studies (SST)" else ""
            prompt = f"{MASTER_PROMPT}\nGenerate HARD MOCK for {grade} {subject}. SECTION A 20Q. SECTION B 40Q a,b,c. DIFFICULTY: P4=0,P5=6,P6=16,P7=18. {sst_rule} ROTATE TOPICS: {get_all_topics(grade)}."
        ask_ai(prompt, f"HARD_MOCK_{subject}")

with tabs[3]:
    st.header("➗ Mathematics Worked Examples")
    if subject == "Mathematics":
        if st.button("Generate 7 Hard Worked Examples With Diagrams", type="primary"):
            ask_ai(f"{MASTER_PROMPT}\nGenerate 7 HARD P6-P7 math questions for {grade}. Use [DIAGRAM:] for 3 questions. Each a),b). Then UNEB MARKING GUIDE.", f"Math_Work_{grade}")
    else: st.info("Select Mathematics subject.")

with tabs[4]:
    st.header("👩‍🏫 Teacher Tools - UNEB EXAMINER SUITE")
    st.subheader("1. Test Paper Generator")
    if st.button("Generate Test Paper"):
        if subject == "English Language":
            ask_ai(f"{MASTER_PROMPT}\nGenerate UNEB ENGLISH TEST for {grade}. Sec A 50Q, Sec B 5Q.", "Test_Paper_Eng")
        elif subject == "Integrated Science":
            ask_ai(f"{MASTER_PROMPT}\nGenerate UNEB SCIENCE TEST for {grade}. Sec A 40Q, Sec B 15Q.", "Test_Paper_Sci")
        else:
            sst_rule = "FOR SST: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE" if subject == "Social Studies (SST)" else ""
            ask_ai(f"{MASTER_PROMPT}\nGenerate Test for {grade} {subject}. 60Q. {sst_rule}", "Test_Paper")

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
