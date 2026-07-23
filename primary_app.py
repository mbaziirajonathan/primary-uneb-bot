import streamlit as st
import os, io, json, random
import pandas as pd
from datetime import datetime
from groq import Groq
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from gtts import gTTS
import speech_recognition as sr

# ===================== CONFIG =====================
CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7. Confirm with Class Teacher.")

# ===================== 1. NEW NCDC 2026 SYSTEM PROMPT - SCENARIO BASED =====================
SYSTEM_PROMPT = """
You are TEACHERK, a Senior NCDC 2026 Uganda Examiner and Master Teacher for PRIMARY P4-P7.

YOUR MISSION: Help students understand deeply by showing MULTIPLE SCENARIOS and MULTIPLE WAYS to solve 1 problem. Like UNEB marking guide.

MANDATORY OUTPUT FORMAT - USE THIS EVERY TIME:

### **PART 1: SCENARIO 1 - [Give it a Ugandan Title]**
Write a 4-5 sentence real-life Ugandan scenario. Use: market, school, boda, farm, clinic, home.

**COMPETENCY TASK:** State what learner must be able to DO.

**QUESTION 1:** 1 clear scenario-based question with marks. [4 marks]

**METHOD 1: Formula/Concept Method**
Step 1: State concept/formula
Step 2: Substitute values
Step 3: Calculate with units
Answer: ___

**METHOD 2: Logical/Story Method**
Explain how to solve it without formula. Using reasoning or drawing.
Answer: ___

---
### **PART 2: SCENARIO 2 - [Different Ugandan Title]**
Different scenario but testing SAME competency/topic.

**COMPETENCY TASK:** State what learner must be able to DO.

**QUESTION 2:** Different question but same concept. [4 marks]

**METHOD 1 & 2:** Show 2 different ways to answer again.

---
### **PART 3: COMMON MISTAKES & EXAM TIPS**
1. List 3 mistakes pupils make on this topic in PLE
2. Give 1 "Trick" to remember

### **PART 4: QUICK PRACTICE FOR PUPILS**
Give 2 more short questions for pupil to try alone. No answers.

CURRICULUM RULES:
1. LOCK: Only NCDC 2026 P4-P7 topics. If outside, say: "That is not in NCDC P4-P7. Let's do [suggest closest topic] instead."
2. EXAMPLES: All scenarios must be Ugandan and realistic.
3. LANGUAGE: Simple English for ages 9-13. Step by step.
4. MATH/SCIENCE: Always show units. Always show 2 methods minimum.
5. GOAL: Pupil should say "Ahh I now get it 2 different ways"

TONE: Patient teacher. Use "Let's try", "Notice that", "Why does this work?"
"""

