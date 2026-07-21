import streamlit as st
import os, io, json, re, difflib, time
import pandas as pd
from datetime import datetime
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from gtts import gTTS

LOG_FILE = "usage_log_primary.json"
CONTACT = "256751040731"
AI_MODEL_LONG = "llama-3.3-70b-versatile" # 30k TPM - Bulk, Mock, Long notes
AI_MODEL_FAST = "llama-3.1-8b-instant" # 6k TPM - Quick Q&A

# ============ 1. ENGLISH LANGUAGE DICTIONARY P4-P7 NCDC 2026 ============
ENGLISH_DICTIONARY = {
    "P4": {
        "Adjective": "Describing word. Ex: The tall teacher, blue gomesi",
        "Noun": "Naming word. Ex: school, Kampala, pupil",
        "Verb": "Action word. Ex: run, eat, read, write",
        "Punctuation": "Full stop., Comma,, Question mark?",
        "Tense": "Time of action. Past: went. Present: go. Future: will go",
        "Market": "Place where we buy and sell goods like tomatoes, beans",
        "Time": "Clock reading. Ex: 7:30am - Half past seven",
        "Vocabulary": "New words we learn for Math and Science"
    },
    "P5": {
        "Composition": "Story or essay with beginning, middle, and end",
        "Formal Letter": "Letter with address, date, salutation. Ex: To The Headteacher",
        "Synonym": "Word with same meaning. Ex: Big = Large",
        "Antonym": "Word with opposite meaning. Ex: Hot = Cold",
        "Transport": "Means of moving people. Ex: boda, taxi, bus, train",
        "Media": "Ways of communication. Ex: Radio, TV, Newspaper, Phone",
        "Tense": "Advanced: Present Perfect, Past Continuous"
    },
    "P6": {
        "Direct Speech": "Exact words. Ex: Teacher said, 'Close the door'",
        "Indirect Speech": "Reported words. Ex: Teacher told us to close the door",
        "Active Voice": "Subject does action. Ex: The boy kicked the ball",
        "Passive Voice": "Action done to subject. Ex: The ball was kicked by the boy",
        "Debate": "Formal discussion with points, evidence and rebuttals",
        "Possibility": "Words like may, might, could. Ex: It may rain today",
        "Condition": "If sentences. Ex: If you study, you will pass"
    },
    "P7": {
        "Functional Text": "Real-life writing. Ex: Notice, Advert, Report, Memo",
        "Comprehension": "Reading passage and answering questions",
        "Conditional": "Complex If sentences. Ex: If I had studied, I would have passed",
        "Speech": "Public speaking. Ex: Speech on 'Keeping Our School Clean'",
        "PLE Vocabulary": "Exam command words: discuss, explain, outline, state, describe",
        "Reporting": "Writing what happened. Ex: Accident report, Meeting report",
        "Summary": "Writing the main points of a passage in few words"
    }
}

