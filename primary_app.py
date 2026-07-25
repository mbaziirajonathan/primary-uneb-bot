import streamlit as st
import os, io, json, random, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from datetime import datetime
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import streamlit.components.v1 as components

# ===================== CONFIG =====================
CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7. Confirm with Class Teacher.")

SYSTEM_PROMPT = """
You are TEACHERK, a Senior NCDC 2026 Uganda PLE Examiner and Master Teacher for PRIMARY P4-P7.
You think like Meta AI: flexible, deep reasoning, but you ONLY teach NCDC 2026 Uganda Primary Curriculum.

CORE RULES:
1. ANSWER THE EXACT QUESTION ASKED. Do not force it into the selected topic.
2. USE DEEP REASONING: Break down, give examples, give 2 methods if math.
3. ANTI-HALLUCINATION LOCK: Only teach topics in P4-P7 NCDC. If question is outside P4-P7, say: "This topic is not in NCDC P4-P7. The closest NCDC topic is: [topic]"
4. ACCURACY: Use exact numbers from question. Never invent measurements.
5. PRECISION: Show all steps. End math with "Therefore the... was [number][unit]"
6. TONE: Friendly, patient, Ugandan. Use local examples: boda boda, market, shamba, school.

IF MATH:
Use this format and SHOW ALL STEPS. NO JUMPING.
Step 1: Given:...
Step 2: Formula:...
Step 3: Substitute:...
Step 4: Calculate:...
Step 5: Answer:... Therefore the...

IF GEOMETRY: ADD DIAGRAM TAG AT END WITH EXACT MEASUREMENTS FROM QUESTION:
[DIAGRAM: Topic=Triangle, Measurements="Base=8cm, Angle=50deg", Question="Construct triangle"]

SYLLABUS REFERENCE: Use the provided NCDC topics to check if question is valid. If valid, reference the topic name.
"""

