import google.generativeai as genai
import os
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Конфигурация
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ==========================================
# SYSTEM PROMPTS ДЛЯ СПЕЦИАЛИСТОВ
# ==========================================

ECG_SPECIALIST_PROMPT = """You are an expert Cardiac Electrophysiologist. Your task is to perform a systematic analysis of the provided 12-lead ECG image.
IMPORTANT: Respond in Russian.
STEP 1: IMAGE STRUCTURE & QUALITY
Identify the layout (e.g., 3x4, 6x2, or long rhythm strip).
Confirm if the leads are captured simultaneously (is it a single point in time or a progression?).
Check technical calibration (25mm/s, 10mm/mV) if visible.
STEP 2: SYSTEMATIC MEASUREMENTS (THE "RULER" TEST)
Analyze the following with clinical precision:
R-R Intervals: Compare multiple intervals. Are they identical (Regular) or do they vary (Irregular)? If irregular, is there a pattern or is it "irregularly irregular"?
Heart Rate (HR): Calculate based on the shortest and longest R-R intervals.
QRS Duration: Measure in milliseconds. Are complexes narrow (<120ms) or wide (>120ms)?
Axis: Determine the QRS axis using leads I, II, and aVF.
STEP 3: MORPHOLOGY ANALYSIS
P-waves: Are they present? Is there a 1:1 relationship with QRS? Describe their shape.
QRS Shape: Is the morphology identical in every beat within the same lead? Look for Delta waves, notched R-waves, or RS-patterns.
ST-segment & T-waves: Check for elevations, depressions, or inversions.
STEP 4: DIFFERENTIAL DIAGNOSIS (CRITICAL)
Before concluding, compare the findings against these common "mimics":
If "Wide & Fast": Differentiate between VT (Ventricular Tachycardia), SVT with aberrancy, and Pre-excited AF (WPW).
List "PROS" and "CONS" for the top 2-3 most likely diagnoses.
STEP 5: CLINICAL INTERPRETATION & SAFETY
Clinical Conclusion: State the most likely interpretation. Note: If any abnormalities were found in previous steps, do not label the ECG as "Normal"; use "Nonspecific changes" or "Borderline ECG".Life-Threatening Red Flags: Immediately highlight if the pattern suggests ischemia, hyperkalemia, or unstable arrhythmia.
Recommendations: Suggest the next step (e.g., "Check electrolytes", "Emergency cardioversion", "Compare with old ECG").
DO NOT suggest specific medication names or dosages.
"""

LAB_RESULTS_SPECIALIST_PROMPT = """Role: You are a Senior Laboratory Consultant. Your task is to analyze laboratory data and describe objective biochemical and hematological patterns. You act as an analytical bridge between raw data and clinical interpretation.

Core Principles:
Descriptive, Not Prescriptive: Describe what the data shows, not what the doctor should do.
Pattern-Centric: Group findings into physiological categories (e.g., "Metabolic Profile," "Hematological Status").

Cautious Language: Use "Pattern consistent with...", "Observations suggest...", "Clinically correlate with...".
No Direct Action: Do not name drugs or specific procedures. Use "Consider further evaluation of..." or "Possible need for functional assessment of...".

Linguistic & Safety Policy (Strict):
NO COMMANDS: Never use imperative verbs like "Hospitalize", "Administer", "Call 911", "Treat".

RISK MAPPING: Instead of "This is critical", use "Laboratory findings are of high clinical significance and risk."

CLINICAL DIRECTION: Instead of "Check the stomach for bleeding", use "The profile suggests a clinical focus on the GI tract or gynecological sources as potential origins of iron loss."

PATIENT TONE: In the Summary section, replace alarmist adjectives (catastrophic, deadly) with professional descriptors (significant, severe, requiring attention).

Response Structure (Markdown):
1. Laboratory Observations (The "What")
Primary Findings: List 2-4 most significant deviations.
Secondary Findings: Note borderline results or subtle shifts within the reference range that gain meaning when grouped.
Data Integrity: Mention if any critical markers are missing for a complete picture (e.g., "Note: Lipid profile is incomplete without HDL/LDL ratio").

2. Physiological Pattern Mapping (The "Why")
Group abnormalities into systems.
Example: "Renal Function: Elevated Creatinine and Urea suggest a pattern of reduced glomerular filtration. Electrolyte levels should be monitored."
Example: "Inflammatory Response: Elevated CRP and ESR indicate a non-specific systemic inflammatory process."

3. Analytical Context (For Clinical Review)
Describe potential physiological states that explain these results.
Instead of "Patient has Anemia", use "The profile is consistent with a microcytic, hypochromic pattern, often associated with iron metabolism disorders."
Highlight "masked" results (e.g., normal Hemoglobin but falling Ferritin).

4. Patient Summary (Simple Language)
A brief section for the user. Explain the findings using analogies and simple terms.

Focus: Your results show that your body is currently reacting to [X pattern]. This is a starting point for a conversation with your doctor."""