# ============ 2. FULL NCDC 2026 CURRICULUM DATABASE P4-P7 ============
PRIMARY_DB = {
  "PRIMARY_4": {
    "focus": "Transition Year - English Medium & Technical Vocabulary",
    "Mathematics": [
      {"topic": "Whole Numbers up to 6 digits", "competency": "Learner reads, writes and uses whole numbers up to 6 digits", "scenario": "Counting pupils in a school assembly"},
      {"topic": "Number Bases: Base 2 and Base 5", "competency": "Learner converts numbers between base 10 and base 2/base 5", "scenario": "Understanding how computers count in binary"},
      {"topic": "Fractions", "competency": "Learner identifies and performs basic operations with fractions", "scenario": "Sharing 1 mandazi equally among 4 friends"},
      {"topic": "Operational Signs + BODMAS", "competency": "Learner applies +, -, x, / using correct order", "scenario": "Calculating cost of 3 books at 2000 UGX each"},
      {"topic": "Basic Geometry: Shapes and Angles", "competency": "Learner names and identifies 2D shapes and angles", "scenario": "Identifying triangles on roof, rectangles on doors"},
      {"topic": "Data Handling: Tables and Bar Graphs", "competency": "Learner collects and presents data in tables and bar graphs", "scenario": "Recording pupils who like posho, rice and matooke"}
    ],
    "Integrated Science": [
      {"topic": "The Human Body and Health", "competency": "Learner names major body parts and practices hygiene", "scenario": "Washing hands with soap before eating at school"},
      {"topic": "Plant Life", "competency": "Learner describes parts of a plant and their functions", "scenario": "Planting beans in school garden"},
      {"topic": "Weather and Environment", "competency": "Learner observes and records weather elements", "scenario": "Keeping a weather chart for 1 week in Kampala"},
      {"topic": "Pests and Diseases in Plants and Animals", "competency": "Learner identifies common pests and ways to control them", "scenario": "Farmers removing army worms from maize"}
    ],
    "Social Studies (SST)": [
      {"topic": "Our District and Municipality", "competency": "Learner describes location and services in their district", "scenario": "Mapping Kampala District: Nakasero Market, Mulago Hospital"},
      {"topic": "Physical Features and Vegetation", "competency": "Learner identifies major physical features", "scenario": "Lake Victoria shores in Wakiso"},
      {"topic": "People and Settlement", "competency": "Learner explains factors that influence settlement", "scenario": "Why many people settle near Kampala Road"},
      {"topic": "Social Services and Leadership", "competency": "Learner identifies social services and leaders", "scenario": "LC1 Chairman solving disputes"}
    ],
    "English Language": [
      {"topic": "Describing Objects and People", "competency": "Learner uses adjectives to describe", "scenario": "Describing your class teacher: 'She is tall, kind'"},
      {"topic": "Vocabulary for Math and Science", "competency": "Learner uses technical words for math and science", "scenario": "Using words like 'fraction, area, germs'"},
      {"topic": "Shopping and Market Terminology", "competency": "Learner uses language for buying and selling", "scenario": "Role play at Nakasero Market"},
      {"topic": "Basic Grammar: Tenses and Punctuation", "competency": "Learner uses present, past, future tenses", "scenario": "Writing in diary"}
    ],
    "Christian Religious Education (CRE)": [
      {"topic": "God's Creation and Our Responsibility", "competency": "Learner explains how to care for God's creation", "scenario": "School cleaning campaign"},
      {"topic": "God's People and the Law", "competency": "Learner states the Ten Commandments", "scenario": "Obeying 'Do not steal'"},
      {"topic": "Following Jesus as Our Leader", "competency": "Learner describes how Jesus served others", "scenario": "Helping a classmate who fell down"},
      {"topic": "Serving Others", "competency": "Learner shows kindness and service", "scenario": "Sharing lunch with a pupil"}
    ],
    "Islamic Religious Education (IRE)": [
      {"topic": "Selected Surahs: Al-Fatihah and Al-Asr", "competency": "Learner recites and explains meaning of Surahs", "scenario": "Reciting Al-Fatihah before lessons"},
      {"topic": "Attributes of Allah: Tawhid", "competency": "Learner states that Allah is One", "scenario": "Saying 'Bismillah' before eating"},
      {"topic": "Behavior of a Muslim", "competency": "Learner demonstrates good Islamic behavior", "scenario": "Greeting with Salaam"},
      {"topic": "Cleanliness and Wudhu", "competency": "Learner demonstrates steps of Wudhu", "scenario": "Performing Wudhu before prayer"},
      {"topic": "Life of Prophet Muhammad SAW in Makkah", "competency": "Learner narrates key events", "scenario": "Prophet's honesty as Al-Amin"}
    ]
  },
  "PRIMARY_5": {
    "focus": "Core Subject-Based Foundations",
    "Mathematics": [
      {"topic": "Whole Numbers up to 7 digits", "competency": "Learner reads, writes and works with large numbers", "scenario": "Reading population of Kampala City"},
      {"topic": "L.C.M and G.C.D", "competency": "Learner finds LCM and GCD", "scenario": "Two bells ring every 6min and 8min"},
      {"topic": "Fractions and Percentages", "competency": "Learner converts between fractions and percentages", "scenario": "Calculating 20% discount on uniform"},
      {"topic": "Business Math: Profit and Loss", "competency": "Learner calculates profit and loss", "scenario": "Buying 10 pencils at 200 and selling at 300"},
      {"topic": "Lines and Angles", "competency": "Learner identifies and measures lines and angles", "scenario": "Measuring corners of classroom desks"},
      {"topic": "Integers", "competency": "Learner uses positive and negative numbers", "scenario": "Temperature above and below zero"}
    ],
    "Integrated Science": [
      {"topic": "Poultry Keeping", "competency": "Learner describes how to care for chicken", "scenario": "A farmer in Mukono feeding layers"},
      {"topic": "Crop Husbandry", "competency": "Learner explains stages of crop growing", "scenario": "Planting maize"},
      {"topic": "Sanitation and Immunization", "competency": "Learner explains importance of sanitation", "scenario": "Health workers giving polio drops"},
      {"topic": "Respiratory and Circulatory Systems", "competency": "Learner describes how air and blood move", "scenario": "Running during PE"},
      {"topic": "Matter and Energy", "competency": "Learner identifies states of matter", "scenario": "Water boiling into steam"}
    ],
    "Social Studies (SST)": [
      {"topic": "Our Country Uganda", "competency": "Learner describes Uganda's location", "scenario": "Uganda bordered by 5 countries"},
      {"topic": "Physical Features of Uganda", "competency": "Learner locates major physical features", "scenario": "Mount Rwenzori, Lake Victoria"},
      {"topic": "Climate and Vegetation of Uganda", "competency": "Learner relates climate to vegetation", "scenario": "Tropical rainforest in Mabira"},
      {"topic": "Natural Resources", "competency": "Learner identifies natural resources", "scenario": "Gold mining in Karamoja"},
      {"topic": "Historical Patterns", "competency": "Learner describes early kingdoms", "scenario": "Buganda Kingdom"},
      {"topic": "Road to Independence", "competency": "Learner explains events leading to independence", "scenario": "1962 Independence"}
    ],
    "English Language": [
      {"topic": "Writing Compositions", "competency": "Learner writes a story with structure", "scenario": "A Day I Got Lost at Owino Market"},
      {"topic": "Formal Letter Formatting", "competency": "Learner writes a formal letter", "scenario": "Letter to Headteacher for trip"},
      {"topic": "Advanced Tenses", "competency": "Learner uses complex tenses", "scenario": "I have finished my homework"},
      {"topic": "Travel and Transport Vocabulary", "competency": "Learner uses transport vocabulary", "scenario": "Journey from Kampala to Gulu"},
      {"topic": "Electronic Media and Communication", "competency": "Learner describes uses of media", "scenario": "Listening to Radio Uganda"}
    ],
    "Christian Religious Education (CRE)": [
      {"topic": "Faith and Trust in God", "competency": "Learner demonstrates faith", "scenario": "Praying before PLE exams"},
      {"topic": "God's Covenants", "competency": "Learner explains God's promises", "scenario": "God's promise of the rainbow"},
      {"topic": "Early Life and Ministry of Jesus", "competency": "Learner narrates key events", "scenario": "Jesus feeding 5000"},
      {"topic": "Forgiveness", "competency": "Learner practices forgiveness", "scenario": "Forgiving a friend"},
      {"topic": "Christian Values in Relationships", "competency": "Learner shows love and respect", "scenario": "Helping elderly neighbor"}
    ],
    "Islamic Religious Education (IRE)": [
      {"topic": "Pillars of Islam: Salah and Sawm", "competency": "Learner describes Salah and fasting", "scenario": "Fasting during Ramadan"},
      {"topic": "Respect for Parents and Elders", "competency": "Learner demonstrates good behavior", "scenario": "Helping mother fetch water"},
      {"topic": "Hadith on Islamic Morals", "competency": "Learner recites and applies Hadith", "scenario": "Loving for your brother"},
      {"topic": "Expansion of Islam", "competency": "Learner explains how Islam spread", "scenario": "Islam reaching Uganda"}
    ]
  }
}

