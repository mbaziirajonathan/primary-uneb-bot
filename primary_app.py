import streamlit as st
import os, io, json, difflib, time
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

# ===================== 1. OFFLINE DICTIONARY =====================
ENGLISH_DICTIONARY = {
    "P4": {"Adjective": "A describing word. Ex: tall teacher, red book", "Noun": "A naming word. Ex: school, pupil, Kampala", "Verb": "An action word. Ex: run, read, write"},
    "P5": {"Composition": "A story with beginning, middle, and end. Use 5 paragraphs.", "Synonym": "Words with same meaning. Ex: Big = Large", "Antonym": "Words with opposite meaning. Ex: Hot = Cold"},
    "P6": {"Direct Speech": "When we quote exact words. Ex: Teacher said, 'Close the door'", "Active Voice": "Subject does action. Ex: The boy kicked the ball", "Debate": "A formal discussion where people argue for/against"},
    "P7": {"Functional Text": "Real life texts: Notice, Advert, Report, Letter", "Comprehension": "Reading a passage and answering questions", "Speech": "Talking to many people. Start with greeting."}
}

# ===================== 2. NCDC PRIMARY DATABASE =====================
PRIMARY_DB = {
  "PRIMARY_4": {
    "focus": "Foundation & Concrete Concepts",
    "Mathematics": [
      {"topic": "Whole Numbers up to 6 digits", "competency": "Read and write numbers up to 999,999", "scenario": "Counting all pupils in 5 schools"},
      {"topic": "Addition and Subtraction", "competency": "Add and subtract up to 6 digits", "scenario": "Counting total mangoes harvested"}
    ],
    "English Language": [
      {"topic": "Parts of Speech: Noun and Verb", "competency": "Identify nouns and verbs", "scenario": "The teacher writes on the board"},
      {"topic": "Composition: Picture Composition", "competency": "Write 5 sentences from a picture", "scenario": "Describe a market day"}
    ],
    "Integrated Science": [
      {"topic": "Living Things and Non-Living Things", "competency": "Differentiate living and non-living", "scenario": "Plant vs Stone"},
      {"topic": "The Human Body", "competency": "Name 5 sense organs", "scenario": "We use eyes to see"}
    ],
    "Social Studies (SST)": [
      {"topic": "My School", "competency": "Describe school facilities", "scenario": "Drawing school map"},
      {"topic": "Direction and Weather", "competency": "Identify 4 cardinal points", "scenario": "Sun rises in the East"}
    ],
    "Christian Religious Education (CRE)": [
      {"topic": "God the Creator", "competency": "State 3 things God created", "scenario": "Genesis 1 story"},
      {"topic": "The Ten Commandments", "competency": "List 5 commandments", "scenario": "Obeying parents"}
    ],
    "Islamic Religious Education (IRE)": [
      {"topic": "Allah the Creator", "competency": "State 3 creations of Allah", "scenario": "Sun, Moon, Animals"},
      {"topic": "Prophet Muhammad (SAW)", "competency": "State 2 teachings of the Prophet", "scenario": "Being kind to neighbors"}
    ]
  },
  "PRIMARY_5": {
    "focus": "Building Skills & Local Context",
    "Mathematics": [
      {"topic": "LCM and GCD", "competency": "Find LCM and GCD of numbers", "scenario": "Two bells ring every 6 and 8 minutes"},
      {"topic": "Fractions", "competency": "Add and subtract fractions", "scenario": "Sharing 1/2 cake among 4 pupils"}
    ],
    "English Language": [
      {"topic": "Parts of Speech: Adjective and Adverb", "competency": "Use adjectives and adverbs", "scenario": "The fast car. The girl runs quickly"},
      {"topic": "Letter Writing", "competency": "Write an informal letter", "scenario": "Letter to a friend in Gulu"}
    ],
    "Integrated Science": [
      {"topic": "Matter: Solids, Liquids, Gases", "competency": "State 3 properties of each", "scenario": "Water in 3 states"},
      {"topic": "First Aid", "competency": "Describe how to treat a cut", "scenario": "Pupil falls in class"}
    ],
    "Social Studies (SST)": [
      {"topic": "Our District", "competency": "Name leaders and economic activities", "scenario": "Kampala district activities"},
      {"topic": "Climate and Vegetation", "competency": "Describe equatorial climate", "scenario": "Rainforests in Uganda"}
    ],
    "Christian Religious Education (CRE)": [
      {"topic": "Jesus' Miracles", "competency": "Narrate 2 miracles", "scenario": "Feeding 5000 people"},
      {"topic": "Parables of Jesus", "competency": "Explain the Good Samaritan", "scenario": "Helping a stranger"}
    ],
    "Islamic Religious Education (IRE)": [
      {"topic": "The 5 Pillars of Islam", "competency": "List and explain the 5 pillars", "scenario": "Praying 5 times a day"},
      {"topic": "Stories of Prophets", "competency": "Narrate story of Prophet Musa", "scenario": "Pharaoh and the Red Sea"}
    ]
  },
  "PRIMARY_6": {
    "focus": "Advanced Application & Regional Scope - EAC",
    "Mathematics": [
      {"topic": "Ratios and Proportions", "competency": "Solve ratio problems", "scenario": "Mixing juice in ratio 2:3"},
      {"topic": "Percentages", "competency": "Calculate discounts and profit", "scenario": "Shopkeeper sells a book"}
    ],
    "English Language": [
      {"topic": "Active vs Passive Voice", "competency": "Convert active to passive", "scenario": "The chef cooked the food"},
      {"topic": "Debate and Speech", "competency": "Present points for and against", "scenario": "Should P7 do homework?"}
    ],
    "Integrated Science": [
      {"topic": "Animal Husbandry", "competency": "Describe cattle rearing", "scenario": "Zero grazing in Wakiso"},
      {"topic": "Heat and Temperature", "competency": "Explain methods of heat transfer", "scenario": "Cooking on a charcoal stove"}
    ],
    "Social Studies (SST)": [
      {"topic": "East African Community", "competency": "Describe EAC member states", "scenario": "A boda rider going to Kenya"},
      {"topic": "Transport and Communication", "competency": "Compare road and railway", "scenario": "SGR from Kampala to Mombasa"}
    ],
    "Christian Religious Education (CRE)": [
      {"topic": "The Holy Spirit", "competency": "Explain fruits of the Holy Spirit", "scenario": "Being patient during PLE"},
      {"topic": "The Early Church", "competency": "Describe work of apostles", "scenario": "Sharing in Acts 2"}
    ],
    "Islamic Religious Education (IRE)": [
      {"topic": "The Pillars of Iman", "competency": "List the 6 articles of faith", "scenario": "Believing in angels and Qadr"},
      {"topic": "Islamic Festivals", "competency": "Explain Eid Adhuha", "scenario": "Slaughtering a ram"}
    ]
  },
  "PRIMARY_7": {
    "focus": "PLE Candidate Class - Mastery & Critical Thinking",
    "Mathematics": [
      {"topic": "Speed, Distance and Time", "competency": "Solve SDT problems", "scenario": "A taxi from Kampala to Jinja 80km"},
      {"topic": "Geometry: Angles and Constructions", "competency": "Construct 60 and 90 degrees", "scenario": "Using ruler and compass"}
    ],
    "English Language": [
      {"topic": "Analyzing Functional Texts", "competency": "Interpret notices and adverts", "scenario": "Understanding a health poster"},
      {"topic": "Comprehension and Summary", "competency": "Summarize a passage in 8 sentences", "scenario": "PLE Paper 2 format"}
    ],
    "Integrated Science": [
      {"topic": "Environmental Degradation", "competency": "Suggest ways to conserve environment", "scenario": "NEMA cutting trees in Mabira"},
      {"topic": "Electricity", "competency": "Draw and explain simple circuits", "scenario": "Connecting bulbs in series"}
    ],
    "Social Studies (SST)": [
      {"topic": "The African Continent", "competency": "Describe location and size of Africa", "scenario": "Second largest continent"},
      {"topic": "Global Issues: COVID-19", "competency": "State effects and prevention", "scenario": "Washing hands and sanitizers"}
    ],
    "Christian Religious Education (CRE)": [
      {"topic": "Witnessing for Christ", "competency": "Explain ways of sharing Christian values", "scenario": "Helping in Sunday school"},
      {"topic": "Christian Living", "competency": "Apply Christian values today", "scenario": "Not cheating in PLE"}
    ],
    "Islamic Religious Education (IRE)": [
      {"topic": "Akhlaq: Good Character", "competency": "Demonstrate honesty and respect", "scenario": "Returning lost property"},
      {"topic": "Islam and Society", "competency": "Explain role of Islam in development", "scenario": "Muslims building schools"}
    ]
  }
}