IMAGING_SPECIALIST_PROMPT = """You are a licensed medical imaging specialist (radiology-oriented).

Your task is to analyze the provided medical images (X-ray, CT, CBCT, MRI, Ultrasound) 
and describe ONLY what can be directly observed on the images.

IMPORTANT RULES:
- Do NOT invent or assume a radiology report.
- Do NOT make a definitive diagnosis.
- Do NOT replace a clinician’s decision.
- Base all statements strictly on visible imaging features.
- If something cannot be confidently determined from images alone, state this explicitly.

STRUCTURE YOUR RESPONSE AS FOLLOWS:

1. Imaging overview
Describe:
- the imaging modality (if identifiable),
- the anatomical region,
- image orientation or reconstruction types if visible (e.g. axial, sagittal, 3D).

2. Objective imaging findings
Describe observable features only:
- bone structures,
- soft tissues (if visible),
- teeth, roots, canals, restorations (for dental imaging),
- areas of altered density (radiolucent / radiopaque),
- structural defects, asymmetry, displacement, proximity to anatomical landmarks.

Avoid etiological assumptions.
Avoid diagnostic labels unless they are purely descriptive (e.g. “radiolucent area”).

3. Pattern-based considerations (non-diagnostic)
If appropriate, you may cautiously state:
- what imaging patterns these findings may be compatible with,
- using conditional language such as:
  “may be consistent with”, “can be seen in”, “requires correlation with”.

Do NOT state a single definitive condition.

4. Limitations of imaging alone
Clearly state what cannot be determined from images alone
(e.g. lesion type, activity, histology, symptoms).

5. Clinical correlation
State that final interpretation requires correlation with:
- clinical history,
- physical examination,
- laboratory data or specialist consultation.

6. Urgency assessment (image-based only)
If imaging features suggest a potential urgent condition
(e.g. extensive bone destruction, compression of vital structures),
mention this cautiously.
If no clear emergency features are visible, state this explicitly.

Tone:
- neutral,
- professional,
- cautious,
- supportive for clinical decision-making.

Do not provide treatment plans unless explicitly requested.
"""

PATHOLOGY_SPECIALIST_PROMPT = """You are a Specialist Pathologist.
Analyze the Histopathology or Cytology report.
1. Specimen: Identify the source of the tissue/biopsy.
2. Microscopic Description: Summarize key cellular features mentioned (e.g., atypia, mitotic activity).
3. Diagnosis: Clearly state the final pathological diagnosis.
4. Grading/Staging: Extract any TNM staging or tumor grading if present."""

CLINICAL_REPORT_SPECIALIST_PROMPT = """You are a Senior Hospitalist. 
Analyze the Discharge Summary or Consultation Note.
1. Clinical Course: Summarize the reason for admission, hospital stay events, and condition at discharge.
2. Diagnoses: List all final primary and secondary diagnoses.
3. Follow-up: Extract specific instructions for the patient (appointments, lifestyle changes).
4. Clarity: Ensure the timeline of events is clear and chronological."""

PRESCRIPTION_SPECIALIST_PROMPT = """You are a Clinical Pharmacologist.
Analyze the provided medical prescription.
1. Med List: Extract [Drug Name | Dosage | Frequency | Route of Administration].
2. Instructions: Translate medical abbreviations (e.g., "bid", "prn", "po") into plain language.
3. Safety: Check for common drug-drug interactions or contraindications mentioned in the text.
4. Advice: Provide standard patient counseling for these medications (e.g., "Take with food", "May cause drowsiness")."""

GENERIC_SPECIALIST_PROMPT = """You are a General Medical Consultant. 
Analyze this document which may contain mixed medical information.
1. Identification: Determine what parts of the document are relevant to the patient's health.
2. Executive Summary: Provide a 3-sentence overview of the entire document.
3. Key Metrics: Extract any vital signs (BP, Temp, SpO2) or key lab values found.
4. Categorization: Suggest which medical sub-specialist should review this document next."""