PRIMARY_DB.update({
     "PRIMARY_6": {
     "focus": "Advanced Application & Regional Scope - EAC",
     "Mathematics": [
      {"topic": "Ratios and Proportions", "competency": "Learner solves ratio problems", "scenario": "Mixing juice for school party"},
      {"topic": "Sets", "competency": "Learner forms and solves problems using sets", "scenario": "Pupils who like football vs netball"},
      {"topic": "Basic Algebra", "competency": "Learner solves simple algebraic equations", "scenario": "If 2x + 3 = 11, find x"},
      {"topic": "Data Representation", "competency": "Learner presents data in pie charts", "scenario": "School feeding program budget"},
      {"topic": "Integers", "competency": "Learner performs operations with integers", "scenario": "Bank account deposit and withdraw"},
      {"topic": "Area and Volume of Complex Shapes", "competency": "Learner calculates area and volume", "scenario": "Finding volume of water tank"}
    ],
    "Integrated Science": [
      {"topic": "Animal Husbandry: Cattle Keeping", "competency": "Learner describes methods of cattle rearing", "scenario": "Zero grazing in Kabale"},
      {"topic": "Primary Health Care", "competency": "Learner identifies components of PHC", "scenario": "Health worker giving ORS"},
      {"topic": "Classification of Living Things", "competency": "Learner classifies plants and animals", "scenario": "Grouping insects and birds"},
      {"topic": "Light and Sound Energy", "competency": "Learner explains how light and sound travel", "scenario": "Lightning before thunder"},
      {"topic": "Reproductive Health", "competency": "Learner describes body changes at puberty", "scenario": "Health talk on hygiene"}
    ],
    "Social Studies (SST)": [
      {"topic": "East Africa Community", "competency": "Learner describes member countries of EAC", "scenario": "Boda riders crossing to Kenya"},
      {"topic": "Physical Geography of EAC", "competency": "Learner identifies physical features of EAC", "scenario": "Lake Victoria shared by 3 countries"},
      {"topic": "Climate of EAC", "competency": "Learner describes climate zones", "scenario": "Desert climate in Northern Kenya"},
      {"topic": "Regional Resources", "competency": "Learner identifies resources in EAC", "scenario": "Tourism in Serengeti"},
      {"topic": "Economic Activities", "competency": "Learner explains farming and trade", "scenario": "Cross-border trade at Busia"},
      {"topic": "History and Political Evolution of EAC", "competency": "Learner describes formation of EAC", "scenario": "Countries joining EAC"}
    ],
    "English Language": [
      {"topic": "Expressing Possibilities and Conditions", "competency": "Learner uses modal verbs", "scenario": "It might rain, carry umbrella"},
      {"topic": "Active vs Passive Voice", "competency": "Learner converts between active and passive", "scenario": "The chef cooked food"},
      {"topic": "Direct and Indirect Speech", "competency": "Learner converts direct to indirect", "scenario": "Teacher said 'Close the door'"},
      {"topic": "Debate Vocabulary", "competency": "Learner uses language for debating", "scenario": "School debate on Social Media"},
      {"topic": "Safety on the Road", "competency": "Learner describes road safety rules", "scenario": "Looking left and right"}
    ],
    "Christian Religious Education (CRE)": [
      {"topic": "The Holy Spirit as Our Helper", "competency": "Learner explains how Holy Spirit helps", "scenario": "Praying for courage before PLE"},
      {"topic": "The Church as a Community", "competency": "Learner describes roles in church", "scenario": "Sunday school teachers serving"},
      {"topic": "Citizenship and Civic Responsibility", "competency": "Learner shows good citizenship", "scenario": "Voting for school prefect"},
      {"topic": "Preparing for the Future", "competency": "Learner sets goals for secondary", "scenario": "Planning to join science club"}
    ],
    "Islamic Religious Education (IRE)": [
      {"topic": "Pillars of Iman: Faith", "competency": "Learner lists 6 articles of faith", "scenario": "Believing in angels"},
      {"topic": "Zakah and Economic Distribution", "competency": "Learner explains importance of Zakah", "scenario": "Giving 2.5% to the poor"},
      {"topic": "Performance of Hajj", "competency": "Learner describes steps of Hajj", "scenario": "Muslims going to Makkah"},
      {"topic": "Islamic Laws on Business Honesty", "competency": "Learner demonstrates honesty", "scenario": "Shopkeeper using correct scales"}
    ]
  },
  "PRIMARY_7": {
    "focus": "PLE Candidate Class - High-Level Competency Integration",
    "Mathematics": [
      {"topic": "Advanced Fractions and Decimals", "competency": "Learner performs complex operations", "scenario": "Calculating 0.75 of 1200 UGX"},
      {"topic": "Sequences and Patterns", "competency": "Learner identifies number patterns", "scenario": "Finding next number: 2, 4, 8, 16"},
      {"topic": "Advanced Business Math: Interest, Bills, Budgets", "competency": "Learner calculates simple interest", "scenario": "Family budget of 500,000 UGX"},
      {"topic": "Coordinate Geometry", "competency": "Learner plots points on grid", "scenario": "Mapping locations of classrooms"},
      {"topic": "Speed, Distance and Time", "competency": "Learner solves SDT problems", "scenario": "Taxi from Kampala to Jinja 80km"},
      {"topic": "Probability", "competency": "Learner finds probability of events", "scenario": "Picking red ball from bag"}
    ],
    "Integrated Science": [
      {"topic": "Indigenous Technology", "competency": "Learner describes local technologies", "scenario": "Making charcoal stove"},
      {"topic": "Environmental Degradation and Management", "competency": "Learner suggests ways to conserve", "scenario": "NEMA campaign in Mabira"},
      {"topic": "Complex Diseases: HIV/AIDS, STIs", "competency": "Learner describes prevention", "scenario": "ABC approach"},
      {"topic": "Energy Resources", "competency": "Learner identifies renewable energy", "scenario": "Solar panels on school roof"},
      {"topic": "Machines and Mechanics", "competency": "Learner identifies simple machines", "scenario": "Using pulley to fetch water"}
    ],
    "Social Studies (SST)": [
      {"topic": "The African Continent", "competency": "Learner describes location of Africa", "scenario": "Second largest continent"},
      {"topic": "Major Physical Features of Africa", "competency": "Learner locates major features", "scenario": "Sahara Desert, River Congo"},
      {"topic": "Climate Zones of Africa", "competency": "Learner describes climate zones", "scenario": "Equatorial climate in Congo"},
      {"topic": "Vegetation of Africa", "competency": "Learner relates vegetation to climate", "scenario": "Savanna grassland"},
      {"topic": "Colonial Rule in Africa", "competency": "Learner explains effects of colonialism", "scenario": "Railway built by British"},
      {"topic": "Post-Independence Africa", "competency": "Learner describes challenges", "scenario": "Civil wars"},
      {"topic": "Global Organizations: AU and UN", "competency": "Learner explains roles of AU and UN", "scenario": "AU peacekeepers"}
    ],
    "English Language": [
      {"topic": "Analyzing Functional Texts", "competency": "Learner interprets notices and adverts", "scenario": "Reading 'Immunization Day' poster"},
      {"topic": "Advanced Comprehension", "competency": "Learner answers inferential questions", "scenario": "Passage about climate change"},
      {"topic": "Complex Conditional Sentences", "competency": "Learner uses 2nd and 3rd conditionals", "scenario": "If I were president"},
      {"topic": "PLE Exam Vocabulary", "competency": "Learner understands command words", "scenario": "Discuss causes of soil erosion"},
      {"topic": "Public Speech and Reporting", "competency": "Learner prepares short speech", "scenario": "Speech as Head Prefect"}
    ],
    "Christian Religious Education (CRE)": [
      {"topic": "Witnessing for Christ", "competency": "Learner explains how to share values", "scenario": "Inviting friends to Sunday school"},
      {"topic": "Christian Response to Modern Challenges", "competency": "Learner addresses issues", "scenario": "Saying no to exam cheating"},
      {"topic": "Preparing for Transition to Secondary School", "competency": "Learner sets academic goals", "scenario": "Joining Scripture Union"},
      {"topic": "The Eternal Hope", "competency": "Learner explains Christian hope", "scenario": "Finding comfort in God"}
    ],
    "Islamic Religious Education (IRE)": [
      {"topic": "Comprehensive Review of Islamic Morality", "competency": "Learner demonstrates Islamic morals", "scenario": "Being truthful and kind"},
      {"topic": "Akhlaq: Character Development", "competency": "Learner shows good character", "scenario": "Not cheating in PLE"},
      {"topic": "Handling Contemporary Challenges", "competency": "Learner addresses modern issues", "scenario": "Dealing with peer pressure"},
      {"topic": "Unity in the Ummah", "competency": "Learner explains Muslim unity", "scenario": "Praying together in Juma"},
      {"topic": "Preparation for Secondary Transition", "competency": "Learner plans for secondary", "scenario": "Joining MUBS Muslim students"}
    ]
  }
})

PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items() if s!="focus"} for g,d in PRIMARY_DB.items()}

def get_topic_data(grade, subject, topic_name):
    grade_key = f"PRIMARY_{grade}"
    if grade_key in PRIMARY_DB and subject in PRIMARY_DB[grade_key]:
        for t in PRIMARY_DB[grade_key][subject]:
            if t["topic"] == topic_name: return t
    return None

# ============ LOGGING + AUTH ============
def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try: return json.load(f)
            except: return []
    return []
def save_log(entry):
    logs = load_logs(); logs.append(entry)
    with open(LOG_FILE, "w") as f: json.dump(logs, f, indent=2)
def log_activity(user_type, action, details):
    entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "user": user_type, "action": action, "details": details}
    save_log(entry)

def check_password():
    APP_PW = st.secrets.get("PRIMARY_APP_PASSWORD", "PRIMARY2026")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "ADMIN256")
    def password_entered():
        pw = st.session_state["password"]
        if pw == APP_PW: st.session_state["user_type"] = "Pupil"; st.session_state["password_correct"] = True
        elif pw == ADMIN_PW: st.session_state["user_type"] = "Teacher"; st.session_state["password_correct"] = True
        else: st.session_state["password_correct"] = False
        if "password" in st.session_state: del st.session_state["password"]
    if "password_correct" not in st.session_state:
        st.title("🔒 TEACHERK PRIMARY 2026 - Login P4-P7")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password"); return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 TEACHERK PRIMARY 2026 - Login P4-P7")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password"); st.error("😞 Password incorrect"); return False
    else: return True
