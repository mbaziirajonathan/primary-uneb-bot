import streamlit as st
import os, io, json, random
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
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

# ===================== 1. SYSTEM PROMPT - UNEB STEP BY STEP + DIAGRAM + BUDGET =====================
SYSTEM_PROMPT = """
You are TEACHERK, a Senior NCDC 2026 Uganda PLE Examiner and Master Teacher for PRIMARY P4-P7.

CRITICAL UNEB 2026 MARKING RULE: PUPILS LOSE MARKS IF THEY JUMP STEPS.
YOU MUST SHOW EVERY SINGLE CALCULATION STEP LIKE A PUPIL WRITING IN PLE EXAM.

DIAGRAM RULE: If the question involves Geometry, Angles, Area, Triangle, Circle, Sector, Parallel Lines, Graph, then output this exact tag at the end:
[DIAGRAM: Topic=Isosceles Triangle, Measurements="Base=8cm, Angle=50deg", Question="Label all sides"]

MANDATORY MATH WORKING FORMAT - USE FOR ALL 7 SCENARIOS:

### **SCENARIO 1: [Ugandan Title]**
Write a 3-4 sentence Ugandan scenario with real numbers.

**COMPETENCY TASK:** What the learner must be able to DO.

**QUESTION 1:** [2 marks]

**FULL WORKING METHOD 1: FORMULA/CONCEPT METHOD - SHOW ALL STEPS**
Step 1: Write down what is given
        Given:...
Step 2: Write the formula/concept to use
        Formula:...
Step 3: Substitute the values into the formula
        Therefore:...
Step 4: Do the calculation step by step. DO NOT JUMP.
        =...
        =...
Step 5: State the answer WITH CORRECT UNITS AND UNEB CLOSING
        Answer: 3kg or 3m or 3cm or 3L
        Therefore the budget needed was ugsh300,000

**FULL WORKING METHOD 2: LOGICAL/STORY METHOD - SHOW ALL STEPS**
Step 1: Explain the problem in words
Step 2: Break it down step by step
Step 3: Calculate each part
Step 4: Combine to get final answer WITH UNITS AND UNEB CLOSING
        Final Answer: 3kg
        Therefore the budget needed was ugsh300,000

---
REPEAT FOR SCENARIO 2, 3, 4, 5, 6, 7. ALL DIFFERENT UGANDA CONTEXTS.

### **PART 8: COMMON MISTAKES & UNEB EXAM TIPS**
1. Mistake 1: Forgetting to write units. PLE penalty: -1 mark
2. Mistake 2: Jumping steps. PLE penalty: -1 mark per missing step
3. Mistake 3: Wrong units e.g writing m instead of cm
4. TRICK: "Always end with 'Therefore the...' and box your final answer with units"

### **PART 9: QUICK PRACTICE FOR PUPILS**
Give 3 more questions. Tell them "Show all working and units. End with Therefore the..."

UNIT RULES - CRITICAL FOR PLE:
Money=ugsh, Mass=kg/g, Length=cm/m/km, Capacity=L/ml, Time=s/min/hr, Area=m2/cm2, Volume=m3/cm3, Speed=km/h
CLOSING RULE: End each scenario with "Therefore the [answer] was [number][unit]".
"""

