# gemini_analyzer.py - Очищенная версия для медицинского анализа

import os
import json
import google.generativeai as genai
import asyncio
from PIL import Image
from typing import Tuple, List, Dict
from db_postgresql import t

GEMINI_TIMELINE_TIMEOUT = 60
GEMINI_IMAGE_TIMEOUT = 120

class GeminiMedicalAnalyzer:
    """Анализатор медицинских изображений через Gemini API"""
    
    def __init__(self):
        """Инициализация с API ключом"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY не найден в .env файле!")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-3-pro-preview')
        print("✅ Gemini 3 Pro Preview инициализирован")
    
    async def analyze_medical_image(self, image_path: str, lang: str = "ru", custom_prompt: str = None) -> Tuple[str, str]:
        try:
            if not os.path.exists(image_path):
                return "", t("gemini_file_not_found", lang, path=image_path)
            
            image = Image.open(image_path)
            prompt = custom_prompt or self._get_educational_prompt(lang)
            
            safety_settings = {
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            }
            
            response = await asyncio.wait_for(
                self.model.generate_content_async(
                    [prompt, image],
                    generation_config=genai.types.GenerationConfig(
                        temperature=1.0,
                        max_output_tokens=5000,
                        candidate_count=1
                    ),
                    safety_settings=safety_settings
                ),
                timeout=GEMINI_IMAGE_TIMEOUT
            )
            
            analysis_text = ""
            
            if hasattr(response, 'text') and response.text:
                analysis_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                if hasattr(candidate, 'finish_reason'):
                    if candidate.finish_reason == 2:  # SAFETY
                        alt_prompt = self._get_alternative_prompt(lang)
                        response = await asyncio.wait_for(
                            self.model.generate_content_async(
                                [alt_prompt, image],
                                generation_config=genai.types.GenerationConfig(
                                    temperature=1.0,
                                    max_output_tokens=3000,
                                    candidate_count=1
                                ),
                                safety_settings=safety_settings
                            ),
                            timeout=GEMINI_IMAGE_TIMEOUT
                        )
                        
                        if hasattr(response, 'text') and response.text:
                            analysis_text = response.text
                        else:
                            return "", t("gemini_safety_blocked", lang)
                            
                    elif candidate.finish_reason == 3:  # RECITATION
                        return "", t("gemini_copyright_violation", lang)
                
                if not analysis_text and hasattr(candidate, 'content') and candidate.content.parts:
                    try:
                        analysis_text = candidate.content.parts[0].text
                    except:
                        pass
            
            if not analysis_text:
                return "", t("gemini_no_analysis", lang)
            
            return analysis_text, ""

        except asyncio.TimeoutError:
            return "", t("gemini_temporary_error", lang, error="timeout")
            
        except Exception as e:
            error_msg = f"Ошибка Gemini: {str(e)}"
            if "finish_reason" in str(e) and "2" in str(e):
                return "", t("gemini_safety_policies", lang)
            elif "The `response.text`" in str(e):
                return "", t("gemini_processing_failed", lang)
            else:
                return "", t("gemini_temporary_error", lang, error=error_msg)
    
    def _get_educational_prompt(self, lang: str) -> str:
        """Простой медицинский промпт на английском с указанием языка ответа"""
        
        # Определяем язык ответа
        response_language = {
            "ru": "Russian",
            "uk": "Ukrainian", 
            "en": "English",
            "de": "German"
        }.get(lang, "Russian")
        
        return f"""You are an expert Cardiac Electrophysiologist. Your task is to perform a systematic analysis of the provided 12-lead ECG image.

        IMPORTANT: Please respond in {response_language} language.

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
        Clinical Conclusion: State the most likely interpretation. Note: If any abnormalities were found in previous steps, do not label the ECG as "Normal"; use "Nonspecific changes" or "Borderline ECG".
        Life-Threatening Red Flags: Immediately highlight if the pattern suggests ischemia, hyperkalemia, or unstable arrhythmia.
        Recommendations: Suggest the next step (e.g., "Check electrolytes", "Emergency cardioversion", "Compare with old ECG").
        DO NOT suggest specific medication names or dosages.

        IMPORTANT: Respond in {response_language} language."""

    def _get_alternative_prompt(self, lang: str) -> str:
        """Альтернативный более нейтральный промпт"""
        
        response_language = {
            "ru": "Russian",
            "uk": "Ukrainian", 
            "en": "English",
            "de": "German"  # ← ДОБАВЛЕНО
        }.get(lang, "Russian")
        
        return f"""Please describe what you observe in this image from an educational perspective. Focus on:

