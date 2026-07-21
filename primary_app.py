import streamlit as st
import os, io, json, difflib, random, time
import pandas as pd
from datetime import datetime
from groq import Groq
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from gtts import gTTS

# ===================== CONFIG =====================
LOG_FILE = "usage_log_primary.json"
CONTACT = "256751040731"
AI_MODEL_LONG = "llama-3.3-70b-versatile"
AI_MODEL_FAST = "llama-3.1-8b-instant"

st.set_page_config(page_title="TEACHERK PRIMARY 2026", page_icon="🐢", layout="wide")

# ===================== 1. DISCLAIMER =====================
def show_disclaimer():
    st.warning("⚠️ **DISCLAIMER**: TEACHERK is an AI learning assistant. Pupils must confirm all answers with your Class Teacher before exams. AI can make mistakes.")

# ===================== 2. OFFLINE ENGLISH DICTIONARY PER CLASS =====================
ENGLISH_DICTIONARY = {
    "P4": {"Adjective": "Describing word. Ex: tall teacher", "Noun": "Naming word. Ex: school", "Verb": "Action word. Ex: run", "Sentence": "Group of words with meaning"},
    "P5": {"Composition": "Story with beginning, middle, end", "Synonym": "Big = Large", "Antonym": "Hot = Cold", "Paragraph": "Group of sentences"},
    "P6": {"Direct Speech": "Teacher said, 'Close door'", "Indirect Speech": "Teacher told us to close the door", "Active Voice": "Boy kicked ball", "Debate": "Formal discussion"},
    "P7": {"Functional Text": "Notice, Advert, Report, Letter", "Comprehension": "Reading and answering questions", "Speech": "Talking to many people", "Summary": "Short version of passage"}
}

# ===================== 3. FULL NCDC PRIMARY DATABASE P4-P7 =====================
PRIMARY_DB = {
  "PRIMARY_4": {
    "focus": "Foundation",
    "Mathematics": [{"topic": "Whole Numbers", "competency": "Read up to 999,999", "scenario": "Counting pupils"}, {"topic": "Addition and Subtraction", "competency": "Add/subtract 6 digits", "scenario": "Counting mangoes"}],
    "English Language": [{"topic": "Parts of Speech", "competency": "Identify nouns and verbs", "scenario": "The teacher writes"}],
    "Integrated Science": [{"topic": "Living Things", "competency": "Differentiate living", "scenario": "Plant vs Stone"}],
    "Social Studies (SST)": [{"topic": "My School", "competency": "Describe facilities", "scenario": "School map"}],
    "Christian Religious Education (CRE)": [{"topic": "God the Creator", "competency": "State 3 creations", "scenario": "Genesis 1"}],
    "Islamic Religious Education (IRE)": [{"topic": "Allah the Creator", "competency": "State 3 creations", "scenario": "Sun, Moon"}]
  },
  "PRIMARY_5": {
    "focus": "Building Skills",
    "Mathematics": [{"topic": "LCM and GCD", "competency": "Find LCM and GCD", "scenario": "Two bells ring"}, {"topic": "Fractions", "competency": "Add fractions", "scenario": "Share cake"}],
    "English Language": [{"topic": "Letter Writing", "competency": "Write informal letter", "scenario": "Letter to friend"}],
    "Integrated Science": [{"topic": "Matter", "competency": "State properties", "scenario": "Water states"}],
    "Social Studies (SST)": [{"topic": "Our District", "competency": "Name leaders", "scenario": "Kampala"}],
    "Christian Religious Education (CRE)": [{"topic": "Jesus' Miracles", "competency": "Narrate 2 miracles", "scenario": "Feeding 5000"}],
    "Islamic Religious Education (IRE)": [{"topic": "5 Pillars of Islam", "competency": "List 5 pillars", "scenario": "Praying"}]
  },
  "PRIMARY_6": {
    "focus": "EAC Scope",
    "Mathematics": [{"topic": "Ratios and Proportions", "competency": "Solve ratios", "scenario": "Mix juice"}, {"topic": "Percentages", "competency": "Calculate discount", "scenario": "Shop"}],
    "English Language": [{"topic": "Active vs Passive Voice", "competency": "Convert voices", "scenario": "Chef cooked"}],
    "Integrated Science": [{"topic": "Animal Husbandry", "competency": "Describe cattle", "scenario": "Zero grazing"}],
    "Social Studies (SST)": [{"topic": "East African Community", "competency": "Describe EAC", "scenario": "Boda to Kenya"}],
    "Christian Religious Education (CRE)": [{"topic": "The Holy Spirit", "competency": "Explain fruits", "scenario": "Being patient"}],
    "Islamic Religious Education (IRE)": [{"topic": "6 Pillars of Iman", "competency": "List 6 articles", "scenario": "Believe angels"}]
  },
  "PRIMARY_7": {
    "focus": "PLE Candidate",
    "Mathematics": [{"topic": "Speed Distance Time", "competency": "Solve SDT", "scenario": "Taxi Kampala-Jinja"}, {"topic": "Geometry", "competency": "Construct angles", "scenario": "Ruler and compass"}],
    "English Language": [{"topic": "Functional Texts", "competency": "Interpret notices", "scenario": "Health poster"}],
    "Integrated Science": [{"topic": "Environmental Degradation", "competency": "Suggest conservation", "scenario": "NEMA Mabira"}],
    "Social Studies (SST)": [{"topic": "African Continent", "competency": "Describe Africa", "scenario": "Second largest"}],
    "Christian Religious Education (CRE)": [{"topic": "Witnessing for Christ", "competency": "Explain sharing", "scenario": "Sunday school"}],
    "Islamic Religious Education (IRE)": [{"topic": "Akhlaq", "competency": "Show good character", "scenario": "No cheating"}]
  }
}