# ===================== 2. DIAGRAM GENERATOR - PIXEL PERFECT =====================
 def draw_math_diagram(d_type, data, question_text):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal'); plt.axis('off')
    ax.set_title(f"{d_type}\n{question_text}", fontsize=12, pad=20)
    data = data.lower() # MAKE EVERYTHING LOWERCASE TO AVOID BUG

    # 1. TRIANGLE / CIRCLE / ANGLE
    if d_type.lower() == "triangle":
        base = 8.0
        if "base=" in data:
            try: base = float(data.split("base=")[1].split("cm")[0].strip())
            except: base = 8.0 # fallback if parsing fails
        angle_deg = 50.0
        if "angle=" in data:
            try: angle_deg = float(data.split("angle=")[1].split("deg")[0].strip())
            except: angle_deg = 50.0

        angle_rad = math.radians(angle_deg)
        apex_x = base / 2; apex_y = (base / 2) * math.tan(angle_rad) if angle_deg < 90 else base
        side_len = math.sqrt(apex_x**2 + apex_y**2)
        A, B, C = (0, 0), (base, 0), (apex_x, apex_y)
        triangle = patches.Polygon([A, B, C], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(triangle)
        ax.text(A[0]-0.5, A[1]-0.5, "A", fontsize=12); ax.text(B[0]+0.5, B[1]-0.5, "B", fontsize=12); ax.text(C[0], C[1]+0.5, "C", fontsize=12)
        ax.text(base/2, -0.5, f"{base}cm", ha='center'); ax.text(apex_x/2 - 0.3, apex_y/2, f"{side_len:.1f}cm", ha='right'); ax.text((apex_x+base)/2 + 0.3, apex_y/2, f"{side_len:.1f}cm", ha='left')
        arc = patches.Arc(A, 1.5, 1.5, theta1=0, theta2=angle_deg, color='red', linewidth=1.5); ax.add_patch(arc); ax.text(1, 0.3, f"{angle_deg}°", color='red')
        ax.set_xlim(-2, base+2); ax.set_ylim(-2, apex_y+2)

    elif d_type.lower() == "circle" or d_type.lower() == "sector":
        r = 7.0
        if "radius=" in data:
            try: r = float(data.split("radius=")[1].split("cm")[0].strip())
            except: r = 7.0
        angle_deg = 90.0
        if "angle=" in data:
            try: angle_deg = float(data.split("angle=")[1].split("deg")[0].strip())
            except: angle_deg = 90.0
        circle = patches.Circle((0,0), r, fill=False, edgecolor='black', linewidth=2); ax.add_patch(circle)
        sector = patches.Wedge((0,0), r, 0, angle_deg, fill=True, alpha=0.3, color='skyblue'); ax.add_patch(sector)
        theta2_rad = math.radians(angle_deg); x2 = r * math.cos(theta2_rad); y2 = r * math.sin(theta2_rad)
        ax.plot([0, r], [0, 0], 'k-'); ax.plot([0, x2], [0, y2], 'k-')
        ax.text(0, -r-0.5, f"Radius = {r}cm", ha='center'); mid_angle = math.radians(angle_deg/2); ax.text((r/2)*math.cos(mid_angle), (r/2)*math.sin(mid_angle), f"{angle_deg}°", ha='center')
        ax.set_xlim(-r-1, r+1); ax.set_ylim(-r-1, r+1)

    # 2. VENN DIAGRAM - 2 SETS
    elif d_type.lower() == "venn":
        a=20; b=15; ab=5
        if "a=" in data:
            try: a = int(data.split("a=")[1].split(",")[0])
            except: a=20
        if "b=" in data:
            try: b = int(data.split("b=")[1].split(",")[0])
            except: b=15
        if "ab=" in data:
            try: ab = int(data.split("ab=")[1].split(",")[0])
            except: ab=5
        circle1 = patches.Circle((0.3, 0.5), 0.3, fill=False, edgecolor='blue', linewidth=2)
        circle2 = patches.Circle((0.7, 0.5), 0.3, fill=False, edgecolor='green', linewidth=2)
        ax.add_patch(circle1); ax.add_patch(circle2)
        ax.text(0.3, 0.5, f"{a-ab}", ha='center', va='center', fontsize=14, color='blue')
        ax.text(0.7, 0.5, f"{b-ab}", ha='center', va='center', fontsize=14, color='green')
        ax.text(0.5, 0.5, f"{ab}", ha='center', va='center', fontsize=14)
        ax.text(0.1, 0.8, "A", fontsize=14, color='blue'); ax.text(0.9, 0.8, "B", fontsize=14, color='green')
        ax.set_xlim(0,1); ax.set_ylim(0,1)

    # 3. BAR GRAPH
    elif d_type.lower() == "bar":
        labels = []; values = []
        for item in data.split(","):
            if ":" in item:
                k,v = item.split(":"); labels.append(k.strip().title());
                try: values.append(int(v))
                except: values.append(0)
        ax.bar(labels, values, color='teal')
        ax.set_ylabel("Frequency"); ax.set_title(question_text)
        for i,v in enumerate(values): ax.text(i, v+0.5, str(v), ha='center')
        plt.xticks(rotation=15)

    plt.tight_layout()
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150); buf.seek(0); plt.close(fig)
    return buf

def parse_diagram_tag(text):
    if "[DIAGRAM:" not in text: return None
    try:
        tag = text.split("[DIAGRAM:")[1].split("]")[0]; parts = {}
        for item in tag.split(","): k,v = item.split("=",1); parts[k.strip()] = v.strip().strip('"')
        return parts
    except: return None

