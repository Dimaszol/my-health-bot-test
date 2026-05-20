"""
lab_extractor.py — Асинхронное извлечение биомаркеров из анализов крови и других лабораторных результатов.

Запускается fire-and-forget после сохранения документа типа lab_results.
"""

import asyncio
import json
import logging
import os
from datetime import date
from typing import Optional

import google.generativeai as genai
from db_postgresql import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

# По аналогии с gemini_classifier.py
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

GEMINI_EXTRACTOR_TIMEOUT = 120  # секунд


# ── Промт (из базы знаний проекта) ────────────────────────────────────────────
BIOMARKER_MAPPING = {

# --- CBC ---
"hemoglobin": [["hemoglobin","hb","hgb"],"g/dL"],
"hematocrit": [["hematocrit","hct"],"%"],
"rbc": [["red blood cells","rbc","erythrocytes"],"x10^12/L"],
"wbc": [["white blood cells","wbc","leukocytes","white cell count"],"x10^9/L"],
"platelets": [["platelets","plt","platelet count"],"x10^9/L"],
"pdw": [["platelet distribution width","pdw"],"fL"],
"mpv": [["mean platelet volume","mpv"],"fL"],
"mcv": [["mean corpuscular volume","mcv"],"fL"],
"mch": [["mean corpuscular hemoglobin","mch"],"pg"],
"mchc": [["mean corpuscular hemoglobin concentration","mchc"],"g/dL"],
"rdw": [["red cell distribution width","rdw"],"%"],

"neutrophils": [["neutrophils","neut","neutrophil","absolute neutrophils","neutrophil count","neut #"],"x10^9/L"],
"lymphocytes": [["lymphocytes","lymph","lymphocyte","absolute lymphocytes","lymphocyte count","lymph #"],"x10^9/L"],
"monocytes": [["monocytes","mono","monocyte","absolute monocytes","monocyte count","mono #"],"x10^9/L"],
"eosinophils": [["eosinophils","eos","eosinophil","absolute eosinophils","eosinophil count","eos #"],"x10^9/L"],
"basophils": [["basophils","baso","basophil","absolute basophils","basophil count","baso #"],"x10^9/L"],
"reticulocyte": [["reticulocytes","retic","reticulocyte","reticulocyte count"],"x10^9/L"],
"anc": [["absolute neutrophils","anc","absolute neutrophil count"],"cells/µL"],

"neutrophils_pct": [["neutrophils %","neut %","neutrophils percentage"],"%"],
"lymphocytes_pct": [["lymphocytes %","lymph %","lymphocytes percentage"],"%"],
"monocytes_pct": [["monocytes %","mono %"],"%"],
"eosinophils_pct": [["eosinophils %","eos %"],"%"],
"basophils_pct": [["basophils %","baso %"],"%"],
"reticulocyte_pct": [["reticulocytes %","retic %"],"%"],

# --- Biochemistry ---
"glucose": [["glucose","glu","blood glucose"],"mmol/L"],
"total_protein": [["total protein"],"g/L"],
"albumin": [["albumin"],"g/L"],
"globulin": [["globulin"],"g/dL"],
"ag_ratio": [["albumin globulin ratio","a/g"],"ratio"],
"pyruvate": [["pyruvate"],"mmol/L"],

"urea": [["urea","bun","blood urea nitrogen"],"mg/dL"],
"creatinine": [["creatinine","crea"],"mg/dL"],
"uric_acid": [["uric acid","urate"],"mg/dL"],

# --- Blood gas ---
"po2": [["po2","pO2","partial pressure oxygen"],"mmHg"],
"pco2": [["pco2","pCO2","partial pressure carbon dioxide"],"mmHg"],
"sao2": [["oxygen saturation","sao2","o2 saturation"],"%"],
"blood_ph": [["blood ph","ph"],"pH"],

# --- Metabolism ---
"homocysteine": [["homocysteine"],"µmol/L"],
"g6pd": [["g6pd"],"U/g Hb"],
"mma": [["methylmalonic acid","mma"],"nmol/L"],
"lactate": [["lactate","lactic acid"],"mmol/L"],
"osmolality": [["osmolality"],"mOsm/kg"],

# --- Enzymes ---
"amylase": [["amylase"],"U/L"],
"lipase": [["lipase"],"U/L"],
"ldh": [["ldh","lactate dehydrogenase"],"U/L"],

"prealbumin": [["prealbumin"],"mg/dL"],
"ceruloplasmin": [["ceruloplasmin"],"mg/dL"],

# --- Lipids ---
"total_cholesterol": [["total cholesterol","cholesterol"],"mmol/L"],
"ldl": [["ldl","ldl cholesterol"],"mmol/L"],
"hdl": [["hdl","hdl cholesterol"],"mmol/L"],
"non_hdl": [["non hdl","non-hdl"],"mmol/L"],
"triglycerides": [["triglycerides","tg"],"mmol/L"],
"vldl": [["vldl"],"mmol/L"],
"apoa1": [["apolipoprotein a1","apo a1"],"mg/dL"],
"apob": [["apolipoprotein b","apo b"],"g/L"],
"lpa": [["lipoprotein a","lp(a)","lpa"],"mg/dL"],

# --- Liver ---
"alt": [["alt","alanine aminotransferase"],"U/L"],
"ast": [["ast","aspartate aminotransferase"],"U/L"],
"alp": [["alp","alkaline phosphatase"],"U/L"],
"ggt": [["ggt","gamma gt"],"U/L"],
"bilirubin_total": [["total bilirubin","bilirubin"],"µmol/L"],
"bilirubin_direct": [["direct bilirubin","conjugated bilirubin"],"mg/dL"],
"bilirubin_indirect": [["indirect bilirubin","unconjugated bilirubin"],"mg/dL"],

# --- Kidney ---
"egfr": [["egfr","eGFR"],"mL/min/1.73m²"],
"bun_creatinine_ratio": [["bun creatinine ratio"],"ratio"],
"cystatin_c": [["cystatin c"],"mg/L"],
"acr": [["albumin creatinine ratio","acr","microalbumin ratio"],"mg/g"],

# --- Thyroid ---
"tsh": [["tsh"],"mIU/L"],
"ft4": [["free t4","ft4"],"pmol/L"],
"ft3": [["free t3","ft3"],"pg/mL"],
"t4": [["total t4"],"µg/dL"],
"t3": [["total t3"],"ng/dL"],
"calcitonin": [["calcitonin"],"pg/mL"],
"tg": [["thyroglobulin","tg"],"ng/mL"],
"anti_tpo": [["anti tpo","tpo antibodies"],"IU/mL"],
"anti_tg": [["anti tg","tg antibodies"],"IU/mL"],
"rt3": [["reverse t3"],"ng/dL"],
"trab": [["tsh receptor antibodies","trab"],"IU/L"],

# --- Cardiac ---
"troponin_i": [["troponin i"],"pg/mL"],
"troponin_t": [["troponin t"],"ng/L"],
"bnp": [["bnp"],"pg/mL"],
"nt_probnp": [["nt probnp"],"ng/L"],
"ck": [["creatine kinase","ck"],"U/L"],
"ck_mb": [["ck mb"],"ng/mL"],
"myoglobin": [["myoglobin"],"mcg/L"],

# --- Inflammation ---
"hs_crp": [["hs crp"],"mg/L"],
"crp": [["crp"],"mg/L"],
"esr": [["esr"],"mm/hr"],
"procalcitonin": [["procalcitonin"],"ng/mL"],

# --- Hormones ---
"cortisol": [["cortisol"],"mcg/dL"],
"acth": [["acth"],"pg/mL"],
"c_peptide": [["c peptide"],"ng/mL"],

"testosterone": [["testosterone"],"ng/dL"],
"free_testosterone": [["free testosterone"],"ng/dL"],
"estradiol": [["estradiol","e2"],"pg/mL"],
"progesterone": [["progesterone"],"ng/mL"],
"lh": [["lh"],"IU/L"],
"fsh": [["fsh"],"mIU/mL"],
"prolactin": [["prolactin"],"ng/mL"],
"shbg": [["shbg"],"nmol/L"],
"dhea_s": [["dhea s"],"mcg/dL"],

"plgf": [["plgf"],"pg/mL"],
"free_beta_hcg": [["free beta hcg"],"IU/L"],
"gh": [["growth hormone","gh"],"ng/mL"],
"afc": [["afc"],"count"],
"papp_a": [["papp a"],"MoM"],
"erythropoietin": [["erythropoietin"],"mU/mL"],
"pth": [["pth"],"pg/mL"],
"amh": [["amh"],"ng/mL"],
"sflt1": [["sflt1"],"pg/mL"],
"androstenedione": [["androstenedione"],"ng/dL"],
"17_hydroxyprogesterone": [["17 hydroxyprogesterone"],"ng/dL"],
"fai": [["free androgen index"],"%"],
"aldosterone": [["aldosterone"],"ng/dL"],
"renin_activity": [["renin activity"],"ng/mL/hr"],
"vasopressin": [["adh","vasopressin"],"pg/mL"],
"igf_1": [["igf 1"],"ng/mL"],

# --- Vitamins ---
"vitamin_d": [["vitamin d"],"nmol/L"],
"b12": [["vitamin b12"],"ng/L"],
"folate": [["folate"],"ng/mL"],
"rbc_folate": [["rbc folate"],"ng/mL"],
"fad": [["fad"],"nmol/L"],
"fmn_riboflavin": [["fmn"],"nmol/L"],
"vitamin_a": [["vitamin a"],"µg/dL"],
"vitamin_e": [["vitamin e"],"mg/L"],
"vitamin_c": [["vitamin c"],"mg/dL"],
"vitamin_k": [["vitamin k"],"ng/mL"],
"beta_carotene": [["beta carotene"],"mcg/dL"],
"egrac": [["egrac"],"ratio"],
"pivka_ii": [["pivka"],"mAU/mL"],
"b1": [["vitamin b1"],"nmol/L"],
"b2": [["vitamin b2"],"mcg/L"],
"b6": [["vitamin b6"],"nmol/L"],
"zinc": [["zinc"],"µg/dL"],

# --- Coagulation ---
"pt": [["pt","prothrombin time"],"seconds"],
"inr": [["inr"],"ratio"],
"aptt": [["aptt"],"seconds"],
"fibrinogen": [["fibrinogen"],"g/L"],
"d_dimer": [["d dimer"],"ng/mL FEU"],
"thrombin_time": [["thrombin time"],"seconds"],

# --- Diabetes ---
"fpg": [["fasting glucose"],"mmol/L"],
"hba1c": [["hba1c"],"%"],
"insulin": [["insulin"],"µU/mL"],
"insulin_antibodies": [["insulin antibodies"],"U/mL"],
"homa_ir": [["homa ir"],"index"],
"eag": [["estimated average glucose"],"mg/dL"],
"fructosamine": [["fructosamine"],"µmol/L"],
"gad_antibodies": [["gad antibodies"],"IU/mL"],
"ica": [["islet cell antibodies"],"JDF units"],
"ia_2_antibodies": [["ia 2 antibodies"],"U/mL"],
"znt8_antibodies": [["znt8 antibodies"],"U/mL"],
"ogtt": [["ogtt"],"mmol/L"],

# --- Electrolytes ---
"sodium": [["sodium","na"],"mmol/L"],
"potassium": [["potassium","k"],"mmol/L"],
"chloride": [["chloride","cl"],"mmol/L"],
"anion_gap": [["anion gap"],"mmol/L"],
"calcium": [["calcium"],"mg/dL"],
"ionized_calcium": [["ionized calcium"],"mg/dL"],
"magnesium": [["magnesium"],"mg/dL"],
"phosphate": [["phosphate"],"mg/dL"],
"copper": [["copper"],"mcg/dL"],
"bicarbonate": [["bicarbonate"],"mmol/L"],

# --- Iron ---
"ferritin": [["ferritin"],"ng/mL"],
"serum_iron": [["serum iron"],"µg/dL"],
"tibc": [["tibc"],"µg/dL"],
"transferrin": [["transferrin"],"mg/dL"],
"stfr": [["stfr"],"mg/L"],
"transferrin_saturation": [["transferrin saturation"],"%"],
"uibc": [["uibc"],"µg/dL"],

# --- Tumor markers ---
"psa": [["psa"],"ng/mL"],
"free_psa": [["free psa"],"%"],
"ca_125": [["ca 125"],"U/mL"],
"ca_19_9": [["ca 19 9"],"U/mL"],
"cea": [["cea"],"ng/mL"],
"afp": [["afp"],"ng/mL"],
"hcg": [["hcg"],"mIU/mL"],
"he4": [["he4"],"pmol/L"],

# --- Urine ---
"urine_ph": [["urine ph"],"pH"],
"urine_specific_gravity": [["specific gravity"],"ratio"],
"urine_protein": [["urine protein"],"g/L"],
"pcr": [["protein creatinine ratio"],"mg/g"],
"urine_glucose": [["urine glucose"],"mmol/L"],
"urine_ketones": [["ketones"],"mg/dL"],
"urine_blood": [["urine blood"],"RBC/HPF"],
"urine_leukocytes": [["urine leukocytes"],"cells/HPF"],
"urine_nitrites": [["nitrites"],"neg/pos"],
"urine_osmolality": [["urine osmolality"],"mOsm/kg"],
"upep": [["upep"],"mg/24h"],
"urine_albumin": [["urine albumin"],"mg/mmol"],
"urine_creatinine": [["urine creatinine"],"mmol/L"],
"urine_copper_24h": [["urine copper"],"µg/24h"],
"urinary_b2": [["urinary b2"],"µg/g creatinine"],

# --- Immunology ---
"c3": [["complement c3"],"g/L"],
"c4": [["complement c4"],"mg/dL"],
"ana": [["ana"],"titer"],
"anti_dsdna": [["anti dsdna"],"IU/mL"],
"anti_smith": [["anti smith"],"U/mL"],
"tnf_alpha": [["tnf alpha"],"pg/mL"],
"il_10": [["il 10"],"pg/mL"],
"il_8": [["il 8"],"pg/mL"],
"il_6": [["il 6"],"pg/mL"],
"anti_u1_rnp": [["anti u1 rnp"],"AI"],
"ch50": [["ch50"],"U/mL"],
"ige": [["ige"],"kU/L"],
"total_ige": [["total ige"],"IU/mL"],
"specific_ige": [["specific ige"],"kU/L"],
"igg": [["igg"],"g/L"],
"iga": [["iga"],"mg/dL"],
"igm": [["igm"],"mg/dL"],
"spep": [["spep"],"g/dL"],
"ttg_iga": [["ttg iga"],"U/mL"],
"free_light_chains": [["free light chains"],"mg/L"],
"ife": [["ife"],"qualitative"],
"ema_iga": [["ema iga"],"titer"],
"dgp_antibodies": [["dgp antibodies"],"U/mL"],

}

