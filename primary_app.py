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

# ===================== 1. NEW NCDC 2026 SYSTEM PROMPT - 7 SCENARIOS LOOP =====================
SYSTEM_PROMPT = """
You are TEACHERK, a Senior NCDC 2026 Uganda Examiner and Master Teacher for PRIMARY P4-P7.

YOUR MISSION: Help students understand deeply by showing AT LEAST 7 DIFFERENT SCENARIOS for 1 topic. Like UNEB marking guide.

MANDATORY OUTPUT FORMAT - LOOP THIS 7 TIMES:

### **SCENARIO 1: [Give it a Ugandan Title]**
Write a 3-4 sentence real-life Ugandan scenario. Use: market, school, boda, farm, clinic, home.

**COMPETENCY TASK:** State what learner must be able to DO.

**QUESTION 1:** 1 clear scenario-based question with marks. [2 marks]

**METHOD 1: Formula/Concept Method**
Step 1: State concept/formula
Step 2: Substitute values
Step 3: Calculate with units
Answer: ___

**METHOD 2: Logical/Story Method**
Explain how to solve it without formula. Using reasoning or drawing.
Answer: ___

---
REPEAT FOR SCENARIO 2, 3, 4, 5, 6, 7. Each must be DIFFERENT.

### **PART 8: COMMON MISTAKES & EXAM TIPS**
1. List 3 mistakes pupils make on this topic in PLE
2. Give 1 "Trick" to remember

### **PART 9: QUICK PRACTICE FOR PUPILS**
Give 3 more short questions for pupil to try alone. No answers.

CURRICULUM RULES:
1. LOCK: Only use the NCDC 2026 P4-P7 topics provided below. If outside, say: "That is not in NCDC P4-P7. Let's do [suggest closest topic] instead."
2. EXAMPLES: All 7 scenarios must be Ugandan and realistic and DIFFERENT.
3. LANGUAGE: Simple English for ages 9-13. Step by step.
4. MATH/SCIENCE: Always show units. Always show 2 methods minimum.
5. QUANTITY RULE: MUST GENERATE AT LEAST 7 SCENARIOS. NO LESS.

TONE: Patient teacher. Use "Let's try", "Notice that", "Why does this work?"
"""

# ===================== 2. FULL NCDC 2026 DB - EXACT TOPICS PROVIDED - NO CHANGE =====================
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
if topic_data is None: st.error("Topic not found in NCDC P4-P7. Please select another."); st.stop()

st.subheader(f"{grade} {subject}: {topic_data['topic']}")
st.info(f"**NCDC Competency**: {topic_data['competency']}")
st.success(f"**Example Scenario**: {topic_data['scenario']}")

tabs = st.tabs(["AI Chat + Voice", "Theory + Practicals", "Quiz + Evaluation", "Math Work", "Teacher Tools"])

with tabs[0]:
    st.header("Ask TeacherK NCDC - 7 Scenarios")
    q = st.text_input("Type question here e.g: Teach me Fractions")
    audio_input = st.audio_input("Or record your question")
    if audio_input:
        with st.spinner("Transcribing..."):
            q = speech_to_text_from_audio(audio_input.getvalue())
            st.success(f"You said: {q}")
    if st.button("Ask") and q:
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\n\nLevel: {grade}, Subject: {subject}, Topic: {topic_data['topic']}\n\nStudent Request: {q}\n\nNOW TEACH THIS TOPIC USING AT LEAST 7 DIFFERENT UGANDA SCENARIOS AND SHOW MULTIPLE WAYS TO SOLVE EACH TASK."
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}],
                temperature=0.2, max_tokens=4000
            )
            answer = res.choices[0].message.content
            st.markdown(answer)
            audio = text_to_speech(answer)
            if audio: st.audio(audio)
            st.download_button("Download Lesson + Marking Guide as PDF", generate_pdf(answer, f"{grade} {subject} {topic_data['topic']}"), "lesson.pdf")

with tabs[1]:
    st.header("Theory + 2 Practicals - 7 Scenarios")
    if st.button("Generate Theory and Practicals"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nFor {grade} {subject} Topic: {topic_data['topic']}. Give 7 scenarios and 2 practical activities pupils can do with local materials."
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], temperature=0.3, max_tokens=4000)
            theory = res.choices[0].message.content
            st.markdown(theory)
            st.download_button("Download Theory as PDF", generate_pdf(theory, f"Theory {topic_data['topic']}"), "theory.pdf")