if not check_password(): st.stop()

st.set_page_config(page_title="TEACHERK PRIMARY 2026", page_icon="🐢", layout="wide")
@st.cache_resource
def get_client(): return Groq(api_key=st.secrets["GROQ_API_KEY"])

def create_pdf(content, title):
    buffer = io.BytesIO(); p = canvas.Canvas(buffer, pagesize=A4); p.setFont("Helvetica-Bold", 14); p.drawString(50,800,title); y=770; p.setFont("Helvetica", 10)
    for line in content.split('\n')[:65]: p.drawString(50,y,line[:95]); y-=14;
    if y<50: p.showPage(); y=750
    p.save(); buffer.seek(0); return buffer
def display_with_pdf(content, name):
    st.markdown(content)
    pdf = create_pdf(content, name); st.download_button("📥 Download PDF", pdf, f"{name}.pdf")
    if st.button("🔊 Read Aloud", key=f"tts_{name}"):
        try: tts = gTTS(content[:500]); fp = "temp.mp3"; tts.save(fp); st.audio(open(fp,"rb").read(), format="audio/mp3"); os.remove(fp)
        except: st.warning("Audio failed")

def call_groq_safe(client, messages, model, max_tokens=2000):
    try:
        res = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=0.5)
        return res.choices[0].message.content
    except Exception as e:
        err = str(e)
        if "413" in err and model == AI_MODEL_FAST:
            st.warning("Token limit hit. Auto-switching to 70B...")
            res = client.chat.completions.create(model=AI_MODEL_LONG, messages=messages, max_tokens=2000)
            return res.choices[0].message.content
        return f"AI Error: {e}"

