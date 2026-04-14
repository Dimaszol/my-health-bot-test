import os
import asyncio
import logging
import google.generativeai as genai
from typing import Dict, Any, Optional
from datetime import date

from gemini_classifier import classify_document
from gemini_specialist import analyze_with_assistant, analyze_with_specialist, build_patient_context
from gpt import generate_title_from_text, ask_structured, generate_medical_summary
from db_postgresql import get_user_profile, t

logger = logging.getLogger(__name__)


async def process_document(
    file_path: str,
    user_id: int,
    lang: str = "ru",
    additional_context: Optional[str] = None,
    use_medical_history: bool = False
) -> Dict[str, Any]:
    temp_truncated_path = None
    gemini_file = None

    try:
        # Обрезаем PDF до 10 страниц
        MAX_PDF_PAGES = 10
        truncated_file_path = file_path

        if file_path.lower().endswith('.pdf'):
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                if len(reader.pages) > MAX_PDF_PAGES:
                    writer = pypdf.PdfWriter()
                    for i in range(MAX_PDF_PAGES):
                        writer.add_page(reader.pages[i])
                    temp_truncated_path = file_path + "_truncated.pdf"
                    with open(temp_truncated_path, 'wb') as f:
                        writer.write(f)
                    truncated_file_path = temp_truncated_path
                    logger.info("PDF truncated for AI analysis")
            except Exception as e:
                logger.warning(f"PDF truncation failed, using original: {e}")

        # Один upload для всего флоу
        gemini_file = await asyncio.to_thread(genai.upload_file, truncated_file_path)
        logger.info("File uploaded to Gemini")

        # Классификация
        classification = await classify_document(uploaded_file=gemini_file)

        logger.info(f"Classification: {classification.get('document_type')} (confidence: {classification.get('confidence')})")

        is_medical = classification.get('is_medical', False)
        if not is_medical:
            return {
                "success": False,
                "error_type": "not_medical",
                "message": t("not_medical_doc", lang)
            }

        # Контекст пациента
        profile = await get_user_profile(user_id)
        patient_context = build_patient_context(profile, additional_context)

        document_type = classification.get('document_type', 'generic')
        confidence = classification.get('confidence', 0.5)

        if confidence < 0.85:
            document_type = 'generic'

        medical_history = ""
        if use_medical_history:
            from medical_timeline import get_objective_history_for_specialist
            medical_history = await get_objective_history_for_specialist(user_id, document_type)

        # Анализ ассистентом
        assistant_result = await analyze_with_assistant(
            uploaded_file=gemini_file,
            document_type=document_type,
            lang=lang,
            patient_context=patient_context
        )

        if not assistant_result.get('success', False):
            return {
                "success": False,
                "error_type": "assistant_failed",
                "message": t("document_processing_error", lang)
            }

        assistant_analysis = assistant_result.get('analysis', '')

        if not assistant_analysis:
            return {
                "success": False,
                "error_type": "empty_assistant_analysis",
                "message": t("document_processing_error", lang)
            }

        # Анализ специалистом
        specialist_result = await analyze_with_specialist(
            uploaded_file=gemini_file,
            document_type=document_type,
            lang=lang,
            patient_context=patient_context,
            assistant_analysis=assistant_analysis,
            medical_history=medical_history
        )

        if not specialist_result.get('success', False):
            return {
                "success": False,
                "error_type": "specialist_failed",
                "message": t("document_processing_error", lang)
            }

        vision_text = specialist_result.get('analysis', '')

        if not vision_text:
            return {
                "success": False,
                "error_type": "empty_analysis",
                "message": t("document_processing_error", lang)
            }

        # GPT пост-обработка
        title = await generate_title_from_text(
            text=vision_text[:1500],
            lang=lang
        )

        raw_text = await ask_structured(
            lang=lang,
            assistant_analysis=assistant_analysis,
            specialist_analysis=vision_text,
            patient_context=additional_context or ""
        )

        document_date = classification.get('document_date')
        if not document_date or str(document_date).strip() in ["", "null", "None"]:
            document_date = date.today().isoformat()

        summary = await generate_medical_summary(
            vision_text[:8000],
            lang,
            document_date
        )

        return {
            "success": True,
            "title": title,
            "raw_text": raw_text,
            "summary": summary,
            "full_analysis": vision_text,
            "first_analysis": assistant_analysis,
            "document_type": classification.get('document_type'),
            "subtype": classification.get('subtype'),
            "confidence": classification.get('confidence'),
            "document_date": document_date
        }

    except Exception as e:
        logger.error(f"Critical error in document processing: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_type": "critical_error",
            "message": t("document_processing_error", lang),
            "error_details": str(e)
        }

    finally:
        # Один delete для всего флоу
        if gemini_file:
            try:
                await asyncio.to_thread(genai.delete_file, gemini_file.name)
            except Exception:
                pass
        if temp_truncated_path and os.path.exists(temp_truncated_path):
            os.remove(temp_truncated_path)