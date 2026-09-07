"""
Ayurvedic Knowledge Base for MediKiosk RAG Pipeline
=====================================================
Grounded on:
1. AyurGenixAI: Ayurvedic Clinical Dataset (Kaggle: kagglekirti123/ayurgenixai-ayurvedic-dataset)
   - 447 clinical condition mappings across 35 standard Ayurvedic parameters
2. BharatGenAI: AyurParam LLM (Hugging Face: bharatgenai/AyurParam)
   - Domain-specialized 2.9B bilingual Ayurvedic foundation model & classical Samhita corpus
"""

from typing import List, Dict, Any

AYURVEDIC_DATASET_METADATA = {
    "dataset_name": "AyurGenixAI Ayurvedic Dataset",
    "dataset_source": "kagglekirti123/ayurgenixai-ayurvedic-dataset",
    "dataset_url": "https://www.kaggle.com/datasets/kagglekirti123/ayurgenixai-ayurvedic-dataset",
    "llm_model": "AyurParam (2.9B Bilingual Instruct)",
    "llm_source": "bharatgenai/AyurParam",
    "llm_url": "https://huggingface.co/bharatgenai/AyurParam",
    "parameters_count": 35,
    "conditions_count": 447,
    "classical_samhitas": ["Charaka Samhita", "Sushruta Samhita", "Ashtanga Hridaya", "Madhava Nidana", "Sharangadhara Samhita"]
}

