import streamlit as st
import io, re, hashlib, json, requests
from datetime import datetime, timedelta
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

CONTACT = "256751040731"
ADMIN_WHATSAPP = "256751040731" # Admin number to receive alerts + requests
st.set_page_config(page_title="TEACHERK PRO 2026 NCDC", page_icon="👩‍🏫", layout="wide")

# ===================== WHATSAPP ALERT FUNCTION =====================
def send_whatsapp_alert(message):
    """Sends WhatsApp message via Meta Cloud API. Add tokens in Secrets"""
    try:
        token = st.secrets.get("WHATSAPP_TOKEN", "")
        phone_id = st.secrets.get("WHATSAPP_PHONE_ID", "")
        if not token or not phone_id: return
        url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        data = {"messaging_product": "whatsapp", "to": ADMIN_WHATSAPP, "type": "text", "text": {"body": message}}
        requests.post(url, headers=headers, json=data, timeout=5)
    except: pass

# ===================== MASTER PROMPT - NCDC 2026 + UNEB COMPLIANT =====================
MASTER_PROMPT = """
YOU ARE: An Expert Educational Assistant AI, specifically trained for the Ugandan school system.
YOUR ROLE: Help Teachers and Directors of Studies (DOS) generate high-quality, legally compliant academic documents on a per-term basis.

STRICT OPERATIONAL STANDARDS - YOU MUST FOLLOW ALL:

1. CURRICULUM ALIGNMENT
    - PRIMARY: Follow the NCDC 2026 Revised Primary Curriculum for P4-P7. Emphasize Competency-Based Learning and Activities of Integration (AoI).
    - SECONDARY: Follow the New Lower Secondary Curriculum (NLSC) frameworks by NCDC. Emphasize Competency-Based Learning, AoI, and formative/summative assessment strands.
    - NATIONAL TESTING: Ensure all exams and marking guides align with Uganda National Examinations Board (UNEB) standards for PLE, UCE, and UACE formats.

2. DOCUMENT OUTPUT REQUIREMENTS
    - Lesson Plans: MUST include: Standard Competencies, Learning Outcomes, Introduction, Teacher Activities, Learner Activities, Instructional Materials, Evaluation/Assessment methods, and Reflection.
    - Schemes of Work: Format as a TABLE by Week, Period, Topic/Sub-topic, Competencies, Learning Objectives, Methods, Instructional Materials, and Remarks. Break down by Term 1, Term 2, or Term 3.
    - Marking Guides: Provide clear, step-by-step scoring grids. Allocate marks for competency achievements and application, not just rote recall. Show method marks.
    - Report Card Comments: Generate professional, constructive continuous-assessment comments. Avoid generic phrases. Focus on learner competencies, behaviour, and areas for improvement using Ugandan context-friendly tone.

3. LOCALIZATION AND CONTEXT
    - Use British English spelling: "Programme", "Learner", "Continuous Assessment", "Centre", "Analyse".
    - Use local context, Ugandan names, scenarios, and examples in exam questions and AoI. Use UGX, local markets, farming, and Ugandan geographical features.

4. OUTPUT FORMATTING
    - Keep all outputs highly structured, clean, and ready to be copied into Microsoft Word, Excel, or Google Docs.
    - Use clear Markdown headers: ##, ### and bullet points.
    - NO SVG, NO IMAGES, NO DIAGRAMS. Text and Tables only.

5. INPUT CLARIFICATION RULE
    - Before generating, you MUST have: Class/Class Level, Subject, Term, and Specific Topic.
    - If any are missing, STOP and ask the user: "To generate a compliant document, please confirm: 1. Class Level: 2. Subject: 3. Term: 4. Topic: "

TONE: Professional, supportive, like a DOS/Headteacher. End every document with "TEACHER NOTES: NCDC 2026 Competency Alignment".
"""

# ===================== FULL DB RESTORED - 205 TOPICS + CRE + IRE =====================
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

# ===================== LOGGING IN MEMORY =====================
if "usage_log" not in st.session_state:
    st.session_state.usage_log = []

def log_action(action, grade="", subject="", topic="", details=""):
    log_entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "school": st.session_state.get("school_name", "Unknown"), "action": action, "grade": grade, "subject": subject, "topic": topic, "details": details}
    st.session_state.usage_log.append(log_entry)

# ===================== GROQ + PDF ENGINE =====================
if "cache" not in st.session_state:
    st.session_state.cache = {}

def smart_groq_call(client, system_prompt, user_prompt):
    cache_key = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
    if cache_key in st.session_state.cache:
        return st.session_state.cache[cache_key]
    models_to_try = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    for model in models_to_try:
        try:
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.2, max_tokens=2500, timeout=60)
            if res and res.choices[0].message.content:
                st.session_state.cache[cache_key] = res
                return res
        except RateLimitError: continue
        except Exception: continue
    return None

def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("GROQ_API_KEY missing in Secrets"); return None

