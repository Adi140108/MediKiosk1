// MediKiosk Multilingual Translation Dictionary (i18n)
const TRANSLATIONS = {
  en: {
    safety_notice: 'Safety Notice: MediKiosk does not diagnose conditions or prescribe medications. Your healthcare provider reviews all information.',
    physician_in_loop: 'Physician-in-the-Loop',
    how_it_works: 'How does this work?',
    brand_tagline: 'Traditional Wisdom. Modern Care.',
    kiosk_tab: 'Patient Kiosk',
    physician_tab: 'Physician Portal',
    speech_ready: 'Speech-to-Speech Ready',
    hero_title: 'Your Intelligent Clinical Check-In.',
    hero_sub: 'Complete your pre-consultation intake before you see your doctor. MediKiosk collects your symptoms using AI and hands-free voice — in your language.',
    begin_checkin: 'Begin Check-In',
    secure_private: 'Secure and Private',
    secure_sub: 'All information is encrypted and securely transmitted directly to your physician.',
    step_lang_title: 'Select Language',
    step_lang_sub: 'Choose your preferred language for voice and text intake',
    step_consent_title: 'Patient Consent and Privacy Notice',
    step_consent_sub: 'Ayushman Bharat Digital Mission (ABDM) Compliance',
    consent_body: 'By proceeding, you consent to MediKiosk processing your health symptoms and medical documents using AI to prepare a clinical summary for your attending physician. MediKiosk does not replace medical advice.',
    consent_agree: 'I understand and agree to the clinical intake terms',
    continue_btn: 'Continue',
    step_patient_title: 'Patient Details',
    step_patient_sub: 'Enter your identification or Ayushman Bharat Health Account (ABHA)',
    full_name: 'Full Name',
    age: 'Age',
    gender: 'Gender',
    phone: 'Phone Number',
    abha_id: 'ABHA ID (Ayushman Bharat Health Account)',
    attendant_toggle: 'Attendant / Family Member Assisting Patient',
    attendant_name: 'Attendant Name',
    attendant_phone: 'Attendant Phone',
    relationship: 'Relationship to Patient',
    step_complaint_title: 'Chief Health Complaint',
    step_complaint_sub: 'What brings you to the clinic today?',
    complaint_placeholder: 'e.g. Severe headache for 3 days and occasional chest tightness',
    pain_level: 'Symptom Severity / Pain Level (1-10)',
    quick_tags: 'Common Symptoms:',
    step_docs_title: 'Previous Medical Documents and Prescriptions',
    step_docs_sub: 'Upload previous prescriptions, discharge summaries, or lab reports (Images -> Cloudinary, PDFs -> Backblaze B2)',
    upload_doc_btn: 'Upload and Run OCR',
    skip_docs: 'Skip Document Upload',
    step_intake_title: 'AI Clinical Intake Interview',
    step_intake_sub: 'Powered by Gemma 4 12B and AI4Bharat',
    listen_btn: 'Speak Question',
    mic_speak_btn: 'Tap to Speak Answer',
    mic_listening: 'Listening... Speak now',
    answer_placeholder: 'Type your answer or use microphone...',
    submit_answer: 'Submit Answer',
    step_summary_title: 'Intake Complete — Case Triage Summary',
    step_summary_sub: 'Your case has been summarized and routed to your physician.',
    ticket_num: 'Consultation Ticket #',
    rec_dept: 'Recommended Department:',
    triage_priority: 'Triage Priority:',
    chief_complaint_summary: 'Chief Complaint Summary:',
    start_new: 'Start New Patient Intake',
    doctor_review_queue: 'Doctor Review Queue',
    fire_synced: 'Firestore synced',
    search_patient: 'Search patient by name or ID...',
    all_severities: 'All Severities',
    critical_only: 'Critical Only',
    high_only: 'High Only',
    medium_only: 'Medium Only',
    stable_only: 'Stable Only',
    ocr_evidence_title: 'Document Evidence Traceability',
    confirm_record: 'Confirm Clinical Record',
    back_to_queue: 'Back to Queue',
    back_to_dept: 'Switch Department'
  },
  hi: {
    safety_notice: 'सुरक्षा सूचना: मेडीकियोस्क बीमारियों का निदान या दवाएं नहीं लिखता है। आपके चिकित्सक सभी जानकारी की समीक्षा करते हैं।',
    physician_in_loop: 'चिकित्सक की निगरानी में',
    how_it_works: 'यह कैसे काम करता है?',
    brand_tagline: 'पारंपरिक ज्ञान। आधुनिक देखभाल।',
    kiosk_tab: 'मरीज़ कियोस्क',
    physician_tab: 'डॉक्टर पोर्टल',
    speech_ready: 'आवाज़ और स्पीच तैयार',
    hero_title: 'आपका बुद्धिमान क्लिनिकल चेक-इन।',
    hero_sub: 'डॉक्टर से मिलने से पहले अपनी जांच पूरी करें। मेडीकियोस्क आपकी भाषा में एआई और आवाज़ द्वारा लक्षणों को समझता है।',
    begin_checkin: 'चेक-इन शुरू करें',
    secure_private: 'सुरक्षित एवं गोपनीय',
    secure_sub: 'सभी जानकारी सुरक्षित रूप से सीधे आपके डॉक्टर को भेजी जाती है।',
    step_lang_title: 'भाषा चुनें',
    step_lang_sub: 'अपनी पसंदीदा भाषा चुनें',
    step_consent_title: 'मरीज़ की सहमति एवं गोपनीयता',
    step_consent_sub: 'आयुष्मान भारत डिजिटल मिशन (ABDM) अनुपालन',
    consent_body: 'आगे बढ़कर, आप अपने डॉक्टर के लिए क्लिनिकल सारांश तैयार करने हेतु मेडीकियोस्क को अपने लक्षणों का विश्लेषण करने की सहमति देते हैं।',
    consent_agree: 'मैं नियमों और शर्तों से सहमत हूँ',
    continue_btn: 'आगे बढ़ें',
    step_patient_title: 'मरीज़ की जानकारी',
    step_patient_sub: 'अपना विवरण या आभा (ABHA) आईडी दर्ज करें',
    full_name: 'पूरा नाम',
    age: 'उम्र',
    gender: 'लिंग',
    phone: 'फ़ोन नंबर',
    abha_id: 'आभा आईडी (ABHA ID)',
    attendant_toggle: 'मरीज़ के साथ सहायक / परिजन मौजूद हैं',
    attendant_name: 'सहायक का नाम',
    attendant_phone: 'सहायक का फ़ोन',
    relationship: 'मरीज़ से संबंध',
    step_complaint_title: 'मुख्य स्वास्थ्य समस्या',
    step_complaint_sub: 'आज आप अस्पताल किस कारण आए हैं?',
    complaint_placeholder: 'उदा. 3 दिनों से तेज़ सिरदर्द और सीने में भारीपन',
    pain_level: 'दर्द / समस्या की गंभीरता (1-10)',
    quick_tags: 'सामान्य लक्षण:',
    step_docs_title: 'पुराने मेडिकल दस्तावेज़ व पर्चियां',
    step_docs_sub: 'अपनी पुरानी पर्चियां, डिस्चार्ज सारांश या जांच रिपोर्ट अपलोड करें',
    upload_doc_btn: 'अपलोड करें और ओसीआर चलाएं',
    skip_docs: 'दस्तावेज़ छोड़ें',
    step_intake_title: 'एआई क्लिनिकल बातचीत',
    step_intake_sub: 'जेम्मा 4 12B और AI4Bharat द्वारा संचालित',
    listen_btn: 'प्रश्न सुनें',
    mic_speak_btn: 'बोलकर उत्तर दें',
    mic_listening: 'सुन रहा हूँ... अब बोलें',
    answer_placeholder: 'उत्तर लिखें या माइक दबाकर बोलें...',
    submit_answer: 'उत्तर भेजें',
    step_summary_title: 'जांच पूरी — केस सारांश',
    step_summary_sub: 'आपकी जानकारी आपके डॉक्टर को भेज दी गई है।',
    ticket_num: 'परामर्श टोकन #',
    rec_dept: 'अनुशंसित विभाग:',
    triage_priority: 'प्राथमिकता:',
    chief_complaint_summary: 'मुख्य लक्षण सारांश:',
    start_new: 'नया मरीज़ चेक-इन करें',
    doctor_review_queue: 'डॉक्टर समीक्षा सूची',
    fire_synced: 'फायरस्टोर सिंक',
    search_patient: 'मरीज़ का नाम या आईडी खोजें...',
    all_severities: 'सभी प्राथमिकताएं',
    critical_only: 'अति गंभीर (Critical)',
    high_only: 'उच्च प्राथमिकता (High)',
    medium_only: 'मध्यम (Medium)',
    stable_only: 'सामान्य (Stable)',
    ocr_evidence_title: 'दस्तावेज़ साक्ष्य व ओसीआर विवरण',
    confirm_record: 'रिकॉर्ड सत्यापित करें',
    back_to_queue: 'सूची पर वापस जाएं',
    back_to_dept: 'विभाग बदलें'
  },
  kn: {
    safety_notice: 'ಸುರಕ್ಷತಾ ಸೂಚನೆ: ಮೆಡಿಕಿಯೋಸ್ಕ್ ರೋಗನಿರ್ಣಯ ಮಾಡುವುದಿಲ್ಲ. ನಿಮ್ಮ ವೈದ್ಯರು ಎಲ್ಲಾ ಮಾಹಿತಿಯನ್ನು ಪರಿಶೀಲಿಸುತ್ತಾರೆ.',
    physician_in_loop: 'ವೈದ್ಯರ ಮೇಲ್ವಿಚಾರಣೆಯಲ್ಲಿ',
    brand_tagline: 'ಸಾಂಪ್ರದಾಯಿಕ ಜ್ಞಾನ. ಆಧುನಿಕ ಆರೈಕೆ.',
    kiosk_tab: 'ರೋಗಿ ಕಿಯೋಸ್ಕ್',
    physician_tab: 'ವೈದ್ಯರ ಪೋರ್ಟಲ್',
    hero_title: 'ನಿಮ್ಮ ಬುದ್ಧಿವಂತ ಕ್ಲಿನಿಕಲ್ ಚೆಕ್-ಇನ್.',
    hero_sub: 'ವೈದ್ಯರನ್ನು ಭೇಟಿಯಾಗುವ ಮೊದಲು ನಿಮ್ಮ ರೋಗಲಕ್ಷಣಗಳ ವಿವರಗಳನ್ನು ಧ್ವನಿಯ ಮೂಲಕ ಸುಲಭವಾಗಿ ನೀಡಿ.',
    begin_checkin: 'ಚೆಕ್-ಇನ್ ಪ್ರಾರಂಭಿಸಿ',
    step_lang_title: 'ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
    step_patient_title: 'ರೋಗಿಯ ವಿವರಗಳು',
    full_name: 'ಪೂರ್ಣ ಹೆಸರು',
    age: 'ವಯಸ್ಸು',
    gender: 'ಲಿಂಗ',
    continue_btn: 'ಮುಂದುವರಿಯಿರಿ',
    submit_answer: 'ಉತ್ತರ ಸಲ್ಲಿಸಿ',
    step_summary_title: 'ಪೂರ್ಣಗೊಂಡಿದೆ — ಕೇಸ್ ಸಾರಾಂಶ'
  },
  ta: {
    safety_notice: 'பாதுகாப்பு அறிவிப்பு: மெடிகியோஸ்க் மருந்துகளை பரிந்துரைக்காது. உங்கள் மருத்துவர் அனைத்து தகவல்களையும் மதிப்பாய்வு செய்வார்.',
    physician_in_loop: 'மருத்துவர் மேற்பார்வையில்',
    brand_tagline: 'பாரம்பரிய அறிவு. நவீன சிகிச்சை.',
    kiosk_tab: 'நோயாளி கியோஸ்க்',
    physician_tab: 'மருத்துவர் போர்ட்டல்',
    hero_title: 'உங்கள் அறிவார்ந்த மருத்துவ செக்-இன்.',
    hero_sub: 'மருத்துவரை சந்திக்கும் முன் உங்கள் அறிகுறிகளை குரல் மூலம் உங்கள் மொழியிலேயே பதிவு செய்யுங்கள்.',
    begin_checkin: 'செக்-இன் தொடங்கு',
    step_lang_title: 'மொழியைத் தேர்ந்தெடுக்கவும்',
    step_patient_title: 'நோயாளி விவரங்கள்',
    full_name: 'முழு பெயர்',
    age: 'வயது',
    gender: 'பாலினம்',
    continue_btn: 'தொடரவும்',
    submit_answer: 'பதிலை சமர்ப்பிக்கவும்',
    step_summary_title: 'முடிந்தது — வழக்கு சுருக்கம்'
  },
  te: {
    safety_notice: 'భద్రతా నోటీసు: మెడికియోస్క్ వ్యాధిని నిర్ధారించదు. మీ వైద్యులు మొత్తం సమాచారాన్ని సమీక్షిస్తారు.',
    physician_in_loop: 'వైద్యుల పర్యవేక్షణలో',
    brand_tagline: 'సాంప్రదాయ జ్ఞానం. ఆధునిక సంరక్షణ.',
    kiosk_tab: 'రోగి కియోస్క్',
    physician_tab: 'డాక్టర్ పోర్టల్',
    hero_title: 'మీ తెలివైన క్లినికల్ చెక్-ఇన్.',
    hero_sub: 'డాక్టర్‌ను కలిసే ముందు మీ ఆరోగ్య లక్షణాలను మీ భాషలోనే సులభంగా తెలియజేయండి.',
    begin_checkin: 'చెక్-ఇన్ ప్రారంభించండి',
    step_lang_title: 'భాషను ఎంచుకోండి',
    step_patient_title: 'రోగి వివరాలు',
    full_name: 'పూర్తి పేరు',
    age: 'వయస్సు',
    gender: 'లింగం',
    continue_btn: 'కొనసాగించండి',
    submit_answer: 'సమాధానం సమర్పించండి',
    step_summary_title: 'పూర్తయింది — సారాంశం'
  },
  ml: {
    safety_notice: 'സുരക്ഷാ അറിയിപ്പ്: മെഡികിയോസ്ക് രോഗനിർണയം നടത്തുന്നില്ല. നിങ്ങളുടെ ഡോക്ടർ എല്ലാ വിവരങ്ങളും പരിശോധിക്കുന്നു.',
    physician_in_loop: 'ഡോക്ടറുടെ മേൽനോട്ടത്തിൽ',
    brand_tagline: 'പാരമ്പര്യ ജ്ഞാനം. ആധുനിക പരിചരണം.',
    kiosk_tab: 'രോഗി കിയോസ്ക്',
    physician_tab: 'ഡോക്ടർ പോർട്ടൽ',
    hero_title: 'നിങ്ങളുടെ സ്മാർട്ട് ക്ലിനിക്കൽ ചെക്ക്-ഇൻ.',
    begin_checkin: 'ചെക്ക്-ഇൻ ആരംഭിക്കുക',
    step_lang_title: 'ഭാഷ തിരഞ്ഞെടുക്കുക',
    step_patient_title: 'രോഗിയുടെ വിവരങ്ങൾ',
    continue_btn: 'തുടരുക'
  },
  mr: {
    safety_notice: 'सुरक्षा सूचना: मेडीकियोस्क आजाराचे निदान करत नाही. आपले डॉक्टर सर्व माहिती तपासतात.',
    physician_in_loop: 'डॉक्टरांच्या देखरेखीखाली',
    brand_tagline: 'पारंपारिक ज्ञान. आधुनिक काळजी.',
    kiosk_tab: 'रुग्ण किऑस्क',
    physician_tab: 'डॉक्टर पोर्टल',
    hero_title: 'आपले इंटेलिजंट क्लिनिकल चेक-इन.',
    begin_checkin: 'चेक-इन सुरू करा',
    step_lang_title: 'भाषा निवडा',
    step_patient_title: 'रुग्णाची माहिती',
    continue_btn: 'पुढे जा'
  },
  bn: {
    safety_notice: 'সুরক্ষা বিজ্ঞপ্তি: মেডিকিওস্ক রোগ নির্ণয় করে না। আপনার ডাক্তার সমস্ত তথ্য পর্যালোচনা করবেন।',
    physician_in_loop: 'চিকিৎসকের তত্ত্বাবধানে',
    brand_tagline: 'ঐতিহ্যবাহী জ্ঞান। আধুনিক যত্ন।',
    kiosk_tab: 'রোগী কিয়স্ক',
    physician_tab: 'ডাক্তার পোর্টাল',
    hero_title: 'আপনার ইন্টেলিজেন্ট ক্লিনিকাল চেক-ইন।',
    begin_checkin: 'চেক-ইন শুরু করুন',
    step_lang_title: 'ভাষা নির্বাচন করুন',
    step_patient_title: 'রোগীর বিবরণ',
    continue_btn: 'এগিয়ে যান'
  },
  gu: {
    safety_notice: 'સુરક્ષા સૂચના: મેડિકિયોસ્ક નિદાન કરતું નથી. તમારા ડૉક્ટર બધી માહિતીની સમીક્ષા કરે છે.',
    physician_in_loop: 'તબીબી દેખરેખ હેઠળ',
    brand_tagline: 'પરંપરાગત જ્ઞાન. આધુનિક સંભાળ.',
    kiosk_tab: 'દર્દી કિઓસ્ક',
    physician_tab: 'ડૉક્ટર પોર્ટલ',
    hero_title: 'તમારું ઇન્ટેલિજન્ટ ક્લિનિકલ ચેક-ઇન.',
    begin_checkin: 'ચેક-ઇન શરૂ કરો',
    step_lang_title: 'ભાષા પસંદ કરો',
    step_patient_title: 'દર્દીની વિગતો',
    continue_btn: 'આગળ વધો'
  },
  pa: {
    safety_notice: 'ਸੁਰੱਖਿਆ ਨੋਟਿਸ: ਮੈਡੀਕਿਓਸਕ ਬਿਮਾਰੀ ਦਾ ਨਿਦਾਨ ਨਹੀਂ ਕਰਦਾ। ਤੁਹਾਡੇ ਡਾਕਟਰ ਸਾਰੀ ਜਾਣਕਾਰੀ ਦੀ ਜਾਂਚ ਕਰਦੇ ਹਨ।',
    physician_in_loop: 'ਡਾਕਟਰ ਦੀ ਨਿਗਰਾਨੀ ਹੇਠ',
    brand_tagline: 'ਰਵਾਇਤੀ ਗਿਆਨ। ਆਧੁਨਿਕ ਦੇਖਭਾਲ।',
    kiosk_tab: 'ਮਰੀਜ਼ ਕਿਓਸਕ',
    physician_tab: 'ਡਾਕਟਰ ਪੋਰਟਲ',
    hero_title: 'ਤੁਹਾਡਾ ਇੰਟੈਲੀਜੈਂਟ ਕਲੀਨਿਕਲ ਚੈੱਕ-ਇਨ।',
    begin_checkin: 'ਚੈੱਕ-ਇਨ ਸ਼ੁਰੂ ਕਰੋ',
    step_lang_title: 'ਭਾਸ਼ਾ ਚੁਣੋ',
    step_patient_title: 'ਮਰੀਜ਼ ਦੇ ਵੇਰਵੇ',
    continue_btn: 'ਅੱਗੇ ਵਧੋ'
  }
};

const I18n = {
  currentLang: 'en',

  t(key) {
    const langObj = TRANSLATIONS[this.currentLang] || TRANSLATIONS.en;
    return langObj[key] || TRANSLATIONS.en[key] || key;
  },

  setLanguage(lang) {
    if (!TRANSLATIONS[lang]) lang = 'en';
    this.currentLang = lang;
    document.documentElement.lang = lang;

    // Update all elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      const val = this.t(key);
      if (val) el.innerText = val;
    });

    // Update all placeholders with data-i18n-ph
    document.querySelectorAll('[data-i18n-ph]').forEach((el) => {
      const key = el.getAttribute('data-i18n-ph');
      const val = this.t(key);
      if (val) el.placeholder = val;
    });

    // Update current active language badge in header
    const langBadge = document.getElementById('current-lang-pill');
    if (langBadge) {
      langBadge.innerText = lang.toUpperCase();
    }
  }
};
