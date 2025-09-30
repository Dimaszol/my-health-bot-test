# gemini_analyzer.py - Очищенная версия для медицинского анализа

import os
import json
import google.generativeai as genai
import asyncio
from PIL import Image
from typing import Tuple, List, Dict
from db_postgresql import t

class GeminiMedicalAnalyzer:
    """Анализатор медицинских изображений через Gemini API"""
    
    def __init__(self):
        """Инициализация с API ключом"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY не найден в .env файле!")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        print("✅ Gemini 1.5 Pro Latest инициализирован")
    
    async def analyze_medical_image(self, image_path: str, lang: str = "ru", custom_prompt: str = None) -> Tuple[str, str]:
        """
        Анализирует медицинское изображение
        
        Args:
            image_path: Путь к изображению
            lang: Язык ответа (ru, uk, en)
            custom_prompt: Кастомный промпт (если нужен)
            
        Returns:
            Tuple[analysis_text, error_message]
        """
        try:
            
            # Проверяем существование файла
            if not os.path.exists(image_path):
                return "", t("gemini_file_not_found", lang, path=image_path)
            
            # Загружаем изображение
            image = Image.open(image_path)
            
            # Используем хитрый образовательный промпт
            prompt = custom_prompt or self._get_educational_prompt(lang)
            
            # Более мягкие настройки безопасности
            safety_settings = {
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            }
            
            # Генерируем ответ асинхронно
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=5000,
                    candidate_count=1
                ),
                safety_settings=safety_settings
            )
            
            # Умная обработка ответа
            analysis_text = ""
            
            # Проверяем разные способы получения текста
            if hasattr(response, 'text') and response.text:
                analysis_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Проверяем finish_reason
                if hasattr(candidate, 'finish_reason'):
                    if candidate.finish_reason == 2:  # SAFETY
                        # Пробуем с более нейтральным промптом
                        alt_prompt = self._get_alternative_prompt(lang)
                        response = await asyncio.to_thread(
                            self.model.generate_content,
                            [alt_prompt, image],
                            generation_config=genai.types.GenerationConfig(
                                temperature=0.2,
                                max_output_tokens=3000,
                                candidate_count=1
                            ),
                            safety_settings=safety_settings
                        )
                        
                        if hasattr(response, 'text') and response.text:
                            analysis_text = response.text
                        else:
                            return "", t("gemini_safety_blocked", lang)
                            
                    elif candidate.finish_reason == 3:  # RECITATION
                        return "", t("gemini_copyright_violation", lang)
                
                # Если finish_reason нормальный, пробуем извлечь текст
                if not analysis_text and hasattr(candidate, 'content') and candidate.content.parts:
                    try:
                        analysis_text = candidate.content.parts[0].text
                    except:
                        pass
            
            if not analysis_text:
                return "", t("gemini_no_analysis", lang)
            
            return analysis_text, ""
            
        except Exception as e:
            error_msg = f"Ошибка Gemini: {str(e)}"
            # Специальная обработка известных ошибок
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
            "de": "German"  # ← ДОБАВЛЕНО
        }.get(lang, "Russian")
        
        return f"""You are an experienced diagnostic doctor. Analyze medical images professionally and in detail.

IMPORTANT: Please respond in {response_language} language.

First, determine what type of image this is:

**If this is a medical TEXT document** (medical records, lab results, prescriptions, discharge summaries, etc.) - transcribe ALL visible text EXACTLY as written, including:
- All numerical values with their units
- All reference ranges in parentheses  
- All medical terminology exactly as shown
- All handwritten notes
- Do NOT interpret, analyze, or change any medical assessments
- Do NOT add phrases like "within normal range" - copy the exact text
- Simply return what you see written

**If this is NOT a medical image** (photos, non-medical documents, random images) - respond: "This is not a medical image or document."

**If this is a medical IMAGING study** (ECG, EEG, X-ray, MRI, ultrasound, CT scan, etc.) - analyze it professionally:

1. **Type of study** - what is this?
2. **Technical data** - visible parameters and settings  
3. **Detailed findings** - what specifically is visible, measurements
4. **Pathological changes** - deviations from the norm, if any
5. **Diagnostic conclusion** - what this means clinically
6. **Recommendations** - what to do next, which doctor to consult

CRITICAL: For TEXT documents - be a transcriber, not a doctor. For IMAGING studies - be a doctor.

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
    """
    Извлечение медицинских событий через Gemini
    
    Args:
        document_text: Текст медицинского документа
        existing_timeline: Существующая медкарта (последние 10 записей)
        lang: Язык ответа (ru, uk, en)
    
    Returns:
        List[Dict]: Список новых/обновленных медицинских событий
    """
    
    try:
        import google.generativeai as genai
        import os
        
        # Проверяем API ключ
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return []
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Форматируем существующую медкарту
        timeline_text = ""
        if existing_timeline:
            timeline_text = "\n".join([
                f"{entry['event_date']} | {entry['category']} | {entry['importance']} | \"{entry['description']}\""
                for entry in existing_timeline
            ])
        else:
            timeline_text = "Медкарта пустая"
        
        # Определяем язык ответа
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

        # Отправляем запрос к Gemini
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Низкая для точности
                max_output_tokens=1500,
                candidate_count=1
            ),
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_MEDICAL",
                    "threshold": "BLOCK_NONE"
                }
            ]
        )
        
        # Обрабатываем ответ
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
        
        
        # Проверяем на "NO_CHANGES"
        if result_text.upper() in ['NO_CHANGES', 'БЕЗ ИЗМЕНЕНИЙ', 'БЕЗ_ИЗМЕНЕНИЙ']:
            return []
        
        # Пробуем парсить JSON
        try:
            # Очищаем ответ от лишнего текста (могут быть ``` или объяснения)
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = result_text[json_start:json_end]
                events = json.loads(json_text)
                
                if isinstance(events, list):
                    return events
                else:
                    return []
            else:
                return []
                
        except json.JSONDecodeError as e:
            return []
        
    except Exception as e:
        from error_handler import log_error_with_context
        log_error_with_context(e, {"function": "extract_medical_timeline_gemini"})
        return []