AYURVEDIC_KNOWLEDGE_RECORDS: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # CARDIOLOGY / CARDIOVASCULAR (HRIDROGA / HRIDSHULA)
    # -------------------------------------------------------------
    {
        "id": "ayur_hridroga_01",
        "category": "cardiology",
        "ayurvedic_nidana": "Vata-Pittaja Hridroga / Hridshula",
        "modern_correlation": "Angina Pectoris, Coronary Insufficiency, Cardiac Dysrhythmia",
        "keywords": ["chest pain", "chest tightness", "palpitations", "left arm radiation", "सीने में दर्द", "छाती", "हृदय", "घबराहट"],
        "dominant_dosha": "Vata-Pitta (Vyana Vata & Sadhaka Pitta Dushti)",
        "prakriti_vikriti": "Vata-Pitta Vikriti with Rasavaha Srotorodha",
        "agni_status": "Vishama Agni / Mandagni with Ama formation",
        "dhatu_affected": ["Rasa (Plasma)", "Rakta (Blood)", "Mamsa (Cardiac Muscle)"],
        "srotas_affected": ["Rasavaha Srotas", "Pranavaha Srotas"],
        "clinical_presentation": "Constricting substernal chest discomfort radiating to left upper extremity, palpitations (Hridrava), dyspnea on minimal exertion, mental fatigue, diaphoresis.",
        "classical_herbs_formulations": [
            "Arjuna Ksheerapaka (Terminalia arjuna)",
            "Prabhakara Vati",
            "Hridayarnava Rasa",
            "Dashamula Kwatha",
            "Akik Pishti"
        ],
        "pathya": [
            "Lashuna (Garlic) in warm milk",
            "Dadima (Pomegranate) juice",
            "Draksha (Raisins)",
            "Ushnodaka (Warm water)",
            "Laghu Ahara (Light easily digestible meals)"
        ],
        "apathya": [
            "Guru (heavy) and Ati-Snigdha (excessively oily/fried) foods",
            "Ativyayama (excessive physical exhaustion)",
            "Vegadharana (suppression of natural urges like urine, defecation, flatus)",
            "Chinta & Krodha (excessive anxiety, stress and anger)",
            "Ratrijagarana (night vigil / sleep deprivation)"
        ],
        "classical_reference": "Charaka Samhita, Chikitsa Sthana, Chapter 26 (Trimarmiya Chikitsa, Sloka 77-84)",
        "source_dataset": "kagglekirti123/ayurgenixai-ayurvedic-dataset",
        "model_reference": "bharatgenai/AyurParam"
    },
    {
        "id": "ayur_hridroga_02",
        "category": "cardiology",
        "ayurvedic_nidana": "Kaphaja Hridroga / Dhamani Pratichaya",
        "modern_correlation": "Atherosclerosis, Hyperlipidemia, Coronary Artery Plaque",
        "keywords": ["chest heaviness", "cholesterol", "sluggishness", "breathlessness on exertion", "सीने में भारीपन", "मोटापा"],
        "dominant_dosha": "Kapha-Vata (Avalambaka Kapha & Medo Dhatu Dushti)",
        "prakriti_vikriti": "Kapha Medovaha Srotorodha",
        "agni_status": "Mandagni (Sluggish cellular metabolism)",
        "dhatu_affected": ["Medas (Fat tissue)", "Rasa", "Rakta"],
        "srotas_affected": ["Medovaha Srotas", "Rasavaha Srotas"],
        "clinical_presentation": "Heaviness over precordium, lethargy, expectoration, sluggish circulation, elevated lipid profile.",
        "classical_herbs_formulations": [
            "Guggulu formulations (Medohar Guggulu, Arogyavardhini Vati)",
            "Lekhaniya Mahakashaya",
            "Pushkarmula (Inula racemosa)",
            "Shilajit"
        ],
        "pathya": [
            "Yava (Barley)",
            "Madhu (Raw aged honey)",
            "Triphala Kashaya",
            "Takra (Spiced buttermilk with roasted cumin)"
        ],
        "apathya": [
            "Navanna (newly harvested grains)",
            "Dadhi (curds)",
            "Divaswapna (daytime sleep)",
            "Sedentary lifestyle (Alasya)"
        ],
        "classical_reference": "Ashtanga Hridaya, Nidana Sthana, Chapter 5 (Hridroga Nidana)",
        "source_dataset": "kagglekirti123/ayurgenixai-ayurvedic-dataset",
        "model_reference": "bharatgenai/AyurParam"
    },

    # -------------------------------------------------------------
    # ORTHOPEDICS & RHEUMATOLOGY (SANDHIVATA / AMAVATA / GRIDHRASI)
    # -------------------------------------------------------------
    {
        "id": "ayur_sandhivata_01",
        "category": "orthopedics",
        "ayurvedic_nidana": "Sandhigata Vata",
        "modern_correlation": "Osteoarthritis, Degenerative Joint Disease",
        "keywords": ["joint pain", "knee pain", "crepitus", "stiffness", "difficulty walking", "जोड़ों में दर्द", "घुटनों में दर्द", "कमर दर्द", "हड्डी"],
        "dominant_dosha": "Vata (Vyanavayu & Shleshaka Kapha Kshaya)",
        "prakriti_vikriti": "Vataja Asthivaha Srotodushti",
        "agni_status": "Vishama Agni (Irregular digestive fire)",
        "dhatu_affected": ["Asthi (Bone)", "Majja (Bone Marrow)", "Sandhi (Joint Cartilage)"],
        "srotas_affected": ["Asthivaha Srotas", "Majjavaha Srotas"],
        "clinical_presentation": "Joint pain on weight-bearing, crepitus (Vata Purna Driti Sparsha), swelling without active erythema, morning stiffness lasting < 30 minutes.",
        "classical_herbs_formulations": [
            "Yogaraj Guggulu",
            "Shallaki (Boswellia serrata)",
            "Rasnasaptaka Kwatha",
            "Dashamularishta",
            "Mahanarayana Taila (external Snehana & Janu Basti)"
        ],
        "pathya": [
            "Godhuma (Whole wheat)",
            "Ushnodaka (Warm water drinking)",
            "Eranda Taila (Castor oil) micro-dose at bedtime",
            "Ghee cooked with digestive herbs",
            "Sunthi (Dry ginger)"
        ],
        "apathya": [
            "Sheeta jala (Cold water baths and cold drinks)",
            "Vatala ahara (Dry, stale, cold, astringent food items)",
            "Dadhi (Curds) and sprouts in excess",
            "Excessive stair climbing and unpadded hard-floor walking"
        ],
        "classical_reference": "Charaka Samhita, Chikitsa Sthana, Chapter 28 (Vatavyadhi Chikitsa, Sloka 37)",
        "source_dataset": "kagglekirti123/ayurgenixai-ayurvedic-dataset",
        "model_reference": "bharatgenai/AyurParam"
    },
    {
        "id": "ayur_amavata_02",
        "category": "orthopedics",
        "ayurvedic_nidana": "Amavata",
        "modern_correlation": "Rheumatoid Arthritis, Inflammatory Polyarthritis",
        "keywords": ["joint swelling", "morning stiffness", "heat in joints", "symmetric pain", "जोड़ों में सूजन", "गठिया", "अकड़न"],
        "dominant_dosha": "Vata-Kapha with Ama Toxic Bio-accumulation",
        "prakriti_vikriti": "Amavata Srotorodha (Rasavaha & Asthivaha Srotas)",
        "agni_status": "Mandagni (Severely compromised digestive capacity)",
        "dhatu_affected": ["Rasa", "Asthi", "Majja"],
        "srotas_affected": ["Rasavaha Srotas", "Asthivaha Srotas"],
        "clinical_presentation": "Bilateral symmetrical joint swelling, intense morning stiffness (>1 hour), thirst, anorexia (Aruchi), body aches, feverish sensation (Jwara).",
        "classical_herbs_formulations": [
            "Simhanada Guggulu",
            "Amavatari Rasa",
            "Rasnadi Kwatha",
            "Vaishwanara Churna",
            "Valuka Sweda (Dry sand hot fermentation)"
        ],
        "pathya": [
            "Kulattha (Horse gram soup)",
            "Yava (Barley)",
            "Shunthi & Pippali (Ginger & Long Pepper)",
            "Patola (Pointed gourd), Karavellaka (Bitter gourd)"
        ],
        "apathya": [
            "Sneha / Taila massage in active inflammatory stage (Ama avastha)",
            "Dadhi (Curds), Milk, Fish, Sweets",
            "Purvavata (exposure to cold easterly breeze)",
            "Day sleeping (Divaswapna)"
        ],
        "classical_reference": "Madhava Nidana, Chapter 25 (Amavata Nidana, Sloka 1-10)",
        "source_dataset": "kagglekirti123/ayurgenixai-ayurvedic-dataset",
        "model_reference": "bharatgenai/AyurParam"
    },

    # -------------------------------------------------------------
    # NEUROLOGY & CEPHALALGIA (SHIROROGA / ARDHAVABHEDAKA)
    # -------------------------------------------------------------
    {
        "id": "ayur_shiroroga_01",
        "category": "neurology",
        "ayurvedic_nidana": "Ardhavabhedaka / Vata-Pittaja Shirashoola",
        "modern_correlation": "Migraine, Hemicephalic Cephalalgia, Tension Headache",
        "keywords": ["headache", "migraine", "throbbing head pain", "light sensitivity", "nausea with headache", "सिरदर्द", "आधा सीसी", "माइग्रेन", "माथा दर्द"],
        "dominant_dosha": "Vata-Pitta (Prana Vayu & Alochaka/Sadhaka Pitta)",
        "prakriti_vikriti": "Vata-Pitta Manovaha Srotodushti",
        "agni_status": "Tikshna / Vishama Agni",
        "dhatu_affected": ["Rakta", "Majja", "Rasa"],
        "srotas_affected": ["Manovaha Srotas", "Raktavaha Srotas"],
        "clinical_presentation": "Unilateral throbbing headache, photophobia, phonophobia, nausea, worsening with sunlight (Suryavarta) or skipping meals, relieved in dark quiet room.",
        "classical_herbs_formulations": [
            "Pathyadi Kwatha",
            "Shirashoolavajra Rasa",
            "Brahmi Vati",
            "Godanti Bhasma",
            "Ksheerabala 101 Taila (Nasya therapy & Shirodhara)"
        ],
        "pathya": [
            "Ghrita (Pure A2 Cow Ghee with meals)",
            "Godugdha (Warm milk at bedtime)",
            "Mudga (Mung bean soup)",
            "Shiroabhyanga (Gentle scalp massage)",
            "Adequate hydration with coconut water"
        ],
        "apathya": [
            "Ati-Aatapa (excessive exposure to direct sun and heat)",
            "Skipping meals or fasting irregularly (Anashana)",
            "Fermented, excessively spicy and sour foods",
            "Loud noise, digital screen glare late at night"
        ],
        "classical_reference": "Sushruta Samhita, Uttara Tantra, Chapter 25 (Shiroroga Pratishedha)",
        "source_dataset": "kagglekirti123/ayurgenixai-ayurvedic-dataset",
        "model_reference": "bharatgenai/AyurParam"
    },

    # -------------------------------------------------------------
    # GASTROENTEROLOGY (AMLAPITTA / GRAHANI / AGNIMANDYA)
    # -------------------------------------------------------------
    {
        "id": "ayur_amlapitta_01",
        "category": "gastroenterology",
        "ayurvedic_nidana": "Amlapitta / Vidagdhajirna",
        "modern_correlation": "Gastroesophageal Reflux Disease (GERD), Gastritis, Dyspepsia",
        "keywords": ["stomach pain", "acid reflux", "heartburn", "sour belching", "indigestion", "पेट दर्द", "एसिडिटी", "खट्टी डकार", "जलन"],
        "dominant_dosha": "Pitta (Pachaka Pitta with Drava & Amla Guna Vriddhi)",
        "prakriti_vikriti": "Pittaja Annavaha Srotodushti",
        "agni_status": "Tikshnagni / Mandagni with Vidagdha (Acidic fermentation)",
        "dhatu_affected": ["Rasa", "Rakta"],
        "srotas_affected": ["Annavaha Srotas", "Purishavaha Srotas"],
        "clinical_presentation": "Retrosternal burning (Hrit Kanthadaha), sour/bitter eructations (Amlodgara), epigastric discomfort, nausea, loss of appetite.",
        "classical_herbs_formulations": [
            "Avipattikar Churna",
            "Kamadudha Rasa (Mukta yukta)",
            "Sutshekhar Rasa",
            "Shatavari Churna",
            "Shankha Bhasma"
        ],
        "pathya": [
            "Takra (Fresh churned buttermilk with roasted cumin and coriander)",
            "Dadima (Pomegranate)",
            "Kushmanda (Ash gourd juice)",
            "Cold milk in small sips",
            "Purana Shali (Old aged rice)"
        ],
        "apathya": [
            "Katu (Chili, pepper), Amla (sour vinegar, pickles), Lavana (excess salt)",
            "Deep-fried snacks and fast food",
            "Viruddhahara (Incompatible foods like milk with citrus fruits)",
            "Alcohol, tobacco and carbonated beverages"
        ],
        "classical_reference": "Charaka Samhita, Chikitsa Sthana, Chapter 15 (Grahani Dosha Chikitsa)",
        "source_dataset": "kagglekirti123/ayurgenixai-ayurvedic-dataset",
        "model_reference": "bharatgenai/AyurParam"
    },

    # -------------------------------------------------------------
    # PULMONOLOGY & RESPIRATORY (TAMAKA SHWASA / KASA)
    # -------------------------------------------------------------
    {
        "id": "ayur_shwasa_01",
        "category": "pulmonology",
        "ayurvedic_nidana": "Tamaka Shwasa",
        "modern_correlation": "Bronchial Asthma, Reactive Airway Disease, Chronic Bronchitis",
        "keywords": ["breathlessness", "wheezing", "cough", "chest congestion", "सांस फूलना", "दमा", "खांसी", "कफ"],
        "dominant_dosha": "Vata-Kapha (Prana Vata obstructed by Avalambaka Kapha)",
        "prakriti_vikriti": "Pranavaha Srotorodha",
        "agni_status": "Mandagni",
        "dhatu_affected": ["Rasa", "Prana"],
        "srotas_affected": ["Pranavaha Srotas", "Udakovaha Srotas"],
        "clinical_presentation": "Paroxysmal dyspnea worsening at night or cloudy weather, wheezing (Ghurghuraka), productive cough with difficulty expectorating, relief upon sitting upright (Aasino Labhate Saukhyam).",
        "classical_herbs_formulations": [
            "Shwasakasa Chintamani Rasa",
            "Sitopaladi Churna with honey and ghee",
            "Talisadi Churna",
            "Kanakasava",
            "Vasa Avaleha (Adhatoda vasica)"
        ],
        "pathya": [
            "Ushnodaka (Warm drinking water strictly)",
            "Ardraka (Ginger) and Maricha (Black pepper) tea",
            "Laja Manda (Puffed rice water)",
            "Kulattha and Yava preparations"
        ],
        "apathya": [
            "Sheeta ahara (Cold refrigerated foods and chilled water)",
            "Milk and dairy products at dinner time",
            "Dust (Raja), Smoke (Dhuma), Cold breeze exposure",
            "Suppressing sneeze or cough urges"
        ],
        "classical_reference": "Charaka Samhita, Chikitsa Sthana, Chapter 17 (Hikka-Shwasa Chikitsa, Sloka 55-62)",
        "source_dataset": "kagglekirti123/ayurgenixai-ayurvedic-dataset",
        "model_reference": "bharatgenai/AyurParam"
    },

    # -------------------------------------------------------------
    # ENDOCRINE & METABOLIC (PRAMEHA / MEDOROGA)
    # -------------------------------------------------------------
    {
        "id": "ayur_prameha_01",
        "category": "general-medicine",
        "ayurvedic_nidana": "Kaphaja / Vataja Prameha",
        "modern_correlation": "Type 2 Diabetes Mellitus, Metabolic Syndrome",
        "keywords": ["frequent urination", "excessive thirst", "sweet urine", "fatigue", "बार-बार पेशाब", "शुगर", "मधुमेह", "कमजोरी"],
        "dominant_dosha": "Kapha-Vata with Bahu-Drava Shleshma & Medas Dushti",
        "prakriti_vikriti": "Medovaha & Mutravaha Srotodushti",
        "agni_status": "Mandagni (Tissue level metabolic impairment / Dhatwagni Mandya)",
        "dhatu_affected": ["Medas", "Mamsa", "Kleda", "Majja"],
        "srotas_affected": ["Medovaha Srotas", "Mutravaha Srotas"],
        "clinical_presentation": "Polyuria with turbid urine (Prabhuta Avila Mutrata), polydipsia, burning sensations in soles and palms (Kara-Pada Daha), lethargy, slow wound healing.",
        "classical_herbs_formulations": [
            "Nishamalaki Churna (Curcuma longa + Emblica officinalis)",
            "Chandraprabha Vati",
            "Vasantakusumakara Rasa",
            "Mehamudgara Bati",
            "Gudmar (Gymnema sylvestre)"
        ],
        "pathya": [
            "Yava (Barley) roti and porridge",
            "Karavellaka (Bitter gourd), Methi (Fenugreek)",
            "Amalaki (Indian gooseberry)",
            "Mudga (Green gram)",
            "Daily brisk walking (Vyayama)"
        ],
        "apathya": [
            "Guda (Jaggery), Sugar, Sweets, Pastries",
            "Navanna (New rice, potatoes, starchy tubers)",
            "Dadhi (Curds) and heavy cream",
            "Divaswapna (Daytime sleeping) and sedentary lifestyle (Asyasukh)"
        ],
        "classical_reference": "Charaka Samhita, Nidana Sthana, Chapter 4 (Prameha Nidana)",
        "source_dataset": "kagglekirti123/ayurgenixai-ayurvedic-dataset",
        "model_reference": "bharatgenai/AyurParam"
    },

    # -------------------------------------------------------------
    # MULTI-SYMPTOM COMPLEX (CHEST + JOINT PAIN INTEGRATION)
    # -------------------------------------------------------------
    {
        "id": "ayur_multi_chest_joint_01",
        "category": "cardiology",
        "ayurvedic_nidana": "Vata-Kaphaja Sannipata with Asthi & Rasavaha Srotorodha",
        "modern_correlation": "Cardio-Orthopedic Multi-System Presentation (e.g. Anginal symptoms co-existing with Osteoarticular degenerative pain)",
        "keywords": ["chest and joint pain", "chest pain and knee pain", "छाती और जोड़ों में दर्द", "सीने और घुटने में दर्द"],
        "dominant_dosha": "Tridoshaja / Vata-Pitta-Kapha with Vata Prominence",
        "prakriti_vikriti": "Prana-Vyana Vayu & Asthivaha Srotodushti",
        "agni_status": "Manda-Vishama Agni",
        "dhatu_affected": ["Rasa", "Rakta", "Asthi", "Majja"],
        "srotas_affected": ["Rasavaha Srotas", "Pranavaha Srotas", "Asthivaha Srotas"],
        "clinical_presentation": "Combined presentation of cardiovascular strain (substernal pressure, exertional breathlessness) with peripheral joint stiffness, knee tenderness, and generalized musculoskeletal fatigue.",
        "classical_herbs_formulations": [
            "Arjuna Ksheerapaka (for cardioprotection)",
            "Yogaraj Guggulu (for joint mobility and Vata pacification)",
            "Dashamula Kwatha (systemic anti-inflammatory and Vata regulator)",
            "Ashwagandha Churna (adaptogen and cardiac/musculoskeletal tonic)"
        ],
        "pathya": [
            "Warm freshly cooked light meals with mild spices (Cumin, Ginger, Coriander)",
            "Ushnodaka (Warm water)",
            "Pomegranate and soaked almonds",
            "Gentle joint mobilization without cardiac exertion"
        ],
        "apathya": [
            "Cold drinks, ice water, heavy fried meals",
            "Vigorous strain or heavy weightlifting",
            "Day sleep, suppression of urges, cold exposure"
        ],
        "classical_reference": "Charaka Samhita, Chikitsa Sthana, Chapter 28 (Vatavyadhi Chikitsa) & Chapter 26 (Trimarmiya)",
        "source_dataset": "kagglekirti123/ayurgenixai-ayurvedic-dataset",
        "model_reference": "bharatgenai/AyurParam"
    }
]
