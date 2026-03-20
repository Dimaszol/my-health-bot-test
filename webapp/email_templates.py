# webapp/email_templates.py
# 📧 Шаблоны email писем (мультиязычные)

import os

BASE_URL = os.getenv("BASE_URL", "https://pulsebook.health")


def _build_html(subject: str, heading: str, body_lines: list[str], cta_text: str, cta_url: str) -> str:
    """Базовый HTML шаблон письма в стиле PulseBook"""
    lines_html = "".join(
        f"<p style='margin:0 0 14px 0;color:#4a5568;font-size:15px;line-height:1.7'>{line}</p>"
        for line in body_lines
    )
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light">
</head>
<body style="margin:0;padding:0;background:#f7fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f7fafc;padding:40px 20px">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%">
 
        <!-- Header -->
        <tr><td style="background:#ffffff;border-radius:16px 16px 0 0;padding:28px 40px;border-bottom:3px solid #00C9A7;text-align:center">
        <img src="https://pulsebook.health/static/apple-touch-icon.png" 
            alt="PulseBook" 
            width="48" height="48"
            style="display:block;margin:0 auto 8px auto;border-radius:12px">
        <span style="font-size:20px;font-weight:700;color:#00C9A7;letter-spacing:-0.5px">PulseBook</span>
        </td></tr>
 
        <!-- Body -->
        <tr><td style="background:#ffffff;padding:36px 40px 28px">
          <h1 style="margin:0 0 20px 0;color:#1a202c;font-size:22px;font-weight:700;line-height:1.3">{heading}</h1>
          {lines_html}
        </td></tr>
 
        <!-- CTA -->
        <tr><td style="background:#ffffff;padding:0 40px 36px">
          <a href="{cta_url}"
             style="display:inline-block;background:linear-gradient(135deg,#00C9A7 0%,#00D4BD 100%);color:#ffffff;text-decoration:none;font-size:15px;font-weight:600;padding:14px 32px;border-radius:24px;box-shadow:0 4px 15px rgba(0,201,167,0.35)"
          >{cta_text}</a>
        </td></tr>
 
        <!-- Разделитель -->
        <tr><td style="background:#ffffff;padding:0 40px">
          <div style="height:1px;background:linear-gradient(90deg,transparent,#e2e8f0,transparent)"></div>
        </td></tr>
 
        <!-- Footer -->
        <tr><td style="background:#ffffff;border-radius:0 0 16px 16px;padding:20px 40px">
          <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;text-align:center">
            PulseBook &nbsp;·&nbsp; <a href="https://pulsebook.health" style="color:#00C9A7;text-decoration:none">pulsebook.health</a>
          </p>
        </td></tr>
        
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ==========================================
# 📧 ШАБЛОНЫ ПИСЕМ
# ==========================================