# BUILD MAP FROM DB - NO HALLUCINATION
PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items() if s!="focus"} for g,d in PRIMARY_DB.items()}

def get_topic_data(grade, subject, topic_name):
    grade_key = f"PRIMARY_{grade}"
    if grade_key in PRIMARY_DB and subject in PRIMARY_DB[grade_key]:
        for t in PRIMARY_DB[grade_key][subject]:
            if t["topic"] == topic_name: return t
    return None

# ===================== 4. HELPERS =====================
@st.cache_resource
def get_client(): return Groq(api_key=st.secrets["GROQ_API_KEY"])

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        fp = io.BytesIO(); tts.write_to_fp(fp); fp.seek(0); return fp
    except: return None

def generate_pdf(content, title):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
    c.setFont("Helvetica-Bold", 16); c.drawString(50, height-50, title)
    y = height - 80; c.setFont("Helvetica", 10)
    for line in content.split('\n'):
        c.drawString(40, y, line[:95]); y -= 15
        if y < 50: c.showPage(); y = height - 50
    c.save(); buffer.seek(0); return buffer

def log_usage(entry):
    try:
        data = json.load(open(LOG_FILE)) if os.path.exists(LOG_FILE) else []
        data.append(entry); json.dump(data, open(LOG_FILE, "w"), indent=2)
    except: pass

# ===================== 5. PASSWORD =====================
def check_password():
    APP_PW = st.secrets.get("PRIMARY_APP_PASSWORD", "PRIMARY2026")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "ADMIN256")
    def password_entered():
        pw = st.session_state["password"]
        if pw == APP_PW: st.session_state["user_type"] = "Pupil"; st.session_state["password_correct"] = True
        elif pw == ADMIN_PW: st.session_state["user_type"] = "Teacher"; st.session_state["password_correct"] = True
        else: st.session_state["password_correct"] = False
        del st.session_state["password"]
    if "password_correct" not in st.session_state:
        st.title("🔒 TEACHERK PRIMARY 2026"); st.text_input("Password", type="password", on_change=password_entered, key="password"); st.stop()
    elif not st.session_state["password_correct"]:
        st.title("🔒 TEACHERK PRIMARY 2026"); st.text_input("Password", type="password", on_change=password_entered, key="password"); st.error("Wrong"); st.stop()

check_password()
show_disclaimer()

# ===================== 6. MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"])
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])
topic_data = get_topic_data(grade, subject, topic)

st.subheader(f"{grade} {subject}: {topic_data['topic']}")
st.info(f"**Competency**: {topic_data['competency']}")
st.success(f"**Example**: {topic_data['scenario']}")

tabs = st.tabs(["AI Chat + Voice", "Theory Mode", "Math Work Page", "Quiz Generator", "Teacher Tools", "Dictionary"])