def generate_pdf(content, title):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    year = datetime.now().year
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height-40, f"TEACHERK PRO - {title} {year}")
    c.setFont("Helvetica", 10)
    y = height - 70
    for line in content.split('\n')[:900]:
        if y < 50: c.showPage(); y = height - 50
        c.drawString(40, y, line[:105])
        y -= 14
    c.save(); buffer.seek(0); return buffer

# ===================== LICENSE + ADMIN LOGIN + REQUEST BUTTON =====================
def check_license():
    LICENSE_DATA = st.secrets.get("LICENSE_KEYS", "DEMO:2026-12-31")
    ADMIN_KEY = st.secrets.get("ADMIN_KEY", "ADMIN256")

    if "licensed" not in st.session_state:
        st.title("👩‍🏫 TEACHERK PRO 2026 - LOGIN")
        login_type = st.radio("Login As:", ["School", "Admin"], horizontal=True)

        if login_type == "Admin":
            admin_pw = st.text_input("Enter Admin Key", type="password")
            if st.button("Activate License", type="primary"):
                if admin_pw == ADMIN_KEY:
                    st.session_state["licensed"] = True
                    st.session_state["user_type"] = "Admin"
                    st.session_state["school_name"] = "ADMIN DASHBOARD"
                    send_whatsapp_alert(f"🚨 ADMIN LOGIN: Admin logged into TEACHERK PRO at {datetime.now()}")
                    st.rerun()
                else: st.error("Wrong Admin Key")
            st.stop()
        else:
            st.info("This is a Licensed Product for Schools. Contact Admin to get a License Key.")
            req_school = st.text_input("School Name to Request Key For")
            req_contact = st.text_input("Your WhatsApp Number")
            if st.button("📲 Request License Key"):
                if req_school and req_contact:
                    send_whatsapp_alert(f"📩 NEW LICENSE REQUEST\nSchool: {req_school}\nContact: {req_contact}\nTime: {datetime.now()}")
                    st.success("Request Sent! Admin will WhatsApp you shortly with payment details.")
                else:
                    st.warning("Please enter School Name and Your Number")
            st.markdown("---")
            license_input = st.text_input("Enter License Key: SCHOOLCODE:YYYY-MM-DD", type="password")
            school_name = st.text_input("School Name")

            if st.button("Login with License Key", type="primary"):
                try:
                    key, expiry_str = license_input.strip().split(":")
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                    today = datetime.now().date()
                    days_left = (expiry_date - today).days
                    if key in LICENSE_DATA and school_name.strip()!= "":
                        if today <= expiry_date:
                            st.session_state["licensed"] = True
                            st.session_state["user_type"] = "School"
                            st.session_state["school_name"] = school_name
                            st.session_state["expiry_date"] = expiry_date
                            log_action("LOGIN")
                            send_whatsapp_alert(f"✅ NEW LOGIN: {school_name} logged in. Expires in {days_left} days")
                            if days_left <= 7:
                                send_whatsapp_alert(f"⚠️ RENEWAL ALERT: {school_name} license expires in {days_left} days on {expiry_date}")
                            st.success(f"License Activated for {school_name}")
                            st.rerun()
                        else: st.error(f"License Expired on {expiry_date}. Contact Admin.")
                    else: st.error("Invalid License Key or School Name")
                except: st.error("Wrong Format. Use: SCHOOLCODE:YYYY-MM-DD")
            st.stop()

    if st.session_state.get("user_type") == "School":
        if datetime.now().date() > st.session_state["expiry_date"]:
            st.error(f"🚨 LICENSE EXPIRED. Contact School Admin to Renew.")
            st.stop()

check_license()

# ===================== MAIN APP =====================
if st.session_state.user_type == "Admin":
    st.title("🔐 TEACHERK PRO - ADMIN DASHBOARD")
    st.sidebar.error("ADMIN MODE")
    admin_tabs = st.tabs(["📊 Live Usage Logs", "🏫 License Management", "📈 Analytics"])
    with admin_tabs[0]:
        st.header("Live Monitoring Logs - Session Only")
        if st.session_state.usage_log:
            for log in reversed(st.session_state.usage_log[-100:]):
                st.write(f"`{log['timestamp']}` | **{log['school']}** | {log['action']} | {log['grade']} {log['subject']} {log['topic']}")
        else: st.write("No activity yet.")
    with admin_tabs[1]:
        st.header("License Management")
        st.code(st.secrets.get("LICENSE_KEYS", "Add LICENSE_KEYS in secrets"))
        st.warning("To add new school: Add SCHOOLCODE:YYYY-MM-DD to LICENSE_KEYS in Secrets and Redeploy")
    with admin_tabs[2]:
        st.header("Analytics")
        schools = [log['school'] for log in st.session_state.usage_log]
        st.metric("Total Actions This Session", len(st.session_state.usage_log))
        st.metric("Unique Schools Active", len(set(schools)))
    st.stop()

# ===================== SCHOOL USER INTERFACE =====================
days_left = (st.session_state["expiry_date"] - datetime.now().date()).days
st.title(f"👩‍🏫 TEACHERK PRO v7.8 - {st.session_state.school_name}")
st.sidebar.success(f"Licensed School: {st.session_state.school_name}")
st.sidebar.warning(f"License Expires in: {days_left} days")
if days_left <= 7:
    st.sidebar.error(f"⚠️ License expires in {days_left} days. Contact Admin to Renew.")