TEMPLATES = {

    "welcome": {
        "en": {
            "subject": "Your personal medical assistant is ready",
            "heading": "Understand your medical results in minutes",
            "body": [
                "PulseBook helps you understand medical results in simple language — without complex terms.",
                "",
                "Upload your first document — it takes just a couple of minutes.",
                "",
                "What you’ll get:",
                "• which values are outside the normal range",
                "• what it may mean",
                "• what to pay attention to",
                "",
                "Example:",
                "Low hemoglobin → possible iron deficiency",
                "",
                "Any document works:",
                "• blood tests &nbsp;• MRI / CT scans &nbsp;• doctor reports &nbsp;• even a phone photo",
            ],
            "cta": "Upload Document",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "ru": {
            "subject": "Ваш персональный медицинский помощник готов",
            "heading": "Поймите свои анализы за несколько минут",
            "body": [
                "PulseBook помогает понять медицинские анализы простым языком — без сложных терминов.",
                "",
                "Загрузите документ — это займёт всего пару минут.",
                "",
                "Что вы получите:",
                "• какие показатели вне нормы",
                "• что это может значить",
                "• на что стоит обратить внимание",
                "",
                "Пример:",
                "Гемоглобин ниже нормы → возможен дефицит железа",
                "",
                "Подойдёт любой документ:",
                "• анализ крови &nbsp;• МРТ / КТ &nbsp;• заключение врача &nbsp;• даже фото с телефона",
            ],
            "cta": "Загрузить документ",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "uk": {
            "subject": "Ваш персональний медичний помічник готовий",
            "heading": "Зрозумійте свої аналізи за кілька хвилин",
            "body": [
                "PulseBook допомагає зрозуміти медичні аналізи простою мовою — без складних термінів.",
                "",
                "Завантажте документ — це займе лише кілька хвилин.",
                "",
                "Що ви отримаєте:",
                "• які показники виходять за межі норми",
                "• що це може означати",
                "• на що варто звернути увагу",
                "",
                "Приклад:",
                "Гемоглобін нижче норми → можливий дефіцит заліза",
                "",
                "Підійде будь-який документ:",
                "• аналіз крові &nbsp;• МРТ / КТ &nbsp;• висновок лікаря &nbsp;• навіть фото з телефону",
            ],
            "cta": "Завантажити документ",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "de": {
            "subject": "Ihr persönlicher medizinischer Assistent ist bereit",
            "heading": "Verstehen Sie Ihre medizinischen Ergebnisse in wenigen Minuten",
            "body": [
                "PulseBook hilft Ihnen, medizinische Ergebnisse einfach zu verstehen — ohne komplexe Fachbegriffe.",
                "",
                "Laden Sie Ihr Dokument hoch — es dauert nur ein paar Minuten.",
                "",
                "Was Sie erhalten:",
                "• welche Werte außerhalb der Norm liegen",
                "• was das bedeuten kann",
                "• worauf Sie achten sollten",
                "",
                "Beispiel:",
                "Niedriger Hämoglobinwert → möglicher Eisenmangel",
                "",
                "Jedes Dokument ist geeignet:",
                "• Bluttests &nbsp;• MRT / CT &nbsp;• Arztberichte &nbsp;• sogar ein Foto vom Handy",
            ],
            "cta": "Dokument hochladen",
            "cta_url": f"{BASE_URL}/dashboard",
        },
    },

    "reminder_24h": {
        "en": {
            "subject": "You haven’t tried PulseBook yet",
            "heading": "Try it with your first document",
            "body": [
                "You created your PulseBook account but haven’t uploaded a document yet.",
                "",
                "Upload any medical file and get a clear explanation of your results.",
                "",
                "Example:",
                "Low hemoglobin → possible iron deficiency",
                "",
                "Any document works:",
                "• blood tests &nbsp;• MRI / CT scans &nbsp;• doctor reports &nbsp;• even a phone photo",
            ],
            "cta": "Upload Document",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "ru": {
            "subject": "Вы ещё не попробовали PulseBook",
            "heading": "Попробуйте с первым документом",
            "body": [
                "Вы зарегистрировались в PulseBook, но ещё не загрузили документ.",
                "",
                "Загрузите любой медицинский файл и получите понятное объяснение результатов.",
                "",
                "Пример:",
                "Гемоглобин ниже нормы → возможен дефицит железа",
                "",
                "Подойдёт любой документ:",
                "• анализ крови &nbsp;• МРТ / КТ &nbsp;• заключение врача &nbsp;• даже фото с телефона",
            ],
            "cta": "Загрузить документ",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "uk": {
            "subject": "Ви ще не спробували PulseBook",
            "heading": "Спробуйте з першим документом",
            "body": [
                "Ви зареєструвалися в PulseBook, але ще не завантажили документ.",
                "",
                "Завантажте будь-який медичний файл і отримайте зрозуміле пояснення результатів.",
                "",
                "Приклад:",
                "Гемоглобін нижче норми → можливий дефіцит заліза",
                "",
                "Підійде будь-який документ:",
                "• аналіз крові &nbsp;• МРТ / КТ &nbsp;• висновок лікаря &nbsp;• навіть фото з телефону",
            ],
            "cta": "Завантажити документ",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "de": {
            "subject": "Sie haben PulseBook noch nicht ausprobiert",
            "heading": "Probieren Sie es mit Ihrem ersten Dokument",
            "body": [
                "Sie haben ein Konto erstellt, aber noch kein Dokument hochgeladen.",
                "",
                "Laden Sie eine medizinische Datei hoch und erhalten Sie eine verständliche Erklärung Ihrer Ergebnisse.",
                "",
                "Beispiel:",
                "Niedriger Hämoglobinwert → möglicher Eisenmangel",
                "",
                "Jedes Dokument ist geeignet:",
                "• Bluttests &nbsp;• MRT / CT &nbsp;• Arztberichte &nbsp;• sogar ein Foto vom Handy",
            ],
            "cta": "Dokument hochladen",
            "cta_url": f"{BASE_URL}/dashboard",
        },
    },

    "reminder_4d": {
        "en": {
            "subject": "You haven’t used PulseBook yet",
            "heading": "Try it with one document",
            "body": [
                "You created a PulseBook account but haven’t used it yet.",
                "",
                "Upload one medical document and see how it works.",
                "",
                "Try asking:",
                "• What do these results mean? &nbsp;• Are these values normal? &nbsp;• What should I monitor?",
                "",
                "It takes just a couple of minutes to get your first result.",
            ],
            "cta": "Upload Document",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "ru": {
            "subject": "Вы так и не попробовали PulseBook",
            "heading": "Попробуйте на одном документе",
            "body": [
                "Вы зарегистрировались в PulseBook, но так и не воспользовались сервисом.",
                "",
                "Загрузите один медицинский документ и посмотрите, как это работает.",
                "",
                "Попробуйте спросить:",
                "• Что означают эти результаты? &nbsp;• Эти значения в норме? &nbsp;• За чем мне следить?",
                "",
                "Это займёт всего пару минут.",
            ],
            "cta": "Загрузить документ",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "uk": {
            "subject": "Ви так і не скористалися PulseBook",
            "heading": "Спробуйте на одному документі",
            "body": [
                "Ви зареєструвалися в PulseBook, але так і не скористалися сервісом.",
                "",
                "Завантажте один медичний документ і подивіться, як це працює.",
                "",
                "Спробуйте запитати:",
                "• Що означають ці результати? &nbsp;• Чи ці значення в нормі? &nbsp;• За чим мені стежити?",
                "",
                "Це займе лише кілька хвилин.",
            ],
            "cta": "Завантажити документ",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "de": {
            "subject": "Sie haben PulseBook noch nicht genutzt",
            "heading": "Probieren Sie es mit einem Dokument",
            "body": [
                "Sie haben ein Konto erstellt, aber den Service noch nicht genutzt.",
                "",
                "Laden Sie ein medizinisches Dokument hoch und sehen Sie, wie es funktioniert.",
                "",
                "Versuchen Sie zu fragen:",
                "• Was bedeuten diese Ergebnisse? &nbsp;• Sind diese Werte normal? &nbsp;• Was sollte ich beobachten?",
                "",
                "Es dauert nur ein paar Minuten.",
            ],
            "cta": "Dokument hochladen",
            "cta_url": f"{BASE_URL}/dashboard",
        },
    },

    "first_document_uploaded": {
        "en": {
            "subject": "Your medical report is ready",
            "heading": "Your document has been analyzed",
            "followup_line": "Answer a few follow-up questions to better understand your situation.",
            "cta": "Discuss Analysis",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "ru": {
            "subject": "Ваш медицинский отчёт готов",
            "heading": "Ваш документ проанализирован",
            "followup_line": "Ответьте на уточняющие вопросы, чтобы точнее понять ситуацию.",
            "cta": "Обсудить анализ",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "uk": {
            "subject": "Ваш медичний звіт готовий",
            "heading": "Ваш документ проаналізовано",
            "followup_line": "Відповідайте на уточнюючі запитання, щоб краще зрозуміти ситуацію.",
            "cta": "Обговорити аналіз",
            "cta_url": f"{BASE_URL}/dashboard",
        },
        "de": {
            "subject": "Ihr medizinischer Bericht ist fertig",
            "heading": "Ihr Dokument wurde analysiert",
            "followup_line": "Beantworten Sie ein paar kurze Fragen, um Ihre Situation besser zu verstehen.",
            "cta": "Analyse besprechen",
            "cta_url": f"{BASE_URL}/dashboard",
        },
    },
}


def get_email_content(email_type: str, lang: str, document_id: int = None, first_message: str = None, doc_title: str = None) -> dict | None:
    template = TEMPLATES.get(email_type)
    if not template:
        return None

    content = template.get(lang) or template.get("en")
    if not content:
        return None

    cta_url = content["cta_url"]
    if document_id and email_type == "first_document_uploaded":
        cta_url = f"{BASE_URL}/dashboard/document/{document_id}/chat"

    # Собираем body_lines
    if email_type == "first_document_uploaded":
        if first_message:
            first_paragraph = first_message.split('\n\n')[0].strip()
        else:
            first_paragraph = ""

        followup = content.get("followup_line", "")

        if first_paragraph:
            body_lines = []
            if doc_title:
                body_lines.append(f"<strong>{doc_title}</strong>")
            body_lines.append(first_paragraph)
            if followup:
                body_lines.append(followup)
        else:
            # Fallback если first_message нет
            body_lines = [followup] if followup else ["Your document has been analyzed."]
    else:
        body_lines = content.get("body", [])

    html = _build_html(
        subject=content["subject"],
        heading=content["heading"],
        body_lines=body_lines,
        cta_text=content["cta"],
        cta_url=cta_url,
    )

    return {
        "subject": content["subject"],
        "html": html,
    }