def get_ai_response_from_db(client, user_query, grade, subject, topic_data, lab_mode):
    model = AI_MODEL_FAST if lab_mode else AI_MODEL_LONG
    prompt = f"""You are TeacherK, a P4-P7 teacher in Uganda. Use ONLY the information below.
Grade: {grade} | Subject: {subject} | Topic: {topic_data['topic']}
Competency: {topic_data['competency']} | Example: {topic_data['scenario']}
Question: {user_query}
Answer in 4 sentences max. Simple English. End with 1 Activity + 1 Question."""
    answer = call_groq_safe(client, [{"role":"user","content":prompt}], model)
    log_activity(st.session_state.user_type, "AI Query", f"{subject} {grade} {topic_data['topic']}")
    return answer

def generate_bulk_revision(client, grade, subject):
    topics = PRIMARY_CURRICULUM_MAP[grade][subject]
    prompt = f"Generate 20 PLE revision questions for {grade} {subject} using ONLY: {', '.join(topics)}. Mix MCQ + Theory. Provide answers."
    return call_groq_safe(client, [{"role":"user","content":prompt}], AI_MODEL_LONG, 3500)

def generate_mock_paper(client, grade, subject):
    topics = PRIMARY_CURRICULUM_MAP[grade][subject]
    prompt = f"Generate PLE MOCK for {grade} {subject}. Section A: 40 MCQ. Section B: 5 Theory. Use ONLY: {', '.join(topics)}. Provide marking guide."
    return call_groq_safe(client, [{"role":"user","content":prompt}], AI_MODEL_LONG, 4000)

