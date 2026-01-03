import os
import logging
from typing import Dict, Any, Optional
from gemini_classifier import classify_document
from gemini_specialist import analyze_with_specialist, build_patient_context
from gpt import generate_title_from_text, ask_structured, generate_medical_summary
from db_postgresql import get_user_profile, t

logger = logging.getLogger(__name__)


async def process_document(
    file_path: str,
    user_id: int,
    lang: str = "ru",
    additional_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Главный оркестратор обработки медицинского документа
    
    Процесс:
    1. Классификация документа (Gemini Classifier)
    2. Проверка is_medical
    3. Анализ специалистом (Gemini Specialist)
    4. GPT пост-обработка (title, raw_text, summary)
    5. Возврат готовых данных для сохранения
    
    Args:
        file_path: Путь к файлу документа
        user_id: ID пользователя
        lang: Язык пользователя
        additional_context: Дополнительный контекст от пользователя
        
    Returns:
        Dict с результатами обработки или ошибкой
    """
    
    try:
        logger.info("=" * 80)
        logger.info("🚀 DOCUMENT PROCESSING STARTED")
        logger.info("=" * 80)
        logger.info(f"📁 File path: {file_path}")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🌍 Language: {lang}")
        logger.info(f"📝 Additional context: {additional_context[:100] if additional_context else 'None'}...")
        logger.info("=" * 80)
        
        # ==========================================
        # ШАГ 1: КЛАССИФИКАЦИЯ ДОКУМЕНТА
        # ==========================================
        
        logger.info("")
        logger.info("📋 STEP 1/5: DOCUMENT CLASSIFICATION (Gemini 2.5 Flash)")
        logger.info("-" * 80)
        logger.info("⏳ Calling classify_document()...")
        
        classification = await classify_document(file_path)
        
        logger.info("✅ Classification completed!")
        logger.info(f"   ├─ is_medical: {classification.get('is_medical')}")
        logger.info(f"   ├─ document_type: {classification.get('document_type')}")
        logger.info(f"   ├─ subtype: {classification.get('subtype')}")
        logger.info(f"   └─ confidence: {classification.get('confidence')}")
        logger.info(f"Full classification result: {classification}")
        
        # ==========================================
        # ШАГ 2: ПРОВЕРКА IS_MEDICAL
        # ==========================================
        
        logger.info("")
        logger.info("🔍 STEP 2/5: CHECKING IF DOCUMENT IS MEDICAL")
        logger.info("-" * 80)
        
        is_medical = classification.get('is_medical', False)
        logger.info(f"is_medical = {is_medical}")
        
        if not is_medical:
            logger.warning("❌ STOP: Document is NOT medical!")
            logger.warning("⛔ Processing aborted. Returning error to user.")
            logger.info("=" * 80)
            return {
                "success": False,
                "error_type": "not_medical",
                "message": t("not_medical_doc", lang)
            }
        
        logger.info("✅ Document IS medical. Proceeding to next step...")
        
        # ==========================================
        # ШАГ 3: ПОДГОТОВКА КОНТЕКСТА ПАЦИЕНТА
        # ==========================================
        
        logger.info("")
        logger.info("👤 STEP 3/5: BUILDING PATIENT CONTEXT")
        logger.info("-" * 80)
        logger.info("⏳ Loading user profile from database...")
        
        profile = await get_user_profile(user_id)
        
        if profile:
            logger.info("✅ Profile loaded successfully!")
            logger.info(f"   ├─ Gender: {profile.get('gender', 'N/A')}")
            logger.info(f"   ├─ Birth year: {profile.get('birth_year', 'N/A')}")
            logger.info(f"   ├─ Height: {profile.get('height_cm', 'N/A')} cm")
            logger.info(f"   └─ Weight: {profile.get('weight_kg', 'N/A')} kg")
        else:
            logger.info("⚠️ No profile found for this user")
        
        logger.info("⏳ Building patient context string...")
        patient_context = build_patient_context(profile, additional_context)
        
        logger.info(f"✅ Patient context built! Length: {len(patient_context)} characters")
        if patient_context:
            logger.info(f"Context preview:\n{patient_context[:200]}...")
        else:
            logger.info("Context is empty (no profile data or additional context)")
        
        # ==========================================
        # ШАГ 4: АНАЛИЗ СПЕЦИАЛИСТОМ
        # ==========================================
        
        logger.info("")
        logger.info("🩺 STEP 4/5: SPECIALIST ANALYSIS (Gemini 3 Pro Preview)")
        logger.info("-" * 80)
        
        document_type = classification.get('document_type', 'generic')
        confidence = classification.get('confidence', 0.5)
        
        logger.info(f"Original document_type: {document_type}")
        logger.info(f"Confidence level: {confidence}")
        
        # Если уверенность низкая, используем Generic специалиста
        if confidence < 0.85:
            logger.info(f"⚠️ Confidence is below 0.85 threshold")
            logger.info(f"🔄 Switching to GENERIC specialist for safety")
            document_type = 'generic'
        else:
            logger.info(f"✅ Confidence is good, using specialized prompt: {document_type}")
        
        logger.info(f"⏳ Sending to specialist: {document_type.upper()}")
        logger.info(f"   ├─ Model: gemini-3-pro-preview")
        logger.info(f"   ├─ Temperature: 1.0")
        logger.info(f"   └─ Context included: {'Yes' if patient_context else 'No'}")
        
        specialist_result = await analyze_with_specialist(
            file_path=file_path,
            document_type=document_type,
            lang=lang,
            patient_context=patient_context
        )
        
        logger.info("📊 Specialist response received!")
        logger.info(f"   ├─ Success: {specialist_result.get('success')}")
        logger.info(f"   ├─ Specialist type: {specialist_result.get('specialist_type')}")
        logger.info(f"   └─ Analysis length: {len(specialist_result.get('analysis', ''))} characters")
        
        if not specialist_result.get('success', False):
            logger.error("❌ Specialist analysis FAILED!")
            logger.error(f"Error: {specialist_result.get('error')}")
            logger.info("=" * 80)
            return {
                "success": False,
                "error_type": "specialist_failed",
                "message": t("document_processing_error", lang)
            }
        
        vision_text = specialist_result.get('analysis', '')
        
        if not vision_text:
            logger.error("❌ Specialist returned EMPTY analysis!")
            logger.info("=" * 80)
            return {
                "success": False,
                "error_type": "empty_analysis",
                "message": t("document_processing_error", lang)
            }
        
        logger.info(f"✅ Specialist analysis complete: {len(vision_text)} chars")
        logger.info(f"Analysis preview:\n{vision_text[:300]}...")
        
        # ==========================================
        # ШАГ 5: GPT ПОСТ-ОБРАБОТКА
        # ==========================================
        
        logger.info("")
        logger.info("🤖 STEP 5/5: GPT POST-PROCESSING (GPT-4o-mini)")
        logger.info("-" * 80)
        logger.info("Processing specialist analysis into user-friendly format...")
        
        # 5.1: Генерируем заголовок
        logger.info("")
        logger.info("📌 5.1: Generating document title...")
        logger.info(f"   └─ Input: First 1500 chars of specialist analysis")
        
        title = await generate_title_from_text(
            text=vision_text[:1500],
            lang=lang
        )
        
        logger.info(f"✅ Title generated: '{title}'")
        
        # 5.2: Создаём структурированный текст (для пользователя)
        logger.info("")
        logger.info("📄 5.2: Creating structured text (raw_text for user)...")
        logger.info(f"   └─ Input: First 8000 chars of specialist analysis")
        
        raw_text = await ask_structured(
            vision_text[:8000],
            lang=lang
        )
        
        logger.info(f"✅ Raw text generated: {len(raw_text)} characters")
        logger.info(f"Raw text preview:\n{raw_text[:200]}...")

        # Получаем дату из классификации или используем текущую дату
        from datetime import date
        document_date = classification.get('document_date')
        if not document_date or str(document_date).strip() in ["", "null", "None"]:
            document_date = date.today().isoformat()  # YYYY-MM-DD

        logger.info(f"📅 Document date: {document_date}")

        # 5.3: Создаём summary (для векторной базы)
        logger.info("")
        logger.info("🔍 5.3: Creating summary (for vector search)...")
        logger.info(f"   └─ Input: First 8000 chars of specialist analysis")
        
        summary = await generate_medical_summary(
            vision_text[:8000],
            lang,
            document_date
        )
                
        # ==========================================
        # ШАГ 6: ВОЗВРАТ РЕЗУЛЬТАТА
        # ==========================================
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ DOCUMENT PROCESSING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info("📊 FINAL RESULTS:")
        logger.info(f"   ├─ Title: {title}")
        logger.info(f"   ├─ Document type: {classification.get('document_type')}")
        logger.info(f"   ├─ Subtype: {classification.get('subtype')}")
        logger.info(f"   ├─ Confidence: {classification.get('confidence')}")
        logger.info(f"   ├─ Raw text length: {len(raw_text)} chars")
        logger.info(f"   ├─ Summary length: {len(summary)} chars")
        logger.info(f"   └─ Full analysis length: {len(vision_text)} chars")
        logger.info("=" * 80)
        logger.info("")             

        return {
            "success": True,
            "title": title,
            "raw_text": raw_text,
            "summary": summary,
            "full_analysis": vision_text,
            "document_type": classification.get('document_type'),
            "subtype": classification.get('subtype'),
            "confidence": classification.get('confidence'),
            "document_date": document_date
        }
        
    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error("💥 CRITICAL ERROR IN DOCUMENT PROCESSING")
        logger.error("=" * 80)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Full traceback:", exc_info=True)
        logger.error("=" * 80)
        logger.error("")
        
        return {
            "success": False,
            "error_type": "critical_error",
            "message": t("document_processing_error", lang),
            "error_details": str(e)
        }