# ===================== 2. FULL NCDC 2026 DB =====================
PRIMARY_DB = {
  "PRIMARY_4": {
    "Mathematics": [
        {"topic": "Sets", "competency": "Identify types and elements of sets", "scenario": "Venn diagram of fruits"},
        {"topic": "Whole Numbers", "competency": "Place values up to 100,000, rounding, Roman numerals", "scenario": "Count pupils"},
        {"topic": "Operation on Whole Numbers", "competency": "Add, subtract, multiply, long division", "scenario": "Market money"},
        {"topic": "Fractions", "competency": "Types, add, subtract, word problems", "scenario": "Share cake"},
        {"topic": "Graphs", "competency": "Pictographs, bar graphs, interpret data", "scenario": "Class attendance"},
        {"topic": "Geometry", "competency": "Lines, angles, symmetry, 2D shapes", "scenario": "Window shapes"},
        {"topic": "Measures", "competency": "Time, Money, Length, Mass, Capacity", "scenario": "Buying sugar"}],
    "English": [
        {"topic": "Sub-county/Division", "competency": "Describe sub-county features", "scenario": "Nakasongola TC"},
        {"topic": "School Environment", "competency": "Talk about school", "scenario": "My classroom"},
        {"topic": "Elements of Weather", "competency": "Name weather elements", "scenario": "Rainy day"},
        {"topic": "Market", "competency": "Vocabulary of market items", "scenario": "Buying tomatoes"},
        {"topic": "Hygiene", "competency": "Explain personal hygiene", "scenario": "Washing hands"},
        {"topic": "Sub-county Leaders", "competency": "Name leaders", "scenario": "LC1 Chairman"},
        {"topic": "Peace and Security", "competency": "Explain peace", "scenario": "No fighting"}],
    "Integrated Science": [
        {"topic": "Plant Life", "competency": "Flowering and non-flowering, roots, leaves, photosynthesis", "scenario": "Mango tree"},
        {"topic": "Animal Life", "competency": "Insects, domestic, wild animals", "scenario": "Chicken and lion"},
        {"topic": "Human Body", "competency": "Teeth, skeletal system, hygiene", "scenario": "Brushing teeth"},
        {"topic": "Sanitation and Personal Hygiene", "competency": "Handwashing, clean environment", "scenario": "Tippy tap"},
        {"topic": "Weather and Climate", "competency": "Elements of weather, water cycle", "scenario": "Rainfall"},
        {"topic": "Accidents and First Aid", "competency": "Common accidents, first aid box", "scenario": "Cut finger"},
        {"topic": "Matter", "competency": "Solids, liquids, gases", "scenario": "Water"}],
    "Social Studies (SST)": [
        {"topic": "Location of our Sub-county/District", "competency": "Compass directions, maps", "scenario": "Map of Nakasongola"},
        {"topic": "Physical Features in our District", "competency": "Mountains, rivers, lakes", "scenario": "Lake Kyoga"},
        {"topic": "Vegetation in our District", "competency": "Forests, swamps, conservation", "scenario": "Mabira"},
        {"topic": "People in our District", "competency": "Ethnic groups, clans, culture", "scenario": "Baganda, Banyoro"},
        {"topic": "Economic Activities", "competency": "Farming, trade, fishing", "scenario": "Growing beans"},
        {"topic": "Social Services and Leaders", "competency": "Schools, hospitals, LC", "scenario": "Health center"}]
  },
  "PRIMARY_5": {
    "Mathematics": [
        {"topic": "Sets", "competency": "Subsets, intersection, union, Venn applications", "scenario": "Students who play football"},
        {"topic": "Whole Numbers", "competency": "Values up to 1,000,000, bases, Roman numerals", "scenario": "Population"},
        {"topic": "Operations on Whole Numbers", "competency": "Mixed operations, BODMAS", "scenario": "Shop calculation"},
        {"topic": "Number Patterns and Sequences", "competency": "Factors, multiples, LCM, HCF", "scenario": "Two bells"},
        {"topic": "Fractions", "competency": "Decimals, percentages, conversion", "scenario": "50% discount"},
        {"topic": "Graphs", "competency": "Line graphs, coordinate grids", "scenario": "Temperature chart"},
        {"topic": "Geometry", "competency": "Construction of angles, triangles", "scenario": "Using protractor"},
        {"topic": "Measures", "competency": "Speed, Distance, Time; Area and Perimeter", "scenario": "Taxi journey"},
        {"topic": "Integers", "competency": "Number line, add, subtract", "scenario": "Debt and money"},
        {"topic": "Algebra", "competency": "Simple equations, substitution", "scenario": "Find x"}],
    "English": [
        {"topic": "Our District/Municipality", "competency": "Describe district", "scenario": "Kampala"},
        {"topic": "Occupations/Professions", "competency": "Name jobs", "scenario": "Doctor, teacher"},
        {"topic": "Vehicles and Transport", "competency": "Types of transport", "scenario": "Boda boda"},
        {"topic": "Letter Writing", "competency": "Informal letter", "scenario": "Letter to friend"},
        {"topic": "Health and Hygiene", "competency": "Healthy living", "scenario": "Boiling water"},
        {"topic": "Communication", "competency": "Post office, phone, internet", "scenario": "Sending email"}],
    "Integrated Science": [
        {"topic": "Plant Life", "competency": "Crop husbandry, pests, organic manure", "scenario": "Growing maize"},
        {"topic": "Animal Life", "competency": "Poultry, bee-keeping, fish farming", "scenario": "Chicken house"},
        {"topic": "Human Body", "competency": "Digestive and respiratory system", "scenario": "Eating food"},
        {"topic": "Primary Health Care", "competency": "PHC, immunization, cold chain", "scenario": "Vaccination"},
        {"topic": "Soil", "competency": "Components, erosion, conservation", "scenario": "Planting grass"},
        {"topic": "Matter and Energy", "competency": "Heat transfer", "scenario": "Boiling water"}],
    "Social Studies (SST)": [
        {"topic": "Location of Uganda", "competency": "Neighbors, coordinates", "scenario": "Map of Uganda"},
        {"topic": "Physical Features of Uganda", "competency": "Rift valley, lakes, mountains", "scenario": "Mt. Rwenzori"},
        {"topic": "Climate and Vegetation of Uganda", "competency": "Factors of climate", "scenario": "Rain forest"},
        {"topic": "People of Uganda", "competency": "Migration, Nilotics, Bantu", "scenario": "Legends"},
        {"topic": "Natural Resources of Uganda", "competency": "Minerals, wildlife, tourism", "scenario": "Gorillas"},
        {"topic": "Governance and Leadership", "competency": "Executive, judiciary, parliament", "scenario": "President"}]
  },
  "PRIMARY_6": {
    "Mathematics": [
        {"topic": "Sets", "competency": "Complement, listing, problem solving", "scenario": "Students not in class"},
        {"topic": "Whole Numbers", "competency": "Up to 10,000,000, squares, square roots", "scenario": "Big population"},
        {"topic": "Number Patterns and Sequences", "competency": "Consecutive, triangular numbers", "scenario": "Counting pattern"},
        {"topic": "Fractions, Decimals, and Percentages", "competency": "Ratios, proportions, % change", "scenario": "Profit"},
        {"topic": "Integers", "competency": "Ordering, deep operations", "scenario": "Temperature"},
        {"topic": "Geometry", "competency": "Angles on line, parallel, triangle", "scenario": "Road junction"},
        {"topic": "Measures", "competency": "Volume, Surface Area, Time schedules", "scenario": "Water tank"},
        {"topic": "Graphs", "competency": "Pie charts, mean data", "scenario": "Family budget"},
        {"topic": "Algebra", "competency": "Linear equations, inequalities", "scenario": "Solve for y"}],
    "English": [
        {"topic": "Safety on the Road", "competency": "Road safety rules", "scenario": "Crossing road"},
        {"topic": "Postal Services and Telecoms", "competency": "How mail works", "scenario": "Post office"},
        {"topic": "Institutional Buildings", "competency": "Name institutions", "scenario": "Hospital"},
        {"topic": "Buying and Selling", "competency": "Banking, markets", "scenario": "Bank account"},
        {"topic": "Hotels and Catering", "competency": "Hotel services", "scenario": "Restaurant"},
        {"topic": "Environmental Protection", "competency": "Conserving environment", "scenario": "Planting trees"}],
    "Integrated Science": [
        {"topic": "Plant Life", "competency": "Woodland, agroforestry, conservation", "scenario": "Tree planting"},
        {"topic": "Animal Life", "competency": "Classification of vertebrates", "scenario": "Cow, bird, snake"},
        {"topic": "Human Body", "competency": "Circulatory, reproductive, adolescence", "scenario": "Blood circulation"},
        {"topic": "Sanitation and Disease Control", "competency": "HIV/AIDS, Malaria, Cholera", "scenario": "Use mosquito net"},
        {"topic": "Sound Energy", "competency": "Production, echoes", "scenario": "Clapping"},
        {"topic": "Resources in the Environment", "competency": "Renewable and non-renewable", "scenario": "Solar"}],
    "Social Studies (SST)": [
        {"topic": "Location of East Africa", "competency": "EAC member states", "scenario": "Map of EAC"},
        {"topic": "Physical Features and Climate", "competency": "Impact on settlement", "scenario": "Highlands"},
        {"topic": "People of East Africa", "competency": "Pre-colonial societies", "scenario": "Buganda Kingdom"},
        {"topic": "Colonialism in East Africa", "competency": "Scramble, resistance", "scenario": "Kabaka Mwanga"},
        {"topic": "Road to Independence", "competency": "Nationalists, parties", "scenario": "UPC"},
        {"topic": "Economic Development and EAC", "competency": "Trade, transport", "scenario": "Northern Corridor"}]
  },
  "PRIMARY_7": {
    "Mathematics": [
        {"topic": "Sets", "competency": "3-circle Venn, probability intro", "scenario": "Subjects in class"},
        {"topic": "Number Bases", "competency": "Base 2 to 12, operations", "scenario": "Computer binary"},
        {"topic": "Whole Numbers", "competency": "Large numbers, standard form, indices", "scenario": "National budget"},
        {"topic": "Fractions and Percentages", "competency": "Profit, loss, discount, interest", "scenario": "Bank loan"},
        {"topic": "Integers", "competency": "Real-life applications", "scenario": "Profit and loss"},
        {"topic": "Geometry", "competency": "Construction, nets, bearings", "scenario": "Direction of Kampala"},
        {"topic": "Measures", "competency": "Speed, Velocity, complex area/volume", "scenario": "Bus journey"},
        {"topic": "Graphs and Data Handling", "competency": "Pie charts, coordinate geometry", "scenario": "Election results"},
        {"topic": "Algebra", "competency": "Simultaneous equations", "scenario": "Word problems"}],
    "English": [
        {"topic": "National Environment", "competency": "Describe environment", "scenario": "Uganda wildlife"},
        {"topic": "Wildlife/Tourism", "competency": "Tourist attractions", "scenario": "Queen Elizabeth Park"},
        {"topic": "Marriage/Family", "competency": "Family values", "scenario": "Nuclear family"},
        {"topic": "Elections/Democracy", "competency": "Voting process", "scenario": "School prefect"},
        {"topic": "National Assembly/Parliament", "competency": "Role of parliament", "scenario": "MPs"},
        {"topic": "Prints and Media", "competency": "Newspapers, radio", "scenario": "Daily Monitor"},
        {"topic": "Examination/High School Readiness", "competency": "Exam skills", "scenario": "PLE"}],
    "Integrated Science": [
        {"topic": "Plant Life", "competency": "Reproduction, pollination, germination", "scenario": "Bean seed"},
        {"topic": "Animal Life", "competency": "Invertebrates: worms, mollusks", "scenario": "Earthworm"},
        {"topic": "Human Body", "competency": "Excretory, nervous system", "scenario": "Kidneys"},
        {"topic": "Health and Diseases", "competency": "Non-communicable diseases", "scenario": "Diabetes"},
        {"topic": "Physical Science and Energy", "competency": "Light, electricity, magnetism", "scenario": "Bulb"},
        {"topic": "Simple Machines", "competency": "Levers, pulleys, inclined plane", "scenario": "Wheelbarrow"},
        {"topic": "Environment and Interdependence", "competency": "Ecosystems, pollution", "scenario": "Global warming"}],
    "Social Studies (SST)": [
        {"topic": "Location of Africa", "competency": "Continents, oceans", "scenario": "Map of world"},
        {"topic": "Physical Features and Drainage", "competency": "Rivers Nile, Congo", "scenario": "River Nile"},
        {"topic": "Climate and Vegetation Zones", "competency": "Equatorial, desert", "scenario": "Sahara"},
        {"topic": "History and Colonization", "competency": "Slave trade, exploration", "scenario": "Speke"},
        {"topic": "Independence and Post-Independence", "competency": "Pan-Africanism, AU", "scenario": "OAU"},
        {"topic": "Major World Organizations", "competency": "UN, Commonwealth", "scenario": "United Nations"}]
  }
}

PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}

def get_topic_data(grade, subject, topic_name):
    grade_num = grade.replace("P","")
    grade_key = f"PRIMARY_{grade_num}"
    if grade_key in PRIMARY_DB and subject in PRIMARY_DB[grade_key]:
        for t in PRIMARY_DB[grade_key][subject]:
            if t["topic"] == topic_name: return t
    return None

@st.cache_resource
def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("Add GROQ_API_KEY in Streamlit Secrets"); return None

def generate_pdf(content, title):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height-50, title)
    y = height - 80
    c.setFont("Helvetica", 9)
    for line in content.split('\n')[:60]:
        c.drawString(40, y, line[:95])
        y -= 14
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()
    buffer.seek(0)
    return buffer

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except: return None

def speech_to_text_from_audio(audio_bytes):
    r = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    try:
        return r.recognize_google(audio)
    except:
        return ""

# ===================== 3. PASSWORD =====================
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

# ===================== 4. MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026 NCDC")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"])
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])

topic_data = get_topic_data(grade, subject, topic)
if topic_data is None: st.error("Topic not found"); st.stop()

st.subheader(f"{grade} {subject}: {topic_data['topic']}")
st.info(f"**NCDC Competency**: {topic_data['competency']}")
st.success(f"**Example**: {topic_data['scenario']}")