EXTRACTION_SYSTEM_PROMPT = f"""You are a lab result extraction API.
Your ONLY job: extract biomarker values from medical documents and return strict JSON.

--- OUTPUT RULES ---
- Return ONLY valid JSON. No markdown, no explanation, no preamble, no ```json fences.
- For every found biomarker include: original_value, original_unit, standard_value, standard_unit, status.
- original_value MUST be exactly as written in the document (e.g. "POSITIVE", "1:40 H", "118", "<0.01"). Do NOT normalize it.
- standard_value is the converted numeric value (or null if the original is qualitative and cannot be converted).
- status MUST be one of: "normal", "high", "low" — never null, never any other string.
- If the document contains multiple results for the same biomarker (trend/history table), extract ONLY the most recent value based on the latest date in the document.

--- STATUS RULES ---
Numeric values:
  - "normal" if within reference range
  - "high" if above reference range
  - "low" if below reference range
  - If no reference range is given and the value is numeric, use "normal" as a safe default.

Qualitative values (POSITIVE/NEGATIVE, DETECTED/NOT DETECTED, REACTIVE/NON-REACTIVE, etc.):
  - Determine the expected normal result from context.
  - If the result matches the expected normal → "normal"
  - If the result is abnormal → "high"
  - If the result is below normal → "low"

Titer values (e.g., "1:40 H", ">1:80"):
  - Treat as qualitative. Use the "H" flag or reference range to determine status.

--- MATCHING PRINCIPLE ---

You MUST map biomarkers based on semantic meaning, not exact wording.

Aliases are only hints, not strict rules.

If a biomarker in the document clearly refers to an existing biomarker concept,
you MUST use the existing slug — even if the wording is different.

Different phrasing, prefixes, or suffixes (e.g. "absolute", "count", "level", symbols, abbreviations)
DO NOT make it a new biomarker.

When multiple slugs are possible, choose the most clinically appropriate one.

--- CRITICAL MATCHING RULE ---
BEFORE creating a new slug, you MUST perform a 3-step check:
1. Does the document term mean the same as any existing slug or its aliases?
2. If the term is a synonym (e.g., "PLT" vs "Platelets"), you MUST use the existing slug "platelets".
3. ONLY if the biomarker is fundamentally different (e.g., a rare genetic test not in the list), create a new slug.

--- FALLBACK RULE ---

Only create a new slug if the biomarker represents a fundamentally different medical concept
that cannot be matched to any existing slug.

When creating a new slug:
- use lowercase English
- use underscores
- keep it concise and meaningful
- add: "display_name": "<exact name from the document>"

When in doubt, prefer mapping to an existing slug rather than creating a new one.

--- CONVERSION RULES ---
Apply when original unit differs from the standard unit:
  г/л → g/dL: divide by 10
  г/л → g/L: no conversion
  мкмоль/л → mg/dL (creatinine): × 0.0113
  ммоль/л → mmol/L: no conversion
  ммоль/л → mg/dL (glucose): × 18.0
  ммоль/л → mg/dL (cholesterol): × 38.67
  мг/дл → mg/dL: no conversion
  мМЕ/л → mIU/L: no conversion
  пмоль/л → pmol/L: no conversion
  нг/мл → ng/mL: no conversion
  U/L, Е/л → U/L: no conversion
  мм/ч → mm/hr: no conversion

For qualitative values: set standard_value to null, standard_unit to null.

--- BIOMARKER MAPPING ---
{json.dumps(BIOMARKER_MAPPING, ensure_ascii=False)}

--- OUTPUT FORMAT ---
{{
  "hemoglobin": {{
    "original_value": "118",
    "original_unit": "г/л",
    "standard_value": 11.8,
    "standard_unit": "g/dL",
    "status": "low"
  }},
  "ana_screen_ifa": {{
    "display_name": "ANA Screen IFA",
    "original_value": "POSITIVE",
    "original_unit": null,
    "standard_value": null,
    "standard_unit": null,
    "status": "high"
  }}
}}"""