# ===================== 3. FULL NCDC 2026 DB - ALL 6 SUBJECTS P4-P7 - NO DATA LOST =====================
PRIMARY_DB = {
  "PRIMARY_4": {
    "Mathematics": [
        {"topic": "Set Concepts", "competency": "Identify, name and form sets", "scenario": "Grouping pupils in class"},
        {"topic": "Whole Numbers (Up to 99,999)", "competency": "Read, write, place value up to 99,999", "scenario": "Counting people at taxi park"},
        {"topic": "Operations on Whole Numbers", "competency": "Add, subtract, multiply, divide whole numbers", "scenario": "Buying books in market"},
        {"topic": "Fractions", "competency": "Identify, compare, add and subtract fractions", "scenario": "Sharing a mandazi"},
        {"topic": "Geometric Shapes and Symmetry", "competency": "Identify shapes and lines of symmetry", "scenario": "Shapes in classroom"},
        {"topic": "Measures (Time, Length, Mass, Capacity)", "competency": "Measure and convert units", "scenario": "Cooking at home"},
        {"topic": "Money and Financial Literacy", "competency": "Count money and make budgets", "scenario": "School pocket money"},
        {"topic": "Patterns and Sequences", "competency": "Identify and complete patterns", "scenario": "Beads on a string"},
        {"topic": "Basic Data Handling (Pictographs and Bar Graphs)", "competency": "Draw and interpret graphs", "scenario": "Favorite foods in class"}
        ],
    "English Language": [
        {"topic": "Sub-Counties/Divisions", "competency": "Describe sub-county features", "scenario": "My sub-county"},
        {"topic": "Holidays (Travel and Activities)", "competency": "Talk about holiday experiences", "scenario": "Visiting village"},
        {"topic": "Games and Sports", "competency": "Name and describe games", "scenario": "Football at school"},
        {"topic": "Our Environment (Weather and Elements)", "competency": "Describe weather elements", "scenario": "Rainy season"},
        {"topic": "Buying and Selling", "competency": "Use market vocabulary", "scenario": "At Owino market"},
        {"topic": "Cleanliness and Health", "competency": "Explain personal hygiene", "scenario": "Washing hands"},
        {"topic": "Expressing Feelings and Emotions", "competency": "Express feelings appropriately", "scenario": "When I am happy"},
        {"topic": "Telling Time and Calendar Skills", "competency": "Read time and calendar", "scenario": "School timetable"},
        {"topic": "Map Work and Directions", "competency": "Give and follow directions", "scenario": "From school to home"},
        {"topic": "Composition and Picture Composition Writing", "competency": "Write compositions", "scenario": "My best friend"}
        ],
    "Integrated Science": [
        {"topic": "Plant Life and Flowering Plants", "competency": "Identify parts of flowering plants", "scenario": "Mango tree in compound"},
        {"topic": "Crop Husbandry and Basic Farming Tools", "competency": "Name farming tools and uses", "scenario": "Digging in garden"},
        {"topic": "Weather and Its Elements", "competency": "Identify weather elements", "scenario": "Measuring rainfall"},
        {"topic": "Human Body (External Parts and Cleanliness)", "competency": "Name external body parts", "scenario": "Bathing"},
        {"topic": "Personal Hygiene and Sanitation", "competency": "Practice hygiene", "scenario": "Tippy tap at school"},
        {"topic": "Vectors and Pests (Houseflies, Mosquitoes)", "competency": "Identify vectors and control", "scenario": "Malaria prevention"},
        {"topic": "First Aid (Common Accidents)", "competency": "Give first aid", "scenario": "Cut finger"},
        {"topic": "Air and Its Properties", "competency": "State properties of air", "scenario": "Flying kite"},
        {"topic": "Water and Its Uses", "competency": "State uses of water", "scenario": "Washing clothes"},
        {"topic": "Introduction to Indigenous Crafts", "competency": "Make simple crafts", "scenario": "Weaving basket"}
        ],
    "Social Studies (SST)": [
        {"topic": "Location of Our Sub-County/Division", "competency": "Locate sub-county on map", "scenario": "Map of Nakawa"},
        {"topic": "Physical Features and Environment of Our Sub-County", "competency": "Describe physical features", "scenario": "Wetland in area"},
        {"topic": "Vegetation and Animals in Our Locality", "competency": "Name vegetation and animals", "scenario": "Trees in school"},
        {"topic": "People and Culture in Our Sub-County", "competency": "Describe culture", "scenario": "Traditional dance"},
        {"topic": "Economic Activities (Farming, Trade, Crafting)", "competency": "Name economic activities", "scenario": "Selling tomatoes"},
        {"topic": "Social Services and Infrastructure", "competency": "Identify social services", "scenario": "Health center"},
        {"topic": "Leadership and Governance in Our Locality", "competency": "Name local leaders", "scenario": "LC1 Chairman"}
        ],
    "Christian Religious Education (CRE)": [
        {"topic": "God's Creation and Our Talents", "competency": "Appreciate God's creation", "scenario": "Gifts from God"},
        {"topic": "Knowing Jesus Christ and His Early Life", "competency": "Narrate Jesus' early life", "scenario": "Jesus in the temple"},
        {"topic": "Christian Values (Honesty, Forgiveness, Love)", "competency": "Practice Christian values", "scenario": "Forgiving a friend"},
        {"topic": "The Bible as God's Holy Word", "competency": "Respect the Bible", "scenario": "Reading Bible"},
        {"topic": "Prayer and Fellowship", "competency": "Participate in prayer", "scenario": "Morning assembly"},
        {"topic": "Relationships in the Family and School", "competency": "Maintain good relationships", "scenario": "Helping parents"},
        {"topic": "Serving Others in the Community", "competency": "Serve others", "scenario": "Visiting sick"}
        ],
    "Islamic Religious Education (IRE)": [
        {"topic": "Selected Surahs from the Holy Qur'an (Memorization and Meanings)", "competency": "Memorize and recite Surahs", "scenario": "Surat Al-Fatiha"},
        {"topic": "Pillars of Islam (Focus on Shahadah and Salat)", "competency": "Explain Shahadah and Salat", "scenario": "Five daily prayers"},
        {"topic": "Pillars of Iman (Faith in Allah and His Angels)", "competency": "Explain faith in Allah and Angels", "scenario": "Believing in Allah"},
        {"topic": "The Life of Prophet Muhammad (PBUH) - Early Childhood", "competency": "Narrate early life of Prophet", "scenario": "Prophet as orphan"},
        {"topic": "Islamic Manners and Akhlaq (Cleanliness, Truthfulness)", "competency": "Practice Islamic manners", "scenario": "Speaking truth"},
        {"topic": "Introduction to Wudhu (Ablution) and Adhan", "competency": "Perform Wudhu and Adhan", "scenario": "Before prayer"}
        ]
  },
  "PRIMARY_5": {
    "Mathematics": [
        {"topic": "Set Theory (Union, Intersection, Venn Diagrams)", "competency": "Solve problems using Venn diagrams", "scenario": "Pupils who like math and english"},
        {"topic": "Whole Numbers (Up to 999,999 and Place Values)", "competency": "Read and write numbers up to 999,999", "scenario": "District population"},
        {"topic": "Operations on Whole Numbers", "competency": "Apply BODMAS", "scenario": "Shop calculations"},
        {"topic": "Number Patterns and Sequences (LCM, GCF, Prime Factorization)", "competency": "Find LCM and GCF", "scenario": "Two bells ringing"},
        {"topic": "Fractions (Addition, Subtraction, Multiplication, Division)", "competency": "Perform operations on fractions", "scenario": "Sharing cake"},
        {"topic": "Decimals", "competency": "Read, write and operate on decimals", "scenario": "Buying sugar"},
        {"topic": "Geometry (Lines, Angles, and Construction)", "competency": "Construct angles and lines", "scenario": "Using protractor"},
        {"topic": "Measures (Perimeter, Area, and Volume)", "competency": "Calculate perimeter, area, volume", "scenario": "School garden"},
        {"topic": "Graphs and Data Interpretation", "competency": "Draw and interpret graphs", "scenario": "Rainfall data"},
        {"topic": "Business Mathematics (Profit, Loss, and Simple Budgets)", "competency": "Calculate profit and loss", "scenario": "Selling mandazi"}
        ],
    "English Language": [
        {"topic": "Our District/Municipality", "competency": "Describe district features", "scenario": "Kampala City"},
        {"topic": "Animals and Breeding", "competency": "Talk about animal breeding", "scenario": "Rearing goats"},
        {"topic": "Wild Animals and Tourism", "competency": "Describe wild animals", "scenario": "Visiting Murchison"},
        {"topic": "Keeping a Diary and Calendar", "competency": "Write diary entries", "scenario": "My school week"},
        {"topic": "Post Office and Letters", "competency": "Write letters", "scenario": "Posting letter"},
        {"topic": "Communication (Telephones and Internet)", "competency": "Use communication tools", "scenario": "Calling parent"},
        {"topic": "Banking and Saving", "competency": "Explain banking", "scenario": "Opening account"},
        {"topic": "Virtual Shopping and Markets", "competency": "Describe shopping", "scenario": "Online market"},
        {"topic": "Health and Hygiene (Diseases and Medical Personnel)", "competency": "Talk about health", "scenario": "Visiting clinic"},
        {"topic": "Formal Invitation Letters", "competency": "Write formal invitations", "scenario": "Inviting guest"}
        ],
    "Integrated Science": [
        {"topic": "Soil Science (Composition, Erosion, and Conservation)", "competency": "Explain soil conservation", "scenario": "Planting grass"},
        {"topic": "Non-Flowering Plants and Fungi", "competency": "Classify non-flowering plants", "scenario": "Mushrooms"},
        {"topic": "Matter and Its States", "competency": "State properties of matter", "scenario": "Boiling water"},
        {"topic": "Poultry Keeping and Management", "competency": "Manage poultry", "scenario": "Chicken house"},
        {"topic": "Bee Keeping (Apiculture)", "competency": "Explain bee keeping", "scenario": "Harvesting honey"},
        {"topic": "Human Body Systems (Digestive and Respiratory Systems)", "competency": "Describe digestive system", "scenario": "Eating food"},
        {"topic": "Immunization and Child Health", "competency": "Explain immunization", "scenario": "Vaccination day"},
        {"topic": "Sanitation and Waste Management", "competency": "Manage waste", "scenario": "Rubbish pit"},
        {"topic": "Primary Health Care (PHC)", "competency": "Explain PHC elements", "scenario": "Health education"},
        {"topic": "First Aid for Fractures, Burns, and Poisoning", "competency": "Give first aid", "scenario": "Burnt hand"}
        ],
    "Social Studies (SST)": [
        {"topic": "Location and Geography of Uganda (Map Work, Boundaries, Districts)", "competency": "Locate Uganda on map", "scenario": "Map of Uganda"},
        {"topic": "Physical Features of Uganda and Their Importance", "competency": "Describe physical features", "scenario": "Lake Victoria"},
        {"topic": "Climate and Weather Patterns in Uganda", "competency": "Explain climate", "scenario": "Rainy season"},
        {"topic": "Vegetation Zones of Uganda", "competency": "Identify vegetation zones", "scenario": "Rain forest"},
        {"topic": "Natural Resources and Economic Activities (Tourism, Mining, Agriculture)", "competency": "State natural resources", "scenario": "Gold mining"},
        {"topic": "The People of Uganda (Ethnic Groups, Migration, Settlement)", "competency": "Name ethnic groups", "scenario": "Baganda, Banyankole"},
        {"topic": "Cultural Governance and Kingdom Structures", "competency": "Describe kingdoms", "scenario": "Buganda Kingdom"},
        {"topic": "Pre-Colonial and Colonial History of Uganda", "competency": "Explain colonialism", "scenario": "British rule"},
        {"topic": "Road to Independence and Post-Independence Leadership", "competency": "Explain independence", "scenario": "1962 independence"}
        ],
    "Christian Religious Education (CRE)": [
        {"topic": "God's Covenant with His People", "competency": "Explain God's covenant", "scenario": "Noah's ark"},
        {"topic": "The Birth and Ministry of Jesus Christ", "competency": "Narrate Jesus' ministry", "scenario": "Jesus healing"},
        {"topic": "The Miracles and Parables of Jesus", "competency": "Explain parables", "scenario": "Good Samaritan"},
        {"topic": "Christian Responses to Suffering and Difficulties", "competency": "Respond to suffering", "scenario": "Praying in trouble"},
        {"topic": "The Church as a Family of Believers", "competency": "Describe the Church", "scenario": "Sunday service"},
        {"topic": "Christian Holy Days and Ceremonies", "competency": "Observe holy days", "scenario": "Christmas"},
        {"topic": "Developing Positive Moral Values and Integrity", "competency": "Show integrity", "scenario": "Not cheating"}
        ],
    "Islamic Religious Education (IRE)": [
        {"topic": "Advanced Recitation and Meanings of Selected Surahs", "competency": "Recite with meaning", "scenario": "Surat Ikhlas"},
        {"topic": "Surat Al-Fatiha Deep Study", "competency": "Explain Surat Al-Fatiha", "scenario": "Meaning of Fatiha"},
        {"topic": "The Pillars of Islam (Focus on Zakat and Sawm/Fasting)", "competency": "Explain Zakat and Fasting", "scenario": "Ramadhan"},
        {"topic": "The Pillars of Iman (Faith in Holy Books and Prophets)", "competency": "Explain faith in books", "scenario": "The Qur'an"},
        {"topic": "The Life of Prophet Muhammad (PBUH) - The Call to Prophethood", "competency": "Narrate call to prophethood", "scenario": "Angel Jibril"},
        {"topic": "Islamic Etiquette in Daily Interpersonal Relationships", "competency": "Practice etiquette", "scenario": "Greeting elders"},
        {"topic": "Historical Mosques and Holy Sites", "competency": "Name holy sites", "scenario": "Mecca"}
        ]
  },
  "PRIMARY_6": {
    "Mathematics": [
        {"topic": "Advanced Set Operations", "competency": "Solve 3-set problems", "scenario": "Pupils in sports"},
        {"topic": "Whole Numbers (Integers, Bases, and Large Numbers)", "competency": "Work with integers and bases", "scenario": "Temperature"},
        {"topic": "Operations on Fractions and Decimals", "competency": "Operate on fractions and decimals", "scenario": "Market prices"},
        {"topic": "Ratios, Proportions, and Percentages", "competency": "Solve ratio problems", "scenario": "Mixing juice"},
        {"topic": "Sequences and Number Patterns", "competency": "Find nth term", "scenario": "Number pattern"},
        {"topic": "Geometry (Angles in Polygons, Circle Properties)", "competency": "Find angles in polygons", "scenario": "Pentagon"},
        {"topic": "Speed, Distance, and Time", "competency": "Calculate speed", "scenario": "Taxi journey"},
        {"topic": "Area, Volume, and Capacity", "competency": "Calculate area and volume", "scenario": "Water tank"},
        {"topic": "Business Math (Simple Interest, Bills)", "competency": "Calculate simple interest", "scenario": "Bank loan"},
        {"topic": "Introduction to Algebraic Expressions and Equations", "competency": "Solve simple equations", "scenario": "Find x"},
        {"topic": "Basic Probability", "competency": "Find probability", "scenario": "Tossing coin"}
        ],
    "English Language": [
        {"topic": "Safety on the Road and Traffic Rules", "competency": "Explain road safety", "scenario": "Crossing road"},
        {"topic": "Debating and Expressing Opinions", "competency": "Debate issues", "scenario": "School rules"},
        {"topic": "Printing and Book Publishing", "competency": "Describe printing", "scenario": "Newspaper"},
        {"topic": "In the Library", "competency": "Use library", "scenario": "Borrowing books"},
        {"topic": "Caring for the Environment (Pollution and Conservation)", "competency": "Conserve environment", "scenario": "Planting trees"},
        {"topic": "Elections and Democratic Leadership", "competency": "Explain elections", "scenario": "School prefect"},
        {"topic": "Legal Systems (Courts and Police)", "competency": "Describe legal system", "scenario": "Police station"},
        {"topic": "Hakuna Matata: Cultural Ceremonies and Festivals", "competency": "Describe culture", "scenario": "Imbalu"},
        {"topic": "Leisure and Entertainment", "competency": "Talk about leisure", "scenario": "Watching TV"},
        {"topic": "Advanced Composition Writing", "competency": "Write advanced compositions", "scenario": "My career"}
        ],
    "Integrated Science": [
        {"topic": "Plant Classification and Reproduction", "competency": "Classify plants", "scenario": "Flowering plants"},
        {"topic": "Invertebrates (Insects, Worms, Mollusks)", "competency": "Classify invertebrates", "scenario": "Earthworm"},
        {"topic": "Vertebrates (Fish, Amphibians, Reptiles, Birds, Mammals)", "competency": "Classify vertebrates", "scenario": "Chicken and cow"},
        {"topic": "Domestic Animals (Cattle, Goats, Pigs, Sheep Keeping)", "competency": "Keep domestic animals", "scenario": "Goat rearing"},
        {"topic": "Sound Energy", "competency": "Explain sound", "scenario": "Echo"},
        {"topic": "Classification of Matter (Elements, Compounds, Mixtures)", "competency": "Classify matter", "scenario": "Salt water"},
        {"topic": "Human Body Systems (Circulatory and Reproductive Systems)", "competency": "Describe circulatory system", "scenario": "Blood flow"},
        {"topic": "Contagious and Communicable Diseases (HIV/AIDS, Malaria)", "competency": "Prevent diseases", "scenario": "Mosquito net"},
        {"topic": "Indigenous Technology and Waste Innovations", "competency": "Use indigenous tech", "scenario": "Charcoal stove"},
        {"topic": "Introduction to Basic Digital Tech and Coding Logic", "competency": "Use basic digital tech", "scenario": "Computer"}
        ],
    "Social Studies (SST)": [
        {"topic": "East Africa (Location, Neighbors, and Map Reading)", "competency": "Locate EAC countries", "scenario": "Map of EAC"},
        {"topic": "Physical Features and Climate of East Africa", "competency": "Describe features", "scenario": "Mt. Kilimanjaro"},
        {"topic": "Vegetation and Wildlife Conservation in East Africa", "competency": "Conserve wildlife", "scenario": "National parks"},
        {"topic": "The People of East Africa (Origins and Economic Interdependence)", "competency": "Explain origins", "scenario": "Trade"},
        {"topic": "Major Historic Milestones and Colonialism in East Africa", "competency": "Explain colonialism", "scenario": "Scramble"},
        {"topic": "Main Inventions and Indigenous Political Systems", "competency": "Describe inventions", "scenario": "Iron tools"},
        {"topic": "Democratic Elections, Citizenship, and Human Rights", "competency": "Explain democracy", "scenario": "Voting"},
        {"topic": "Regional Economic Blocs (East African Community - EAC)", "competency": "Explain EAC", "scenario": "Common market"},
        {"topic": "Social Services, Security, and Public Infrastructure", "competency": "Identify services", "scenario": "Hospital"}
        ],
    "Christian Religious Education (CRE)": [
        {"topic": "God's Guidance and the Prophets", "competency": "Explain prophets", "scenario": "Moses"},
        {"topic": "The Death and Resurrection of Jesus", "competency": "Explain resurrection", "scenario": "Easter"},
        {"topic": "The Holy Spirit and His Gifts", "competency": "Explain Holy Spirit", "scenario": "Pentecost"},
        {"topic": "The Early Church and Christian Missionaries", "competency": "Describe early church", "scenario": "Missionaries"},
        {"topic": "Christian Witness and Community Service", "competency": "Witness Christ", "scenario": "Helping poor"},
        {"topic": "Respect for Authority, Justice, and Law", "competency": "Respect authority", "scenario": "Obeying teacher"},
        {"topic": "Preparing for the Future with Christian Values", "competency": "Plan future", "scenario": "Career"}
        ],
    "Islamic Religious Education (IRE)": [
        {"topic": "Advanced Recitation and Memorization of Surahs", "competency": "Memorize longer Surahs", "scenario": "Surat Yaseen"},
        {"topic": "The Pillars of Islam (Focus on Hajj)", "competency": "Explain Hajj", "scenario": "Pilgrimage"},
        {"topic": "The Pillars of Iman (Faith in Day of Judgment)", "competency": "Explain Day of Judgment", "scenario": "After life"},
        {"topic": "Stories of Prophets in the Qur'an", "competency": "Narrate prophet stories", "scenario": "Prophet Musa"},
        {"topic": "Islamic Social Values and Community Life", "competency": "Practice social values", "scenario": "Helping neighbor"},
        {"topic": "Islamic Festivals and Celebrations", "competency": "Celebrate festivals", "scenario": "Eid"}
        ]
  },
  "PRIMARY_7": {
    "Mathematics": [
        {"topic": "Advanced Sets (Three Categories/Word Problems)", "competency": "Solve 3-set word problems", "scenario": "Pupils in 3 subjects"},
        {"topic": "Whole Numbers and Bases (Base Two and Base Five)", "competency": "Convert bases", "scenario": "Computer binary"},
        {"topic": "Number Theory and Properties", "competency": "Apply number properties", "scenario": "Prime numbers"},
        {"topic": "Fractions, Decimals, and Percentages", "competency": "Convert and solve problems", "scenario": "Discount"},
        {"topic": "Ratios and Proportion", "competency": "Solve proportion problems", "scenario": "Sharing money"},
        {"topic": "Integers", "competency": "Operate on integers", "scenario": "Debt"},
        {"topic": "Business Mathematics (Advanced Budgets, Profit/Loss, Taxes, Insurance, Compound Interest)", "competency": "Calculate compound interest", "scenario": "Bank savings"},
        {"topic": "Graphs and Advanced Data Handling", "competency": "Draw pie charts", "scenario": "Election results"},
        {"topic": "Geometry (Complex Constructions and Coordinate Geometry)", "competency": "Construct geometric figures", "scenario": "Using compass"},
        {"topic": "Speed, Velocity, and Acceleration", "competency": "Calculate velocity", "scenario": "Boda boda"},
        {"topic": "Area, Surface Area, and Volume", "competency": "Calculate surface area", "scenario": "Box"},
        {"topic": "Advanced Equations and Inequalities", "competency": "Solve inequalities", "scenario": "Word problem"}
        ],
    "English Language": [
        {"topic": "National Environmental Conservation", "competency": "Discuss conservation", "scenario": "Wetlands"},
        {"topic": "Regional Inventions and Indigenous Technology", "competency": "Describe inventions", "scenario": "Backcloth"},
        {"topic": "Media, Radio, and Television", "competency": "Use media", "scenario": "Radio Uganda"},
        {"topic": "Modern Communication (Emails and Social Media)", "competency": "Use modern communication", "scenario": "Sending email"},
        {"topic": "National and International Holidays", "competency": "Describe holidays", "scenario": "Independence Day"},
        {"topic": "Occupations, Career Guidance, and Jobs", "competency": "Choose career", "scenario": "Becoming doctor"},
        {"topic": "Regional Cross-Border Trade", "competency": "Explain cross-border trade", "scenario": "Kenya border"},
        {"topic": "Examination Preparation and Instructions", "competency": "Prepare for exams", "scenario": "PLE tips"},
        {"topic": "Letter Writing (Formal, Informal, and Applications)", "competency": "Write application letters", "scenario": "Job application"},
        {"topic": "Comprehension and Advanced Comprehension Strategies", "competency": "Answer comprehension", "scenario": "Reading passage"}
        ],
    "Integrated Science": [
        {"topic": "Plant Life and Advanced Crop Husbandry", "competency": "Practice crop husbandry", "scenario": "Maize garden"},
        {"topic": "Animal Management and Animal Breeding", "competency": "Manage animals", "scenario": "Cattle breeding"},
        {"topic": "Energy (Light, Heat, Electricity, Magnetism)", "competency": "Explain energy forms", "scenario": "Solar panel"},
        {"topic": "Simple Machines and Mechanics", "competency": "Use simple machines", "scenario": "Wheelbarrow"},
        {"topic": "Human Body Systems (Excretory, Nervous, and Endocrine Systems)", "competency": "Describe excretory system", "scenario": "Kidneys"},
        {"topic": "Human Health, Sanitation, and Public Health", "competency": "Promote public health", "scenario": "COVID-19"},
        {"topic": "Environmental Management and Eco-Systems", "competency": "Manage environment", "scenario": "Ecosystem"},
        {"topic": "Interdependence of Living Things", "competency": "Explain interdependence", "scenario": "Food chain"},
        {"topic": "Scientific Innovation and Technological Applications", "competency": "Apply science innovation", "scenario": "Mobile phone"}
        ],
    "Social Studies (SST)": [
        {"topic": "Africa (Location, Size, Boundaries, and Physical Map Work)", "competency": "Locate Africa", "scenario": "Map of Africa"},
        {"topic": "Major Drainage Systems, Climate, and Vegetation Zones of Africa", "competency": "Describe drainage", "scenario": "River Nile"},
        {"topic": "Economic Resources and Trade Dynamics across Africa", "competency": "Explain trade", "scenario": "AfCFTA"},
        {"topic": "The People of Africa (Races, Ethnic Migration, and Culture)", "competency": "Describe people of Africa", "scenario": "Bantu migration"},
        {"topic": "Foreign Influence, Slave Trade, and Colonial Rule in Africa", "competency": "Explain slave trade", "scenario": "European explorers"},
        {"topic": "The Struggle for Independence and Pan-Africanism", "competency": "Explain independence", "scenario": "Nkrumah"},
        {"topic": "Major Regional and Global Bodies (African Union - AU, United Nations - UN)", "competency": "Explain AU and UN", "scenario": "AU headquarters"},
        {"topic": "Post-Independence Achievements, Challenges, and Leadership in Africa", "competency": "Discuss challenges", "scenario": "Corruption"}
        ],
    "Christian Religious Education (CRE)": [
        {"topic": "God's Ultimate Plan for Salvation", "competency": "Explain salvation", "scenario": "Jesus died for us"},
        {"topic": "The Teachings of Jesus Christ on the Kingdom of God", "competency": "Explain Kingdom of God", "scenario": "Parables"},
        {"topic": "Christian Service, Leadership, and Stewardship", "competency": "Show leadership", "scenario": "Church leader"},
        {"topic": "Contemporary Moral Challenges (Corruption, Peer Pressure, Substance Abuse)", "competency": "Respond to challenges", "scenario": "Say no to drugs"},
        {"topic": "Marriage, Family Life, and Responsible Behavior", "competency": "Practice responsible behavior", "scenario": "Good marriage"},
        {"topic": "Death, Resurrection, and the Christian Hope", "competency": "Explain Christian hope", "scenario": "Life after death"},
        {"topic": "Living Peacefully in a Multi-Faith Society", "competency": "Live peacefully", "scenario": "Muslim neighbor"}
        ],
    "Islamic Religious Education (IRE)": [
        {"topic": "Advanced Qur'anic Studies and Tafsir", "competency": "Explain Tafsir", "scenario": "Meaning of verses"},
        {"topic": "The Pillars of Iman (Faith in Divine Decree)", "competency": "Explain Divine Decree", "scenario": "Qadar"},
        {"topic": "Islamic Law (Shariah) and Social Justice", "competency": "Explain Shariah", "scenario": "Justice"},
        {"topic": "The Life of the Prophet's Companions (Sahaba)", "competency": "Narrate Sahaba stories", "scenario": "Abu Bakr"},
        {"topic": "Islamic Economic System (Zakat, Sadaqa, Waqf)", "competency": "Practice Islamic economics", "scenario": "Giving Zakat"},
        {"topic": "Contemporary Issues in Islam", "competency": "Address contemporary issues", "scenario": "Drug abuse"}
        ]
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
    for line in content.split('\n')[:80]:
        c.drawString(40, y, line[:95])
        y -= 14
        if y < 50: c.showPage(); y = height - 50
    c.save(); buffer.seek(0)
    return buffer

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en'); fp = io.BytesIO(); tts.write_to_fp(fp); fp.seek(0); return fp
    except: return None

def speech_to_text_from_audio(audio_bytes):
    r = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source: audio = r.record(source)
    try: return r.recognize_google(audio)
    except: return ""

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
st.title("🐢 TEACHERK PRIMARY 2026 NCDC")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"], key="grade_select")
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()), key="subject_select")
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject], key="topic_select")

