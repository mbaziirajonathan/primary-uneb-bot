import streamlit as st
import io, re, json, random
import hashlib
from datetime import datetime
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7.")

# ===================== MASTER PROMPT =====================
MASTER_PROMPT = """
You are an OFFICIAL UNEB PLE EXAMINER + ELITE SVG ARCHITECT for Uganda P4-P7 following NCDC 2026 Competency-Based Curriculum.
ROTATION RULE: You MUST use ALL topics provided for the grade.
DIFFICULTY RULE BY CLASS: P7 = 18 HARD, P6 = 16 HARD, P5 = 6 MEDIUM, P4 = 0 EASY
FORMAT RULES: C. MATH/SST/CRE/IRE: SEC A: 20Q. SEC B: 40Q a,b,c. TOTAL 60Q. IF SST THEN Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE
CRITICAL SVG RULES: 1. Every SVG MUST start with style="background-color: #ffffff;" 2. Wrap EVERY SVG with [SVG]...[/SVG]
EXACT SVG TEMPLATES:
SCIENCE PANEL P7: <svg viewBox="0 0 1400 1350" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"></svg>
SKETCH MAP SST: <svg viewBox="0 0 700 500" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"></svg>
UNEB VENN UNIVERSAL: <svg viewBox="0 0 600 420" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"></svg>
VENN 3 CIRCLES: <svg viewBox="0 0 700 500" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"></svg>
SHADING VENN A-B: <svg viewBox="0 0 500 300" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"></svg>
SQUARE: <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"></svg>
"""

# ===================== FULL DB RESTORED =====================
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
def get_all_topics(grade):
    return [t["topic"] for sub in PRIMARY_DB[f"PRIMARY_{grade[1:]}"].values() for t in sub]

# ===================== SESSION STATE =====================
if "cache" not in st.session_state:
    st.session_state.cache = {}
    st.session_state['last_svgs'] = []

# ===================== SVG RENDERER =====================
def render_with_svg(text):
    if not text:
        st.error("No response from AI. Try again.")
        return
    st.session_state['last_svgs'] = []
    parts = re.split(r'(\[SVG\].*?\[/SVG\])', text, flags=re.DOTALL)
    for part in parts:
        if part.startswith("[SVG]"):
            svg_code = part[5:-6]
            if 'background-color' not in svg_code:
                svg_code = svg_code.replace('<svg ', '<svg style="background-color: #ffffff;" ')
            st.session_state['last_svgs'].append(svg_code)
            st.markdown(svg_code, unsafe_allow_html=True)
        else:
            st.markdown(part)

# ===================== GROQ + PDF =====================
def smart_groq_call(client, system_prompt, user_prompt):
    cache_key = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
    if cache_key in st.session_state.cache:
        return st.session_state.cache[cache_key]

    models_to_try = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    for model in models_to_try:
        try:
            res = client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
                temperature=0.3,
                max_tokens=2500,
                timeout=60
            )
            if res and res.choices[0].message.content:
                st.session_state.cache[cache_key] = res
                return res
        except RateLimitError:
            continue
        except Exception:
            continue
    return None

def get_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("GROQ_API_KEY missing in Secrets")
        return None

def generate_pdf(content, title, subject, grade):
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        year = datetime.now().year
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width/2, height-40, f"UNEB PRIMARY {grade[1:]} {subject.upper()} {year}")
        y = height - 80
        svg_index = 0
        for line in content.split('\n')[:600]:
            if "[SVG]" in line and svg_index < len(st.session_state['last_svgs']):
                svg_code = st.session_state['last_svgs'][svg_index]
                svg_io = io.StringIO(svg_code)
                drawing = svg2rlg(svg_io)
                if drawing:
                    drawing.scale(0.5, 0.5)
                    renderPDF.draw(drawing, c, 40, y-200)
                    y -= 210
                    svg_index += 1
            if y < 50:
                c.showPage()
                y = height - 50
            clean_line = re.sub(r'\[/?SVG\]', '', line)
            c.drawString(40, y, clean_line[:95])
            y -= 14
        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.warning(f"PDF SVG embed failed: {e}")
        return None

# ===================== PASSWORD =====================
def check_password():
    APP_PW = st.secrets.get("PRIMARY_APP_PASSWORD", "PRIMARY2026")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "ADMIN256")
    if "password_correct" not in st.session_state:
        st.title("🔒 TEACHERK PRIMARY 2026 NCDC")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == APP_PW:
                st.session_state["user_type"] = "Pupil"
                st.session_state["password_correct"] = True
                st.rerun()
            elif pw == ADMIN_PW:
                st.session_state["user_type"] = "Teacher"
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Wrong password")
        st.stop()
check_password()

# ===================== MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026 NCDC v6.2.2")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"])
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])

tabs = st.tabs(["🔍 General Search", "📖 Theory", "📝 HARD MOCK", "➗ Math Work", "👩‍🏫 Teacher Tools"])

def ask_ai(prompt, dl_name):
    client = get_client()
    if not client:
        return
    with st.spinner("Generating NCDC Diagram..."):
        res = smart_groq_call(client, MASTER_PROMPT, prompt)
    if res:
        answer = res.choices[0].message.content
        render_with_svg(answer)
        pdf = generate_pdf(answer, dl_name, subject, grade)
        if pdf:
            st.download_button("📥 Download PDF with SVG", pdf, f"{dl_name}.pdf")
    else:
        st.error("AI Busy. Please wait 1 minute and retry.")

with tabs[0]:
    st.header("🔍 General Search")
    q = st.text_input("Ask Anything: e.g 'Draw Venn 3 Circles' or 'Draw Science Panel'")
    if st.button("Ask", type="primary") and q:
        ask_ai(f"You are a smart UNEB tutor for {grade} {subject}. Topic: {topic}. Request: {q}", "answer_general")

st.sidebar.caption(f"NCDC 2026 | Contact: {CONTACT}")
