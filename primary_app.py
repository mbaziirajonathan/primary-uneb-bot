import streamlit as st
import io, re, json, random
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
You are an OFFICIAL UNEB PLE EXAMINER for Uganda P4-P7.

ROTATION RULE: You MUST use ALL topics provided for the grade. Spread questions evenly across topics in both Section A and Section B.

DIFFICULTY RULE BY CLASS:
P7 = 18 HARD questions, P6 = 16 HARD questions, P5 = 6 MEDIUM questions, P4 = 0 EASY questions

FORMAT RULES:
A. ENGLISH: TIME 2hr15min. SEC A: 30Q Grammar + 20Q Comprehension. SEC B: 5Q Composition 10marks each. TOTAL 100
B. SCIENCE: TIME 2hr15min. SEC A: 40Q 1mark. SEC B: 15Q 4marks with a),b). TOTAL 100
C. MATH/SST/CRE/IRE: SEC A: 20Q. SEC B: 40Q a,b,c. TOTAL 60Q. IF SST THEN Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE

FOR MATH ONLY: If question needs a diagram, START with [DIAGRAM: Topic="venn2", Measurements="a=10,b=15,ab=5", Question="In a class..."]
If diagram generation fails, just write the question in text. DO NOT skip the question.
SUPPORTED DIAGRAMS: Triangle, Rectangle, venn2, venn3. Keep them simple.
NO DIAGRAMS FOR OTHER SUBJECTS.
"""

# ===================== FULL NCDC 2026 DB - 100% RESTORED =====================
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

# ===================== DIAGRAM GENERATOR - FAIL SAFE =====================
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
            v = venn2(subsets = (max(1,A-AB), max(1,B-AB), max(1,AB)), set_labels = ('Set A', 'Set B'))
        elif "venn3" in d_type.lower():
            v = venn3(subsets = (3,3,1,2,1,1,1), set_labels = ('A', 'B', 'C'))
        elif "triangle" in d_type.lower():
            base = sf(data.split("base=")[1], 8.0) if "base=" in data else 8.0
            height = sf(data.split("height=")[1], base*0.7) if "height=" in data else base*0.7
            triangle = patches.Polygon([(0, 0), (base, 0), (base/2, height)], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(triangle)
            ax.text(base/2, -0.5, f"Base = {base}{unit}", ha='center')
        else: return None

        plt.tight_layout(); buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=120, bbox_inches='tight'); buf.seek(0); plt.close(fig); return buf
    except: return None

def parse_tag(tag_str):
    try:
        tag_str = tag_str.replace("Topic=", '"Topic":').replace("Measurements=", '"Measurements":').replace("Question=", '"Question":')
        return json.loads("{" + tag_str + "}")
    except: return None

def render_with_diagrams(text, subject):
    if not text: st.error("No response from AI. Try again."); return
    if "### **Question" not in text: st.markdown(text); return

    parts = re.split(r'(### \*\*Question \d+:)', text)
    for i in range(0, len(parts), 2):
        header = parts[i] if i < len(parts) else ""
        question = parts[i+1] if i+1 < len(parts) else ""

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
    for model in models_to_try:
        try:
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.5, max_tokens=2000, timeout=60)
            if res and res.choices[0].message.content:
                st.session_state.cache[cache_key] = res; return res
        except RateLimitError: continue
        except: continue
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
        y = height - 80; c.setFont("Helvetica", 9)
        for line in content.split('\n')[:550]:
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
        render_with_diagrams(answer, subject)
        pdf = generate_pdf(answer, dl_name, subject, grade)
        if pdf: st.download_button("📥 Download PDF", pdf, f"{dl_name}.pdf")
    else:
        st.error("AI Busy. Please wait 1 minute and retry.")
    st.markdown("---")
    st.file_uploader("Upload student work for marking", type=["txt","pdf"], key=f"upload_{dl_name}")

with tabs[0]:
    st.header("🔍 General Search")
    q = st.text_input("Ask Anything")
    if st.button("Ask", type="primary") and q:
        ask_ai(f"You are a smart UNEB tutor for {grade} {subject}. Answer: {q}", "answer_general")

with tabs[1]:
    st.header(f"📖 Theory: {grade} {subject}")
    if st.button("Generate Full Theory Notes", type="primary"):
        ask_ai(f"Generate detailed NCDC 2026 theory notes for {grade} {subject} Topic: {topic}.", f"Theory_{topic}")

with tabs[2]:
    st.header("📝 HARD COMBINED MOCK PLE")
    is_english = subject == "English Language"
    is_science = subject == "Integrated Science"
    diff_map = {"P4": "0 EASY", "P5": "6 MEDIUM", "P6": "16 HARD", "P7": "18 HARD"}
    st.info(f"{grade} DIFFICULTY: {diff_map[grade]}. All {len(get_all_topics(grade))} topics will be rotated.")

    if st.button("Generate HARD COMBINED MOCK PLE", type="primary"):
        all_topics = get_all_topics(grade)
        random.shuffle(all_topics)

        if is_english:
            prompt = f"{MASTER_PROMPT}\nGenerate HARD UNEB PLE MOCK for {grade} ENGLISH. TIME: 2 hours 15 minutes. DIFFICULTY: {diff_map[grade]}. ROTATE ALL THESE TOPICS: {all_topics}. SECTION A: 30Q + 20Q. SECTION B: 5Q."
        elif is_science:
            prompt = f"{MASTER_PROMPT}\nGenerate HARD UNEB PLE MOCK for {grade} INTEGRATED SCIENCE. TIME: 2 hours 15 minutes. DIFFICULTY: {diff_map[grade]}. ROTATE ALL THESE TOPICS: {all_topics}. SECTION A: 40Q. SECTION B: 15Q with a), b)."
        else:
            sst_rule = "FOR SST: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE" if subject == "Social Studies (SST)" else ""
            venn_rule = "For Mathematics, include 1-2 simple venn2 questions if topic is Sets. If diagram fails, write text version." if subject=="Mathematics" else ""
            prompt = f"{MASTER_PROMPT}\nGenerate HARD MOCK for {grade} {subject}. DIFFICULTY: {diff_map[grade]}. ROTATE ALL THESE TOPICS: {all_topics}. SECTION A 20Q. SECTION B 40Q. {sst_rule} {venn_rule}"
        ask_ai(prompt, f"HARD_MOCK_{subject}_{grade}")

with tabs[3]:
    st.header("➗ Mathematics Worked Examples")
    if subject == "Mathematics":
        if st.button("Generate 7 Hard Worked Examples", type="primary"):
            ask_ai(f"{MASTER_PROMPT}\nGenerate 7 questions for {grade} Mathematics. ROTATE TOPICS: {get_all_topics(grade)}. For Sets topic, try 1 simple venn2. Each a),b). Then MARKING GUIDE.", f"Math_Work_{grade}")
    else: st.info("Select Mathematics subject.")

with tabs[4]:
    st.header("👩‍🏫 Teacher Tools")
    st.subheader("1. Test Paper Generator")
    if st.button("Generate Test Paper"):
        ask_ai(f"{MASTER_PROMPT}\nGenerate Test for {grade} {subject}. ROTATE TOPICS: {get_all_topics(grade)}.", "Test_Paper")
    st.subheader("2. UNEB Marking Guide Generator")
    questions = st.text_area("Paste PLE Question(s) Here", height=150)
    if st.button("Generate UNEB Marking Guide"):
        ask_ai(f"Act as UNEB Examiner for {subject}. Q: {questions}\nOutput: Answer Key, Marking Guide.", "Marking_Guide")
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
        ask_ai(f"Generate NCDC 2026 Lesson Plan for {grade} {subject} Topic: {topic}.", "Lesson_Plan")
    st.subheader("6. Scheme of Work Generator")
    if st.button("Generate Scheme of Work"):
        ask_ai(f"Create 1-week scheme of work for {grade} {subject} Topic: {topic}.", "Scheme_of_Work")

st.sidebar.caption(f"NCDC 2026 | Contact: {CONTACT}")