# ── Функции извлечения (по аналогии с gemini_classifier.py) ──────────────────

import re as _re

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",        "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",  "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",  "threshold": "BLOCK_NONE"},
]


def _parse_json_response(raw_text: str) -> dict:
    """Парсит JSON из ответа Gemini, убирает возможные markdown-обёртки."""
    text = raw_text.strip()
    # Убираем ```json ... ``` если модель нарушила инструкцию
    json_match = _re.search(r'\{.*\}', text, _re.DOTALL)
    clean = json_match.group(0) if json_match else text
    return json.loads(clean)


async def _extract_biomarkers_from_file(file_path: str) -> dict:
    """
    Загружает файл (PDF или изображение) в Gemini Files API
    и извлекает биомаркеры — по аналогии с gemini_classifier.py.
    """
    uploaded_file = None
    try:
        uploaded_file = await asyncio.to_thread(genai.upload_file, file_path)

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=EXTRACTION_SYSTEM_PROMPT
        )

        response = await asyncio.wait_for(
            model.generate_content_async(
                [uploaded_file, "Extract ALL biomarkers from this lab document. Return ONLY valid JSON."],
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
                safety_settings=SAFETY_SETTINGS
            ),
            timeout=GEMINI_EXTRACTOR_TIMEOUT
        )

        return _parse_json_response(response.text)

    except asyncio.TimeoutError:
        logger.warning("lab_extractor: Gemini timeout for file extraction")
        raise
    finally:
        if uploaded_file:
            try:
                await asyncio.to_thread(genai.delete_file, uploaded_file.name)
            except Exception:
                pass


