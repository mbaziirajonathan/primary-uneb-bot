import streamlit as st
import os, io, json, difflib, random
import pandas as pd
from datetime import datetime
from groq import Groq
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from gtts import gTTS

# ===================== CONFIG =====================
LOG_FILE = "usage_log_primary.json"
CONTACT = "256751040731"

st.set_page_config(page_title="TEACHERK PRIMARY 2026", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Curriculum. Pupils must confirm all answers with your Class Teacher before exams.")

# ===================== 1. NCDC 2026 SYSTEM PROMPT LOCK =====================
SYSTEM_PROMPT = """
You are TEACHERK, an AI Tutor locked to NCDC 2026 Uganda Primary Curriculum for P4 to P7 only.
CRITICAL RULES:
1. ONLY teach topics from NCDC 2026 Primary syllabus. If asked about Secondary, University, or topics not in NCDC, say: "I can only teach P4-P7 NCDC topics."
2. ANTI-HALLUCINATION: Do not make up facts. Use simple examples from Uganda: boda, matatu, posho, matooke, Kampala.
3. CHAIN OF THOUGHT: Explain step by step. 1. What is it? 2. Example. 3. How to solve.
4. LANGUAGE: Use very simple English for pupils aged 9-13. No hard words. Short sentences.
5. TONE: Friendly teacher. Encourage the pupil.
6. TASK: Help with questions, quizzes, lesson plans, and mock papers for P4-P7 only.
"""

# ===================== 2. DICTIONARY =====================
ENGLISH_DICTIONARY = {
    "P4": {"Adjective": "Describing word. Ex: tall teacher", "Noun": "Naming word. Ex: school", "Verb": "Action word. Ex: run"},
    "P5": {"Composition": "Story with beginning, middle, end", "Synonym": "Big = Large", "Antonym": "Hot = Cold"},
    "P6": {"Direct Speech": "Exact words. Ex: Teacher said 'Stop'", "Active Voice": "Subject does action", "Debate": "Formal discussion"},
    "P7": {"Functional Text": "Notice, Advert, Letter", "Comprehension": "Reading and answering", "Summary": "Short version of story"}
}

# ===================== 3. FULL NCDC 2026 DB P4-P7 =====================
PRIMARY_DB = {
  "PRIMARY_4": {
    "Mathematics": [{"topic": "Whole Numbers", "competency": "Read and write up to 999,999", "scenario": "Counting pupils in class"}, {"topic": "Addition and Subtraction", "competency": "Add and subtract up to 6 digits", "scenario": "Counting mangoes at market"}],
    "English Language": [{"topic": "Parts of Speech", "competency": "Identify nouns and verbs", "scenario": "The teacher writes on board"}],
    "Integrated Science": [{"topic": "Living Things and Non-Living Things", "competency": "Differentiate living and non-living", "scenario": "Plant vs Stone"}],
    "Social Studies (SST)": [{"topic": "My School", "competency": "Describe school facilities", "scenario": "Drawing school map"}],
    "Christian Religious Education (CRE)": [{"topic": "God the Creator", "competency": "State 3 things God created", "scenario": "Genesis 1"}],
    "Islamic Religious Education (IRE)": [{"topic": "Allah the Creator", "competency": "State 3 creations of Allah", "scenario": "Sun, Moon, People"}]
  },
  "PRIMARY_5": {
    "Mathematics": [{"topic": "LCM and GCD", "competency": "Find LCM and GCD", "scenario": "Two bells ring together"}, {"topic": "Fractions", "competency": "Add and subtract fractions", "scenario": "Sharing cake"}],
    "English Language": [{"topic": "Letter Writing", "competency": "Write an informal letter", "scenario": "Letter to friend in village"}],
    "Integrated Science": [{"topic": "Matter", "competency": "State properties of matter", "scenario": "Water in 3 states"}],
    "Social Studies (SST)": [{"topic": "Our District", "competency": "Name district leaders", "scenario": "Kampala City"}],
    "Christian Religious Education (CRE)": [{"topic": "Jesus' Miracles", "competency": "Narrate 2 miracles", "scenario": "Feeding 5000"}],
    "Islamic Religious Education (IRE)": [{"topic": "5 Pillars of Islam", "competency": "List the 5 pillars", "scenario": "Praying 5 times"}]
  },
  "PRIMARY_6": {
    "Mathematics": [{"topic": "Ratios and Proportions", "competency": "Solve ratio problems", "scenario": "Mixing juice"}, {"topic": "Percentages", "competency": "Calculate discount", "scenario": "Buying in shop"}],
    "English Language": [{"topic": "Active vs Passive Voice", "competency": "Convert active to passive", "scenario": "Chef cooked the food"}],
    "Integrated Science": [{"topic": "Animal Husbandry", "competency": "Describe cattle rearing", "scenario": "Zero grazing"}],
    "Social Studies (SST)": [{"topic": "East African Community", "competency": "Describe EAC countries", "scenario": "Boda to Kenya"}],
    "Christian Religious Education (CRE)": [{"topic": "The Holy Spirit", "competency": "Explain fruits of Holy Spirit", "scenario": "Being patient"}],
    "Islamic Religious Education (IRE)": [{"topic": "6 Pillars of Iman", "competency": "List 6 articles of faith", "scenario": "Believing in angels"}]
  },
  "PRIMARY_7": {
    "Mathematics": [{"topic": "Speed Distance Time", "competency": "Solve SDT problems", "scenario": "Taxi from Kampala to Jinja"}, {"topic": "Geometry", "competency": "Construct angles", "scenario": "Using ruler and compass"}],
    "English Language": [{"topic": "Functional Texts", "competency": "Interpret notices and adverts", "scenario": "Health poster"}],
    "Integrated Science": [{"topic": "Environmental Degradation", "competency": "Suggest ways to conserve", "scenario": "NEMA and Mabira forest"}],
    "Social Studies (SST)": [{"topic": "The African Continent", "competency": "Describe Africa", "scenario": "Second largest continent"}],
    "Christian Religious Education (CRE)": [{"topic": "Witnessing for Christ", "competency": "Explain sharing values", "scenario": "Sunday school"}],
    "Islamic Religious Education (IRE)": [{"topic": "Akhlaq", "competency": "Show good character", "scenario": "Not cheating in exams"}]
  }
}

PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}