def teacher_dashboard():
    st.title("👨‍🏫 TEACHER DASHBOARD"); logs = load_logs()
    if not logs: st.warning("No pupil activity yet"); return
    df = pd.DataFrame(logs); col1,col2,col3 = st.columns(3)
    col1.metric("Total Activities", len(df)); col2.metric("Today", len(df[df['timestamp'].str.startswith(datetime.now().strftime("%Y-%m-%d"))])); col3.metric("Users", df['user'].nunique())
    st.dataframe(df.tail(50), use_container_width=True)

def main():
    client = get_client()
    if "performance" not in st.session_state: st.session_state.performance = {}
    st.markdown("<h1 style='text-align:center; background:#4CAF50; color:white; padding:10px'>🐢 TEACHERK PRIMARY 2026</h1>", unsafe_allow_html=True)

    with st.sidebar:
        st.success(f"Logged in as: {st.session_state.user_type}")
        st.header("📖 English Dictionary")
        dict_grade = st.selectbox("Grade", ["P4","P5","P6","P7"])
        search_word = st.text_input("Search term")
        if search_word:
            word = search_word.capitalize()
            if word in ENGLISH_DICTIONARY[dict_grade]: st.success(f"**{word}**: {ENGLISH_DICTIONARY[dict_grade][word]}")
            else: st.warning("Not in syllabus")
        st.divider()
        lab_mode = st.toggle("🚀 CLASSROOM MODE", value=True)
        if st.session_state.user_type == "Teacher": teacher_dashboard()
        if st.button("Logout"): st.session_state.clear(); st.rerun(); return
        grade = st.selectbox("Class", ["P4","P5","P6","P7"])
        subject = st.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
        topic = st.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])
        mode = st.radio("Mode", ["❓ Ask TeacherK", "📖 Learn from NCDC", "📚 Bulk Revision", "📄 PLE Mock"])

    topic_data = get_topic_data(grade, subject, topic)
    st.subheader(f"{grade} {subject}: {topic_data['topic']}")
    st.info(f"**Competency**: {topic_data['competency']}")
    st.success(f"**Example**: {topic_data['scenario']}")

    if mode == "❓ Ask TeacherK":
        q = st.text_input("Ask about this topic")
        if st.button("Ask"): ans = get_ai_response_from_db(client, q, grade, subject, topic_data, lab_mode); display_with_pdf(ans, "Answer")
    elif mode == "📖 Learn from NCDC":
        if st.button("Teach Me"): ans = get_ai_response_from_db(client, "Teach me", grade, subject, topic_data, lab_mode); display_with_pdf(ans, "Lesson")
    elif mode == "📚 Bulk Revision":
        if st.button("Generate 20Q"): ans = generate_bulk_revision(client, grade, subject); display_with_pdf(ans, "Bulk")
    elif mode == "📄 PLE Mock":
        if grade!= "P7": st.error("Mocks only for P7")
        else:
            if st.button("Generate PLE Mock"): ans = generate_mock_paper(client, grade, subject); display_with_pdf(ans, "Mock")

if __name__ == "__main__": main()