async def _extract_biomarkers_from_text(raw_text: str) -> dict:
    """
    Извлекает биомаркеры из текста — используется в основном флоу
    (fire-and-forget после сохранения документа, когда raw_text уже есть).
    """
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=EXTRACTION_SYSTEM_PROMPT
    )

    response = await asyncio.wait_for(
        model.generate_content_async(
            [f"Extract ALL biomarkers from this lab document:\n\n{raw_text[:12000]}"],
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
            safety_settings=SAFETY_SETTINGS
        ),
        timeout=GEMINI_EXTRACTOR_TIMEOUT
    )

    return _parse_json_response(response.text)


async def _save_biomarkers_to_db(
    user_id: int,
    document_id: int,
    test_date: date,
    biomarkers: dict
) -> int:
    """Сохраняет биомаркеры в таблицу lab_results. Возвращает количество сохранённых строк."""
    if not biomarkers:
        return 0

    conn = await get_db_connection()
    saved = 0
    try:
        for slug, data in biomarkers.items():
            # Пропускаем записи с невалидным статусом (на всякий случай)
            status = data.get("status")
            if status not in ("normal", "high", "low"):
                continue

            # original_value: сохраняем как строку (может быть <3.0, POSITIVE, 1:40 и т.д.)
            original_value = str(data.get("original_value", "") or "")[:50] or None

            # standard_value: числовое нормализованное значение
            from decimal import Decimal, InvalidOperation
            try:
                standard_value = Decimal(str(data["standard_value"])) if data.get("standard_value") is not None else None
            except (InvalidOperation, TypeError, ValueError):
                standard_value = None

            original_unit = (data.get("original_unit") or "")[:50] or None
            standard_unit = (data.get("standard_unit") or "")[:50] or None
            display_name = (data.get("display_name") or "")[:200] or None

            await conn.execute(
                """
                INSERT INTO lab_results
                    (user_id, document_id, test_date, slug,
                     original_value, original_unit,
                     standard_value, standard_unit,
                     status, display_name)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (user_id, document_id, slug) DO UPDATE SET
                    original_value  = EXCLUDED.original_value,
                    original_unit   = EXCLUDED.original_unit,
                    standard_value  = EXCLUDED.standard_value,
                    standard_unit   = EXCLUDED.standard_unit,
                    status          = EXCLUDED.status,
                    display_name    = EXCLUDED.display_name
                """,
                user_id, document_id, test_date,
                slug[:100],
                original_value, original_unit,
                standard_value, standard_unit,
                status, display_name
            )
            saved += 1

    finally:
        await release_db_connection(conn)

    return saved