def get_topic_data(grade, subject, topic_name):
    grade_key = f"PRIMARY_{grade}"
    if grade_key in PRIMARY_DB and subject in PRIMARY_DB[grade_key]:
        for t in PRIMARY_DB[grade_key][subject]:
            if t["topic"] == topic_name: return t
    return None

@st.cache_resource
def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("GROQ_API_KEY missing in secrets"); return None

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en'); fp = io.BytesIO(); tts.write_to_fp(fp); fp.seek(0); return fp
    except: return None

def generate_pdf(content, title):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14); c.drawString(40, height-50, title)
    y = height - 80; c.setFont("Helvetica", 9)
    for line in content.split('\n')[:40]:
        c.drawString(40, y, line[:90]); y -= 14
        if y < 50: break
    c.save(); buffer.seek(0); return buffer

# ===================== 4. PASSWORD =====================
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

# ===================== 5. MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026 NCDC")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"])
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])

topic_data = get_topic_data(grade, subject, topic)

if topic_data is None:
    st.error(f"⚠️ Topic not found in NCDC 2026 for {grade} {subject}")
    st.stop()

st.subheader(f"{grade} {subject}: {topic_data['topic']}")
st.info(f"**NCDC Competency**: {topic_data['competency']}")
st.success(f"**Ugandan Example**: {topic_data['scenario']}")

tabs = st.tabs(["AI Chat + Voice", "Theory Mode", "Math Work Page", "Quiz Generator", "Teacher Tools", "Dictionary"])

with tabs[0]:
    st.header("Ask TeacherK + Voice Answer")
    user_question = st.text_input("Ask any question about this NCDC topic")
    if st.button("🚀 Ask") and user_question:
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\n\nGrade: P{grade}\nSubject: {subject}\nTopic: {topic_data['topic']}\nCompetency: {topic_data['competency']}\nPupil Question: {user_question}"
            res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
            answer = res.choices[0].message.content
            st.write(answer)
            audio = text_to_speech(answer)
            if audio: st.audio(audio)

with tabs[1]:
    st.header("Theory Mode - Step by Step")
    if st.button("Explain Topic Simply"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\n\nExplain P{grade} {subject} topic: {topic_data['topic']} in 5 simple steps for a 12 year old. Use Ugandan example."
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
            st.write(res.choices[0].message.content)

with tabs[2]:
    st.header("Mathematics Work Page - Mental Math")
    op = st.selectbox("Operation", ["Addition", "Subtraction", "Multiplication", "Division"])
    if st.button("Generate 10 Questions"):
        max_num = 20 if grade in ["P4","P5"] else 100
        for i in range(10):
            a=random.randint(1,max_num); b=random.randint(1,10)
            st.write(f"{i+1}. {a} {op[0]} {b} =?")

with tabs[3]:
    st.header("Primary Quiz Generator - NCDC Style")
    if st.button("Generate 10 Q Quiz"):
        client = get_client()
        if client:
            difficulty = "Easy" if grade=="P4" else "Medium" if grade in ["P5","P6"] else "Hard PLE level"
            prompt = f"{SYSTEM_PROMPT}\n\nGenerate 10 {difficulty} MCQ quiz for P{grade} {subject} topic: {topic_data['topic']}. Follow NCDC format. Provide answers."
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
            st.write(res.choices[0].message.content)

with tabs[4]:
    st.header("Teacher Tools - NCDC 2026")
    if st.session_state.user_type == "Teacher":
        if st.button("1. Generate NCDC Lesson Plan"):
            client = get_client()
            if client:
                prompt = f"{SYSTEM_PROMPT}\n\nWrite NCDC 2026 lesson plan for P{grade} {subject} Topic: {topic_data['topic']}. Include: Objectives, Materials, Introduction, Steps, Conclusion, Assessment"
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
                plan = res.choices[0].message.content
                st.write(plan)
                st.download_button("Download Lesson PDF", generate_pdf(plan, "NCDC Lesson Plan"), "lesson.pdf")

        if st.button("2. Generate P7 PLE Mock Paper"):
            st.info("Generating 50 questions. Wait 30 seconds...")
            client = get_client()
            if client:
                prompt = f"{SYSTEM_PROMPT}\n\nGenerate full P7 {subject} PLE mock paper 50 questions with marking guide. Follow NCDC 2026 format."
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
                paper = res.choices[0].message.content
                st.write(paper)
                st.download_button("Download Mock PDF", generate_pdf(paper, "P7 PLE Mock"), "mock.pdf")

with tabs[5]:
    st.header("Offline English Dictionary")
    word = st.text_input("Search word")
    if st.button("Search"):
        meaning = ENGLISH_DICTIONARY.get(grade, {}).get(word, "Not found in P4-P7 dictionary")
        st.success(f"**{word}**: {meaning}")

st.sidebar.divider()
st.sidebar.caption("Locked to NCDC 2026 Uganda Primary")
st.sidebar.markdown(f"**Support**: WhatsApp {CONTACT}")