# ===================== 3. HELPERS =====================
PRIMARY_CURRICULUM_MAP = {}
for grade_key, grade_data in PRIMARY_DB.items():
    grade_label = grade_key.replace("PRIMARY_","P")
    PRIMARY_CURRICULUM_MAP[grade_label] = {subject: [t["topic"] for t in topics] for subject, topics in grade_data.items() if subject!= "focus"}

def get_topic_data(grade, subject, topic_name):
    grade_key = f"PRIMARY_{grade}"
    if grade_key in PRIMARY_DB and subject in PRIMARY_DB[grade_key]:
        for t in PRIMARY_DB[grade_key][subject]:
            if t["topic"] == topic_name:
                return t
    return None

def fuzzy_match(word, dictionary):
    matches = difflib.get_close_matches(word.lower(), dictionary.keys(), n=1, cutoff=0.7)
    return dictionary[matches[0]] if matches else None

def generate_pdf_report(df, grade, subject):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16); c.drawString(50, height-50, f"TEACHERK PRIMARY {grade} REPORT")
    c.setFont("Helvetica", 12); c.drawString(50, height-75, f"Subject: {subject}"); c.drawString(50, height-95, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    y = height - 130
    for i, row in df.iterrows():
        text = f"{i+1}. Q: {row['Question'][:80]}... | A: {row['AI_Response'][:80]}..."
        c.drawString(40, y, text); y -= 20
        if y < 50: c.showPage(); y = height - 50
    c.save(); buffer.seek(0); return buffer

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        fp = io.BytesIO(); tts.write_to_fp(fp); fp.seek(0); return fp
    except: return None

def log_usage(grade, subject, topic, question):
    entry = {"timestamp": datetime.now().isoformat(), "grade": grade, "subject": subject, "topic": topic, "question": question}
    try:
        data = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: data = json.load(f)
        data.append(entry)
        with open(LOG_FILE, "w") as f: json.dump(data, f, indent=2)
    except: pass

# ===================== 4. PASSWORD =====================
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
        st.title("🔒 TEACHERK PRIMARY 2026")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.info("Pupil: PRIMARY2026 | Teacher: ADMIN256"); st.stop()
    elif not st.session_state["password_correct"]:
        st.title("🔒 TEACHERK PRIMARY 2026")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😠 Wrong password"); st.stop()

check_password()
st.set_page_config(page_title="TEACHERK PRIMARY 2026", page_icon="🐢", layout="wide")

@st.cache_resource
def get_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

# ===================== 5. MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026")
st.caption("NCDC Aligned | AI + Dictionary + Dashboard")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

col1, col2, col3 = st.sidebar.columns(3)
grade = col1.selectbox("Class", ["P4","P5","P6","P7"])
subject = col2.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = col3.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])

