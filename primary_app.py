import streamlit as st
import os, io, json, random, re 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from datetime import datetime
from groq import Groq, RateLimitError # <- Added RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import streamlit.components.v1 as components

# ===================== CONFIG =====================
CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7. Confirm with Class Teacher.")

SYSTEM_PROMPT = """
You are TEACHERK, a Senior NCDC 2026 Uganda PLE Examiner and Master Teacher for PRIMARY P4-P7.
You teach like a real classroom teacher in Uganda using Competency-Based Curriculum CBC.

CRITICAL UNEB 2026 MARKING RULE: PUPILS LOSE MARKS IF THEY JUMP STEPS.
YOU MUST SHOW EVERY SINGLE CALCULATION STEP LIKE A PUPIL WRITING IN PLE EXAM.

TONE: Friendly, patient, Ugandan. Use local examples: boda boda, market, shamba, school, posho, beans.

MANDATORY MATH WORKING FORMAT - USE FOR ALL 7 SCENARIOS:

### **SCENARIO 1: [Ugandan Title]**
Write a 3-4 sentence Ugandan scenario with real numbers.

**COMPETENCY TASK:** What the learner must be able to DO by the end.

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

NEW: CONSTRUCTION & ACCURATE DIAGRAM RULES FOR UNEB NCDC 2026 - MANDATORY
When the question involves Geometry, Angles, Area, Triangle, Circle, Sector, Square, Rectangle, Rhombus, Kite, Trapezium, Polygon, Hexagon, Cube, Cone, Cylinder, Construction, you MUST do 3 things:

A. LIST UNEB CONSTRUCTION SET REQUIREMENTS FIRST:
1. A well calibrated 30cm ruler
2. A pair of compasses
3. A pair of dividers
4. A protractor 0-180 degrees
5. A sharp HB pencil and eraser
6. Plain paper

B. STEP BY STEP CONSTRUCTION GUIDE:
Teach exactly like in class:
Step 1: Sketch: Draw a rough freehand sketch and label all parts.
Step 2: Construction: Using ruler, draw base line AB =...cm
Step 3: Using compass, place at A, radius =...cm, draw arc.
Step 4: Using protractor, measure... degrees from AB. For angles: 45deg, 60deg, 90deg, 80deg, 120deg
Step 5: Join points. Label all sides, angles with arcs and measurements.

C. DIAGRAM TAG: Output this exact tag at the end of the response:
[DIAGRAM: Topic=Triangle, Measurements="Base=8cm, Angle=50deg", Question="Construct isosceles triangle"]
[DIAGRAM: Topic=Square, Measurements="Width=5cm", Question="Construct square"]
[DIAGRAM: Topic=Rectangle, Measurements="Length=8cm, Height=4cm", Question="Draw rectangle"]
[DIAGRAM: Topic=Rhombus, Measurements="Width=6cm, Height=5cm", Question="Construct rhombus"]
[DIAGRAM: Topic=Kite, Measurements="Width=8cm, Height=6cm", Question="Draw kite"]
[DIAGRAM: Topic=Trapezium, Measurements="Base1=10cm, Base2=6cm, Height=4cm", Question="Draw trapezium"]
[DIAGRAM: Topic=Polygon, Measurements="Sides=6, Radius=4cm", Question="Construct regular hexagon"]
[DIAGRAM: Topic=Circle, Measurements="Radius=3cm", Question="Draw circle"]
[DIAGRAM: Topic=Cone, Measurements="Radius=2cm, Height=5cm", Question="Draw net of cone"]
[DIAGRAM: Topic=Cylinder, Measurements="Radius=2cm, Height=6cm", Question="Draw net of cylinder"]
[DIAGRAM: Topic=Cube, Measurements="Side=3cm", Question="Draw net of cube"]
[DIAGRAM: Topic=Angle, Measurements="Angle=60deg", Question="Construct 60 degree angle"]
[DIAGRAM: Topic=Venn, Measurements="A=20, B=15, AB=5", Question="Venn diagram"]
[DIAGRAM: Topic=Bar, Measurements="Apples:10, Oranges:15", Question="Bar graph"]

Your job is to teach, not just answer. Always follow NCDC 2026 Competency-Based approach.
"""

