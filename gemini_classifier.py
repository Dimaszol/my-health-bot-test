import google.generativeai as genai
import os
import json
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Конфигурация
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

GEMINI_CLASSIFIER_TIMEOUT = 60  # секунд — добавь вверху gemini_classifier.py

# JSON Schema для валидации ответа
CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "is_medical": {"type": "boolean"},
        "document_type": {
            "type": "string",
            "enum": ["ecg", "lab_results", "imaging", "pathology", "clinical_report", "prescription", "generic"]
        },
        "subtype": {"type": "string"},       
        "confidence": {"type": "number"},
        "document_date": {"type": "string"} 
    },
    "required": ["is_medical", "document_type", "confidence", "document_date"]
}

CLASSIFIER_SYSTEM_PROMPT = """You are a highly accurate Medical Document Classifier API.
Your role is to categorize uploaded images or PDFs into specific medical domains for further routing to specialists.

### OPERATIONAL CONSTRAINTS:
1. OUTPUT ONLY A VALID JSON. No preamble, no conversational text, no markdown code blocks.
2. DO NOT ANALYZE CLINICAL DATA. Do not extract values, do not interpret health status.
3. VISUAL ANALYSIS: Evaluate document layout, headers, stamps, and signatures.
4. If the document contains multiple types, classify based on the DOMINANT content.

### CLASSIFICATION TAXONOMY:
- "ecg": Graphs with wave patterns (P, QRS, T), cardiac stress tests.
- "lab_results": Tables with biomarkers (e.g., Blood, Urine), reference ranges, and units.
- "imaging": Radiology images or scans (X-ray, MRI, CT, Ultrasound) where the image itself is the primary clinical content, with minimal or no descriptive text.
- "pathology": Biopsy, histology, or cytology reports (look for "macroscopic/microscopic description").
- "clinical_report": Text-based medical reports describing findings, procedures, or examinations, including procedural protocols (e.g., endoscopy, colonoscopy) even if images are attached.
- "prescription": Doctor's prescriptions with medication names, dosages, and signatures.
- "generic": Any medical document that doesn't fit the above (e.g., certificates, vaccination cards).

### NON-MEDICAL CRITERIA:
If the document is a photo of a person, a landscape, a recipe, a store receipt, or any non-clinical text, set "is_medical": false.

### DATE EXTRACTION:
If you find a date on the document, return it in YYYY-MM-DD format (e.g., "2025-01-15").
If no date is visible or readable, return null."""

CLASSIFIER_USER_PROMPT = """Analyze the provided document (PDF or Image). 
Identify if it is a medical document and classify its type according to the schema. 
For 'subtype', use concise technical terms in English (e.g., 'hematology', 'urinalysis', 'brain_mri').
Extract the document date if visible on the image.

### SCHEMA:
{
  "is_medical": boolean,
  "document_type": "ecg" | "lab_results" | "imaging" | "pathology" | "clinical_report" | "prescription" | "generic",
  "subtype": string | null,
  "confidence": number,
  "document_date": string | null
}

### EXAMPLES FOR GUIDANCE:
- Blood test results dated 15.01.2025 -> {"is_medical": true, "document_type": "lab_results", "subtype": "hematology", "confidence": 1.0, "document_date": "2025-01-15"}
- MRI Brain Report from 03/28/2024 -> {"is_medical": true, "document_type": "imaging", "subtype": "MRI", "confidence": 0.98, "document_date": "2024-03-28"}
- Photo of a cat -> {"is_medical": false, "document_type": "generic", "subtype": null, "confidence": 1.0, "document_date": null}
- Document without visible date -> {..., "document_date": null}

Return ONLY the JSON object."""

async def classify_document(file_path: str = None, uploaded_file=None) -> Dict[str, Any]:
    external_file = uploaded_file is not None
    try:
        if not external_file:
            uploaded_file = await asyncio.to_thread(genai.upload_file, file_path)
            logger.info("File uploaded to Gemini for classification")

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=CLASSIFIER_SYSTEM_PROMPT
        )
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = await asyncio.wait_for(
            model.generate_content_async(
                [uploaded_file, "Classify this document. Return ONLY valid JSON."],
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=CLASSIFICATION_SCHEMA
                ),
                safety_settings=safety_settings
            ),
            timeout=GEMINI_CLASSIFIER_TIMEOUT
        )
        
        raw_text = response.text

        if not raw_text or raw_text.strip() == "":
            logger.warning("Gemini classifier returned empty response")
            return _default_classification()

        import re
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        clean_json = json_match.group(0) if json_match else raw_text

        try:
            result = json.loads(clean_json)
        except json.JSONDecodeError:
            logger.warning("Gemini classifier JSON parse failed")
            return _default_classification()
        
        if not external_file:
            await asyncio.to_thread(genai.delete_file, uploaded_file.name)
        
        logger.info(f"Classification complete: type={result.get('document_type')}, confidence={result.get('confidence')}")
        
        return result

    except asyncio.TimeoutError:
        logger.warning(f"Gemini classifier timeout after {GEMINI_CLASSIFIER_TIMEOUT}s")
        if not external_file and uploaded_file:
            try:
                await asyncio.to_thread(genai.delete_file, uploaded_file.name)
            except Exception:
                pass
        return _default_classification()
        
    except Exception as e:
        logger.error(f"Classification failed: {str(e)}", exc_info=True)
        if not external_file and uploaded_file:
            try:
                await asyncio.to_thread(genai.delete_file, uploaded_file.name)
            except Exception:
                pass
        return _default_classification()


def _default_classification() -> Dict[str, Any]:
    return {
        "is_medical": True,
        "document_type": "generic",
        "subtype": None,
        "confidence": 0.5,
        "document_date": None
    }