grade = st.sidebar.selectbox("Select Class Level", ["P4","P5","P6","P7"])
subject = st.sidebar.selectbox("Select Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = st.sidebar.selectbox("Select Topic", PRIMARY_CURRICULUM_MAP[grade][subject])

tabs = st.tabs(["1. Test Paper Generator", "2. Marking Guide Generator", "3. Auto Marking Assistant", "4. Report Card Generator", "5. Lesson Plan + Scheme"])

def run_ai(task_name, prompt):
    log_action(task_name, grade, subject, topic)
    client = get_client()
    if not client: return
    with st.spinner("Generating NCDC 2026 Compliant Document..."):
        res = smart_groq_call(client, MASTER_PROMPT, prompt)
    if res:
        answer = res.choices[0].message.content
        st.markdown(answer)
        pdf = generate_pdf(answer, task_name)
        st.download_button("📥 Download as PDF for Printing", pdf, f"{task_name}.pdf")
    else:
        st.error("AI Busy. Try again in 1 minute.")

with tabs[0]:
    st.header("1. Test Paper Generator")
    term = st.selectbox("Select Term", ["Term 1", "Term 2", "Term 3"], key="test_term")
    num_qn = st.selectbox("Number of Questions", [10, 20, 30, 40])
    if st.button("Generate Test Paper", type="primary"):
        prompt = f"Generate a {num_qn} question NCDC 2026 {term} test for {grade} {subject} on Topic: {topic}. DIFFICULTY: {grade}. Format: Section A and B. Include 2 Activities of Integration with Ugandan context using UGX and local scenarios. Use UNEB PLE format."
        run_ai(f"Test_{grade}_{subject}_{term}", prompt)

with tabs[1]:
    st.header("2. UNEB Marking Guide Generator")
    term = st.selectbox("Select Term", ["Term 1", "Term 2", "Term 3"], key="mg_term")
    questions = st.text_area("Paste Test Questions Here", height=200)
    total_marks = st.text_input("Total Marks", "100")
    if st.button("Generate Marking Guide"):
        prompt = f"Act as UNEB Examiner for {grade} {subject}, {term}. Create a detailed marking guide for these questions. Total: {total_marks} marks. Use step-by-step scoring grid. Allocate marks for competency achievement and method. Q: {questions}"
        run_ai(f"MarkingGuide_{subject}_{term}", prompt)

with tabs[2]:
    st.header("3. Auto Marking Assistant")
    marking_scheme = st.text_area("Step 1: Paste Marking Scheme", height=150)
    student_answers = st.text_area("Step 2: Paste Student Answers: Name: Answer", height=200)
    if st.button("Mark All Work Now"):
        prompt = f"Act as UNEB Examiner for {grade} {subject}. MARK THIS WORK. Give score, competency comment, and areas for improvement. Use constructive Ugandan context tone.\nSCHEME:\n{marking_scheme}\nSTUDENT WORK:\n{student_answers}"
        run_ai(f"Marked_Work_{subject}", prompt)

with tabs[3]:
    st.header("4. Report Card + Continuous Assessment Comments")
    term = st.selectbox("Select Term", ["Term 1", "Term 2", "Term 3"], key="rc_term")
    pupil_name = st.text_input("Pupil Full Name")
    scores = st.text_area("Paste scores: Subject: Score out of 100")
    conduct = st.selectbox("Conduct", ["Excellent", "Very Good", "Good", "Fair"])
    if st.button("Generate Report Card"):
        prompt = f"Generate an official NCDC 2026 {term} Report Card for {pupil_name} in {grade}. Scores:\n{scores}\nConduct: {conduct}. Include average, position, and professional continuous assessment comments focusing on competencies. Use British English and Ugandan context."
        run_ai(f"ReportCard_{pupil_name}_{term}", prompt)

with tabs[4]:
    st.header("5. Lesson Plan + Scheme of Work Generator")
    term = st.selectbox("Select Term", ["Term 1", "Term 2", "Term 3"], key="lp_term")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Lesson Plan"):
            prompt = f"Generate a detailed NCDC 2026 Lesson Plan for {grade} {subject}, {term}. Topic: {topic}. MUST include: Standard Competencies, Learning Outcomes, Introduction, Teacher Activities, Learner Activities, Instructional Materials, Evaluation/Assessment, and Reflection."
            run_ai(f"LessonPlan_{topic}_{term}", prompt)
    with col2:
        if st.button("Generate Scheme of Work"):
            prompt = f"Create a full {term} Scheme of Work for {grade} {subject} as a TABLE. Columns: Week, Period, Topic/Sub-topic, Competencies, Learning Objectives, Methods, Instructional Materials, Remarks. Break down Topic: {topic}."
            run_ai(f"SOW_{subject}_{term}", prompt)

st.sidebar.caption(f"NCDC 2026 | Licensed to: {st.session_state.school_name} | Support: {CONTACT}")