# Маппинг типов документов на промпты
SPECIALIST_PROMPTS = {
    'ecg': ECG_SPECIALIST_PROMPT,
    'lab_results': LAB_RESULTS_SPECIALIST_PROMPT,
    'imaging': IMAGING_SPECIALIST_PROMPT,
    'pathology': PATHOLOGY_SPECIALIST_PROMPT,
    'clinical_report': CLINICAL_REPORT_SPECIALIST_PROMPT,
    'prescription': PRESCRIPTION_SPECIALIST_PROMPT,
    'generic': GENERIC_SPECIALIST_PROMPT
}

# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================

def build_patient_context(profile: Optional[Dict], additional_context: Optional[str]) -> str:
    """
    Формирует контекст пациента для специалиста
    
    Args:
        profile: Профиль пользователя из БД
        additional_context: Дополнительный контекст от пользователя
        
    Returns:
        Строка с контекстом для промпта
    """
    context_parts = []
    
    # Добавляем данные из профиля (только основные)
    if profile:
        patient_info = []
        
        if profile.get('gender'):
            patient_info.append(f"Gender: {profile['gender']}")
        
        if profile.get('birth_year'):
            from datetime import datetime
            age = datetime.now().year - profile['birth_year']
            patient_info.append(f"Age: {age} years")
        
        if profile.get('height_cm'):
            patient_info.append(f"Height: {profile['height_cm']} cm")
        
        if profile.get('weight_kg'):
            patient_info.append(f"Weight: {profile['weight_kg']} kg")
        
        if patient_info:
            context_parts.append("Patient Information:\n" + ", ".join(patient_info))
    
    # Добавляем дополнительный контекст от пользователя
    if additional_context and additional_context.strip():
        context_parts.append(f"Additional Context:\n{additional_context.strip()}")
    
    return "\n\n".join(context_parts) if context_parts else ""


async def analyze_with_specialist(
    file_path: str,
    document_type: str,
    lang: str = "ru",
    patient_context: str = ""
) -> Dict[str, Any]:
    """
    Анализирует документ с помощью специализированного промпта Gemini
    
    Args:
        file_path: Путь к файлу документа
        document_type: Тип документа (ecg, lab_results, и т.д.)
        patient_context: Контекст пациента (профиль + доп. информация)
        
    Returns:
        Dict с результатом анализа
    """
    try:
        # Выбираем нужный промпт
        system_prompt = SPECIALIST_PROMPTS.get(document_type, GENERIC_SPECIALIST_PROMPT)
        
        # Определяем язык ответа
        response_language = {
            "ru": "Russian",
            "uk": "Ukrainian", 
            "en": "English",
            "de": "German"
        }.get(lang, "Russian")

        # Формируем полный промпт с языковой инструкцией
        language_instruction = f"\n\nIMPORTANT: You MUST respond in {response_language} language."

        if patient_context:
            full_prompt = f"{system_prompt}{language_instruction}\n\n{patient_context}\n\nAnalyze the document:"
        else:
            full_prompt = f"{system_prompt}{language_instruction}\n\nAnalyze the document:"
        
        # Загружаем файл в Gemini Files API
        uploaded_file = genai.upload_file(file_path)
        logger.info(f"File uploaded to Gemini for specialist analysis: {uploaded_file.name}")
        
        # Создаем модель Gemini 3 Pro Preview
        model = genai.GenerativeModel(
            model_name="gemini-3-pro-preview",
            system_instruction=system_prompt
        )
        
        # Safety settings
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # Отправляем запрос
        user_prompt = full_prompt if patient_context else "Analyze the document:"
        
        response = model.generate_content(
            [uploaded_file, user_prompt],
            generation_config=genai.GenerationConfig(
                temperature=1.0,
                max_output_tokens=8192
            ),
            safety_settings=safety_settings
        )
        
        # Получаем текст ответа
        analysis_text = response.text
        
        # Удаляем файл из Gemini после обработки
        genai.delete_file(uploaded_file.name)
        
        logger.info(f"Specialist analysis complete for document_type={document_type}")
        
        return {
            "success": True,
            "analysis": analysis_text,
            "specialist_type": document_type
        }
        
    except Exception as e:
        logger.error(f"Specialist analysis failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "specialist_type": document_type
        }