# ===================== 2. DIAGRAM GENERATOR - ALL SHAPES + ANGLES P4-P7 =====================
def draw_math_diagram(d_type, measurements, question_text):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    plt.axis('off')
    ax.set_title(f"{d_type}\n{question_text}", fontsize=12, pad=20)
    data = measurements.lower() if measurements else ""

    def safe_float(s, default):
        try: return float(re.findall(r"[\d.]+", s)[0])
        except: return default
    def safe_int(s, default):
        try: return int(re.findall(r"\d+", s)[0])
        except: return default

    # ===== 1. TRIANGLE =====
    if d_type and "triangle" in d_type.lower():
        base = 8.0
        if "base=" in data: base = safe_float(data, 8.0)
        angle_deg = 50.0
        if "angle=" in data: angle_deg = safe_float(data, 50.0)
        angle_rad = math.radians(angle_deg); apex_x = base / 2; apex_y = (base / 2) * math.tan(angle_rad) if angle_deg < 90 else base
        side_len = math.sqrt(apex_x**2 + apex_y**2); A, B, C = (0, 0), (base, 0), (apex_x, apex_y)
        triangle = patches.Polygon([A, B, C], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(triangle)
        ax.text(A[0]-0.5, A[1]-0.5, "A"); ax.text(B[0]+0.5, B[1]-0.5, "B"); ax.text(C[0], C[1]+0.5, "C")
        ax.text(base/2, -0.5, f"{base}cm", ha='center'); ax.text(apex_x/2 - 0.3, apex_y/2, f"{side_len:.1f}cm", ha='right'); ax.text((apex_x+base)/2 + 0.3, apex_y/2, f"{side_len:.1f}cm", ha='left')
        arc = patches.Arc(A, 1.5, 1.5, theta1=0, theta2=angle_deg, color='red', linewidth=1.5); ax.add_patch(arc); ax.text(1, 0.3, f"{angle_deg}°", color='red')
        ax.set_xlim(-2, base+2); ax.set_ylim(-2, apex_y+2)

    # ===== 2. SQUARE / RECTANGLE / RHOMBUS / KITE =====
    elif d_type and any(x in d_type.lower() for x in ["square", "rectangle", "rhombus", "kite"]):
        w = 6.0; h = 4.0
        if "width=" in data: w = safe_float(data, 6.0)
        if "length=" in data: w = safe_float(data, 6.0)
        if "height=" in data: h = safe_float(data, 4.0)
        if "square" in d_type.lower(): h = w
        if "rhombus" in d_type.lower(): offset = w * 0.3; A, B, C, D = (offset, 0), (w+offset, 0), (w, h), (0, h)
        elif "kite" in d_type.lower(): A, B, C, D = (w/2, 0), (w, h/2), (w/2, h), (0, h/2) # Diamond kite
        else: A, B, C, D = (0, 0), (w, 0), (w, h), (0, h)
        if "square" in d_type.lower() or "rectangle" in d_type.lower(): A, B, C, D = (0, 0), (w, 0), (w, h), (0, h)
        poly = patches.Polygon([A, B, C, D], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(poly)
        ax.text(A[0]-0.5, A[1]-0.5, "A"); ax.text(B[0]+0.2, B[1]-0.5, "B"); ax.text(C[0]+0.2, C[1]+0.2, "C"); ax.text(D[0]-0.5, D[1]+0.2, "D")
        ax.text(w/2, -0.5, f"{w}cm", ha='center'); ax.text(-0.8, h/2, f"{h}cm", va='center', rotation=90)
        ax.set_xlim(-2, w+2); ax.set_ylim(-2, h+2)

    # ===== 3. TRAPEZIUM =====
    elif d_type and "trapezium" in d_type.lower():
        b1 = 8.0; b2 = 4.0; h = 3.0
        if "base1=" in data: b1 = safe_float(data, 8.0)
        if "base2=" in data: b2 = safe_float(data, 4.0)
        if "height=" in data: h = safe_float(data, 3.0)
        offset = (b1 - b2) / 2; A, B, C, D = (0, 0), (b1, 0), (b1-offset, h), (offset, h)
        poly = patches.Polygon([A, B, C, D], closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(poly)
        ax.text(A[0]-0.5, A[1]-0.5, "A"); ax.text(B[0]+0.2, B[1]-0.5, "B"); ax.text(C[0]+0.2, C[1]+0.2, "C"); ax.text(D[0]-0.5, D[1]+0.2, "D")
        ax.text(b1/2, -0.5, f"{b1}cm", ha='center'); ax.text(b1/2, h+0.2, f"{b2}cm", ha='center'); ax.text(-0.8, h/2, f"{h}cm", va='center', rotation=90)
        ax.set_xlim(-2, b1+2); ax.set_ylim(-2, h+2)

    # ===== 4. REGULAR POLYGON: HEXAGON etc =====
    elif d_type and "polygon" in d_type.lower():
        sides = 6; r = 3.0
        if "sides=" in data: sides = safe_int(data, 6)
        if "radius=" in data: r = safe_float(data, 3.0)
        angles = np.linspace(0, 2*np.pi, sides, endpoint=False); points = [(r*np.cos(a), r*np.sin(a)) for a in angles]
        poly = patches.Polygon(points, closed=True, fill=False, edgecolor='black', linewidth=2); ax.add_patch(poly)
        for i, p in enumerate(points): ax.text(p[0]*1.1, p[1]*1.1, chr(65+i))
        ax.set_xlim(-r-1, r+1); ax.set_ylim(-r-1, r+1)

    # ===== 5. CIRCLE / SECTOR =====
    elif d_type and ("circle" in d_type.lower() or "sector" in d_type.lower()):
        r = 3.0
        if "radius=" in data: r = safe_float(data, 3.0)
        theta1, theta2 = 0, 90
        if "angle=" in data: theta2 = safe_float(data, 90.0)
        cx, cy = 0, 0; p1 = [cx + r * math.cos(math.radians(theta1)), cy + r * math.sin(math.radians(theta1))]
        p2 = [cx + r * math.cos(math.radians(theta2)), cy + r * math.sin(math.radians(theta2))]
        circle = patches.Circle((cx, cy), r, fill=False, edgecolor='black', lw=2); ax.add_patch(circle)
        if theta2!= 360: ax.plot([cx, p1[0]], [cy, p1[1]], 'k-', lw=2); ax.plot([cx, p2[0]], [cy, p2[1]], 'k-', lw=2)
        ax.text(cx - 0.4, cy - 0.4, 'O'); ax.text(p1[0] + 0.3, p1[1] - 0.1, 'A'); ax.text(p2[0] - 0.1, p2[1] + 0.3, 'B')
        ax.text(r/2, -0.5, f'{r} cm', ha='center'); ax.set_xlim(-r-1, r+1); ax.set_ylim(-r-1, r+1)

    # ===== 6. ANGLES: 90,60,45,120,80 + COMPLEMENTARY / SUPPLEMENTARY =====
    elif d_type and "angle" in d_type.lower():
        angle = 60
        if "angle=" in data: angle = safe_float(data, 60)
        ax.plot([0, 4], [0, 0], 'k-', lw=2) # Base line
        end_x = 3 * math.cos(math.radians(angle)); end_y = 3 * math.sin(math.radians(angle))
        ax.plot([0, end_x], [0, end_y], 'k-', lw=2) # Angle line
        arc = patches.Arc((0,0), 1.5, 1.5, theta1=0, theta2=angle, color='red', lw=2); ax.add_patch(arc)
        ax.text(0.8, 0.2, f"{angle}°", color='red', fontsize=12); ax.text(0, -0.5, "Vertex A"); ax.text(end_x, end_y, "B")
        ax.set_xlim(-1, 4); ax.set_ylim(-1, 4)

    # ===== 7. CUBE NET / 3D SHAPES: CONE, CYLINDER =====
    elif d_type and any(x in d_type.lower() for x in ["cube", "cone", "cylinder"]):
        s = 2.0
        if "side=" in data: s = safe_float(data, 2.0)
        if "radius=" in data: s = safe_float(data, 2.0)
        h = s * 2
        if "height=" in data: h = safe_float(data, h)
        if "cube" in d_type.lower():
            for i in range(3):
                for j in range(4):
                    if (i==1 and j<4) or (i<3 and j==1):
                        rect = patches.Rectangle((j*s, i*s), s, s, fill=False, edgecolor='black', lw=2); ax.add_patch(rect)
            ax.text(s*1.5, -0.5, f"Side={s}cm", ha='center'); ax.set_xlim(-1, 4*s+1); ax.set_ylim(-1, 3*s+1)
        elif "cone" in d_type.lower(): # 2D net: sector + circle
            circle = patches.Circle((s*2, s), s/2, fill=False, edgecolor='black', lw=2); ax.add_patch(circle)
            ax.text(s*2, s, f"r={s/2}cm", ha='center')
            ax.text(s*0.5, h+0.5, f"Slant Height", ha='center'); ax.text(s*0.5, -0.5, f"Base r={s/2}cm", ha='center')
            ax.set_xlim(-1, 3*s+1); ax.set_ylim(-1, h+2)
        elif "cylinder" in d_type.lower(): # 2D net: 2 circles + rectangle
            rect = patches.Rectangle((s, s), h, s, fill=False, edgecolor='black', lw=2); ax.add_patch(rect)
            circle1 = patches.Circle((s/2, s*1.5), s/2, fill=False, edgecolor='black', lw=2); ax.add_patch(circle1)
            circle2 = patches.Circle((s+h+s/2, s*1.5), s/2, fill=False, edgecolor='black', lw=2); ax.add_patch(circle2)
            ax.text(s/2, s*1.5, f"r", ha='center'); ax.text(s+h/2, s*1.5, f"h={h}cm", ha='center')
            ax.set_xlim(-1, h+2*s+1); ax.set_ylim(-1, 3*s+1)

    # ===== 8. VENN =====
    elif d_type and "venn" in d_type.lower():
        a=20; b=15; ab=5
        if "a=" in data: a = safe_int(data, 20)
        if "b=" in data: b = safe_int(data, 15)
        if "ab=" in data: ab = safe_int(data, 5)
        circle1 = patches.Circle((0.3, 0.5), 0.3, fill=False, edgecolor='blue', linewidth=2)
        circle2 = patches.Circle((0.7, 0.5), 0.3, fill=False, edgecolor='green', linewidth=2)
        ax.add_patch(circle1); ax.add_patch(circle2)
        ax.text(0.3, 0.5, f"{a-ab}", ha='center', va='center'); ax.text(0.7, 0.5, f"{b-ab}", ha='center', va='center'); ax.text(0.5, 0.5, f"{ab}", ha='center', va='center')
        ax.text(0.1, 0.8, "A"); ax.text(0.9, 0.8, "B"); ax.set_xlim(0,1); ax.set_ylim(0,1)

    # ===== 9. BAR GRAPH =====
    elif d_type and "bar" in d_type.lower():
        labels = []; values = []
        for item in data.split(","):
            if ":" in item:
                k,v = item.split(":"); labels.append(k.strip().title()); values.append(safe_int(v, 0))
        if labels:
            ax.bar(labels, values, color='teal'); ax.set_ylabel("Frequency"); ax.set_title(question_text)
            for i,v in enumerate(values): ax.text(i, v+0.5, str(v), ha='center'); plt.xticks(rotation=15)
        else: ax.text(0.5, 0.5, "No data provided", ha='center', va='center')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

def parse_diagram_tag(text):
    if "[DIAGRAM:" not in text: return None
    try:
        tag = text.split("[DIAGRAM:")[1].split("]")[0]; parts = {}
        for item in tag.split(","):
            if "=" in item:
                k,v = item.split("=",1); parts[k.strip()] = v.strip().strip('"')
        return parts if parts.get("Topic") else None
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

def smart_groq_call(client, system_prompt, user_prompt, max_tokens=2000):
    """Auto fallback if 70b hits rate limit"""
    models_to_try = [MODEL_CHOICE, "llama-3.1-8b-instant", "llama-3.1-70b-versatile"]
    models_to_try = list(dict.fromkeys(models_to_try))

    for model in models_to_try:
        try:
            tokens = max_tokens if "70b" in model else 1024
            res = client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
                temperature=0.2,
                max_tokens=tokens
            )
            if model!= MODEL_CHOICE:
                st.warning(f"⚠️ Switched to {model} because {MODEL_CHOICE} was busy.")
            return res
        except RateLimitError:
            continue
        except Exception:
            continue
    st.error("All Groq models busy. Wait 1 minute.")
    return None

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

st.sidebar.header("⚙️ Settings")
MODEL_CHOICE = st.sidebar.selectbox(
    "AI Brain",
    ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama-3.1-70b-versatile"],
    index=0,
    help="70b = Smartest but slower. 8b = Fastest, no limits. Auto-switches if 70b is full"
)
st.sidebar.caption(f"Current: {MODEL_CHOICE}")

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
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                if res is None: st.stop()
                answer = res.choices[0].message.content
            st.markdown(answer)

            diagram_info = parse_diagram_tag(answer)
            if diagram_info:
                st.subheader("📐 Diagram")
                img_buf = draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question",""))
                if img_buf: st.image(img_buf, use_container_width=True)

            # Browser Text-to-Speech
            st.subheader("🔊 Listen to Lesson")
            tts_html = f"""
            <script>
            function speak(text) {{
                var msg = new SpeechSynthesisUtterance();
                msg.text = text;
                msg.lang = 'en-UG';
                msg.rate = 0.9;
                window.speechSynthesis.speak(msg);
            }}
            </script>
            <button onclick="speak(`{answer.replace('`','')}`)" style="padding:10px 20px; font-size:16px; background:#4CAF50; color:white; border:none; border-radius:5px; cursor:pointer;">
                ▶️ Play Voice
            </button>
            """
            components.html(tts_html, height=60)

            # Browser Speech-to-Text Mic
            st.subheader("🎤 Talk to TeacherK")
            stt_html = """
            <script>
            function startDictation() {
                if (window.hasOwnProperty('webkitSpeechRecognition')) {
                    var recognition = new webkitSpeechRecognition();
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    recognition.lang = "en-UG";
                    recognition.start();
                    recognition.onresult = function(e) {
                        document.getElementById('transcript').value = e.results[0][0].transcript;
                        recognition.stop();
                    };
                    recognition.onerror = function(e) { recognition.stop(); }
                }
            }
            </script>
            <input type="text" id="transcript" placeholder="Click mic and speak..." style="width:70%; padding:8px;">
            <button onclick="startDictation()" style="padding:8px 15px;">🎤</button>
            """
            components.html(stt_html, height=60)

            # DOWNLOAD BUTTON GOES HERE - INSIDE THE IF BLOCK
            st.download_button("📥 Download Lesson PDF", generate_pdf(answer, f"{grade} {subject} {topic_data['topic']}"), "lesson.pdf", key="dl_lesson")

with tabs[1]:
    st.header("Theory + Practical Activities")
    if st.button("Generate Theory + 7 Practicals", key="theory_btn"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nTeach {grade} {subject} Topic: {topic_data['topic']}. Give Theory + 7 Uganda practical activities. Show steps."
            with st.spinner("Generating..."):
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                if res is None: st.stop()
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
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=2000)
                if res is None: st.stop()
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
                    res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=4000)
                    if res is None: st.stop()
                    math_work = res.choices[0].message.content
                st.markdown(math_work)

                diagram_info = parse_diagram_tag(math_work)
                if diagram_info:
                    st.subheader("📐 Diagram")
                    img_buf = draw_math_diagram(diagram_info.get("Topic",""), diagram_info.get("Measurements",""), diagram_info.get("Question",""))
                    if img_buf: st.image(img_buf, use_container_width=True)

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
                res = smart_groq_call(client, SYSTEM_PROMPT, prompt, max_tokens=2000)
                if res is None: st.stop()
                scheme = res.choices[0].message.content
            st.markdown(scheme)
            st.download_button("📥 Download Scheme PDF", generate_pdf(scheme, f"Scheme {topic_data['topic']}"), "scheme.pdf", key="dl_scheme")

st.sidebar.caption("NCDC 2026 Competency-Based | P4-P7 | Pixel-Perfect Diagrams | 7 Scenarios Per Mode | Contact: " + CONTACT)