# ── Публичная точка входа ─────────────────────────────────────────────────────

async def extract_and_save_lab_results(
    user_id: int,
    document_id: int,
    raw_text: str,
    document_date: Optional[str] = None,
) -> None:
    """
    Fire-and-forget задача.
    Вызывается из document_processor / upload.py после сохранения документа
    с типом lab_results.

    Пример вызова (не блокирует поток обработки):
        asyncio.create_task(
            extract_and_save_lab_results(user_id, document_id, raw_text, document_date)
        )
    """
    try:
        # Определяем дату теста
        test_date: date
        if document_date and str(document_date).strip() not in ("", "null", "None"):
            try:
                test_date = date.fromisoformat(str(document_date))
            except ValueError:
                test_date = date.today()
        else:
            test_date = date.today()

        if not raw_text or len(raw_text.strip()) < 20:
            logger.warning("lab_extractor: document %s has no usable text, skipping", document_id)
            return

        biomarkers = await _extract_biomarkers_from_text(raw_text)

        if not isinstance(biomarkers, dict) or not biomarkers:
            logger.warning("lab_extractor: no biomarkers extracted for document %s", document_id)
            return

        saved = await _save_biomarkers_to_db(user_id, document_id, test_date, biomarkers)
        logger.info("lab_extractor: saved %d biomarkers for document %s", saved, document_id)

    except json.JSONDecodeError:
        logger.error("lab_extractor: JSON parse error for document %s", document_id)
    except Exception:
        logger.exception("lab_extractor: unexpected error for document %s", document_id)