tabs = st.tabs(["AI Chat + Voice", "Theory + Practicals", "Quiz + Evaluation", "Math Work", "Teacher Tools"])

with tabs[0]:
    st.header("Ask TeacherK NCDC - Scenario Based")
    q = st.text_input("Type question here e.g: Teach me Fractions")
    audio_input = st.audio_input("Or record your question")
    if audio_input:
        with st.spinner("Transcribing..."):
            q = speech_to_text_from_audio(audio_input.getvalue())
            st.success(f"You said: {q}")
    if st.button("Ask") and q:
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\n\nLevel: {grade}, Subject: {subject}, Topic: {topic_data['topic']}\n\nStudent Request: {q}\n\nNOW TEACH THIS TOPIC USING 2 DIFFERENT UGANDA SCENARIOS AND SHOW MULTIPLE WAYS TO SOLVE EACH TASK."
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile", # 70b for reasoning
                messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}],
                temperature=0.2
            )
            answer = res.choices[0].message.content
            st.markdown(answer) # markdown for bold headers
            audio = text_to_speech(answer)
            if audio: st.audio(audio)
            st.download_button("Download Lesson + Marking Guide as PDF", generate_pdf(answer, f"{grade} {subject} {topic_data['topic']}"), "lesson.pdf")

with tabs[1]:
    st.header("Theory + Practical Activities")
    if st.button("Generate Theory and 2 Practicals"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nFor {grade} {subject} Topic: {topic_data['topic']}. Give 2 scenarios and 2 practical activities pupils can do with local materials."
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], temperature=0.3)
            theory = res.choices[0].message.content
            st.markdown(theory)
            st.download_button("Download Theory as PDF", generate_pdf(theory, f"Theory {topic_data['topic']}"), "theory.pdf")