with tabs[2]:
    st.header("Quiz Generator + Performance Evaluator - 7 Scenarios")
    num_q = st.slider("Number of Questions", 7, 20, 10)
    if st.button("Generate Scenario-Based Quiz"):
        client = get_client()
        if client:
            prompt = f"{SYSTEM_PROMPT}\nGenerate {num_q} scenario-based questions for {grade} {subject} Topic: {topic_data['topic']}. Use at least 7 different Uganda scenarios across the questions. Include marking guide."
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], temperature=0.3, max_tokens=4000)
            st.session_state.quiz = res.choices[0].message.content
            st.markdown(st.session_state.quiz)
            st.download_button("Download Quiz as PDF", generate_pdf(st.session_state.quiz, f"Quiz {topic_data['topic']}"), "quiz.pdf")
    if "quiz" in st.session_state:
        score = st.number_input("Enter Pupil Score out of "+str(num_q), 0, num_q, 5)
        if st.button("Evaluate Performance"):
            client = get_client()
            if client:
                prompt = f"{SYSTEM_PROMPT}\nPupil scored {score}/{num_q} in {grade} {subject} Topic: {topic_data['topic']}. Give: 1.Grade 2.Strengths 3.Weak areas 4.3 Remediation activities with 7 scenarios."
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
                evaluation = res.choices[0].message.content
                st.success(evaluation)
                st.download_button("Download Report as PDF", generate_pdf(evaluation, f"Evaluation {topic_data['topic']}"), "evaluation.pdf")

with tabs[3]:
    st.header("Mathematics Work Page - 7 Scenario Workouts")
    if subject == "Mathematics":
        if st.button("Generate 7 Scenario Worked Examples"):
            client = get_client()
            if client:
                prompt = f"{SYSTEM_PROMPT}\nGenerate 7 fully worked scenario-based math questions for {grade} {subject} Topic: {topic_data['topic']}. Each must have 2 methods. Ugandan context."
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], temperature=0.2, max_tokens=4000)
                math_work = res.choices[0].message.content
                st.markdown(math_work)
                st.download_button("Download Math Work as PDF", generate_pdf(math_work, f"Math Work {topic_data['topic']}"), "math_work.pdf")
   else:
       st.info("This tab is for Mathematics only. Select Mathematics subject to use.")

with tabs[4]:
    st.header("🛠️ Teacher Tools - NCDC 2026 - 7 Scenarios")
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
                    prompt = f"{SYSTEM_PROMPT}\nWrite full NCDC 2026 lesson plan for {grade} {subject} Topic: {topic_data['topic']}. Duration: {duration}. Must include 7 scenarios and multiple methods."
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], max_tokens=4000)
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
                    prompt = f"{SYSTEM_PROMPT}\nGenerate 20 question Beginning of Term diagnostic test for {grade} {subject}. Use at least 7 different Uganda scenarios. Include marking guide."
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], max_tokens=4000)
                    bot = res.choices[0].message.content
                    st.markdown(bot)
                    st.download_button("Download BOT Test PDF", generate_pdf(bot, f"BOT Test {grade} {subject}"), "bot_test.pdf")

    if tool_choice == "4. Mid Term Exam Generator":
        st.subheader("📗 Mid Term Exam")
        topics_covered = st.text_input("Topics covered so far, comma separated", topic_data['topic'])
        if st.button("Generate Mid Term Exam"):
            if client:
                with st.spinner("Generating 50 Marks Exam..."):
                    prompt = f"{SYSTEM_PROMPT}\nGenerate Mid Term Exam for {grade} {subject}. Topics: {topics_covered}. 50 marks. Use at least 7 different scenarios. Include marking guide."
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], max_tokens=4000)
                    midterm = res.choices[0].message.content
                    st.markdown(midterm)
                    st.download_button("Download Mid Term PDF", generate_pdf(midterm, f"Mid Term {grade} {subject}"), "midterm.pdf")

    if tool_choice == "5. End of Term Exam + Marking Guide":
        st.subheader("📙 End of Term Exam - 100 Marks PLE Style")
        if st.button("Generate End of Term Exam"):
            if client:
                with st.spinner("Generating 100 Marks PLE Style Exam..."):
                    prompt = f"{SYSTEM_PROMPT}\nGenerate End of Term Exam for {grade} {subject}. 100 marks PLE style. Use at least 7 different scenarios. Section A: 40 MCQ. Section B: 10 short answer. Section C: 5 essay. Include detailed marking guide."
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}], max_tokens=4000)
                    eot = res.choices[0].message.content
                    st.markdown(eot)
                    st.download_button("Download EOT Exam PDF", generate_pdf(eot, f"End of Term {grade} {subject}"), "eot_exam.pdf")

st.sidebar.caption("NCDC 2026 Competency-Based | P4-P7 | 6 Subjects Locked | 7 Scenarios Per Mode")