# ===================== 2. DIAGRAM GENERATOR - ANTI HALLUCINATION =====================
def draw_math_diagram(d_type, measurements, question_text):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal'); plt.axis('off'); ax.set_title(f"{d_type}\n{question_text}", fontsize=12, pad=20)
    data = measurements.lower() if measurements else ""
    def safe_float(s, default):
        try: return float(re.findall(r"[\d.]+", s)[0])
        except: return default

    if d_type and "triangle" in d_type.lower():
        base = safe_float(data.split("base=")[1], 8.0) if "base=" in data else 8.0
        angle_deg = safe_float(data.split("angle=")[1], 50.0) if "angle=" in data else 50.0
        angle_rad = math.radians(angle_deg); apex_x = base / 2; apex_y = (base / 2) * math.tan(angle_rad) if angle_deg < 90 else base
        side_len = math.sqrt(apex_x**2 + apex_y**2); A, B, C = (0, 0), (base, 0), (apex_x, apex_y)
        triangle = patches.Polygon([A, B, C], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(triangle)
        ax.text(A[0]-0.5, A[1]-0.5, "A"); ax.text(B[0]+0.5, B[1]-0.5, "B"); ax.text(C[0], C[1]+0.5, "C")
        ax.text(base/2, -0.5, f"{base}cm", ha='center'); ax.set_xlim(-2, base+2); ax.set_ylim(-2, apex_y+2)
    elif d_type and any(x in d_type.lower() for x in ["square", "rectangle"]):
        w = safe_float(data.split("width=")[1], 6.0) if "width=" in data else safe_float(data.split("length=")[1], 6.0) if "length=" in data else 6.0
        h = safe_float(data.split("height=")[1], 4.0) if "height=" in data else w if "square" in d_type.lower() else 4.0
        A, B, C, D = (0, 0), (w, 0), (w, h), (0, h)
        poly = patches.Polygon([A, B, C, D], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(poly)
        ax.text(w/2, -0.5, f"{w}cm", ha='center'); ax.text(-0.8, h/2, f"{h}cm", va='center', rotation=90)
        ax.set_xlim(-2, w+2); ax.set_ylim(-2, h+2)
    elif d_type and "circle" in d_type.lower():
        r = safe_float(data.split("radius=")[1], 3.0) if "radius=" in data else 3.0
        circle = patches.Circle((0, 0), r, fill=False, edgecolor='black', lw=2); ax.add_patch(circle)
        ax.text(r/2, -0.5, f'{r} cm', ha='center'); ax.set_xlim(-r-1, r+1); ax.set_ylim(-r-1, r+1)
    plt.tight_layout(); buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight'); buf.seek(0); plt.close(fig); return buf

def parse_diagram_tag(text):
    if "[DIAGRAM:" not in text: return None
    try:
        tag = text.split("[DIAGRAM:")[1].split("]")[0]; parts = {}
        for item in tag.split(","):
            if "=" in item: k,v = item.split("=",1); parts[k.strip()] = v.strip().strip('"')
        return parts if parts.get("Topic") else None
    except: return None

# ===================== 3. FULL NCDC 2026 DB - ALL 6 SUBJECTS NO DATA LOSS =====================
PRIMARY_DB = {
  "PRIMARY_4": {
    "Mathematics": [{"topic": "Set Concepts", "competency": "Identify, name and form sets", "scenario": "Grouping pupils"}, {"topic": "Whole Numbers (Up to 99,999)", "competency": "Read, write, place value", "scenario": "Taxi park"}, {"topic": "Operations on Whole Numbers", "competency": "Add, subtract, multiply, divide", "scenario": "Buying books"}, {"topic": "Fractions", "competency": "Add and subtract fractions", "scenario": "Sharing mandazi"}, {"topic": "Geometric Shapes and Symmetry", "competency": "Identify shapes", "scenario": "Classroom shapes"}, {"topic": "Measures", "competency": "Measure and convert units", "scenario": "Cooking"}, {"topic": "Money and Financial Literacy", "competency": "Count money and budgets", "scenario": "Pocket money"}, {"topic": "Patterns and Sequences", "competency": "Complete patterns", "scenario": "Beads"}, {"topic": "Basic Data Handling", "competency": "Draw bar graphs", "scenario": "Favorite foods"}],
    "English Language": [{"topic": "Describing People and Objects", "competency": "Use adjectives", "scenario": "Describe teacher"}, {"topic": "Giving Directions", "competency": "Use prepositions", "scenario": "School to market"}, {"topic": "Feelings and Preferences", "competency": "Express likes/dislikes", "scenario": "Favorite food"}, {"topic": "Comprehension: Descriptive Paragraphs", "competency": "Answer from paragraphs", "scenario": "Village day"}, {"topic": "Comprehension: Simple Dialogues", "competency": "Interpret dialogues", "scenario": "At shop"}, {"topic": "Comprehension: Picture Interpretation", "competency": "Describe picture", "scenario": "School compound"}],
    "Integrated Science": [{"topic": "Plant Life and Flowering Plants", "competency": "Identify parts", "scenario": "Mango tree"}, {"topic": "Crop Husbandry", "competency": "Name tools", "scenario": "Garden"}, {"topic": "Weather", "competency": "Identify elements", "scenario": "Rainfall"}, {"topic": "Human Body", "competency": "Name body parts", "scenario": "Bathing"}, {"topic": "Personal Hygiene", "competency": "Practice hygiene", "scenario": "Tippy tap"}, {"topic": "Vectors and Pests", "competency": "Control vectors", "scenario": "Malaria"}, {"topic": "First Aid", "competency": "Give first aid", "scenario": "Cut"}, {"topic": "Air", "competency": "Properties of air", "scenario": "Kite"}, {"topic": "Water", "competency": "Uses of water", "scenario": "Washing"}, {"topic": "Indigenous Crafts", "competency": "Make crafts", "scenario": "Basket"}],
    "Social Studies (SST)": [{"topic": "Location of Our Sub-County", "competency": "Locate on map", "scenario": "Nakawa"}, {"topic": "Physical Features", "competency": "Describe features", "scenario": "Wetland"}, {"topic": "Vegetation and Animals", "competency": "Name them", "scenario": "School trees"}, {"topic": "People and Culture", "competency": "Describe culture", "scenario": "Dance"}, {"topic": "Economic Activities", "competency": "Name activities", "scenario": "Selling tomatoes"}, {"topic": "Social Services", "competency": "Identify services", "scenario": "Health center"}, {"topic": "Leadership", "competency": "Name leaders", "scenario": "LC1"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Creation and Our Talents", "competency": "Appreciate creation", "scenario": "Gifts"}, {"topic": "Knowing Jesus Christ", "competency": "Narrate early life", "scenario": "Temple"}, {"topic": "Christian Values", "competency": "Practice values", "scenario": "Forgiving"}, {"topic": "The Bible", "competency": "Respect Bible", "scenario": "Reading"}, {"topic": "Prayer", "competency": "Participate", "scenario": "Assembly"}, {"topic": "Relationships", "competency": "Maintain relationships", "scenario": "Helping"}, {"topic": "Serving Others", "competency": "Serve", "scenario": "Visiting sick"}],
    "Islamic Religious Education (IRE)": [{"topic": "Selected Surahs", "competency": "Memorize Surahs", "scenario": "Al-Fatiha"}, {"topic": "Pillars of Islam", "competency": "Explain Shahadah and Salat", "scenario": "5 prayers"}, {"topic": "Pillars of Iman", "competency": "Explain faith", "scenario": "Believing"}, {"topic": "Life of Prophet Muhammad", "competency": "Narrate early life", "scenario": "Orphan"}, {"topic": "Islamic Manners", "competency": "Practice manners", "scenario": "Truth"}, {"topic": "Wudhu and Adhan", "competency": "Perform Wudhu", "scenario": "Before prayer"}]
  },
  "PRIMARY_5": {
    "Mathematics": [{"topic": "Set Theory", "competency": "Venn diagrams", "scenario": "Math and English"}, {"topic": "Whole Numbers", "competency": "Up to 999,999", "scenario": "Population"}, {"topic": "BODMAS", "competency": "Apply BODMAS", "scenario": "Shop"}, {"topic": "LCM and GCF", "competency": "Find LCM GCF", "scenario": "Bells"}, {"topic": "Fractions", "competency": "Operations", "scenario": "Cake"}, {"topic": "Decimals", "competency": "Operate decimals", "scenario": "Sugar"}, {"topic": "Geometry", "competency": "Construct angles", "scenario": "Protractor"}, {"topic": "Measures", "competency": "Perimeter area volume", "scenario": "Garden"}, {"topic": "Graphs", "competency": "Interpret graphs", "scenario": "Rainfall"}, {"topic": "Business Math", "competency": "Profit loss", "scenario": "Mandazi"}],
    "English Language": [{"topic": "Sanitation and Health", "competency": "Discuss sanitation", "scenario": "Campaign"}, {"topic": "Local Culture", "competency": "Describe culture", "scenario": "Wedding"}, {"topic": "Simple Past Tense", "competency": "Use past tense", "scenario": "Holidays"}, {"topic": "Present Continuous", "competency": "Use present continuous", "scenario": "In garden"}, {"topic": "Conjunctions", "competency": "Use because, although, but", "scenario": "Why I like school"}, {"topic": "Wh- Questions", "competency": "Form Wh- questions", "scenario": "Interview"}, {"topic": "Interpreting Notices", "competency": "Read notices", "scenario": "Health notice"}, {"topic": "Public Announcements", "competency": "Answer from announcements", "scenario": "Assembly"}, {"topic": "Informational Texts", "competency": "Extract facts", "scenario": "Wash hands"}],
    "Integrated Science": [{"topic": "Soil Science", "competency": "Soil conservation", "scenario": "Grass"}, {"topic": "Non-Flowering Plants", "competency": "Classify", "scenario": "Mushrooms"}, {"topic": "Matter", "competency": "States of matter", "scenario": "Boiling"}, {"topic": "Poultry", "competency": "Manage poultry", "scenario": "Chicken"}, {"topic": "Bee Keeping", "competency": "Explain bee keeping", "scenario": "Honey"}, {"topic": "Body Systems", "competency": "Digestive system", "scenario": "Eating"}, {"topic": "Immunization", "competency": "Explain immunization", "scenario": "Vaccination"}, {"topic": "Waste Management", "competency": "Manage waste", "scenario": "Rubbish"}, {"topic": "PHC", "competency": "PHC elements", "scenario": "Health ed"}, {"topic": "First Aid", "competency": "First aid", "scenario": "Burn"}],
    "Social Studies (SST)": [{"topic": "Geography of Uganda", "competency": "Locate Uganda", "scenario": "Map"}, {"topic": "Physical Features", "competency": "Describe features", "scenario": "Lake Victoria"}, {"topic": "Climate", "competency": "Explain climate", "scenario": "Rainy"}, {"topic": "Vegetation Zones", "competency": "Identify zones", "scenario": "Forest"}, {"topic": "Natural Resources", "competency": "State resources", "scenario": "Gold"}, {"topic": "People of Uganda", "competency": "Name ethnic groups", "scenario": "Baganda"}, {"topic": "Kingdoms", "competency": "Describe kingdoms", "scenario": "Buganda"}, {"topic": "Colonial History", "competency": "Explain colonialism", "scenario": "British"}, {"topic": "Independence", "competency": "Explain independence", "scenario": "1962"}],
    "Christian Religious Education (CRE)": [{"topic": "God's Covenant", "competency": "Explain covenant", "scenario": "Noah"}, {"topic": "Ministry of Jesus", "competency": "Narrate ministry", "scenario": "Healing"}, {"topic": "Parables", "competency": "Explain parables", "scenario": "Good Samaritan"}, {"topic": "Christian Responses", "competency": "Respond to suffering", "scenario": "Prayer"}, {"topic": "The Church", "competency": "Describe Church", "scenario": "Service"}, {"topic": "Holy Days", "competency": "Observe holy days", "scenario": "Christmas"}, {"topic": "Integrity", "competency": "Show integrity", "scenario": "No cheating"}],
    "Islamic Religious Education (IRE)": [{"topic": "Recitation of Surahs", "competency": "Recite with meaning", "scenario": "Ikhlas"}, {"topic": "Surat Al-Fatiha", "competency": "Explain Fatiha", "scenario": "Meaning"}, {"topic": "Zakat and Fasting", "competency": "Explain Zakat", "scenario": "Ramadhan"}, {"topic": "Faith in Books", "competency": "Explain faith", "scenario": "Qur'an"}, {"topic": "Call to Prophethood", "competency": "Narrate call", "scenario": "Jibril"}, {"topic": "Islamic Etiquette", "competency": "Practice etiquette", "scenario": "Greeting"}, {"topic": "Holy Sites", "competency": "Name sites", "scenario": "Mecca"}]
  },
  "PRIMARY_6": {
    "Mathematics": [{"topic": "Advanced Set Operations", "competency": "3-set problems", "scenario": "Sports"}, {"topic": "Integers and Bases", "competency": "Work with integers", "scenario": "Temperature"}, {"topic": "Fractions and Decimals", "competency": "Operations", "scenario": "Market"}, {"topic": "Ratios", "competency": "Solve ratios", "scenario": "Juice"}, {"topic": "Sequences", "competency": "Find nth term", "scenario": "Pattern"}, {"topic": "Geometry", "competency": "Angles in polygons", "scenario": "Pentagon"}, {"topic": "Speed", "competency": "Calculate speed", "scenario": "Taxi"}, {"topic": "Area and Volume", "competency": "Calculate area", "scenario": "Tank"}, {"topic": "Simple Interest", "competency": "Calculate interest", "scenario": "Loan"}, {"topic": "Algebra", "competency": "Solve equations", "scenario": "Find x"}, {"topic": "Probability", "competency": "Find probability", "scenario": "Coin"}],
    "English Language": [{"topic": "Electronic Media", "competency": "Discuss radio TV", "scenario": "Radio Uganda"}, {"topic": "Messaging", "competency": "Describe phones", "scenario": "WhatsApp"}, {"topic": "Future Tenses", "competency": "Use will and going to", "scenario": "After PLE"}, {"topic": "If-Conditionals", "competency": "Use if clauses", "scenario": "If it rains"}, {"topic": "Relative Pronouns", "competency": "Use who which that", "scenario": "Teacher who"}, {"topic": "Passive Voice", "competency": "Change to passive", "scenario": "Book was written"}, {"topic": "Short Stories", "competency": "Analyze stories", "scenario": "Clever hare"}, {"topic": "Newspaper", "competency": "Read excerpts", "scenario": "New Vision"}, {"topic": "Dialogue", "competency": "Interpret dialogue", "scenario": "Doctor"}],
    "Integrated Science": [{"topic": "Plant Classification", "competency": "Classify plants", "scenario": "Flowering"}, {"topic": "Invertebrates", "competency": "Classify invertebrates", "scenario": "Earthworm"}, {"topic": "Vertebrates", "competency": "Classify vertebrates", "scenario": "Chicken"}, {"topic": "Domestic Animals", "competency": "Keep animals", "scenario": "Goats"}, {"topic": "Sound", "competency": "Explain sound", "scenario": "Echo"}, {"topic": "Matter", "competency": "Classify matter", "scenario": "Salt water"}, {"topic": "Body Systems", "competency": "Circulatory", "scenario": "Blood"}, {"topic": "Diseases", "competency": "Prevent diseases", "scenario": "Net"}, {"topic": "Indigenous Tech", "competency": "Use tech", "scenario": "Stove"}, {"topic": "Digital Tech", "competency": "Use computer", "scenario": "Computer"}],
    "Social Studies (SST)": [{"topic": "East Africa", "competency": "Locate EAC", "scenario": "Map"}, {"topic": "Physical Features", "competency": "Describe features", "scenario": "Kilimanjaro"}, {"topic": "Wildlife", "competency": "Conserve wildlife", "scenario": "Parks"}, {"topic": "People of EA", "competency": "Explain origins", "scenario": "Trade"}, {"topic": "Colonialism", "competency": "Explain colonialism", "scenario": "Scramble"}, {"topic": "Inventions", "competency": "Describe inventions", "scenario": "Iron"}, {"topic": "Democracy", "competency": "Explain democracy", "scenario": "Voting"}, {"topic": "EAC", "competency": "Explain EAC", "scenario": "Market"}, {"topic": "Social Services", "competency": "Identify services", "scenario": "Hospital"}],
    "Christian Religious Education (CRE)": [{"topic": "Prophets", "competency": "Explain prophets", "scenario": "Moses"}, {"topic": "Resurrection", "competency": "Explain resurrection", "scenario": "Easter"}, {"topic": "Holy Spirit", "competency": "Explain Holy Spirit", "scenario": "Pentecost"}, {"topic": "Early Church", "competency": "Describe church", "scenario": "Missionaries"}, {"topic": "Witness", "competency": "Witness Christ", "scenario": "Helping"}, {"topic": "Authority", "competency": "Respect authority", "scenario": "Teacher"}, {"topic": "Future", "competency": "Plan future", "scenario": "Career"}],
    "Islamic Religious Education (IRE)": [{"topic": "Memorization", "competency": "Memorize Surahs", "scenario": "Yaseen"}, {"topic": "Hajj", "competency": "Explain Hajj", "scenario": "Pilgrimage"}, {"topic": "Day of Judgment", "competency": "Explain judgment", "scenario": "After life"}, {"topic": "Prophets", "competency": "Narrate stories", "scenario": "Musa"}, {"topic": "Social Values", "competency": "Practice values", "scenario": "Neighbor"}, {"topic": "Festivals", "competency": "Celebrate festivals", "scenario": "Eid"}]
  },
  "PRIMARY_7": {
    "Mathematics": [{"topic": "Advanced Sets", "competency": "3-set word problems", "scenario": "3 subjects"}, {"topic": "Bases", "competency": "Convert bases", "scenario": "Binary"}, {"topic": "Number Theory", "competency": "Number properties", "scenario": "Primes"}, {"topic": "Fractions", "competency": "Convert and solve", "scenario": "Discount"}, {"topic": "Ratios", "competency": "Solve proportion", "scenario": "Sharing"}, {"topic": "Integers", "competency": "Operate integers", "scenario": "Debt"}, {"topic": "Business Math", "competency": "Compound interest", "scenario": "Savings"}, {"topic": "Graphs", "competency": "Draw pie charts", "scenario": "Election"}, {"topic": "Geometry", "competency": "Construct figures", "scenario": "Compass"}, {"topic": "Speed", "competency": "Calculate velocity", "scenario": "Boda"}, {"topic": "Surface Area", "competency": "Calculate surface area", "scenario": "Box"}, {"topic": "Inequalities", "competency": "Solve inequalities", "scenario": "Word"}],
    "English Language": [{"topic": "Friendly Letters", "competency": "Write friendly letters", "scenario": "Pen pal"}, {"topic": "Official Letters", "competency": "Write applications", "scenario": "Prefect"}, {"topic": "Timetables", "competency": "Read timetables", "scenario": "Class timetable"}, {"topic": "Apostrophes", "competency": "Use apostrophes", "scenario": "Pupil's"}, {"topic": "Semicolons and Colons", "competency": "Use ; and :", "scenario": "List"}, {"topic": "Direct Indirect Speech", "competency": "Convert speech", "scenario": "She said"}, {"topic": "Perfect Tenses", "competency": "Use perfect tenses", "scenario": "Have finished"}, {"topic": "Complex Prose", "competency": "Answer from prose", "scenario": "Corruption"}, {"topic": "Poetry", "competency": "Analyze poems", "scenario": "Uganda"}, {"topic": "Graphic Data", "competency": "Interpret tables", "scenario": "Attendance"}, {"topic": "Full Sentences", "competency": "Answer in full sentences", "scenario": "PLE"}],
    "Integrated Science": [{"topic": "Crop Husbandry", "competency": "Practice crop husbandry", "scenario": "Maize"}, {"topic": "Animal Breeding", "competency": "Manage animals", "scenario": "Cattle"}, {"topic": "Energy", "competency": "Explain energy", "scenario": "Solar"}, {"topic": "Simple Machines", "competency": "Use machines", "scenario": "Wheelbarrow"}, {"topic": "Body Systems", "competency": "Excretory system", "scenario": "Kidneys"}, {"topic": "Public Health", "competency": "Promote health", "scenario": "COVID"}, {"topic": "Environment", "competency": "Manage environment", "scenario": "Ecosystem"}, {"topic": "Interdependence", "competency": "Explain food chain", "scenario": "Food"}, {"topic": "Innovation", "competency": "Apply innovation", "scenario": "Phone"}],
    "Social Studies (SST)": [{"topic": "Africa", "competency": "Locate Africa", "scenario": "Map"}, {"topic": "Drainage", "competency": "Describe drainage", "scenario": "Nile"}, {"topic": "Trade", "competency": "Explain trade", "scenario": "AfCFTA"}, {"topic": "People of Africa", "competency": "Describe people", "scenario": "Bantu"}, {"topic": "Slave Trade", "competency": "Explain slave trade", "scenario": "Explorers"}, {"topic": "Independence", "competency": "Explain independence", "scenario": "Nkrumah"}, {"topic": "AU and UN", "competency": "Explain AU UN", "scenario": "HQ"}, {"topic": "Challenges", "competency": "Discuss challenges", "scenario": "Corruption"}],
    "Christian Religious Education (CRE)": [{"topic": "Salvation", "competency": "Explain salvation", "scenario": "Jesus died"}, {"topic": "Kingdom of God", "competency": "Explain Kingdom", "scenario": "Parables"}, {"topic": "Leadership", "competency": "Show leadership", "scenario": "Church"}, {"topic": "Moral Challenges", "competency": "Respond to challenges", "scenario": "Drugs"}, {"topic": "Marriage", "competency": "Practice responsibility", "scenario": "Marriage"}, {"topic": "Christian Hope", "competency": "Explain hope", "scenario": "After death"}, {"topic": "Multi-Faith", "competency": "Live peacefully", "scenario": "Neighbor"}],
    "Islamic Religious Education (IRE)": [{"topic": "Tafsir", "competency": "Explain Tafsir", "scenario": "Verses"}, {"topic": "Divine Decree", "competency": "Explain Qadar", "scenario": "Qadar"}, {"topic": "Shariah", "competency": "Explain Shariah", "scenario": "Justice"}, {"topic": "Sahaba", "competency": "Narrate Sahaba", "scenario": "Abu Bakr"}, {"topic": "Islamic Economics", "competency": "Practice economics", "scenario": "Zakat"}, {"topic": "Contemporary Issues", "competency": "Address issues", "scenario": "Drugs"}]
  }
}

PRIMARY_CURRICULUM_MAP = {g.replace("PRIMARY_","P"): {s: [t["topic"] for t in topics] for s, topics in d.items()} for g,d in PRIMARY_DB.items()}

def get_all_topics_text():
    all_topics = []
    for grade, subjects in PRIMARY_DB.items():
        for subject, topics in subjects.items():
            for t in topics:
                all_topics.append(f"{grade} {subject}: {t['topic']}")
    return "\n".join(all_topics)

def smart_groq_call(client, system_prompt, user_prompt, max_tokens=2000):
    models_to_try = [MODEL_CHOICE, "llama-3.1-8b-instant", "llama-3.1-70b-versatile"]
    models_to_try = list(dict.fromkeys(models_to_try))
    for model in models_to_try:
        try:
            tokens = max_tokens if "70b" in model else 1024
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.3, max_tokens=tokens)
            if model!= MODEL_CHOICE: st.warning(f"⚠️ Switched to {model}")
            return res
        except RateLimitError: continue
        except Exception: continue
    st.error("All Groq models busy."); return None

def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("Add GROQ_API_KEY in Streamlit Secrets"); return None

def generate_pdf(content, title):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
    c.setFont("Helvetica-Bold", 14); c.drawString(40, height-50, title); y = height - 80; c.setFont("Helvetica", 9)
    for line in content.split('\n')[:120]: c.drawString(40, y, line[:95]); y -= 14
    if y < 50: c.showPage(); y = height - 50
    c.save(); buffer.seek(0); return buffer

# ===================== 4. PASSWORD =====================
def check_password():
    APP_PW = st.secrets.get("PRIMARY_APP_PASSWORD", "PRIMARY2026")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "ADMIN256")
    if "password_correct" not in st.session_state:
        st.title("🔒 TEACHERK PRIMARY 2026 NCDC")
        pw = st.text_input("Password", type="password", key="pw_input")
        if st.button("Login"):
            if pw == APP_PW: st.session_state["user_type"] = "Pupil"; st.session_state["password_correct"] = True; st.rerun()
            elif pw == ADMIN_PW: st.session_state["user_type"] = "Teacher"; st.session_state["password_correct"] = True; st.rerun()
            else: st.error("Wrong password")
        st.stop()
check_password()

# ===================== 5. MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026 NCDC - Generic Reasoning Mode")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"], key="grade_select")
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()), key="subject_select")
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject], key="topic_select")
MODEL_CHOICE = st.sidebar.selectbox("AI Brain", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"], index=0)

SYLLABUS_CONTEXT = get_all_topics_text()

tabs = st.tabs(["AI Chat - Ask Anything", "Theory", "Quiz/Test", "Math Work", "Teacher Tools"])

with tabs[0]:
    st.header("Ask TeacherK Anything - P4 to P7 NCDC")
    st.caption("Ask any question. I will answer it directly using NCDC curriculum.")
    q = st.text_input("🔍 Ask your question here", placeholder="e.g: What is photosynthesis? or Solve 3/4 + 1/2", key="chat_q")
    if st.button("Ask TeacherK", key="ask_btn") and q:
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\n\nNCDC SYLLABUS FOR REFERENCE:\n{SYLLABUS_CONTEXT}\n\nCurrent Class Context: {grade} {subject}\n\nSTUDENT QUESTION: {q}\n\nINSTRUCTION: Answer the question directly. If it matches a topic above, mention it. If not, say it's not in P4-P7. Use deep reasoning and examples."
            with st.spinner("TeacherK is reasoning..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                if res:
                    answer = res.choices[0].message.content; st.markdown(answer)
                    diagram_info = parse_diagram_tag(answer)
                    if diagram_info: st.image(draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question","")), use_container_width=True)
                    st.download_button("📥 Download Answer PDF", generate_pdf(answer, f"Answer {grade}"), "answer.pdf", key="dl_answer")

with tabs[1]:
    st.header("Generate Theory")
    if st.button("Generate Theory for Selected Topic", key="theory_btn"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nTeach {grade} {subject} Topic: {topic}. Give theory + 5 examples + 5 activities."
            with st.spinner("Generating..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                if res: theory = res.choices[0].message.content; st.markdown(theory)
                st.download_button("📥 Download Theory PDF", generate_pdf(theory, f"Theory {topic}"), "theory.pdf", key="dl_theory")

with tabs[2]:
    st.header("Generate 50Q Test")
    if st.button("Generate 50 Question Test", key="quiz_btn"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nCreate 50 questions for {grade} {subject} Topic: {topic}. Provide marking guide."
            with st.spinner("Generating 50Q..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                if res: quiz = res.choices[0].message.content; st.markdown(quiz)
                st.download_button("📥 Download 50Q Test PDF", generate_pdf(quiz, f"50Q {topic}"), "test_50q.pdf", key="dl_quiz")

with tabs[3]:
    st.header("Mathematics Work")
    if subject == "Mathematics":
        if st.button("Generate 7 Worked Examples", key="mathwork_btn"):
            client = get_client()
            if client:
                prompt = f"{SYSTEM_PROMPT}\nGenerate 7 fully worked scenario-based math questions for {grade} {subject} Topic: {topic}. EACH QUESTION MUST SHOW EVERY STEP. USE EXACT MEASUREMENTS FROM QUESTION."
                with st.spinner("Generating Math Work..."):
                    res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                    if res:
                        math_work = res.choices[0].message.content; st.markdown(math_work)
                        diagram_info = parse_diagram_tag(math_work)
                        if diagram_info: st.image(draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question","")), use_container_width=True)
                        st.download_button("📥 Download Math Work PDF", generate_pdf(math_work, f"Math Work {topic}"), "math_work.pdf", key="dl_math")
    else: st.info("Select Mathematics subject to use.")

with tabs[4]:
    st.header("Teacher Tools - Automation Suite")
    st.markdown("---")
    st.subheader("1. Test / Exam Paper Generator - 50 Questions")
    col1, col2 = st.columns(2)
    with col1: exam_type = st.selectbox("Exam Type", ["Weekly Test", "Mid Term", "End of Term", "Mock PLE"], key="exam_type")
    with col2: num_q = st.slider("Number of Questions", 10, 50, 50, key="num_q")
    if st.button("Generate Test Paper", key="exam_btn"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nGenerate a {exam_type} for {grade} {subject} covering {topic}. Create {num_q} questions. Provide full marking guide with steps and marks. Use UNEB format. ACCURACY: Use exact numbers given."
            with st.spinner("Generating Exam Paper..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                if res: exam = res.choices[0].message.content; st.markdown(exam)
                st.download_button("📥 Download Exam PDF", generate_pdf(exam, f"{exam_type} {grade} {subject}"), "exam.pdf", key="dl_exam")

    st.markdown("---")
    st.subheader("2. Marking / Grading Assistant")
    st.info("Upload pupils' work or type answers. TEACHERK will mark like UNEB examiner. Deducts for no units and jumped steps.")
    uploaded_file = st.file_uploader("Upload Pupils Work.txt or.pdf", type=["txt","pdf"], key="mark_upload")
    student_answers = st.text_area("Or paste student answers here", height=150, key="mark_paste")
    marking_scheme = st.text_area("Paste Marking Scheme / Answers", height=100, key="mark_scheme")
    if st.button("Mark Work Now", key="mark_btn"):
        client = get_client()
        if client and (uploaded_file or student_answers):
            content = uploaded_file.read().decode("utf-8") if uploaded_file else student_answers
            prompt = f"You are a UNEB Examiner. Mark this {grade} {subject} work strictly. Deduct 1 mark for missing units and jumped steps. ACCURACY RULE: Check every number.\n\nMARKING SCHEME:\n{marking_scheme}\n\nSTUDENT WORK:\n{content}\n\nProvide: Total Score, Breakdown per question, Comments, and What to improve."
            with st.spinner("Marking..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=2000)
                if res: marked = res.choices[0].message.content; st.markdown(marked)
                st.download_button("📥 Download Marked Report", generate_pdf(marked, "Marked Work"), "marked.pdf", key="dl_marked")

    st.markdown("---")
    st.subheader("3. Report Card Generator")
    st.info("Upload CSV with columns: Subject, Score, Grade, Remarks")
    report_file = st.file_uploader("Upload Results CSV", type=["csv"], key="report_upload")
    student_name = st.text_input("Student Name", key="student_name")
    if st.button("Generate Report Card", key="report_btn") and report_file and student_name:
        df = pd.read_csv(report_file)
        st.dataframe(df)
        pdf = generate_report_card_pdf(student_name, grade, df)
        st.download_button("📥 Download Report Card PDF", pdf, f"ReportCard_{student_name}.pdf", key="dl_report")

    st.markdown("---")
    st.subheader("4. Scheme of Work Generator")
    if st.button("Generate Scheme of Work", key="scheme_btn"):
        client = get_client()
        if client:
            prompt = f"Create a 1-week scheme of work for {grade} {subject} Topic: {topic} following NCDC 2026. Include Competency, Activities, Assessment."
            with st.spinner("Generating..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=2000)
                if res: scheme = res.choices[0].message.content; st.markdown(scheme)
                st.download_button("📥 Download Scheme PDF", generate_pdf(scheme, f"Scheme {topic}"), "scheme.pdf", key="dl_scheme")

st.sidebar.caption("NCDC 2026 Competency-Based | P4-P7 | Generic Deep Reasoning | Contact: " + CONTACT)