with tabs[2]:
    st.header("Quiz Generator + Performance Evaluator")
    num_q = st.slider("Number of Questions", 5, 20, 10)
    if st.button("Generate Scenario-Based Quiz"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nGenerate {num_q} scenario-based questions for {grade} {subject} Topic: {topic_data['topic']}. Each question must have a short Uganda scenario. Include marking guide."
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], temperature=0.3)
            st.session_state.quiz = res.choices[0].message.content
            st.markdown(st.session_state.quiz)
            st.download_button("Download Quiz as PDF", generate_pdf(st.session_state.quiz, f"Quiz {topic_data['topic']}"), "quiz.pdf")
    if "quiz" in st.session_state:
        score = st.number_input("Enter Pupil Score out of "+str(num_q), 0, num_q, 5)
        if st.button("Evaluate Performance"):
            client = get_client()
            if client:
                prompt = f"{SYSTEM_PROMPT}\nPupil scored {score}/{num_q} in {grade} {subject} Topic: {topic_data['topic']}. Give: 1.Grade 2.Strengths 3.Weak areas 4.3 Remediation activities with scenarios."
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
                evaluation = res.choices[0].message.content
                st.success(evaluation)
                st.download_button("Download Report as PDF", generate_pdf(evaluation, f"Evaluation {topic_data['topic']}"), "evaluation.pdf")

with tabs[3]:
    st.header("Mathematics Work Page")
    if subject == "Mathematics":
        op = st.selectbox("Operation", ["Addition","Subtraction","Multiplication","Division"])
        if st.button("Generate 10 Scenario Questions"):
            questions = ""
            for i in range(10):
                a=random.randint(1,100)
                b=random.randint(1,20)
                q_line = f"{i+1}. At Owino Market, a trader had {a} tomatoes. She sold {b}. How many remained? =?"
                st.write(q_line)
                questions += q_line + "\n"
            st.download_button("Download Questions as PDF", generate_pdf(questions, f"Math Work {op}"), "math_work.pdf")
    else:
        st.info("This tab is for Mathematics only")