with tabs[0]:
    st.header("Ask TeacherK + Voice Answer")
    user_question = st.text_input("Ask any question")
    if st.button("🚀 Ask"):
        client = get_client(); prompt = f"Teach P{grade} {subject}. Topic: {topic_data['topic']}. Use Ugandan examples. Q: {user_question}"
        res = client.chat.completions.create(model=AI_MODEL_FAST, messages=[{"role":"user","content":prompt}])
        answer = res.choices[0].message.content; st.write(answer)
        audio = text_to_speech(answer);
        if audio: st.audio(audio, format="audio/mp3")
        log_usage({"time":str(datetime.now()), "grade":grade, "q":user_question})

with tabs[1]:
    st.header("Theory Mode - Step by Step")
    if st.button("Explain Topic"):
        client = get_client(); prompt = f"Explain P{grade} {subject} topic: {topic_data['topic']} in 5 simple steps for a child with examples"
        res = client.chat.completions.create(model=AI_MODEL_LONG, messages=[{"role":"user","content":prompt}])
        st.write(res.choices[0].message.content)

with tabs[2]:
    st.header("Mathematics Work Page - Mental Math")
    op = st.selectbox("Operation", ["Addition", "Subtraction", "Multiplication", "Division"])
    num_q = st.slider("Questions", 5, 20, 10)
    if st.button("Start Drill"):
        score=0
        for i in range(num_q):
            a=random.randint(1,20 if grade in ["P4","P5"] else 100)
            b=random.randint(1,10 if grade in ["P4","P5"] else 50)
            ans = eval(f"{a}+{b}" if op=="Addition" else f"{a}-{b}" if op=="Subtraction" else f"{a}*{b}" if op=="Multiplication" else f"{a}/{b}")
            user_ans = st.number_input(f"{i+1}. {a} {op[0]} {b} = ", key=f"{i}{op}")
            if user_ans == round(ans,2): score+=1
        st.success(f"Score: {score}/{num_q}")

with tabs[3]:
    st.header("Primary Quiz Generator")
    difficulty = "Easy" if grade in ["P4"] else "Medium" if grade in ["P5","P6"] else "Hard"
    num = st.slider("No. of Questions", 5, 20, 10)
    if st.button("Generate Quiz"):
        client = get_client(); prompt = f"Generate {num} {difficulty} level MCQ quiz for P{grade} {subject} topic: {topic_data['topic']}. Provide answers"
        res = client.chat.completions.create(model=AI_MODEL_LONG, messages=[{"role":"user","content":prompt}])
        st.write(res.choices[0].message.content)

with tabs[4]:
    st.header("Teacher Tools")
    if st.session_state.user_type == "Teacher":
        if st.button("1. Generate Lesson Plan"):
            client = get_client(); prompt = f"Write NCDC lesson plan for P{grade} {subject} Topic: {topic_data['topic']}. Include objectives, materials, steps"
            res = client.chat.completions.create(model=AI_MODEL_LONG, messages=[{"role":"user","content":prompt}])
            plan = res.choices[0].message.content; st.write(plan)
            st.download_button("Download Lesson PDF", generate_pdf(plan, "Lesson Plan"), "lesson.pdf")

        if st.button("2. Generate P7 Mock Paper"):
            client = get_client(); prompt = f"Generate full P7 {subject} mock paper 50 questions with marking guide"
            res = client.chat.completions.create(model=AI_MODEL_LONG, messages=[{"role":"user","content":prompt}])
            paper = res.choices[0].message.content; st.write(paper)
            st.download_button("Download Mock PDF", generate_pdf(paper, "P7 Mock"), "mock.pdf")

        if st.button("3. Class Report"):
            if os.path.exists(LOG_FILE):
                df = pd.DataFrame(json.load(open(LOG_FILE)))
                st.dataframe(df); st.download_button("Download Report", generate_pdf(df.to_string(), "Class Report"), "report.pdf")

with tabs[5]:
    st.header("Offline English Dictionary")
    word = st.text_input("Search word")
    if st.button("Search"):
        meaning = ENGLISH_DICTIONARY.get(grade, {}).get(word, "Not found in this class dictionary")
        st.success(f"**{word}**: {meaning}")

st.sidebar.markdown(f"**Support**: WhatsApp {CONTACT}")