topic_data = get_topic_data(grade, subject, topic)

if topic_data is None:
    st.error(f"⚠️ Topic '{topic}' not found in NCDC database for {grade} {subject} yet.")
    st.stop()

st.subheader(f"{grade} {subject}: {topic_data['topic']}")
st.info(f"**Competency**: {topic_data['competency']}")
st.success(f"**Example**: {topic_data['scenario']}")

st.divider()
colA, colB = st.columns(2)

with colA:
    st.header("1. Ask TeacherK AI")
    user_question = st.text_input("Ask any question about this topic")
    if st.button("🚀 Get Answer", type="primary"):
        if user_question:
            log_usage(grade, subject, topic, user_question)
            client = get_client()
            model = AI_MODEL_LONG if len(user_question) > 100 else AI_MODEL_FAST
            prompt = f"You are TEACHERK for PRIMARY {grade}. Subject: {subject}. Topic: {topic_data['topic']}. Competency: {topic_data['competency']}. Use Ugandan examples. Question: {user_question}"
            with st.spinner("TeacherK is thinking..."):
                res = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
                answer = res.choices[0].message.content
                st.write(answer)
                audio = text_to_speech(answer)
                if audio: st.audio(audio, format="audio/mp3")
        else: st.warning("Type a question first")

with colB:
    st.header("2. Offline English Dictionary")
    word = st.text_input("Look up English term")
    if st.button("📖 Search Dictionary"):
        if word:
            meaning = fuzzy_match(word, ENGLISH_DICTIONARY.get(grade, {}))
            if meaning: st.success(f"**{word}**: {meaning}")
            else: st.warning("Not in P4-P7 dictionary yet")

st.divider()

if st.session_state.user_type == "Teacher":
    st.header("3. Teacher Dashboard & Reports")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f: log_data = json.load(f)
        df = pd.DataFrame(log_data)
        st.dataframe(df.tail(10))
        if st.button("📄 Download PDF Report"):
            pdf = generate_pdf_report(df, grade, subject)
            st.download_button("Download PDF", pdf, "report.pdf", "application/pdf")
    else: st.info("No usage data yet")

st.sidebar.divider()
st.sidebar.markdown(f"**Support**: WhatsApp {CONTACT}")