with tabs[4]:
    st.header("🛠️ Teacher Tools - NCDC 2026")
    tool_choice = st.selectbox("Select Teacher Tool", [
        "1. Lesson Plan Generator",
        "2. Report Card Generator",
        "3. Beginning of Term Test",
        "4. Mid Term Exam Generator",
        "5. End of Term Exam + Marking Guide"
    ])
    client = get_client()

    if tool_choice == "1. Lesson Plan Generator":
        st.subheader("📝 NCDC Lesson Plan")
        duration = st.selectbox("Duration", ["40 Minutes", "80 Minutes Double"])
        if st.button("Generate Lesson Plan"):
            if client:
                with st.spinner("Generating..."):
                    prompt = f"{SYSTEM_PROMPT}\nWrite full NCDC 2026 lesson plan for {grade} {subject} Topic: {topic_data['topic']}. Duration: {duration}. Must include 2 scenarios and multiple methods."
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
                    plan = res.choices[0].message.content
                    st.markdown(plan)
                    st.download_button("Download Lesson Plan PDF", generate_pdf(plan, f"Lesson Plan {grade} {topic_data['topic']}"), "lesson_plan.pdf")

    if tool_choice == "2. Report Card Generator":
        st.subheader("📊 Report Card Generator")
        pupil_name = st.text_input("Pupil Full Name")
        term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"])
        marks = st.text_area("Enter marks: Subject, Score/100", "Mathematics, 78\nEnglish, 65\nScience, 82\nSST, 70")
        if st.button("Generate Report Card"):
            try:
                data = [x.split(",") for x in marks.split("\n") if x.strip()]
                df = pd.DataFrame(data, columns=["Subject","Score"])
                df["Score"] = df["Score"].astype(int)
                df["Grade"] = df["Score"].apply(lambda x: "D1" if x>=80 else "C3" if x>=65 else "P7" if x>=50 else "F9")
                st.dataframe(df)
                avg = df["Score"].mean()
                comment = "Excellent performance" if avg>=75 else "Good performance" if avg>=60 else "Needs to work harder"
                report_text = f"REPORT CARD\nName: {pupil_name}\nClass: {grade}\nTerm: {term}\n\n{df.to_string()}\n\nAverage: {avg:.1f}%\nComment: {comment}"
                st.success(f"Average: {avg:.1f}% | Comment: {comment}")
                st.download_button("Download Report Card PDF", generate_pdf(report_text, f"Report Card {pupil_name}"), "report_card.pdf")
            except:
                st.error("Error in marks format. Use: Subject, 78")

    if tool_choice == "3. Beginning of Term Test":
        st.subheader("📘 Beginning of Term Diagnostic Test")
        if st.button("Generate BOT Test"):
            if client:
                with st.spinner("Generating 20 Scenario Questions..."):
                    prompt = f"{SYSTEM_PROMPT}\nGenerate 20 question Beginning of Term diagnostic test for {grade} {subject}. All questions must have short Uganda scenarios. Include marking guide."
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
                    bot = res.choices[0].message.content
                    st.markdown(bot)
                    st.download_button("Download BOT Test PDF", generate_pdf(bot, f"BOT Test {grade} {subject}"), "bot_test.pdf")

    if tool_choice == "4. Mid Term Exam Generator":
        st.subheader("📗 Mid Term Exam")
        topics_covered = st.text_input("Topics covered so far, comma separated", topic_data['topic'])
        if st.button("Generate Mid Term Exam"):
            if client:
                with st.spinner("Generating 50 Marks Exam..."):
                    prompt = f"{SYSTEM_PROMPT}\nGenerate Mid Term Exam for {grade} {subject}. Topics: {topics_covered}. 50 marks. All questions scenario based. Include marking guide."
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
                    midterm = res.choices[0].message.content
                    st.markdown(midterm)
                    st.download_button("Download Mid Term PDF", generate_pdf(midterm, f"Mid Term {grade} {subject}"), "midterm.pdf")

    if tool_choice == "5. End of Term Exam + Marking Guide":
        st.subheader("📙 End of Term Exam - 100 Marks PLE Style")
        if st.button("Generate End of Term Exam"):
            if client:
                with st.spinner("Generating 100 Marks PLE Style Exam..."):
                    prompt = f"{SYSTEM_PROMPT}\nGenerate End of Term Exam for {grade} {subject}. 100 marks PLE style. All questions must be scenario based. Section A: 40 MCQ. Section B: 10 short answer. Section C: 5 essay. Include detailed marking guide."
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
                    eot = res.choices[0].message.content
                    st.markdown(eot)
                    st.download_button("Download EOT Exam PDF", generate_pdf(eot, f"End of Term {grade} {subject}"), "eot_exam.pdf")

st.sidebar.caption("NCDC 2026 Competency-Based | P4-P7")
