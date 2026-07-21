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

# ===================== 1. DISCLAIMER =====================
st.warning("⚠️ **DISCLAIMER**: TEACHERK is an AI learning assistant. Pupils must confirm all answers with your Class Teacher before exams.")

# ===================== 2. DICTIONARY =====================
ENGLISH_DICTIONARY = {
    "P4": {"Adjective": "Describing word", "Noun": "Naming word", "Verb": "Action word"},
    "P5": {"Composition": "Story with beginning", "Synonym": "Big = Large", "Antonym": "Hot = Cold"},
    "P6": {"Direct Speech": "Exact quotes", "Active Voice": "Subject does action", "Debate": "Formal talk"},
    "P7": {"Functional Text": "Notice, Advert", "Comprehension": "Reading + questions", "Summary": "Short version"}
}

# ===================== 3. FULL DB P4-P7 =====================
PRIMARY_DB = {
  "PRIMARY_4": {
    "Mathematics": [{"topic": "Whole Numbers", "competency": "Read up to 999,999", "scenario": "Counting pupils"}, {"topic": "Addition and Subtraction", "competency": "Add/subtract 6 digits", "scenario": "Counting mangoes"}],
    "English Language": [{"topic": "Parts of Speech", "competency": "Identify nouns", "scenario": "The teacher writes"}],
    "Integrated Science": [{"topic": "Living Things", "competency": "Differentiate", "scenario": "Plant vs Stone"}],
    "Social Studies (SST)": [{"topic": "My School", "competency": "Describe facilities", "scenario": "School map"}],
    "Christian Religious Education (CRE)": [{"topic": "God the Creator", "competency": "State 3 creations", "scenario": "Genesis 1"}],
    "Islamic Religious Education (IRE)": [{"topic": "Allah the Creator", "competency": "State 3 creations", "scenario": "Sun"}]
  },
  "PRIMARY_5": {
    "Mathematics": [{"topic": "LCM and GCD", "competency": "Find LCM", "scenario": "Two bells"}],
    "English Language": [{"topic": "Letter Writing", "competency": "Write letter", "scenario": "Letter to friend"}],
    "Integrated Science": [{"topic": "Matter", "competency": "State properties", "scenario": "Water"}],
    "Social Studies (SST)": [{"topic": "Our District", "competency": "Name leaders", "scenario": "Kampala"}],
    "Christian Religious Education (CRE)": [{"topic": "Jesus' Miracles", "competency": "Narrate miracles", "scenario": "Feeding 5000"}],
    "Islamic Religious Education (IRE)": [{"topic": "5 Pillars of Islam", "competency": "List pillars", "scenario": "Praying"}]
  },
  "PRIMARY_6": {
    "Mathematics": [{"topic": "Ratios and Proportions", "competency": "Solve ratios", "scenario": "Mix juice"}],
    "English Language": [{"topic": "Active vs Passive Voice", "competency": "Convert", "scenario": "Chef cooked"}],
    "Integrated Science": [{"topic": "Animal Husbandry", "competency": "Describe cattle", "scenario": "Zero grazing"}],
    "Social Studies (SST)": [{"topic": "East African Community", "competency": "Describe EAC", "scenario": "Boda"}],
    "Christian Religious Education (CRE)": [{"topic": "The Holy Spirit", "competency": "Explain fruits", "scenario": "Patience"}],
    "Islamic Religious Education (IRE)": [{"topic": "6 Pillars of Iman", "competency": "List 6", "scenario": "Believe"}]
  },
  "PRIMARY_7": {
    "Mathematics": [{"topic": "Speed Distance Time", "competency": "Solve SDT", "scenario": "Taxi"}],
    "English Language": [{"topic": "Functional Texts", "competency": "Interpret notices", "scenario": "Poster"}],
    "Integrated Science": [{"topic": "Environmental Degradation", "competency": "Conserve", "scenario": "NEMA"}],
    "Social Studies (SST)": [{"topic": "African Continent", "competency": "Describe Africa", "scenario": "Second largest"}],
    "Christian Religious Education (CRE)": [{"topic": "Witnessing for Christ", "competency": "Explain", "scenario": "Sunday school"}],
    "Islamic Religious Education (IRE)": [{"topic": "Akhlaq", "competency": "Good character", "scenario": "No cheating"}]
  }
}

# BUILD MAP FROM DB - GUARANTEED TO MATCH
PRIMARY_CURRICULUM_MAP = {}
for g_key, g_data in PRIMARY_DB.items():
    grade = g_key.replace("PRIMARY_","P")
    PRIMARY_CURRICULUM_MAP[grade] = {}
    for subject, topics in g_data.items():
        PRIMARY_CURRICULUM_MAP[grade][subject] = [t["topic"] for t in topics]

