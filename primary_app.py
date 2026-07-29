import streamlit as st
import io, re, json, random
import hashlib
from datetime import datetime
from groq import Groq, RateLimitError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

CONTACT = "256751040731"
st.set_page_config(page_title="TEACHERK PRIMARY 2026 NCDC", page_icon="🐢", layout="wide")
st.warning("⚠️ **DISCLAIMER**: TEACHERK follows NCDC 2026 Uganda Primary Competency-Based Curriculum P4-P7.")

# ===================== MERGED MASTER PROMPT v6.1 NCDC ARCHITECT =====================
MASTER_PROMPT = """
You are an OFFICIAL UNEB PLE EXAMINER + ELITE SVG ARCHITECT for Uganda P4-P7 following NCDC 2026 Competency-Based Curriculum.

ROTATION RULE: You MUST use ALL topics provided for the grade. Spread questions evenly across topics in both Section A and Section B.

DIFFICULTY RULE BY CLASS:
P7 = 18 HARD questions, P6 = 16 HARD questions, P5 = 6 MEDIUM questions, P4 = 0 EASY questions

FORMAT RULES:
A. ENGLISH: TIME 2hr15min. SEC A: 30Q Grammar + 20Q Comprehension. SEC B: 5Q Composition 10marks each. TOTAL 100
B. SCIENCE: TIME 2hr15min. SEC A: 40Q 1mark. SEC B: 15Q 4marks with a),b). TOTAL 100
C. MATH/SST/CRE/IRE: SEC A: 20Q. SEC B: 40Q a,b,c. TOTAL 60Q. IF SST THEN Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE

CRITICAL SVG RULES:
1. Every SVG MUST start with style="background-color: #ffffff;" so it's visible on dark mode
2. Responsive: use viewBox and width="100%" height="100%"
3. Label SIDES with measurements like "5cm", "10cm". DO NOT label corners with 90°.
4. Use black text fill="#000" and black stroke="#000"
5. Wrap EVERY SVG with [SVG]...[/SVG]
6. For Science: Use Bezier C/Q for organs. Label P,Q,R,S or K,L,M
7. For SST Map: MUST have Title, Frame, Key, Scale, Compass N

EXACT SVG TEMPLATES - COPY THESE:

SCIENCE PANEL P7: <svg viewBox="0 0 1400 1350" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><style>.exam-grid-line{stroke:#e2e8f0;stroke-width:2;stroke-dasharray:8 4}.exam-title{font-family:'Times New Roman',serif;font-size:22px;font-weight:bold;fill:#000;text-anchor:middle}.diagram-title{font-family:'Times New Roman',serif;font-size:16px;font-weight:bold;fill:#000;text-anchor:middle}.label-txt{font-family:'Times New Roman',serif;font-size:16px;font-weight:bold;fill:#000}.line-main{stroke:#000;stroke-width:3;fill:none}.line-thin{stroke:#000;stroke-width:1.5;fill:none}.tube{stroke:#000;stroke-width:3;fill:none}.line-water{stroke:#000;stroke-dasharray:4 4;fill:none}.oil-layer{stroke:#000;stroke-width:6}.seed{fill:#000}.mirror{stroke:#000;stroke-width:4}.ray{stroke:#000;stroke-width:2.5}.normal{stroke:#000;stroke-width:1.5;stroke-dasharray:5 5}.organ-outline{stroke:#000;stroke-width:2.5;fill:none}.stage-box{fill:none;stroke:#000;stroke-width:2}</style><text x="700" y="40" class="exam-title">UNEB P7 SCIENCE DIAGRAM COMPILATION PANEL</text><line x1="700" y1="70" x2="700" y2="1300" class="exam-grid-line"/><line x1="50" y1="480" x2="1350" y2="480" class="exam-grid-line"/><line x1="50" y1="900" x2="1350" y2="900" class="exam-grid-line"/><g transform="translate(100, 80)"><text x="250" y="25" class="diagram-title">1. The Lung Model Experiment</text><path d="M 250 60 L 250 130" class="line-main" stroke-width="5"/><path d="M 250 130 L 210 180 M 250 130 L 290 180" class="line-main" stroke-width="4"/><path d="M 220 60 L 280 60 M 220 60 L 160 120 L 160 320 M 280 60 L 340 120 L 340 320" class="line-main"/><path d="M 210 180 C 180 200, 180 250, 210 250 C 230 250, 230 200, 210 180 Z M 290 180 C 270 200, 270 250, 290 250 C 320 250, 320 200, 290 180 Z" class="line-main"/><path d="M 160 320 Q 250 350 340 320" class="line-main"/><line x1="250" y1="335" x2="250" y2="375" class="line-main"/><line x1="250" y1="90" x2="380" y2="90" class="line-thin"/><text x="390" y="95" class="label-txt">P</text><line x1="190" y1="220" x2="70" y2="220" class="line-thin"/><text x="50" y="225" class="label-txt">Q</text><line x1="340" y1="240" x2="410" y2="240" class="line-thin"/><text x="420" y="245" class="label-txt">R</text><line x1="250" y1="350" x2="110" y2="350" class="line-thin"/><text x="90" y="355" class="label-txt">S</text></g><g transform="translate(750, 80)"><text x="270" y="25" class="diagram-title">2. Conditions for Germination</text><g transform="translate(10, 40)"><path d="M 20 20 L 20 200 C 20 230, 80 230, 80 200 L 80 20" class="tube"/><line x1="22" y1="130" x2="78" y2="130" class="oil-layer"/><line x1="22" y1="170" x2="78" y2="170" class="line-water"/><ellipse cx="50" cy="185" rx="10" ry="6" class="seed"/><text x="50" y="250" class="label-txt" text-anchor="middle">Tube A</text></g><g transform="translate(180, 40)"><path d="M 20 20 L 20 200 C 20 230, 80 230, 80 200 L 80 20" class="tube"/><ellipse cx="50" cy="160" rx="10" ry="6" class="seed"/><text x="50" y="250" class="label-txt" text-anchor="middle">Tube B</text></g><g transform="translate(350, 40)"><path d="M 20 20 L 20 200 C 20 230, 80 230, 80 200 L 80 20" class="tube"/><ellipse cx="50" cy="170" rx="10" ry="6" class="seed"/><text x="50" y="250" class="label-txt" text-anchor="middle">Tube C</text></g></g><g transform="translate(100, 520)"><text x="250" y="25" class="diagram-title">3. Reflection of Light</text><line x1="50" y1="220" x2="450" y2="220" class="mirror"/><line x1="250" y1="50" x2="250" y2="220" class="normal"/><text x="230" y="45" class="label-txt">Normal</text><path d="M 100 80 L 250 220 L 400 80" class="ray"/><text x="70" y="75" class="label-txt">Ray X</text><text x="410" y="75" class="label-txt">Ray Y</text><text x="215" y="160" class="label-txt" style="font-style:italic">i</text><text x="275" y="160" class="label-txt" style="font-style:italic">r</text></g><g transform="translate(750, 520)"><text x="250" y="25" class="diagram-title">4. Alimentary Canal</text><path d="M 210 35 L 210 75 M 225 35 L 225 65" stroke="#000" stroke-width="2.5"/><path d="M 210 75 C 130 85, 110 175, 200 185 C 270 190, 300 125, 290 95 C 285 80, 240 65, 225 65" class="organ-outline"/><path d="M 200 185 C 170 205, 170 255, 250 255 C 280 255, 290 235, 290 215" class="organ-outline"/><line x1="150" y1="125" x2="50" y2="125" class="line-thin"/><text x="35" y="130" class="label-txt">K</text><line x1="260" y1="210" x2="380" y2="210" class="line-thin"/><text x="395" y="215" class="label-txt">L</text><line x1="210" y1="235" x2="70" y2="235" class="line-thin"/><text x="50" y="240" class="label-txt">M</text></g><g transform="translate(100, 930)"><text x="250" y="25" class="diagram-title">5. Lifecycle of a Housefly</text><rect x="50" y="120" width="100" height="60" class="stage-box"/><text x="100" y="155" class="label-txt" text-anchor="middle">Eggs</text><line x1="150" y1="150" x2="210" y2="150" class="line-water"/><polygon points="215,150 205,145 205,155" fill="#000"/><rect x="220" y="120" width="100" height="60" class="stage-box"/><text x="270" y="155" class="label-txt" text-anchor="middle">Larva</text><line x1="320" y1="150" x2="380" y2="150" class="line-water"/><polygon points="385,150 375,145 375,155" fill="#000"/><rect x="390" y="120" width="100" height="60" class="stage-box"/><text x="440" y="155" class="label-txt" text-anchor="middle">Pupa</text><path d="M 440 120 C 440 50, 100 50, 100 110" class="line-water"/><polygon points="100,115 95,105 105,105" fill="#000"/><text x="270" y="45" class="label-txt" text-anchor="middle">Adult</text></g><g transform="translate(750, 930)"><text x="250" y="25" class="diagram-title">6. Simple Distillation</text><rect x="150" y="200" width="100" height="80" stroke="#000" stroke-width="2.5" fill="none"/><text x="200" y="290" class="label-txt" text-anchor="middle">Heat</text><circle cx="200" cy="110" r="30" stroke="#000" stroke-width="2.5" fill="none"/><text x="200" y="60" class="label-txt" text-anchor="middle">Flask</text><path d="M 230 110 L 320 110 L 320 150" stroke="#000" stroke-width="2.5"/><rect x="320" y="150" width="80" height="120" stroke="#000" stroke-width="2.5" fill="none"/><text x="360" y="280" class="label-txt" text-anchor="middle">Condenser</text><circle cx="480" cy="210" r="20" stroke="#000" stroke-width="2.5" fill="none"/><text x="480" y="250" class="label-txt" text-anchor="middle">Beaker</text></g></svg>

SKETCH MAP SST: <svg viewBox="0 0 700 500" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><style>.map-frame{fill:#f8fafc;stroke:#0f172a;stroke-width:4}.map-title{font-family:sans-serif;font-size:16px;font-weight:bold;fill:#0f172a;text-anchor:middle}.legend-box{fill:#ffffff;stroke:#475569;stroke-width:2}.legend-title{font-family:sans-serif;font-size:13px;font-weight:bold;fill:#1e293b}.label-style{font-family:sans-serif;font-size:12px;fill:#334155}.lake{fill:#7dd3fc;stroke:#0284c7;stroke-width:1.5}.river{fill:none;stroke:#0284c7;stroke-width:3}.mountain{fill:#b45309;stroke:#78350f;stroke-width:1.5}.swamp{stroke:#15803d;stroke-width:2}.road{stroke:#ef4444;stroke-width:2.5;stroke-dasharray:6 4}</style><rect x="20" y="20" width="660" height="460" class="map-frame"/><text x="350" y="45" class="map-title">{title}</text><path d="M 60 120 C 120 110, 180 140, 150 200 C 120 250, 70 220, 50 180 Z" class="lake"/><path d="M 140 190 Q 220 220, 260 300 T 380 400" class="river"/><path d="M 400 120 L 430 120 M 410 125 L 440 125" class="swamp"/><polygon points="500,280 540,210 580,280" class="mountain"/><path d="M 30 420 Q 250 380, 480 340 T 640 250" class="road"/><g transform="translate(610, 90)"><line x1="0" y1="-40" x2="0" y2="40" stroke="#0f172a" stroke-width="2"/><line x1="-40" y1="0" x2="40" y2="0" stroke="#0f172a" stroke-width="2"/><polygon points="0,-40 -5,-30 5,-30" fill="#0f172a"/><text x="0" y="-45" class="label-style" font-weight="bold" text-anchor="middle">N</text></g><g transform="translate(40, 290)"><rect width="160" height="160" class="legend-box" rx="5"/><text x="15" y="25" class="legend-title">KEY</text></g><g transform="translate(420, 450)"><line x1="0" y1="0" x2="200" y2="0" stroke="#0f172a" stroke-width="3"/><text x="0" y="-10" class="label-style" text-anchor="middle">0</text><text x="100" y="-10" class="label-style" text-anchor="middle">10km</text><text x="200" y="-10" class="label-style" text-anchor="middle">20km</text></g></svg>

UNEB VENN UNIVERSAL: <svg viewBox="0 0 600 420" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><style>.universal-box{fill:#f8fafc;stroke:#1e293b;stroke-width:4}.circle-f{fill:#3b82f6;fill-opacity:0.15;stroke:#2563eb;stroke-width:3}.circle-v{fill:#ef4444;fill-opacity:0.15;stroke:#dc2626;stroke-width:3}.text-title{font-family:sans-serif;font-size:16px;font-weight:bold;fill:#0f172a}.text-val{font-family:sans-serif;font-size:20px;font-weight:bold;fill:#1e293b;text-anchor:middle}.text-set{font-family:sans-serif;font-size:18px;font-weight:bold;fill:#1e293b}</style><rect x="20" y="20" width="560" height="380" rx="10" class="universal-box"/><text x="40" y="55" class="text-set">ε = {total}</text><text x="300" y="50" class="text-title" text-anchor="middle">{title}</text><circle cx="230" cy="220" r="110" class="circle-f"/><circle cx="370" cy="220" r="110" class="circle-v"/><text x="170" y="225" class="text-val">{f_only}</text><text x="300" y="225" class="text-val" style="fill:#7e22ce">{both}</text><text x="430" y="225" class="text-val">{v_only}</text><text x="530" y="360" class="text-val">{neither}</text></svg>

SQUARE: <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><text x="200" y="30" font-family="sans-serif" font-size="14" text-anchor="middle" fill="#000">{title}</text><rect x="100" y="100" width="200" height="200" stroke="#000000" stroke-width="2" fill="none"/><text x="200" y="90" font-size="12" text-anchor="middle" fill="#000000">200mm</text><text x="310" y="200" font-size="12" fill="#000">200mm</text><text x="200" y="320" font-size="12" text-anchor="middle" fill="#000">200mm</text><text x="90" y="200" font-size="12" fill="#000">200mm</text></svg>

RECTANGLE: <svg viewBox="0 0 500 300" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><text x="250" y="30" font-family="sans-serif" font-size="14" text-anchor="middle" fill="#000">{title}</text><rect x="100" y="80" width="300" height="150" stroke="#000" stroke-width="2" fill="none"/><text x="250" y="70" font-size="12" text-anchor="middle" fill="#000">l = 10cm</text><text x="90" y="155" font-size="12" fill="#000">w = 5cm</text></svg>

CIRCLE: <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><text x="200" y="30" font-family="sans-serif" font-size="14" text-anchor="middle" fill="#000">{title}</text><circle cx="200" cy="200" r="100" stroke="#000" stroke-width="2" fill="none"/><line x1="200" y1="200" x2="300" y2="200" stroke="#000" stroke-width="1.5" stroke-dasharray="4,2"/><text x="250" y="190" font-size="12" fill="#000">r = 100mm</text><circle cx="200" cy="200" r="3" fill="#000"/></svg>

HEXAGON: <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><text x="200" y="30" font-family="sans-serif" font-size="14" text-anchor="middle" fill="#000">{title}</text><polygon points="200,80 303.92,140 303.92,260 200,320 96.08,260 96.08,140" stroke="#000" stroke-width="2" fill="none"/><text x="200" y="60" font-size="10" text-anchor="middle" fill="#000">120mm</text></svg>

CYLINDER 3D: <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><text x="200" y="30" font-family="sans-serif" font-size="14" text-anchor="middle" fill="#000">{title}</text><ellipse cx="200" cy="100" rx="80" ry="20" stroke="#000000" stroke-width="2" fill="none"/><ellipse cx="200" cy="250" rx="80" ry="20" stroke="#000" stroke-width="2" fill="none" stroke-dasharray="4,2"/><line x1="120" y1="100" x2="120" y2="250" stroke="#000" stroke-width="2"/><line x1="280" y1="100" x2="280" y2="250" stroke="#000" stroke-width="2"/><text x="290" y="175" font-size="10" fill="#000">150mm</text></svg>

CONE 3D: <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><text x="200" y="30" font-family="sans-serif" font-size="14" text-anchor="middle" fill="#000">{title}</text><ellipse cx="200" cy="300" rx="80" ry="20" stroke="#000" stroke-width="2" fill="none"/><line x1="120" y1="300" x2="200" y2="100" stroke="#000" stroke-width="2"/><line x1="280" y1="300" x2="200" y2="100" stroke="#000" stroke-width="2"/><text x="140" y="200" font-size="10" fill="#000">200mm</text></svg>

60 DEGREE: <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><text x="200" y="30" font-family="sans-serif" font-size="14" text-anchor="middle" fill="#000">{title}</text><line x1="100" y1="300" x2="300" y2="300" stroke="#000" stroke-width="2"/><line x1="100" y1="300" x2="200" y2="126.8" stroke="#000" stroke-width="2"/><path d="M 150 300 A 50 50 0 0 1 125 213.4" stroke="#d9534f" stroke-width="1.5" fill="none"/><text x="135" y="260" font-size="14" fill="#d9534f">60°</text><text x="200" y="310" font-size="10" text-anchor="middle" fill="#000000">200mm</text></svg>

120 DEGREE: <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff;"><text x="200" y="30" font-family="sans-serif" font-size="14" text-anchor="middle" fill="#000">{title}</text><line x1="200" y1="300" x2="350" y2="300" stroke="#000" stroke-width="2"/><line x1="200" y1="300" x2="125" y2="170" stroke="#000" stroke-width="2"/><path d="M 250 300 A 50 50 0 0 0 175 213.4" stroke="#d9534f" stroke-width="1.5" fill="none"/><text x="210" y="240" font-size="14" fill="#d9534f">120°</text><text x="275" y="310" font-size="10" text-anchor="middle" fill="#000">150mm</text></svg>
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
def get_all_topics(grade): return [t["topic"] for sub in PRIMARY_DB[f"PRIMARY_{grade[1:]}"].values() for t in sub]

# ===================== SVG RENDERER =====================
def render_with_svg(text):
    if not text: st.error("No response from AI. Try again."); return
    st.session_state['last_svgs'] = []
    parts = re.split(r'(\[SVG\].*?\[/SVG\])', text, flags=re.DOTALL)
    for part in parts:
        if part.startswith("[SVG]"):
            svg_code = part[5:-6]
            if 'background-color' not in svg_code:
                svg_code = svg_code.replace('<svg ', '<svg style="background-color: #ffffff;" ')
            st.session_state['last_svgs'].append(svg_code)
            st.markdown(svg_code, unsafe_allow_html=True)
        else:
            st.markdown(part)

# ===================== GROQ + PDF =====================
if "cache" not in st.session_state:
    st.session_state.cache = {}
    st.session_state['last_svgs'] = []

def smart_groq_call(client, system_prompt, user_prompt):
    cache_key = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
    if cache_key in st.session_state.cache: return st.session_state.cache[cache_key]
    models_to_try = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    for model in models_to_try:
        try:
                       res = client.chat.completions.create(model=model, messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], temperature=0.3, max_tokens=2500, timeout=60)
                       if res and res.choices[0].message.content:
                st.session_state.cache[cache_key] = res; return res
        except RateLimitError: continue
        except: continue
    return None

def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("GROQ_API_KEY missing in Secrets"); return None

def generate_pdf(content, title, subject, grade):
    try:
        buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
        year = datetime.now().year
        c.setFont("Helvetica-Bold", 12); c.drawCentredString(width/2, height-40, f"UNEB PRIMARY {grade[1:]} {subject.upper()} {year}")
        c.setFont("Helvetica", 10); c.drawCentredString(width/2, height-55, "Time Allowed: 2 hours 15 minutes")
        y = height - 80; svg_index = 0
        for line in content.split('\n')[:600]:
            if "[SVG]" in line and svg_index < len(st.session_state['last_svgs']):
                svg_code = st.session_state['last_svgs'][svg_index]
                svg_io = io.StringIO(svg_code)
                drawing = svg2rlg(svg_io)
                if drawing:
                    drawing.scale(0.5, 0.5)
                    renderPDF.draw(drawing, c, 40, y-200)
                    y -= 210
                    svg_index += 1
            if y < 50: c.showPage(); y = height - 50
            clean_line = re.sub(r'\[/?SVG\]', '', line)
            c.drawString(40, y, clean_line[:95]); y -= 14
        c.save(); buffer.seek(0); return buffer
    except Exception as e:
        st.warning(f"PDF SVG embed failed: {e}")
        return None

# ===================== PASSWORD =====================
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

# ===================== MAIN APP =====================
st.title("🐢 TEACHERK PRIMARY 2026 NCDC v6.1")
st.sidebar.success(f"Logged in as: {st.session_state.user_type}")

grade = st.sidebar.selectbox("Class", ["P4","P5","P6","P7"])
subject = st.sidebar.selectbox("Subject", list(PRIMARY_CURRICULUM_MAP[grade].keys()))
topic = st.sidebar.selectbox("Topic", PRIMARY_CURRICULUM_MAP[grade][subject])

tabs = st.tabs(["🔍 General Search", "📖 Theory", "📝 HARD MOCK", "➗ Math Work", "👩‍🏫 Teacher Tools"])

def ask_ai(prompt, dl_name):
    client = get_client()
    if not client: return
    with st.spinner("Generating NCDC Diagram..."):
        res = smart_groq_call(client, MASTER_PROMPT, prompt)
    if res:
        answer = res.choices[0].message.content
        render_with_svg(answer)
        pdf = generate_pdf(answer, dl_name, subject, grade)
        if pdf: st.download_button("📥 Download PDF with SVG", pdf, f"{dl_name}.pdf")
    else:
        st.error("AI Busy. Please wait 1 minute and retry.")
    st.markdown("---")
    st.file_uploader("Upload student work for marking", type=["txt","pdf"], key=f"upload_{dl_name}")

with tabs[0]:
    st.header("🔍 General Search")
    q = st.text_input("Ask Anything: e.g 'Draw Science Panel' or 'Draw Sketch map of Uganda'")
    if st.button("Ask", type="primary") and q:
        ask_ai(f"You are a smart UNEB tutor for {grade} {subject}. Topic: {topic}. Request: {q}", "answer_general")

with tabs[1]:
    st.header(f"📖 Theory: {grade} {subject}")
    if st.button("Generate Full Theory Notes", type="primary"):
        ask_ai(f"Generate detailed NCDC 2026 theory notes for {grade} {subject} Topic: {topic}. Include SVG diagrams.", f"Theory_{topic}")

with tabs[2]:
    st.header("📝 HARD COMBINED MOCK PLE")
    is_english = subject == "English Language"
    is_science = subject == "Integrated Science"
    diff_map = {"P4": "0 EASY", "P5": "6 MEDIUM", "P6": "16 HARD", "P7": "18 HARD"}
    st.info(f"{grade} DIFFICULTY: {diff_map[grade]}. All {len(get_all_topics(grade))} topics including CRE/IRE will be rotated.")
    if st.button("Generate HARD COMBINED MOCK PLE", type="primary"):
        all_topics = get_all_topics(grade); random.shuffle(all_topics)
        if is_english: prompt = f"{MASTER_PROMPT}\nGenerate HARD UNEB PLE MOCK for {grade} ENGLISH. TIME: 2hr15min. DIFFICULTY: {diff_map[grade]}. ROTATE: {all_topics}. SEC A: 30Q + 20Q. SEC B: 5Q."
        elif is_science: prompt = f"{MASTER_PROMPT}\nGenerate HARD UNEB PLE MOCK for {grade} INTEGRATED SCIENCE. TIME: 2hr15min. DIFFICULTY: {diff_map[grade]}. ROTATE: {all_topics}. SEC A: 40Q. SEC B: 15Q with a),b). Include Science Panel SVG."
        else: sst_rule = "FOR SST: Q21-Q40=SST, Q41-Q50=CRE, Q51-Q60=IRE" if subject == "Social Studies (SST)" else ""; prompt = f"{MASTER_PROMPT}\nGenerate HARD MOCK for {grade} {subject}. DIFFICULTY: {diff_map[grade]}. ROTATE: {all_topics}. SEC A 20Q. SEC B 40Q. {sst_rule}"
        ask_ai(prompt, f"HARD_MOCK_{subject}_{grade}")

with tabs[3]:
    st.header("➗ Mathematics Worked Examples")
    if subject == "Mathematics":
        if st.button("Generate 7 Hard Worked Examples", type="primary"):
            ask_ai(f"{MASTER_PROMPT}\nGenerate 7 questions for {grade} Mathematics. ROTATE TOPICS: {get_all_topics(grade)}. Include SVG diagrams.", f"Math_Work_{grade}")
    else: st.info("Select Mathematics subject.")

with tabs[4]:
    st.header("👩‍🏫 Teacher Tools")
    st.subheader("1. Test Paper Generator")
    if st.button("Generate Test Paper"):
        ask_ai(f"{MASTER_PROMPT}\nGenerate Test for {grade} {subject}. ROTATE TOPICS: {get_all_topics(grade)}.", "Test_Paper")
    st.subheader("2. UNEB Marking Guide Generator")
    questions = st.text_area("Paste PLE Question(s) Here", height=150)
    if st.button("Generate UNEB Marking Guide"):
        ask_ai(f"Act as UNEB Examiner for {subject}. Q: {questions}\nOutput: Answer Key, Marking Guide.", "Marking_Guide")
    st.subheader("3. Marking / Grading Assistant")
    marking_scheme = st.text_area("Paste Marking Scheme", height=100)
    student_answers = st.text_area("Paste Student Answers", height=150)
    if st.button("Mark Work Now"):
        ask_ai(f"Act as UNEB Examiner for {subject}. Mark this.\nSCHEME:\n{marking_scheme}\nSTUDENT:\n{student_answers}", "Marked_Work")
    st.subheader("4. Report Card Generator")
    pupil_name = st.text_input("Pupil Name")
    scores = st.text_area("Paste scores: Subject: Score")
    if st.button("Generate Report Card"):
        ask_ai(f"Generate Report Card for {pupil_name} Class {grade}. Scores:\n{scores}", "Report_Card")
    st.subheader("5. Lesson Plan Generator")
    if st.button("Generate Lesson Plan"):
        ask_ai(f"Generate NCDC 2026 Lesson Plan for {grade} {subject} Topic: {topic}.", "Lesson_Plan")
    st.subheader("6. Scheme of Work Generator")
    if st.button("Generate Scheme of Work"):
        ask_ai(f"Create 1-week scheme of work for {grade} {subject} Topic: {topic}.", "Scheme_of_Work")

st.sidebar.caption(f"NCDC 2026 | Contact: {CONTACT}") 