topic_data = get_topic_data(grade, subject, topic)
if topic_data is None: st.error("Topic not found in NCDC P4-P7. Please select another."); st.stop()

st.subheader(f"{grade} {subject}: {topic_data['topic']}")
st.info(f"**NCDC Competency**: {topic_data['competency']}")
st.success(f"**Example Scenario**: {topic_data['scenario']}")

tabs = st.tabs(["AI Chat + Voice", "Theory + Practicals", "Quiz + Evaluation", "Math Work", "Teacher Tools"])

with tabs[0]:
    st.header("Ask TeacherK NCDC - 7 Scenarios")
    q = st.text_input("Type question here e.g: Teach me Isosceles Triangle", key="chat_q")
    if st.button("Ask", key="ask_btn") and q:
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\n\nLevel: {grade}, Subject: {subject}, Topic: {topic_data['topic']}\n\nStudent Request: {q}\n\nCRITICAL: SHOW EVERY SINGLE STEP. EMPHASIZE UNITS. IF GEOMETRY, ADD [DIAGRAM: Topic=..., Measurements=..., Question=...] TAG"
            with st.spinner("TeacherK is thinking step by step..."):
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], temperature=0.2, max_tokens=4000)
                answer = res.choices[0].message.content
            st.markdown(answer)

            diagram_info = parse_diagram_tag(answer)
            if diagram_info:
                st.subheader("📐 Diagram")
                img_buf = draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question",""))
                st.image(img_buf, use_container_width=True)

            audio = text_to_speech(answer)
            if audio: st.audio(audio)
            st.download_button("📥 Download Lesson PDF", generate_pdf(answer, f"{grade} {subject} {topic_data['topic']}"), "lesson.pdf", key="dl_lesson")