1. Technical aspects and image quality
2. Visible structures and patterns  
3. Any notable characteristics
4. Educational value for learning

This is for academic study purposes only.

IMPORTANT: Please respond in {response_language} language."""

# ✅ ОСНОВНАЯ ФУНКЦИЯ ДЛЯ ИСПОЛЬЗОВАНИЯ В ПРОЕКТЕ
async def send_to_gemini_vision(image_path: str, lang: str = "ru", prompt: str = None) -> Tuple[str, str]:
    """
    Основная функция для анализа медицинских изображений
    
    Args:
        image_path: Путь к изображению
        lang: Язык ответа (ru, uk, en)
        prompt: Кастомный промпт (если нужен)
        
    Returns:
        Tuple[analysis_result, error_message]
    """
    try:
        analyzer = GeminiMedicalAnalyzer()
        return await analyzer.analyze_medical_image(image_path, lang, prompt)
    except Exception as e:
        return "", t("gemini_image_analysis_error", lang, error=str(e))
    
async def extract_medical_timeline_gemini(document_text: str, existing_timeline: List[Dict], lang: str = "ru") -> List[Dict]:
    try:
        import google.generativeai as genai
        import os
        import asyncio

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return []
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        timeline_text = ""
        if existing_timeline:
            timeline_text = "\n".join([
                f"{entry['event_date']} | {entry['category']} | {entry['importance']} | \"{entry['description']}\""
                for entry in existing_timeline
            ])
        else:
            timeline_text = "Медкарта пустая"
        
        lang_names = {
            'ru': 'Russian',
            'uk': 'Ukrainian',
            'en': 'English',
            'de': 'German' 
        }
        response_lang = lang_names.get(lang, 'Russian')
        
        prompt = f"""You are a medical data extraction specialist. Extract key medical events from documents and update patient timeline.

TASK: Analyze the new document and update the medical timeline. Return ONLY changed/new entries or "NO_CHANGES".

RULES:
1. Extract dates from document text (if present) or use current date as fallback
2. Categories: diagnosis, treatment, test, procedure, general
3. Importance: critical (life-threatening), important (significant), normal (routine)  
4. Description: 10-20 words max, key medical facts only
5. If information duplicates existing timeline → DON'T add
6. If information updates existing entry → return updated version
7. Return ONLY valid JSON array or "NO_CHANGES"

OUTPUT FORMAT (JSON array):
[
  {{
    "event_date": "DD.MM.YYYY",
    "category": "ONE OF: diagnosis, treatment, test, procedure, general",
    "importance": "critical|important|normal", 
    "description": "Brief medical description"
  }}
]

EXISTING MEDICAL TIMELINE:
{timeline_text}

NEW DOCUMENT:
{document_text}

IMPORTANT: 
- Respond in {response_lang} language only
- Return ONLY JSON array or "NO_CHANGES" 
- NO explanations, NO additional text
- If no new medical information found, return "NO_CHANGES"

Extract and update medical timeline:"""

        response = await asyncio.wait_for(
            model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1500,
                    candidate_count=1
                ),
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_MEDICAL",
                        "threshold": "BLOCK_NONE"
                    }
                ]
            ),
            timeout=GEMINI_TIMELINE_TIMEOUT
        )
        
        if not response.candidates:
            return []
        
        result_text = ""
        for candidate in response.candidates:
            if hasattr(candidate, 'content') and candidate.content.parts:
                try:
                    result_text = candidate.content.parts[0].text.strip()
                    break
                except:
                    continue
        
        if not result_text:
            return []
        
        if result_text.upper() in ['NO_CHANGES', 'БЕЗ ИЗМЕНЕНИЙ', 'БЕЗ_ИЗМЕНЕНИЙ']:
            return []
        
        try:
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = result_text[json_start:json_end]
                events = json.loads(json_text)
                return events if isinstance(events, list) else []
            else:
                return []
                
        except json.JSONDecodeError:
            return []

    except asyncio.TimeoutError:
        from error_handler import log_error_with_context
        log_error_with_context(Exception(f"Gemini timeline timeout after {GEMINI_TIMELINE_TIMEOUT}s"), {"function": "extract_medical_timeline_gemini"})
        return []
        
    except Exception as e:
        from error_handler import log_error_with_context
        log_error_with_context(e, {"function": "extract_medical_timeline_gemini"})
        return []