def get_topic_data(grade, subject, topic_name):
    grade_key = f"PRIMARY_{grade}"
    if grade_key in PRIMARY_DB and subject in PRIMARY_DB[grade_key]:
        for t in PRIMARY_DB[grade_key][subject]:
            if t["topic"] == topic_name: return t
    return None

@st.cache_resource
def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: return None

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en'); fp = io.BytesIO(); tts.write_to_fp(fp); fp.seek(0); return fp
    except: return None

def generate_pdf(content, title):
    buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
    c.setFont("Helvetica-Bold", 14); c.drawString(40, height-50, title); y = height - 80; c.setFont("Helvetica", 9)
    for line in content.split('\n')[:40]: c.drawString(40, y, line[:90]); y -= 14;
    if y < 50: break
    c.save(); buffer.seek(0); return buffer

# ===================== 4. PASSWORD =====================
def check_password():
    APP_PW = st.secrets.get("PRIMARY_APP_PASSWORD", "PRIMARY2026")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "ADMIN256")
    if "password_correct" not in st.session_state:
        st.title("🔒 TEACHERK PRIMARY 2026")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == APP_PW: st.session_state["user_type"] = "Pupil"; st.session_state["password_correct"] = True; st.rerun()
            elif pw == ADMIN_PW: st.session_state["user_type"] = "Teacher"; st.session_state["password_correct"] = True; st.rerun()
            else: st.error("Wrong password")
        st.stop()

check_password()

# ===================== 5. MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"])
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])

topic_data = get_topic_data(grade, subject, topic)

# THE CRITICAL FIX: NO CRASH IF NONE
if topic_data is None:
    st.error(f"⚠️ Topic data missing for {grade} {subject}. Please select another topic.")
    st.stop()

st.subheader(f"{grade} {subject}: {topic_data['topic']}")
st.info(f"**Competency**: {topic_data['competency']}")
st.success(f"**Example**: {topic_data['scenario']}")

tabs = st.tabs(["AI Chat + Voice", "Theory Mode", "Math Work Page", "Quiz Generator", "Teacher Tools", "Dictionary"])

with tabs[0]:
    st.header("Ask TeacherK + Voice")
    user_question = st.text_input("Ask any question")
    if st.button("🚀 Ask") and user_question:
        client = get_client()
        if client:
            prompt = f"Teach P{grade} {subject}. Topic: {topic_data['topic']}. Use Ugandan examples. Q: {user_question}"
            res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"user","content":prompt}])
            answer = res.choices[0].message.content; st.write(answer)
            audio = text_to_speech(answer);
            if audio: st.audio(audio)

with tabs[1]:
    st.header("Theory Mode")
    if st.button("Explain Topic"):
        client = get_client()
        if client:
            prompt = f"Explain P{grade} {subject} topic: {topic_data['topic']} in 5 simple steps"
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
            st.write(res.choices[0].message.content)

with tabs[2]:
    st.header("Mathematics Work Page")
    op = st.selectbox("Operation", ["Addition", "Subtraction", "Multiplication", "Division"])
    if st.button("Generate 10 Questions"):
        for i in range(10):
            a=random.randint(1,20); b=random.randint(1,10)
            st.write(f"{i+1}. {a} {op[0]} {b} =?")

with tabs[3]:
    st.header("Quiz Generator")
    if st.button("Generate 10 Q Quiz"):
        client = get_client()
        if client:
            prompt = f"Generate 10 MCQ quiz for P{grade} {subject} topic: {topic_data['topic']} with answers"
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
            st.write(res.choices[0].message.content)

with tabs[4]:
    st.header("Teacher Tools")
    if st.session_state.user_type == "Teacher":
        if st.button("Generate Lesson Plan"):
            client = get_client()
            if client:
                prompt = f"Write NCDC lesson plan for P{grade} {subject} Topic: {topic_data['topic']}"
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
                plan = res.choices[0].message.content; st.write(plan)
                st.download_button("Download PDF", generate_pdf(plan, "Lesson Plan"), "lesson.pdf")

        if st.button("Generate P7 Mock Paper"):
            st.info("This will generate 50 questions. Click and wait 30 seconds.")
            client = get_client()
            if client:
                prompt = f"Generate full P7 {subject} mock paper 50 questions with marking guide"
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
                st.write(res.choices[0].message.content)

with tabs[5]:
    st.header("Dictionary")
    word = st.text_input("Search word")
    if st.button("Search"):
        meaning = ENGLISH_DICTIONARY.get(grade, {}).get(word, "Not found")
        st.success(f"**{word}**: {meaning}")

st.sidebar.markdown(f"**Support**: WhatsApp {CONTACT}")