with tabs[1]:
    st.header("Theory + Practical Activities")
    if st.button("Generate Theory + 7 Practicals", key="theory_btn"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nTeach {grade} {subject} Topic: {topic_data['topic']}. Give Theory + 7 Uganda practical activities. Show steps."
            with st.spinner("Generating..."):
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], temperature=0.3, max_tokens=4000)
                theory = res.choices[0].message.content
            st.markdown(theory)
            st.download_button("📥 Download Theory PDF", generate_pdf(theory, f"Theory {topic_data['topic']}"), "theory.pdf", key="dl_theory")

with tabs[2]:
    st.header("Quiz + Evaluation")
    if st.button("Generate 7 Scenario Quiz", key="quiz_btn"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nCreate 7 scenario-based quiz questions for {grade} {subject} Topic: {topic_data['topic']}. Provide answers with full steps and units."
            with st.spinner("Generating Quiz..."):
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], temperature=0.3, max_tokens=4000)
                quiz = res.choices[0].message.content
            st.markdown(quiz)
            st.download_button("📥 Download Quiz PDF", generate_pdf(quiz, f"Quiz {topic_data['topic']}"), "quiz.pdf", key="dl_quiz")

with tabs[3]:
    st.header("Mathematics Work Page - 7 Scenario Workouts")
    if subject == "Mathematics":
        if st.button("Generate 7 Scenario Worked Examples", key="mathwork_btn", type="primary"):
            client = get_client()
            if client:
                prompt = f"{SYSTEM_PROMPT}\nGenerate 7 fully worked scenario-based math questions for {grade} {subject} Topic: {topic_data['topic']}. EACH QUESTION MUST SHOW EVERY STEP. NO JUMPING. FINAL ANSWER MUST HAVE UNITS. IF GEOMETRY, ADD [DIAGRAM:...] TAG"
                with st.spinner("Generating Math Work..."):
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], temperature=0.2, max_tokens=4000)
                    math_work = res.choices[0].message.content
                st.markdown(math_work)

                diagram_info = parse_diagram_tag(math_work)
                if diagram_info:
                    st.subheader("📐 Diagram")
                    img_buf = draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question",""))
                    st.image(img_buf, use_container_width=True)

                st.download_button("📥 Download Math Work PDF", generate_pdf(math_work, f"Math Work {topic_data['topic']}"), "math_work.pdf", key="dl_math")
    else:
        st.info("This tab is for Mathematics only. Select Mathematics subject to use.")

with tabs[4]:
    st.header("Teacher Tools")
    st.write("Tools for Teachers to prepare lessons.")
    if st.button("Generate Scheme of Work Snippet", key="scheme_btn"):
        client = get_client()
        if client:
            prompt = f"Create a 1-week scheme of work for {grade} {subject} Topic: {topic_data['topic']} following NCDC 2026. Include Competency, Activities, Assessment."
            with st.spinner("Generating..."):
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}], temperature=0.2, max_tokens=2000)
                scheme = res.choices[0].message.content
            st.markdown(scheme)
            st.download_button("📥 Download Scheme PDF", generate_pdf(scheme, f"Scheme {topic_data['topic']}"), "scheme.pdf", key="dl_scheme")

st.sidebar.caption("NCDC 2026 Competency-Based | P4-P7 | Pixel-Perfect Diagrams | 7 Scenarios Per Mode | Contact: " + CONTACT)

      
