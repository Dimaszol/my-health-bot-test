# webapp/translations.py
# 🌍 Полная система многоязычности для веб-приложения

"""
Система переводов для Flask веб-приложения с поддержкой 4 языков:
- Русский (ru) 🇷🇺
- Украинский (uk) 🇺🇦
- Английский (en) 🇬🇧
- Немецкий (de) 🇩🇪

Использование в шаблонах:
    {{ t('welcome', lang) }}

Использование в Python:
    from webapp.translations import t
    message = t('welcome', lang='ru')
"""

TRANSLATIONS = {
    # ============================================
    # 🤖 КОНСИЛИУМ AI - компактный блок
    # ============================================
    'ai_consortium_title': {
        'ru': 'PulseBook — первая платформа с консилиумом AI-моделей',
        'en': 'PulseBook — the first platform with an AI consortium',
        'uk': 'PulseBook — перша платформа з консиліумом AI-моделей',
        'de': 'PulseBook — die erste Plattform mit einem KI-Konsortium'
    },
    'ai_consortium_subtitle': {
        'ru': 'Система, где несколько языковых моделей работают вместе над каждым запросом.',
        'en': 'A system where multiple language models work together on each request.',
        'uk': 'Система, де декілька мовних моделей працюють разом над кожним запитом.',
        'de': 'Ein System, bei dem mehrere Sprachmodelle an jeder Anfrage zusammenarbeiten.'
    },
    # ============================================
    # 🎨 HERO ИЛЛЮСТРАЦИЯ (SVG карточки)
    # ============================================
    'hero_svg_card1_title': {
        'ru': 'Загрузите документы',
        'en': 'Upload documents',
        'uk': 'Завантажте документи',
        'de': 'Dokumente hochladen'
    },
    'hero_svg_card1_line1': {
        'ru': 'PDF, фото анализов,',
        'en': 'PDF, test photos,',
        'uk': 'PDF, фото аналізів,',
        'de': 'PDF, Testfotos,'
    },
    'hero_svg_card1_line2': {
        'ru': 'медицинские справки',
        'en': 'medical certificates',
        'uk': 'медичні довідки',
        'de': 'medizinische Bescheinigungen'
    },

    'hero_svg_card2_title': {
        'ru': 'Получите AI-анализ',
        'en': 'Get AI analysis',
        'uk': 'Отримайте AI-аналіз',
        'de': 'KI-Analyse erhalten'
    },
    'hero_svg_card2_line1': {
        'ru': 'Интеллектуальный разбор',
        'en': 'Intelligent analysis',
        'uk': 'Інтелектуальний розбір',
        'de': 'Intelligente Analyse'
    },
    'hero_svg_card2_line2': {
        'ru': 'ваших медданных',
        'en': 'of your medical data',
        'uk': 'ваших медданих',
        'de': 'Ihrer medizinischen Daten'
    },

    'hero_svg_card3_title': {
        'ru': 'Задавайте вопросы',
        'en': 'Ask questions',
        'uk': 'Ставте питання',
        'de': 'Stellen Sie Fragen'
    },
    'hero_svg_card3_line1': {
        'ru': '24/7 консультации',
        'en': '24/7 consultations',
        'uk': '24/7 консультації',
        'de': '24/7 Beratungen'
    },
    'hero_svg_card3_line2': {
        'ru': 'с медицинским AI',
        'en': 'with medical AI',
        'uk': 'з медичним AI',
        'de': 'mit medizinischer KI'
    },

    'hero_svg_card4_title': {
        'ru': 'Храните историю',
        'en': 'Store history',
        'uk': 'Зберігайте історію',
        'de': 'Historie speichern'
    },
    'hero_svg_card4_line1': {
        'ru': 'Вся медицинская история',
        'en': 'All medical history',
        'uk': 'Вся медична історія',
        'de': 'Gesamte Krankengeschichte'
    },
    'hero_svg_card4_line2': {
        'ru': 'в одном месте',
        'en': 'in one place',
        'uk': 'в одному місці',
        'de': 'an einem Ort'
    },
    # ============================================
    # 🏠 ГЛАВНАЯ СТРАНИЦА (index.html)
    # ============================================
    'site_title': {
        'ru': 'Медицинский Ассистент',
        'en': 'Medical Assistant',
        'uk': 'Медичний Асистент',
        'de': 'Medizinischer Assistent'
    },
    'hero_title': {
        'ru': 'Ваш личный медицинский ассистент',
        'en': 'Your Personal Medical Assistant',
        'uk': 'Ваш особистий медичний асистент',
        'de': 'Ihr persönlicher medizinischer Assistent'
    },
    'hero_subtitle': {
        'ru': 'Загружайте медицинские документы, общайтесь с ИИ-помощником и храните всю вашу медицинскую историю в одном месте',
        'en': 'Upload medical documents, chat with AI assistant and store all your medical history in one place',
        'uk': 'Завантажуйте медичні документи, спілкуйтеся з AI-помічником та зберігайте всю вашу медичну історію в одному місці',
        'de': 'Laden Sie medizinische Dokumente hoch, chatten Sie mit dem KI-Assistenten und speichern Sie Ihre gesamte Krankengeschichte an einem Ort'
    },
    'stats_detailed_consultations': {
        'ru': 'Детальных консультаций',
        'uk': 'Детальних консультацій',
        'en': 'Detailed consultations',
        'de': 'Detaillierte Konsultationen'
    },
    'stats_basic_answers': {
        'ru': 'Базовые ответы - в рамках тарифа',
        'uk': 'Базові відповіді - в рамках тарифу',
        'en': 'Basic answers - within the plan',
        'de': 'Grundlegende Antworten - im Rahmen des Tarifs'
    },
    'additional_actions': {
        'ru': 'Дополнительные действия',
        'uk': 'Додаткові дії',
        'en': 'Additional Actions',
        'de': 'Zusätzliche Aktionen'
    },
    'action_connect_telegram': {
        'ru': 'Подключить Telegram',
        'uk': 'Підключити Telegram',
        'en': 'Connect Telegram',
        'de': 'Telegram verbinden'
    },
    'action_connect_telegram_desc': {
        'ru': 'Синхронизация данных с ботом',
        'uk': 'Синхронізація даних з ботом',
        'en': 'Sync data with the bot',
        'de': 'Daten mit dem Bot synchronisieren'
    },  
    'hero_main_title_part1': {
        'ru': 'Загрузите анализ —',
        'en': 'Upload test results —',
        'uk': 'Завантажте аналіз —',
        'de': 'Testergebnisse hochladen —'
    },
    'hero_main_title_highlight': {
        'ru': 'получите понятные медицинские выводы',
        'en': 'get clear medical insights',
        'uk': 'отримайте зрозумілі медичні висновки',
        'de': 'erhalten Sie klare medizinische Einblicke'
    },
    'hero_main_title_part2': {
        'ru': '',
        'en': '', 
        'uk': '',
        'de': ''
    },
    'hero_description': {
        'ru': 'Несколько AI-моделей анализируют документ вместе и формируют единую структурированную сводку. Вы также можете задавать уточняющие вопросы о здоровье в любое время.',
        'en': 'Multiple AI models analyze your document together to produce a single, consolidated summary. You can also ask follow-up questions about your health anytime.',
        'uk': 'Кілька AI-моделей аналізують документ разом і формують єдину структуровану зведену інформацію. Ви також можете ставити уточнювальні питання про здоровʼя у будь-який час.',
        'de': 'Mehrere KI-Modelle analysieren Ihr Dokument gemeinsam und erstellen eine einheitliche, strukturierte Zusammenfassung. Sie können außerdem jederzeit Anschlussfragen zu Ihrer Gesundheit stellen.'
    },
    'btn_try_free': {
        'ru': 'Попробовать бесплатно',
        'en': 'Try it now for free',
        'uk': 'Спробувати безкоштовно',
        'de': 'Jetzt kostenlos ausprobieren'
    },
    'btn_learn_more': {
        'ru': 'Как это работает',
        'en': 'How it works',
        'uk': 'Як це працює',
        'de': 'Wie funktioniert es'
    },
    'btn_google_subtitle': {
        'ru': 'Быстро • Вход через Google • Бесплатно',
        'en': 'Fast • Sign in with Google • Free',
        'uk': 'Швидко • Вхід через Google • Безкоштовно',
        'de': 'Schnell • Anmeldung mit Google • Kostenlos'
    },
    'trustpilot_excellent': {
        'ru': 'Отлично',
        'en': 'Excellent',
        'uk': 'Відмінно',
        'de': 'Ausgezeichnet'
    },
    'trustpilot_rating': {
        'ru': '4.8 из 5 на Trustpilot',
        'en': '4.8 out of 5 on Trustpilot',
        'uk': '4.8 з 5 на Trustpilot',
        'de': '4.8 von 5 auf Trustpilot'
    },
    'btn_get_started': {
        'ru': 'Начать работу',
        'en': 'Get Started',
        'uk': 'Почати роботу',
        'de': 'Jetzt starten'
    },
    'btn_login': {
        'ru': 'Войти',
        'en': 'Login',
        'uk': 'Увійти',
        'de': 'Anmelden'
    },
    'btn_login_google': {
        'ru': 'Войти через Google',
        'en': 'Login with Google',
        'uk': 'Увійти через Google',
        'de': 'Mit Google anmelden'
    },
    'btn_logout': {
        'ru': 'Выход',
        'en': 'Logout',
        'uk': 'Вихід',
        'de': 'Abmelden'
    },
    
    # Секция "Как это работает" (улучшенная версия)
    'how_it_works_title': {
        'ru': 'Как работает PulseBook',
        'en': 'How PulseBook works',
        'uk': 'Як працює PulseBook',
        'de': 'Wie PulseBook funktioniert'
    },

    'how_it_works_subtitle': {
        'ru': 'От загрузки документа до итогового AI-разбора — всего 3 шага',
        'en': 'From document upload to final AI analysis — just 3 steps',
        'uk': 'Від завантаження документа до підсумкового AI-розбору — всього 3 кроки',
        'de': 'Vom Dokumenten-Upload bis zur finalen KI-Analyse — nur 3 Schritte'
    },

    'how_step1_title': {
        'ru': 'Загрузите документ',
        'en': 'Upload document',
        'uk': 'Завантажте документ',
        'de': 'Dokument hochladen'
    },

    'how_step1_text': {
        'ru': 'PDF, фото анализа или медсправку — любой формат принимается системой',
        'en': 'PDF, test photo or medical certificate — any format is accepted',
        'uk': 'PDF, фото аналізу або медичну довідку — будь-який формат приймається',
        'de': 'PDF, Testfoto oder medizinisches Zertifikat — jedes Format wird akzeptiert'
    },

    'how_step2_title': {
        'ru': 'Консилиум AI работает',
        'en': 'AI consortium works',
        'uk': 'Консиліум AI працює',
        'de': 'KI-Konsortium arbeitet'
    },

    'how_step2_text': {
        'ru': 'Несколько AI-моделей анализируют документ и сверяют выводы',
        'en': 'Multiple AI models analyze the document and compare conclusions',
        'uk': 'Декілька AI-моделей аналізують документ та звіряють висновки',
        'de': 'Mehrere KI-Modelle analysieren das Dokument und vergleichen Schlussfolgerungen'
    },

    'how_step3_title': {
        'ru': 'Получите результат',
        'en': 'Get the result',
        'uk': 'Отримайте результат',
        'de': 'Ergebnis erhalten'
    },

    'how_step3_text': {
        'ru': 'Единое итоговое заключение с объяснениями терминов простым языком',
        'en': 'Single consolidated conclusion with terms explained in simple language',
        'uk': 'Єдиний підсумковий висновок з поясненнями термінів простою мовою',
        'de': 'Einheitliche konsolidierte Schlussfolgerung mit Begriffen in einfacher Sprache erklärt'
    },

    'features_title': {
        'ru': 'Что ещё умеет PulseBook',
        'en': 'What else PulseBook can do',
        'uk': 'Що ще вміє PulseBook',
        'de': 'Was PulseBook noch kann'
    },

    'features_subtitle': {
        'ru': 'PulseBook помогает хранить историю, анализировать документы и получать ответы AI 24/7',
        'en': 'PulseBook helps store history, analyze documents and get AI answers 24/7',
        'uk': 'PulseBook допомагає зберігати історію, аналізувати документи та отримувати відповіді AI 24/7',
        'de': 'PulseBook hilft, Verlauf zu speichern, Dokumente zu analysieren und KI-Antworten 24/7 zu erhalten'
    },

    # ============================================
    # 📊 МЕНЮ НАВИГАЦИИ
    # ============================================
    'menu_home': {
        'ru': 'Главная',
        'en': 'Home',
        'uk': 'Головна',
        'de': 'Startseite'
    },
    'menu_dashboard': {
        'ru': 'Кабинет',
        'en': 'Dashboard',
        'uk': 'Кабінет',
        'de': 'Dashboard'
    },
    'menu_chat': {
        'ru': 'Чат с AI',
        'en': 'AI Chat',
        'uk': 'Чат з AI',
        'de': 'KI-Chat'
    },
    'menu_documents': {
        'ru': 'Документы',
        'en': 'Documents',
        'uk': 'Документи',
        'de': 'Dokumente'
    },
    'menu_profile': {
        'ru': 'Профиль',
        'en': 'Profile',
        'uk': 'Профіль',
        'de': 'Profil'
    },
    'menu_how_it_works': {
        'ru': 'Как это работает',
        'en': 'How it works',
        'uk': 'Як це працює',
        'de': 'Wie funktioniert es'
    },
    'menu_features': {
        'ru': 'Возможности',
        'en': 'Features',
        'uk': 'Можливості',
        'de': 'Funktionen'
    },
    'menu_health_tests': {
        'ru': 'Анализы',
        'en': 'Health Tests',
        'uk': 'Аналізи',
        'de': 'Gesundheitstests',
    },
    'footer_navigation': {
        'ru': 'Навигация',
        'en': 'Navigation',
        'uk': 'Навігація',
        'de': 'Navigation'
    },
    'footer_information': {
        'ru': 'Информация',
        'en': 'Information',
        'uk': 'Інформація',
        'de': 'Information'
    },
    'menu_about': {
        'ru': 'О проекте',
        'en': 'About',
        'uk': 'Про проект',
        'de': 'Über uns'
    },
    
    # === БЛОК ВОЗМОЖНОСТИ (обновленные тексты от GPT) ===

    # Карточка 1: Анализ документов
    'feature_upload_title': {
        'ru': 'Анализ документов',
        'en': 'Document Analysis',
        'uk': 'Аналіз документів',
        'de': 'Dokumentenanalyse'
    },

    'feature_upload_text': {
        'ru': 'Загружайте анализы, снимки или заключения врачей — AI извлекает из них всю важную информацию.',
        'en': 'Upload tests, images or doctor reports — AI extracts all important information.',
        'uk': 'Завантажуйте аналізи, знімки або висновки лікарів — AI витягує всю важливу інформацію.',
        'de': 'Laden Sie Tests, Bilder oder Arztberichte hoch — KI extrahiert alle wichtigen Informationen.'
    },

    'feature_upload_list1': {
        'ru': 'Читать PDF, фото, выписки, изображения',
        'en': 'Read PDF, photos, reports, images',
        'uk': 'Читати PDF, фото, виписки, зображення',
        'de': 'PDF, Fotos, Berichte, Bilder lesen'
    },

    'feature_upload_list2': {
        'ru': 'Выделять ключевые показатели (кровь, моча и т.д.)',
        'en': 'Highlight key indicators (blood, urine, etc.)',
        'uk': 'Виділяти ключові показники (кров, сеча тощо)',
        'de': 'Wichtige Indikatoren hervorheben (Blut, Urin usw.)'
    },

    'feature_upload_list3': {
        'ru': 'Анализировать снимки (рентген, МРТ, УЗИ)',
        'en': 'Analyze images (X-ray, MRI, ultrasound)',
        'uk': 'Аналізувати знімки (рентген, МРТ, УЗД)',
        'de': 'Bilder analysieren (Röntgen, MRT, Ultraschall)'
    },

    'feature_upload_list4': {
        'ru': 'Формировать понятное объяснение результата',
        'en': 'Generate clear explanation of results',
        'uk': 'Формувати зрозуміле пояснення результату',
        'de': 'Klare Erklärung der Ergebnisse generieren'
    },

    # Карточка 2: AI-консультант 24/7
    'feature_ai_title_247': {
        'ru': 'AI-консультант 24/7',
        'en': 'AI Consultant 24/7',
        'uk': 'AI-консультант 24/7',
        'de': 'KI-Berater 24/7'
    },

    'feature_ai_text': {
        'ru': 'Задавайте вопросы о здоровье — AI отвечает, учитывая вашу медицинскую историю.',
        'en': 'Ask health questions — AI answers considering your medical history.',
        'uk': 'Ставте питання про здоров\'я — AI відповідає, враховуючи вашу медичну історію.',
        'de': 'Stellen Sie Gesundheitsfragen — KI antwortet unter Berücksichtigung Ihrer Krankengeschichte.'
    },

    'feature_ai_list1': {
        'ru': 'Учитывает вашу историю при формировании ответа',
        'en': 'Considers your history when forming answers',
        'uk': 'Враховує вашу історію при формуванні відповіді',
        'de': 'Berücksichtigt Ihre Geschichte bei der Antwortbildung'
    },

    'feature_ai_list2': {
        'ru': 'Даёт персональный контекстный ответ',
        'en': 'Provides personalized contextual answers',
        'uk': 'Дає персональну контекстну відповідь',
        'de': 'Bietet personalisierte kontextbezogene Antworten'
    },

    'feature_ai_list3': {
        'ru': 'Поясняет медицинские термины простым языком',
        'en': 'Explains medical terms in simple language',
        'uk': 'Пояснює медичні терміни простою мовою',
        'de': 'Erklärt medizinische Begriffe in einfacher Sprache'
    },

    # Карточка 3: Медицинская карта
    'feature_history_title': {
        'ru': 'Медицинская карта',
        'en': 'Medical Record',
        'uk': 'Медична карта',
        'de': 'Medizinische Akte'
    },

    'feature_history_text': {
        'ru': 'Вся ваша медистория всегда под рукой — документы не теряются и автоматически превращаются в краткие записи.',
        'en': 'Your entire medical history always at hand — documents never get lost and are automatically converted to brief notes.',
        'uk': 'Вся ваша медісторія завжди під рукою — документи не губляться та автоматично перетворюються на короткі записи.',
        'de': 'Ihre gesamte Krankengeschichte immer zur Hand — Dokumente gehen nie verloren und werden automatisch in Kurznotizen umgewandelt.'
    },

    'feature_history_list1': {
        'ru': 'Автоматические краткие выдержки под каждым документом',
        'en': 'Automatic brief summaries under each document',
        'uk': 'Автоматичні короткі витяги під кожним документом',
        'de': 'Automatische Kurzzusammenfassungen unter jedem Dokument'
    },

    'feature_history_list2': {
        'ru': 'Возможность скачивать файлы в любой момент',
        'en': 'Download files anytime',
        'uk': 'Можливість завантажувати файли в будь-який момент',
        'de': 'Dateien jederzeit herunterladen'
    },

    'feature_history_list3': {
        'ru': 'AI использует ваши данные для точных рекомендаций',
        'en': 'AI uses your data for accurate recommendations',
        'uk': 'AI використовує ваші дані для точних рекомендацій',
        'de': 'KI verwendet Ihre Daten für genaue Empfehlungen'
    },
   
    'menu_faq': {
        'ru': 'FAQ',
        'en': 'FAQ',
        'uk': 'FAQ',
        'de': 'FAQ'
    },    

    # ============================================
    # ❓ FAQ PREVIEW (ГЛАВНАЯ СТРАНИЦА)
    # ============================================
    'faq_preview_title': {
        'ru': 'Часто задаваемые вопросы',
        'en': 'Frequently Asked Questions',
        'uk': 'Часті запитання',
        'de': 'Häufig gestellte Fragen'
    },
    'faq_preview_q1': {
        'ru': 'Чем PulseBook отличается от обычного AI?',
        'en': 'How is PulseBook different from regular AI?',
        'uk': 'Чим PulseBook відрізняється від звичайного AI?',
        'de': 'Wie unterscheidet sich PulseBook von normaler KI?'
    },
    'faq_preview_a1': {
        'ru': 'PulseBook не ограничивается одной языковой моделью.<br><br>Система сначала определяет тип медицинского документа и подбирает специально обученные профильные AI-модели. Затем несколько моделей независимо анализируют данные и сверяют выводы. После этого формируется единое итоговое заключение, которое помогает снизить риск пропущенных деталей.',
        'en': 'PulseBook is not limited to one language model.<br><br>The system first identifies the type of medical document and selects specially trained AI models. Then multiple models independently analyze the data and cross-check conclusions. Finally, a unified report is formed that helps reduce the risk of missed details.',
        'uk': 'PulseBook не обмежується однією мовною моделлю.<br><br>Система спочатку визначає тип медичного документа та підбирає спеціально навчені профільні AI-моделі. Потім кілька моделей незалежно аналізують дані та звіряють висновки. Після цього формується єдиний підсумковий висновок, який допомагає знизити ризик пропущених деталей.',
        'de': 'PulseBook ist nicht auf ein Sprachmodell beschränkt.<br><br>Das System identifiziert zunächst die Art des medizinischen Dokuments und wählt speziell trainierte KI-Modelle aus. Dann analysieren mehrere Modelle unabhängig die Daten und vergleichen die Ergebnisse. Schließlich wird ein einheitlicher Bericht erstellt, der dazu beiträgt, das Risiko übersehener Details zu verringern.'
    },
    'faq_preview_q2': {
        'ru': 'Заменяет ли PulseBook врача и ставит ли диагнозы?',
        'en': 'Does PulseBook replace a doctor or make diagnoses?',
        'uk': 'Чи замінює PulseBook лікаря та чи ставить діагнози?',
        'de': 'Ersetzt PulseBook einen Arzt oder stellt Diagnosen?'
    },
    'faq_preview_a2': {
        'ru': 'Нет. PulseBook помогает понять анализы и медицинские документы, объясняет показатели и возможные интерпретации. Сервис не заменяет врача и не ставит диагнозы, но помогает подготовиться к консультации и задать правильные вопросы.',
        'en': 'No. PulseBook helps understand tests and medical documents, explains indicators and possible interpretations. The service does not replace a doctor and does not make diagnoses, but helps prepare for a consultation and ask the right questions.',
        'uk': 'Ні. PulseBook допомагає зрозуміти аналізи та медичні документи, пояснює показники та можливі інтерпретації. Сервіс не замінює лікаря та не ставить діагнози, але допомагає підготуватися до консультації та задати правильні питання.',
        'de': 'Nein. PulseBook hilft, Tests und medizinische Dokumente zu verstehen, erklärt Indikatoren und mögliche Interpretationen. Der Service ersetzt keinen Arzt und stellt keine Diagnosen, hilft aber bei der Vorbereitung auf eine Konsultation und beim Stellen der richtigen Fragen.'
    },
    'faq_preview_q3': {
        'ru': 'В безопасности ли мои личные данные?',
        'en': 'Is my personal data safe?',
        'uk': 'Чи в безпеці мої особисті дані?',
        'de': 'Sind meine persönlichen Daten sicher?'
    },
    'faq_preview_a3': {
        'ru': 'Да. Данные передаются и хранятся в зашифрованном виде и всегда доступны вам в личном кабинете. Вы можете в любой момент просмотреть, скачать или удалить отдельный документ, а также полностью удалить аккаунт со всеми данными. Мы соблюдаем требования GDPR, вход осуществляется через защищённый Google-аккаунт.',
        'en': 'Yes. Data is transmitted and stored in encrypted form and is always available to you in your personal account. You can view, download or delete individual documents at any time, as well as completely delete your account with all data. We comply with GDPR requirements, login is via secure Google account.',
        'uk': 'Так. Дані передаються та зберігаються в зашифрованому вигляді та завжди доступні вам в особистому кабінеті. Ви можете в будь-який момент переглянути, завантажити або видалити окремий документ, а також повністю видалити акаунт з усіма даними. Ми дотримуємося вимог GDPR, вхід здійснюється через захищений Google-акаунт.',
        'de': 'Ja. Daten werden verschlüsselt übertragen und gespeichert und sind Ihnen in Ihrem persönlichen Konto jederzeit zugänglich. Sie können jederzeit einzelne Dokumente anzeigen, herunterladen oder löschen sowie Ihr Konto mit allen Daten vollständig löschen. Wir entsprechen den DSGVO-Anforderungen, die Anmeldung erfolgt über ein sicheres Google-Konto.'
    },
    'faq_preview_q4': {
        'ru': 'Нужно ли долго регистрироваться и заполнять формы?',
        'en': 'Do I need to register and fill out long forms?',
        'uk': 'Чи потрібно довго реєструватися та заповнювати форми?',
        'de': 'Muss ich mich lange registrieren und Formulare ausfüllen?'
    },
    'faq_preview_a4': {
        'ru': 'Нет. Вход через Google обеспечивает безопасную авторизацию без паролей. Вы можете сразу загрузить документ — сервис готов к работе без длинных форм и анкет.',
        'en': 'No. Google login provides secure passwordless authorization. You can upload a document right away — the service is ready to work without long forms and questionnaires.',
        'uk': 'Ні. Вхід через Google забезпечує безпечну авторизацію без паролів. Ви можете одразу завантажити документ — сервіс готовий до роботи без довгих форм та анкет.',
        'de': 'Nein. Die Google-Anmeldung bietet sichere passwortlose Autorisierung. Sie können sofort ein Dokument hochladen — der Service ist ohne lange Formulare und Fragebögen einsatzbereit.'
    },
    'faq_preview_more': {
        'ru': 'Остались вопросы? Подробные ответы в разделе',
        'en': 'Have more questions? Detailed answers in the',
        'uk': 'Залишилися питання? Детальні відповіді в розділі',
        'de': 'Haben Sie weitere Fragen? Detaillierte Antworten im'
    },
    
    # ============================================
    # 🚀 ПРИЗЫВ К ДЕЙСТВИЮ
    # ============================================
    'cta_title': {
        'ru': 'Готовы начать заботиться о своём здоровье?',
        'en': 'Ready to start taking care of your health?',
        'uk': 'Готові почати дбати про своє здоров\'я?',
        'de': 'Bereit, sich um Ihre Gesundheit zu kümmern?'
    },
    'cta_description': {
        'ru': 'Присоединяйтесь к людям, которые уже используют AI, чтобы лучше понимать свои медицинские данные',
        'en': 'Join people who are already using AI to better understand their medical data',
        'uk': 'Приєднуйтесь до людей, які вже використовують AI, щоб краще розуміти свої медичні дані',
        'de': 'Schließen Sie sich Menschen an, die bereits KI nutzen, um ihre medizinischen Daten besser zu verstehen'
    },
    'payment_success_heading': {
        'ru': 'Оплата прошла успешно!',
        'en': 'Payment Successful!',
        'uk': 'Оплата пройшла успішно!',
        'de': 'Zahlung erfolgreich!'
    },
    'payment_success_message': {
        'ru': 'Спасибо за покупку! Ваши лимиты обновлены.',
        'en': 'Thank you for your purchase! Your limits have been updated.',
        'uk': 'Дякуємо за покупку! Ваші ліміти оновлено.',
        'de': 'Vielen Dank für Ihren Kauf! Ihre Limits wurden aktualisiert.'
    },
    'go_to_dashboard': {
        'ru': 'Перейти в кабинет',
        'en': 'Go to Dashboard',
        'uk': 'Перейти в кабінет',
        'de': 'Zum Dashboard'
    },
    'auto_redirect_message': {
        'ru': 'Автоматический переход через',
        'en': 'Auto redirect in',
        'uk': 'Автоматичний перехід через',
        'de': 'Automatische Weiterleitung in'
    },
    
    # 🏥 DASHBOARD (Приложение)
    'action_install_app': {
        'ru': 'Установить приложение',
        'en': 'Install App',
        'uk': 'Встановити додаток',
        'de': 'App installieren'
    },
    'action_install_app_desc': {
        'ru': 'Быстрый доступ с главного экрана',
        'en': 'Quick access from home screen',
        'uk': 'Швидкий доступ з головного екрану',
        'de': 'Schnellzugriff vom Startbildschirm'
    },
    'install_app_ios_title': {
        'ru': 'Как установить приложение на iPhone',
        'en': 'How to install app on iPhone',
        'uk': 'Як встановити додаток на iPhone',
        'de': 'App auf iPhone installieren'
    },
    'install_app_ios_step1': {
        'ru': 'Нажмите кнопку "Поделиться" (квадрат со стрелкой) внизу экрана',
        'en': 'Tap the "Share" button (square with arrow) at the bottom',
        'uk': 'Натисніть кнопку "Поділитися" (квадрат зі стрілкою) внизу екрану',
        'de': 'Tippen Sie auf die Schaltfläche "Teilen" (Quadrat mit Pfeil) unten'
    },
    'install_app_ios_step2': {
        'ru': 'Прокрутите вниз и выберите "На экран «Домой»"',
        'en': 'Scroll down and select "Add to Home Screen"',
        'uk': 'Прокрутіть вниз і виберіть "На екран «Домівка»"',
        'de': 'Scrollen Sie nach unten und wählen Sie "Zum Home-Bildschirm"'
    },
    'install_app_ios_step3': {
        'ru': 'Нажмите "Добавить" в правом верхнем углу',
        'en': 'Tap "Add" in the top right corner',
        'uk': 'Натисніть "Додати" у правому верхньому куті',
        'de': 'Tippen Sie oben rechts auf "Hinzufügen"'
    },
    'understood': {
        'ru': 'Понятно',
        'en': 'Got it',
        'uk': 'Зрозуміло',
        'de': 'Verstanden'
    },

    # 🏥 DASHBOARD (Личный кабинет)
    'dashboard_welcome': {
        'ru': 'Добро пожаловать',
        'en': 'Welcome',
        'uk': 'Ласкаво просимо',
        'de': 'Willkommen'
    },
    'dashboard_subtitle': {
        'ru': 'Вся ваша медицинская история — с понятным разбором',
        'en': 'Your complete medical history — with clear explanations',
        'uk': 'Вся ваша медична історія — зі зрозумілим поясненням',
        'de': 'Ihre gesamte Krankengeschichte — mit verständlichen Erklärungen'
    },
    # Після dashboard_subtitle
    'onboarding_upload_title': {
        'ru': 'Начните анализ документа',
        'en': 'Start document analysis',
        'uk': 'Почніть аналіз документа',
        'de': 'Starten Sie die Dokumentenanalyse'
    },
    'onboarding_upload_desc': {
        'ru': 'После загрузки вы получите понятную сводку и ключевые выводы.',
        'en': 'After uploading, you will receive a clear summary and key findings.',
        'uk': 'Після завантаження ви отримаєте зрозуміле зведення та ключові висновки.',
        'de': 'Nach dem Hochladen erhalten Sie eine klare Zusammenfassung und wichtige Erkenntnisse.'
    },
    'onboarding_upload_button': {
        'ru': 'Начать анализ',
        'en': 'Start analysis',
        'uk': 'Почати аналіз',
        'de': 'Analyse starten'
    },
    'onboarding_profile_title': {
        'ru': 'Дополните профиль',
        'en': 'Complete your profile',
        'uk': 'Доповніть профіль',
        'de': 'Profil ergänzen'
    },
    'onboarding_profile_desc': {
        'ru': 'Эти данные учитываются при анализе документов и формировании ответов.',
        'en': 'This information is taken into account when analyzing documents and generating responses.',
        'uk': 'Ці дані враховуються під час аналізу документів та формування відповідей.',
        'de': 'Diese Daten werden bei der Analyse von Dokumenten und der Erstellung von Antworten berücksichtigt.'
    },
    'onboarding_tips_title': {
        'ru': 'Рекомендации для точного анализа',
        'en': 'Recommendations for accurate analysis',
        'uk': 'Рекомендації для точного аналізу',
        'de': 'Empfehlungen für eine präzise Analyse'
    },
    'onboarding_tips_desc': {
        'ru': 'Узнайте, какие факторы влияют на качество анализа и выводов.',
        'en': 'Learn which factors influence the quality of analysis and conclusions.',
        'uk': 'Дізнайтеся, які фактори впливають на якість аналізу та висновків.',
        'de': 'Erfahren Sie, welche Faktoren die Qualität der Analyse und der Schlussfolgerungen beeinflussen.'
    },
    'onboarding_tip1_title': {
        'ru': '1️⃣ Заполненный профиль',
        'en': '1️⃣ Completed profile',
        'uk': '1️⃣ Заповнений профіль',
        'de': '1️⃣ Ausgefülltes Profil'
    },
    'onboarding_tip1_text': {
        'ru': 'Возраст, пол, рост и вес учитываются при интерпретации результатов. Нормальные значения могут отличаться в зависимости от этих параметров. Заполненный профиль позволяет точнее оценивать показатели.',
        'en': 'Age, sex, height and weight are taken into account when interpreting results. Normal values may vary depending on these parameters. A completed profile allows for more accurate evaluation of indicators.',
        'uk': 'Вік, стать, зріст і вага враховуються під час інтерпретації результатів. Нормальні значення можуть відрізнятися залежно від цих параметрів. Заповнений профіль дозволяє точніше оцінювати показники.',
        'de': 'Alter, Geschlecht, Größe und Gewicht werden bei der Interpretation der Ergebnisse berücksichtigt. Normalwerte können je nach diesen Parametern variieren. Ein ausgefülltes Profil ermöglicht eine genauere Bewertung der Werte.'
    },
    'onboarding_tip2_title': {
        'ru': '2️⃣ Качество изображения',
        'en': '2️⃣ Image quality',
        'uk': '2️⃣ Якість зображення',
        'de': '2️⃣ Bildqualität'
    },
    'onboarding_tip2_text': {
        'ru': 'Чёткое изображение без обрезанных фрагментов, бликов и размытия обеспечивает корректное распознавание текста и показателей. Низкое качество может привести к пропуску или искажению данных.',
        'en': 'A clear image without cropped sections, glare or blur ensures accurate recognition of text and indicators. Low quality may lead to missing or distorted data.',
        'uk': 'Чітке зображення без обрізаних фрагментів, відблисків і розмиття забезпечує коректне розпізнавання тексту та показників. Низька якість може призвести до пропуску або спотворення даних.',
        'de': 'Ein klares Bild ohne abgeschnittene Bereiche, Reflexionen oder Unschärfe gewährleistet eine korrekte Erkennung von Text und Werten. Geringe Qualität kann zu fehlenden oder verfälschten Daten führen.'
    },
    'onboarding_tip3_title': {
        'ru': '3️⃣ Правильная ориентация',
        'en': '3️⃣ Correct orientation',
        'uk': '3️⃣ Правильна орієнтація',
        'de': '3️⃣ Richtige Ausrichtung'
    },
    'onboarding_tip3_text': {
        'ru': 'Загружайте документы в правильной ориентации — так, как их обычно читают. Неправильное положение страницы может привести к ошибкам распознавания и искажению выводов.',
        'en': 'Upload documents in the correct reading orientation. Incorrect page positioning may lead to recognition errors and distorted conclusions.',
        'uk': 'Завантажуйте документи у правильній орієнтації — так, як їх зазвичай читають. Неправильне положення сторінки може призвести до помилок розпізнавання та спотворення висновків.',
        'de': 'Laden Sie Dokumente in der korrekten Leseausrichtung hoch. Eine falsche Seitenposition kann zu Erkennungsfehlern und verfälschten Schlussfolgerungen führen.'
    },
    'onboarding_tip4_title': {
        'ru': '4️⃣ Контекст или конкретный вопрос',
        'en': '4️⃣ Context or specific question',
        'uk': '4️⃣ Контекст або конкретне питання',
        'de': '4️⃣ Kontext oder spezifische Frage'
    },
    'onboarding_tip4_text': {
        'ru': 'Если вас интересует конкретный вопрос или есть важный контекст — укажите это при загрузке. Без дополнительной информации документ анализируется изолированно; контекст помогает сосредоточиться на значимых показателях и деталях.',
        'en': 'If you have a specific question or important context, mention it when uploading. Without additional information, the document is analyzed in isolation; context helps focus on the most relevant indicators and details.',
        'uk': 'Якщо у вас є конкретне питання або важливий контекст — вкажіть це під час завантаження. Без додаткової інформації документ аналізується ізольовано; контекст допомагає зосередитися на значущих показниках і деталях.',
        'de': 'Wenn Sie eine konkrete Frage oder wichtigen Kontext haben, geben Sie dies beim Hochladen an. Ohne zusätzliche Informationen wird das Dokument isoliert analysiert; Kontext hilft, sich auf die relevanten Werte und Details zu konzentrieren.'
    },
    'stats_documents_uploaded': {
        'ru': 'Моя медкарта',
        'en': 'My Medical Records',
        'uk': 'Моя медкарта',
        'de': 'Meine Krankenakte'
    },
    'stats_documents_left': {
        'ru': 'Доступно загрузок',
        'en': 'Uploads available',
        'uk': 'Доступно завантажень',
        'de': 'Uploads verfügbar'
    },
    'stats_messages': {
        'ru': 'AI-Консультации',
        'en': 'AI Consultations',
        'uk': 'AI-Консультації',
        'de': 'KI-Beratungen'
    },
    'stats_queries_left': {
        'ru': 'Осталось запросов',
        'en': 'Queries remaining',
        'uk': 'Залишилось запитів',
        'de': 'Verbleibende Anfragen'
    },
    'stats_current_plan': {
        'ru': 'Текущий тариф',
        'en': 'Current Plan',
        'uk': 'Поточний тариф',
        'de': 'Aktueller Tarif'
    },
    'btn_open_chat': {
        'ru': 'Открыть чат',
        'en': 'Open Chat',
        'uk': 'Відкрити чат',
        'de': 'Chat öffnen'
    },
    'btn_upgrade_plan': {
        'ru': 'Обновить план',
        'en': 'Update Plan',
        'uk': 'Оновити план',
        'de': 'Plan aktualisieren'
    },
    'cancel_subscription_title': {
        'ru': 'Отменить подписку',
        'en': 'Cancel Subscription',
        'uk': 'Скасувати підписку',
        'de': 'Abonnement kündigen'
    },
    'cancel_subscription_description': {
        'ru': 'Автоматическое продление будет отключено',
        'en': 'Auto-renewal will be disabled',
        'uk': 'Автоматичне поновлення буде вимкнено',
        'de': 'Automatische Verlängerung wird deaktiviert'
    },
    'cancel_subscription_button': {
        'ru': 'Отменить подписку',
        'en': 'Cancel Subscription',
        'uk': 'Скасувати підписку',
        'de': 'Abonnement kündigen'
    },
    'cancel_modal_title': {
        'ru': 'Подтвердите отмену подписки',
        'en': 'Confirm Subscription Cancellation',
        'uk': 'Підтвердіть скасування підписки',
        'de': 'Abonnementkündigung bestätigen'
    },
    'cancel_modal_warning': {
        'ru': 'Внимание! Это действие нельзя отменить',
        'en': 'Warning! This action cannot be undone',
        'uk': 'Увага! Цю дію не можна скасувати',
        'de': 'Achtung! Diese Aktion kann nicht rückgängig gemacht werden'
    },
    'cancel_modal_info_1': {
        'ru': 'Дальнейшие оплаты производиться не будут',
        'en': 'No further payments will be charged',
        'uk': 'Подальші оплати проводитися не будуть',
        'de': 'Es werden keine weiteren Zahlungen erhoben'
    },
    'cancel_modal_info_2': {
        'ru': 'Текущие лимиты действуют до конца оплаченного периода',
        'en': 'Current limits remain active until the end of paid period',
        'uk': 'Поточні ліміти діють до кінця оплаченого періоду',
        'de': 'Aktuelle Limits bleiben bis zum Ende des bezahlten Zeitraums aktiv'
    },
    'cancel_modal_info_3': {
        'ru': 'Вы сможете оформить подписку заново в любой момент',
        'en': 'You can subscribe again at any time',
        'uk': 'Ви зможете оформити підписку знову в будь-який момент',
        'de': 'Sie können jederzeit erneut abonnieren'
    },
    'cancel_modal_button_back': {
        'ru': 'Назад',
        'en': 'Back',
        'uk': 'Назад',
        'de': 'Zurück'
    },
    'cancel_modal_button_confirm': {
        'ru': 'Подтвердить отмену',
        'en': 'Confirm Cancellation',
        'uk': 'Підтвердити скасування',
        'de': 'Kündigung bestätigen'
    },
    'cancel_success_message': {
        'ru': '✅ Подписка отменена. Автопродление отключено.',
        'en': '✅ Subscription cancelled. Auto-renewal disabled.',
        'uk': '✅ Підписку скасовано. Автопоновлення вимкнено.',
        'de': '✅ Abonnement gekündigt. Automatische Verlängerung deaktiviert.'
    },
    'cancel_error_message': {
        'ru': '❌ Ошибка отмены подписки. Попробуйте позже.',
        'en': '❌ Error cancelling subscription. Please try again later.',
        'uk': '❌ Помилка скасування підписки. Спробуйте пізніше.',
        'de': '❌ Fehler beim Kündigen des Abonnements. Bitte versuchen Sie es später erneut.'
    },
    'quick_actions': {
        'ru': 'Быстрые действия',
        'en': 'Quick Actions',
        'uk': 'Швидкі дії',
        'de': 'Schnellaktionen'
    },
    'action_ask_ai': {
        'ru': 'Задать вопрос AI',
        'en': 'Ask AI',
        'uk': 'Поставити питання AI',
        'de': 'KI fragen'
    },
    'action_ask_ai_desc': {
        'ru': 'Получите консультацию',
        'en': 'Get consultation',
        'uk': 'Отримати консультацію',
        'de': 'Beratung erhalten'
    },
    'action_upload_desc': {
        'ru': 'Анализы, снимки, выписки',
        'en': 'Tests, images, reports',
        'uk': 'Аналізи, знімки, виписки',
        'de': 'Tests, Bilder, Berichte'
    },
    'action_profile': {
        'ru': 'Медицинская анкета',
        'en': 'Medical Profile',
        'uk': 'Медична анкета',
        'de': 'Medizinisches Profil'
    },
    'action_profile_desc': {
        'ru': 'Обновить данные',
        'en': 'Update data',
        'uk': 'Оновити дані',
        'de': 'Daten aktualisieren'
    },
    'recent_activity': {
        'ru': 'Последняя активность',
        'en': 'Recent Activity',
        'uk': 'Остання активність',
        'de': 'Letzte Aktivität'
    },
    'recent_questions': {
        'ru': 'Недавние вопросы',
        'en': 'Recent Questions',
        'uk': 'Останні питання',
        'de': 'Letzte Fragen'
    },
    'tip_of_day': {
        'ru': 'Совет дня',
        'en': 'Tip of the day',
        'uk': 'Порада дня',
        'de': 'Tipp des Tages'
    },    
    'start_ai_conversation': {
        'ru': 'Начните общение с AI',
        'en': 'Start AI conversation',
        'uk': 'Почніть спілкування з AI',
        'de': 'KI-Konversation starten'
    },
    'ask_first_question': {
        'ru': 'Задайте первый вопрос о вашем здоровье',
        'en': 'Ask your first health question',
        'uk': 'Поставте перше питання про ваше здоров\'я',
        'de': 'Stellen Sie Ihre erste Gesundheitsfrage'
    },
    'you': {
        'ru': 'Вы',
        'en': 'You',
        'uk': 'Ви',
        'de': 'Sie'
    },
    'recently': {
        'ru': 'Недавно',
        'en': 'Recently',
        'uk': 'Нещодавно',
        'de': 'Kürzlich'
    },
    'go_to_chat': {
        'ru': 'Перейти в чат',
        'en': 'Go to chat',
        'uk': 'Перейти в чат',
        'de': 'Zum Chat gehen'
    },
    # ============================================
    # 📤 ПРОГРЕСС ЗАГРУЗКИ ДОКУМЕНТОВ
    # ============================================
    
    'progress_completed': {
        'ru': 'Документ успешно обработан!',
        'en': 'Document processed successfully!',
        'uk': 'Документ успішно оброблено!',
        'de': 'Dokument erfolgreich verarbeitet!'
    },    
    "progress_please_wait": {
        "ru": "Анализ занимает около 2 минут. Пожалуйста, не закрывайте и не обновляйте страницу.",
        "en": "The analysis takes about 2 minutes. Please do not close or refresh the page.",
        "uk": "Аналіз займає близько 2 хвилин. Будь ласка, не закривайте та не оновлюйте сторінку.",
        "de": "Die Analyse dauert etwa 2 Minuten. Bitte schließen oder aktualisieren Sie die Seite nicht."
    },
    "progress_notice_sub": {
        "ru": "Документ проходит многоэтапный анализ с использованием специализированных моделей.",
        "en": "The document undergoes multi-stage analysis using specialized models.",
        "uk": "Документ проходить багатоетапний аналіз із використанням спеціалізованих моделей.",
        "de": "Das Dokument durchläuft eine mehrstufige Analyse mit spezialisierten Modellen."
    },
    "progress_step1_title": {
        "ru": "Определяем тип документа",
        "en": "Identifying document type",
        "uk": "Визначаємо тип документа",
        "de": "Dokumenttyp wird ermittelt"
    },
    "progress_step1_sub": {
        "ru": "Подбираем подходящий сценарий анализа",
        "en": "Selecting the appropriate analysis scenario",
        "uk": "Підбираємо відповідний сценарій аналізу",
        "de": "Passendes Analyseszenario wird ausgewählt"
    },
    "progress_step2_title": {
        "ru": "Проводим первичный разбор",
        "en": "Performing initial parsing",
        "uk": "Проводимо первинний розбір",
        "de": "Erste Analyse wird durchgeführt"
    },
    "progress_step2_sub": {
        "ru": "Выделяем ключевые показатели и данные",
        "en": "Extracting key indicators and data",
        "uk": "Виділяємо ключові показники та дані",
        "de": "Wichtige Kennzahlen und Daten werden extrahiert"
    },
    "progress_step3_title": {
        "ru": "Проводим углублённый анализ",
        "en": "Performing in-depth analysis",
        "uk": "Проводимо поглиблений аналіз",
        "de": "Detaillierte Analyse wird durchgeführt"
    },
    "progress_step3_sub": {
        "ru": "Выявляем закономерности и возможные интерпретации",
        "en": "Identifying patterns and possible interpretations",
        "uk": "Виявляємо закономірності та можливі інтерпретації",
        "de": "Muster und mögliche Interpretationen werden identifiziert"
    },
    "progress_step4_title": {
        "ru": "Проверяем и согласуем результаты",
        "en": "Reviewing and validating results",
        "uk": "Перевіряємо та узгоджуємо результати",
        "de": "Ergebnisse werden geprüft und abgestimmt"
    },
    "progress_step4_sub": {
        "ru": "Сопоставляем данные и уточняем результаты",
        "en": "Cross-checking data and refining results",
        "uk": "Зіставляємо дані та уточнюємо результати",
        "de": "Daten werden abgeglichen und Ergebnisse präzisiert"
    },
    "progress_step5_title": {
        "ru": "Формируем итоговый результат",
        "en": "Generating final result",
        "uk": "Формуємо підсумковий результат",
        "de": "Endergebnis wird erstellt"
    },
    "progress_step5_sub": {
        "ru": "Подготавливаем объяснение и сохраняем в медицинскую карту",
        "en": "Preparing the explanation and saving to medical record",
        "uk": "Готуємо пояснення та зберігаємо до медичної картки",
        "de": "Erklärung wird vorbereitet und in die Krankenakte gespeichert"
    },
    # ============================================
    # 📄 СТРАНИЦА ДОКУМЕНТОВ
    # ============================================
    'open_pdf': {
        'ru': 'Посмотреть документ',
        'en': 'View document',
        'uk': 'Переглянути документ',
        'de': 'Dokument ansehen'
    },
    'no_document_limits_title': {
        'ru': 'Лимит документов исчерпан',
        'en': 'Document limit reached',
        'uk': 'Ліміт документів вичерпано',
        'de': 'Dokumentenlimit erreicht'
    },
    'no_document_limits_message': {
        'ru': 'Вы достигли лимита по количеству документов. Оформите подписку или купите дополнительные консультации, чтобы продолжить загрузку.',
        'en': 'You have reached your document limit. Subscribe or purchase additional consultations to continue uploading.',
        'uk': 'Ви досягли ліміту кількості документів. Оформіть підписку або купіть додаткові консультації, щоб продовжити завантаження.',
        'de': 'Sie haben Ihr Dokumentenlimit erreicht. Abonnieren Sie oder kaufen Sie zusätzliche Konsultationen, um weiterhin hochzuladen.'
    },
    'page_documents_title': {
        'ru': 'Моя медкарта',
        'en': 'My Medical Records',
        'uk': 'Моя медкарта',
        'de': 'Meine Krankenakte'
    },    
    'additional_context_label': {
        'ru': 'Контекст или вопрос (необязательно)',
        'en': 'Context or question (optional)',
        'uk': 'Контекст або питання (необовʼязково)',
        'de': 'Kontext oder Frage (optional)'
    },
    'additional_context_placeholder': {
        'ru': 'Например: кашель 2 недели, без температуры, боль в груди, ЭКГ для контроля...',
        'en': 'Example: cough for 2 weeks, no fever, chest pain, ECG for monitoring...',
        'uk': 'Наприклад: кашель 2 тижні, без температури, біль у грудях, ЕКГ для контролю...',
        'de': 'Beispiel: Husten seit 2 Wochen, kein Fieber, Brustschmerzen, EKG zur Kontrolle...'
    },
    'additional_context_hint_description': {
        'ru': 'Помогает точнее интерпретировать результаты.',
        'en': 'Helps interpret results more accurately.',
        'uk': 'Допомагає точніше інтерпретувати результати.',
        'de': 'Hilft, die Ergebnisse genauer zu interpretieren.'
    },
    'select_file': {
        'ru': 'Выберите файл',
        'en': 'Select file',
        'uk': 'Виберіть файл',
        'de': 'Datei auswählen'
    },
    'supported_formats': {
        'ru': 'Форматы: PDF (до 10 стр.), JPG, PNG — до 10 МБ',
        'en': 'Formats: PDF (up to 10 pages), JPG, PNG — up to 10 MB',
        'uk': 'Формати: PDF (до 10 стор.), JPG, PNG — до 10 МБ',
        'de': 'Formate: PDF (bis 10 Seiten), JPG, PNG — bis 10 MB'
    },
    'uploaded_documents': {
        'ru': 'Загруженные документы',
        'en': 'Uploaded documents',
        'uk': 'Завантажені документи',
        'de': 'Hochgeladene Dokumente'
    },
    'btn_upload_document': {
        'ru': 'Добавить документ',
        'en': 'Add document',
        'uk': 'Додати документ',
        'de': 'Dokument hinzufügen'
    },
    'btn_analyze_document': {
        'ru': 'Разобрать документ',
        'en': 'Analyze document',
        'uk': 'Розібрати документ',
        'de': 'Dokument analysieren'
    },
    'stripe_payment_note': {
        'ru': 'Оплата через Stripe · можно отменить на следующем шаге',
        'en': 'Payment via Stripe · can cancel on next step',
        'uk': 'Оплата через Stripe · можна скасувати на наступному кроці',
        'de': 'Zahlung über Stripe · auf nächstem Schritt kündbar'
    },
    'document_uploaded': {
        'ru': 'Загружен',
        'en': 'Uploaded',
        'uk': 'Завантажено',
        'de': 'Hochgeladen'
    },
    'document_type': {
        'ru': 'Тип',
        'en': 'Type',
        'uk': 'Тип',
        'de': 'Typ'
    },
    'document_summary': {
        'ru': 'Краткое содержание',
        'en': 'Summary',
        'uk': 'Короткий зміст',
        'de': 'Zusammenfassung'
    },
    'document_view': {
        'ru': 'Посмотреть',
        'en': 'View',
        'uk': 'Переглянути',
        'de': 'Ansehen'
    },    
    'no_documents_action': {
        'ru': 'Загрузите первый медицинский документ — и PulseBook проведёт комплексный анализ с помощью консилиума AI-моделей. Вы получите ясные объяснения, персональные рекомендации и всю историю здоровья в одном месте.',
        'en': 'Upload your first medical document — and PulseBook will conduct a comprehensive analysis using a consortium of AI models. You will receive clear explanations, personalized recommendations, and all your health history in one place.',
        'uk': 'Завантажте перший медичний документ — і PulseBook проведе комплексний аналіз за допомогою консиліуму AI-моделей. Ви отримаєте зрозумілі пояснення, персональні рекомендації та всю історію здоров\'я в одному місці.',
        'de': 'Laden Sie Ihr erstes medizinisches Dokument hoch — und PulseBook führt eine umfassende Analyse mit einem Konsortium von KI-Modellen durch. Sie erhalten klare Erklärungen, personalisierte Empfehlungen und Ihre gesamte Gesundheitsgeschichte an einem Ort.'
    },
    'unknown': {
        'ru': 'Неизвестно',
        'en': 'Unknown',
        'uk': 'Невідомо',
        'de': 'Unbekannt'
    },
    'please_select_file': {
        'ru': 'Пожалуйста, выберите файл',
        'en': 'Please select a file',
        'uk': 'Будь ласка, виберіть файл',
        'de': 'Bitte wählen Sie eine Datei'
    },
    'confirm_delete_document': {
        'ru': 'Вы уверены что хотите удалить этот документ?',
        'en': 'Are you sure you want to delete this document?',
        'uk': 'Ви впевнені, що хочете видалити цей документ?',
        'de': 'Sind Sie sicher, dass Sie dieses Dokument löschen möchten?'
    },
    'document_deleted': {
        'ru': 'Документ удалён',
        'en': 'Document deleted',
        'uk': 'Документ видалено',
        'de': 'Dokument gelöscht'
    },    
    'upload_birth_year_tip': {
        'ru': 'Возраст и пол влияют на анализ медицинских данных. Эти данные можно указать в профиле.',
        'en': 'Age and gender affect the analysis of medical data. This information can be specified in your profile.',
        'uk': 'Вік і стать впливають на аналіз медичних даних. Ці дані можна вказати в профілі.',
        'de': 'Alter und Geschlecht beeinflussen die Analyse medizinischer Daten. Diese Angaben können im Profil hinterlegt werden.'
    },
    'document_limit_reached_title': {
        'ru': 'Лимит документов в текущем плане достигнут',
        'en': 'Document limit in current plan reached',
        'uk': 'Ліміт документів у поточному плані досягнуто',
        'de': 'Dokumentenlimit im aktuellen Plan erreicht'
    },    
    'one_time_document_button': {
        'ru': 'Разобрать документ — ',
        'en': 'Analyze document — ',
        'uk': 'Розібрати документ — ',
        'de': 'Dokument analysieren — '
    },
    'one_time_payment_note': {
        'ru': 'Разовый платёж · без подписки',
        'en': 'One-time payment · no subscription',
        'uk': 'Разовий платіж · без підписки',
        'de': 'Einmalige Zahlung · kein Abonnement'
    },
    'subscribe_button': {
        'ru': 'Оформить подписку',
        'en': 'Subscribe',
        'uk': 'Оформити підписку',
        'de': 'Abonnieren'
    },
    'month_short': {
        'ru': 'мес',
        'en': 'mo',
        'uk': 'міс',
        'de': 'Monat'
    },

    # ============================================
    # 📘 ЛЕГЕНДА ДОКУМЕНТОВ
    # ============================================
    'legend_title': {
        'ru': 'Как читать карточки документов',
        'en': 'How to read document cards',
        'uk': 'Як читати картки документів',
        'de': 'So lesen Sie Dokumentkarten'
    },
    'legend_download': {
        'ru': 'Скачать исходный документ',
        'en': 'Download original document',
        'uk': 'Завантажити вихідний документ',
        'de': 'Originaldokument herunterladen'
    },    
    'legend_delete': {
        'ru': 'Удалить документ и запись',
        'en': 'Delete document and record',
        'uk': 'Видалити документ і запис',
        'de': 'Dokument und Eintrag löschen'
    },
    'legend_edit': {
        'ru': 'Редактировать название или дату документа',
        'en': 'Edit document name or date',
        'uk': 'Редагувати назву або дату документа',
        'de': 'Dokumentname oder -datum bearbeiten'
    },
    'legend_toggle': {
        'ru': 'Учитывать / не учитывать',
        'en': 'Include / exclude',
        'uk': 'Враховувати / не враховувати',
        'de': 'Einbeziehen / ausschließen'
    },
    'legend_toggle_desc': {
        'ru': 'Если тумблер включён, ИИ использует документ при ответах в чате и анализе последующих документов.',
        'en': 'If the toggle is enabled, the AI will use the document when answering in chat and when analyzing subsequent documents.',
        'uk': 'Якщо перемикач увімкнений, ШІ використовує документ під час відповідей у чаті та аналізу наступних документів.',
        'de': 'Wenn der Schalter aktiviert ist, verwendet die KI das Dokument bei Antworten im Chat und bei der Analyse nachfolgender Dokumente.'
    },
    'legend_analysis': {
        'ru': 'Полный разбор',
        'en': 'Full Analysis',
        'uk': 'Повний розбір',
        'de': 'Vollständige Analyse'
    },
    'back_to_documents': {
        'ru': 'Назад к документам',
        'en': 'Back to documents',
        'uk': 'Назад до документів',
        'de': 'Zurück zu Dokumenten'
    },
    'date_unknown': {
        'ru': 'Дата неизвестна',
        'en': 'Date unknown',
        'uk': 'Дата невідома',
        'de': 'Datum unbekannt'
    },
    'context_label': {
        'ru': 'Контекст',
        'en': 'Context',
        'uk': 'Контекст',
        'de': 'Kontext'
    },
    'preview_unavailable': {
        'ru': 'Предпросмотр недоступен для этого типа файла',
        'en': 'Preview unavailable for this file type',
        'uk': 'Попередній перегляд недоступний для цього типу файлу',
        'de': 'Vorschau für diesen Dateityp nicht verfügbar'
    },
    'first_analysis_title': {
        'ru': 'Первичный анализ',
        'en': 'Initial Analysis',
        'uk': 'Первинний аналіз',
        'de': 'Erstanalyse'
    },
    'first_analysis_description': {
        'ru': 'Анализ данных и формирование клинических рамок для дальнейшего обсуждения. Не является медицинским заключением.',
        'en': 'Data analysis and formation of clinical framework for further discussion. Not a medical conclusion.',
        'uk': 'Аналіз даних та формування клінічних рамок для подальшого обговорення. Не є медичним висновком.',
        'de': 'Datenanalyse und Bildung des klinischen Rahmens für weitere Diskussionen. Keine medizinische Schlussfolgerung.'
    },
    
    'legend_analysis_desc': {
        'ru': 'Подробный анализ документа с интерпретациями нескольких ИИ-моделей.',
        'en': 'Detailed analysis of the document with interpretations from multiple AI models.',
        'uk': 'Детальний аналіз документа з інтерпретаціями кількох ШІ-моделей.',
        'de': 'Detaillierte Analyse des Dokuments mit Interpretationen mehrerer KI-Modelle.'
    },
    'legend_warning': {
        'ru': 'Здесь представлены рассуждения и возможные интерпретации. Это не диагноз и не медицинское заключение. Раздел помогает лучше понять документ и может быть полезен врачу при очной оценке',
        'en': 'This section presents reasoning and possible interpretations. This is not a diagnosis or medical conclusion. The section helps to better understand the document and may be useful to a doctor during an in-person evaluation',
        'uk': 'Тут представлені міркування та можливі інтерпретації. Це не діагноз і не медичний висновок. Розділ допомагає краще зрозуміти документ і може бути корисним лікарю при очній оцінці',
        'de': 'Dieser Abschnitt enthält Überlegungen und mögliche Interpretationen. Dies ist keine Diagnose oder medizinische Schlussfolgerung. Der Abschnitt hilft, das Dokument besser zu verstehen und kann für einen Arzt bei einer persönlichen Bewertung nützlich sein'
    },
    'legend_summary': {
        'ru': 'Сводка',
        'en': 'Summary',
        'uk': 'Зведення',
        'de': 'Zusammenfassung'
    },
    'legend_summary_desc': {
        'ru': 'Краткое описание ключевых наблюдений по документу',
        'en': 'Brief description of key observations from the document',
        'uk': 'Короткий опис ключових спостережень по документу',
        'de': 'Kurze Beschreibung der wichtigsten Beobachtungen aus dem Dokument'
    },
    'legend_discuss': {
        'ru': 'Обсудить',
        'en': 'Discuss',
        'uk': 'Обговорити',
        'de': 'Besprechen'
    },
    'legend_discuss_desc': {
        'ru': 'Отдельный чат по документу. Позволяет детально разобрать его показатели и получить ответы на вопросы',
        'en': 'Separate chat for the document. Allows detailed analysis of its indicators and answers to questions',
        'uk': 'Окремий чат по документу. Дозволяє детально розібрати його показники та отримати відповіді на питання',
        'de': 'Separater Chat für das Dokument. Ermöglicht detaillierte Analyse der Indikatoren und Antworten auf Fragen'
    },
    'legend_indicator_normal': {
        'ru': ' — значимых отклонений не выявлено',
        'en': ' — no significant deviations detected',
        'uk': ' — значних відхилень не виявлено',
        'de': ' — keine signifikanten Abweichungen festgestellt'
    },
    'legend_indicator_attention': {
        'ru': ' — есть находки, требующие внимания или уточнения',
        'en': ' — findings requiring attention or clarification',
        'uk': ' — є знахідки, що потребують уваги або уточнення',
        'de': ' — Befunde, die Aufmerksamkeit oder Klärung erfordern'
    },
    'legend_indicator_serious': {
        'ru': ' — потенциально серьёзные изменения, рекомендуется обсудить с врачом',
        'en': ' — potentially serious changes, recommended to discuss with a doctor',
        'uk': ' — потенційно серйозні зміни, рекомендується обговорити з лікарем',
        'de': ' — potenziell ernsthafte Veränderungen, Besprechung mit einem Arzt empfohlen'
    },

    # ============================================
    # 📤 ЗАГРУЗКА ДОКУМЕНТОВ - API сообщения
    # ============================================
    'file_not_selected': {
        'ru': 'Файл не выбран',
        'en': 'File not selected',
        'uk': 'Файл не вибрано',
        'de': 'Datei nicht ausgewählt'
    },
    'unsupported_file_type': {
        'ru': '❌ Неподдерживаемый тип файла. Разрешены: PDF, DOCX, TXT, JPG, PNG',
        'en': '❌ Unsupported file type. Allowed: PDF, DOCX, TXT, JPG, PNG',
        'uk': '❌ Непідтримуваний тип файлу. Дозволено: PDF, DOCX, TXT, JPG, PNG',
        'de': '❌ Nicht unterstützter Dateityp. Erlaubt: PDF, DOCX, TXT, JPG, PNG'
    },
    'pdf_read_failed': {
        'ru': '❌ Не удалось прочитать PDF файл. Возможно, он повреждён или защищён паролем.',
        'en': '❌ Failed to read PDF file. It may be corrupted or password-protected.',
        'uk': '❌ Не вдалося прочитати PDF файл. Можливо, він пошкоджений або захищений паролем.',
        'de': '❌ PDF-Datei konnte nicht gelesen werden. Sie ist möglicherweise beschädigt oder passwortgeschützt.'
    },
    'pdf_processing_error': {
        'ru': '❌ Ошибка обработки PDF. Попробуйте конвертировать файл в изображение.',
        'en': '❌ PDF processing error. Try converting the file to an image.',
        'uk': '❌ Помилка обробки PDF. Спробуйте конвертувати файл у зображення.',
        'de': '❌ PDF-Verarbeitungsfehler. Versuchen Sie, die Datei in ein Bild zu konvertieren.'
    },
    'image_analysis_error': {
        'ru': '❌ Ошибка анализа изображения. Убедитесь что изображение чёткое и текст читаемый.',
        'en': '❌ Image analysis error. Make sure the image is clear and the text is readable.',
        'uk': '❌ Помилка аналізу зображення. Переконайтеся, що зображення чітке і текст читабельний.',
        'de': '❌ Bildanalysefehler. Stellen Sie sicher, dass das Bild klar und der Text lesbar ist.'
    },
    'file_read_error': {
        'ru': '❌ Не удалось прочитать файл. Проверьте кодировку (должна быть UTF-8 или Windows-1251).',
        'en': '❌ Failed to read file. Check encoding (should be UTF-8 or Windows-1251).',
        'uk': '❌ Не вдалося прочитати файл. Перевірте кодування (має бути UTF-8 або Windows-1251).',
        'de': '❌ Datei konnte nicht gelesen werden. Überprüfen Sie die Kodierung (sollte UTF-8 oder Windows-1251 sein).'
    },
    'not_medical_doc': {
        'ru': '❌ Это не медицинский документ. Пожалуйста, загрузите анализы, снимки или заключения врачей.',
        'en': '❌ This is not a medical document. Please upload test results, images or medical reports.',
        'uk': '❌ Це не медичний документ. Будь ласка, завантажте аналізи, знімки або висновки лікарів.',
        'de': '❌ Dies ist kein medizinisches Dokument. Bitte laden Sie Testergebnisse, Bilder oder Arztberichte hoch.'
    },
    'file_storage_error': {
        'ru': '❌ Ошибка сохранения файла на сервере. Попробуйте ещё раз или обратитесь в поддержку.',
        'en': '❌ File storage error on server. Please try again or contact support.',
        'uk': '❌ Помилка збереження файлу на сервері. Спробуйте ще раз або зверніться до підтримки.',
        'de': '❌ Dateispeicherfehler auf dem Server. Bitte versuchen Sie es erneut oder wenden Sie sich an den Support.'
    },
    'document_uploaded_successfully': {
        'ru': '✅ Документ успешно загружен и обработан!\n\n📄 <b>{title}</b>\n\nДокумент проанализирован AI и добавлен в вашу медицинскую карту.',
        'en': '✅ Document successfully uploaded and processed!\n\n📄 <b>{title}</b>\n\nThe document has been analyzed by AI and added to your medical records.',
        'uk': '✅ Документ успішно завантажено і оброблено!\n\n📄 <b>{title}</b>\n\nДокумент проаналізовано AI і додано до вашої медичної картки.',
        'de': '✅ Dokument erfolgreich hochgeladen und verarbeitet!\n\n📄 <b>{title}</b>\n\nDas Dokument wurde von AI analysiert und zu Ihrer Krankenakte hinzugefügt.'
    },
    'document_processing_error': {
        'ru': '❌ Произошла ошибка при обработке документа. Попробуйте ещё раз или обратитесь в поддержку.',
        'en': '❌ An error occurred while processing the document. Please try again or contact support.',
        'uk': '❌ Сталася помилка при обробці документа. Спробуйте ще раз або зверніться до підтримки.',
        'de': '❌ Beim Verarbeiten des Dokuments ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut oder wenden Sie sich an den Support.'
    },

    # ============================================
    # 🏥 MEDICAL TIMELINE НА СТРАНИЦЕ ДОКУМЕНТОВ
    # ============================================
    'medical_timeline_extracted': {
        'ru': 'Извлечено из документа',
        'uk': 'Витягнуто з документа',
        'en': 'Extracted from document',
        'de': 'Aus dem Dokument extrahiert'
    },
    
    'importance_critical': {
        'ru': 'Критически важно',
        'uk': 'Критично важливо',
        'en': 'Critical',
        'de': 'Kritisch'
    },
    
    'importance_important': {
        'ru': 'Важно',
        'uk': 'Важливо',
        'en': 'Important',
        'de': 'Wichtig'
    },
    
    'importance_normal': {
        'ru': 'Обычное',
        'uk': 'Звичайне',
        'en': 'Normal',
        'de': 'Normal'
    },

    # ============================================
    # 🔽 КНОПКИ ДОКУМЕНТОВ
    # ============================================
    'btn_download': {
        'ru': 'Скачать',
        'uk': 'Завантажити',
        'en': 'Download',
        'de': 'Herunterladen'
    },
    
    'btn_show': {
        'ru': 'Сводка',
        'uk': 'Зведення',
        'en': 'Summary',
        'de': 'Zusammenfassung'
    },

    'btn_hide': {
        'ru': 'Скрыть',
        'en': 'Hide',
        'uk': 'Приховати',
        'de': 'Ausblenden'
    },
    'document_confirmed_enabled': {
        'ru': 'Документ учитывается в ответах ИИ',
        'en': 'Document is included in AI responses',
        'uk': 'Документ враховується у відповідях ШІ',
        'de': 'Dokument wird in KI-Antworten berücksichtigt'
    },
    'document_confirmed_disabled': {
        'ru': 'Документ НЕ учитывается в ответах ИИ',
        'en': 'Document is NOT included in AI responses',
        'uk': 'Документ НЕ враховується у відповідях ШІ',
        'de': 'Dokument wird NICHT in KI-Antworten berücksichtigt'
    },
    'toggle_document_in_chat': {
        'ru': 'Учитывать в памяти чата',
        'en': 'Include in chat memory',
        'uk': 'Враховувати в пам\'яті чату',
        'de': 'In Chat-Speicher einbeziehen'
    },
    'btn_detailed_analysis': {
        'ru': 'Полный разбор',
        'en': 'Full Analysis',
        'uk': 'Повний розбір',
        'de': 'Vollständige Analyse'
    },
    'document_updated': {
        'ru': 'Документ успешно обновлён',
        'en': 'Document updated successfully',
        'uk': 'Документ успішно оновлено',
        'de': 'Dokument erfolgreich aktualisiert'
    },
    'btn_discuss': {
        'ru': 'Обсудить',
        'en': 'Discuss',
        'uk': 'Обговорити',
        'de': 'Besprechen'
    },
    'document_discussion': {
        'ru': 'Консультация по документу',
        'uk': 'Консультація щодо документа',
        'en': 'Consultation on the document',
        'de': 'Beratung zum Dokument'
    },    
    'upgrade_plan': {
        'ru': 'Лимит детальных консультаций достигнут — получить ещё',
        'en': 'Detailed consultation limit reached — get more',
        'uk': 'Ліміт детальних консультацій досягнуто — отримати ще',
        'de': 'Limit für detaillierte Beratungen erreicht — weitere erhalten'
    },
    'document_chat_requires_premium': {
        'ru': 'Обсуждение документа доступно при наличии детальных консультаций',
        'en': 'Document discussion available with detailed consultations',
        'uk': 'Обговорення документа доступне за наявності детальних консультацій',
        'de': 'Dokumentendiskussion verfügbar mit detaillierten Beratungen'
    },
    'use_medical_history_toggle': {
        'ru': 'Учитывать историю медкарты',
        'en': 'Use medical history in analysis',
        'uk': 'Враховувати історію медкарти',
        'de': 'Krankengeschichte in der Analyse berücksichtigen'
    },
    'use_medical_history_on': {
        'ru': 'Учтена история медкарты',
        'en': 'Medical history included in analysis',
        'uk': 'Враховано історію медкарти',
        'de': 'Krankengeschichte wurde berücksichtigt'
    },
    'use_medical_history_off': {
        'ru': 'Анализ только по загруженному документу',
        'en': 'Analysis based only on the uploaded document',
        'uk': 'Аналіз лише за завантаженим документом',
        'de': 'Analyse nur anhand des hochgeladenen Dokuments'
    },
    'use_medical_history_tooltip': {
        'ru': 'Учитывать предыдущие анализы при анализе документа',
        'en': 'Use previous analyses when analyzing the document',
        'uk': 'Враховувати попередні аналізи при аналізі документа',
        'de': 'Frühere Analysen bei der Dokumentenanalyse berücksichtigen'
    },
    'one_document_upsell': {
        'ru': 'Ваш первый анализ готов. Добавьте другие медицинские документы, чтобы анализ учитывал историю медкарты и изменения показателей со временем.',
        'en': 'Your first analysis is ready. Add other medical documents so the analysis can consider your medical history and changes in results over time.',
        'uk': 'Ваш перший аналіз готовий. Додайте інші медичні документи, щоб аналіз враховував історію медкарти та зміни показників з часом.',
        'de': 'Ihre erste Analyse ist fertig. Fügen Sie weitere medizinische Dokumente hinzu, damit die Analyse die Krankengeschichte und Veränderungen der Werte im Laufe der Zeit berücksichtigen kann.'
    },
    
    # ============================================
    # 💬 СТРАНИЦА ЧАТА
    # ============================================
    'page_chat_title': {
        'ru': 'Чат с ИИ-ассистентом',
        'en': 'Chat with AI Assistant',
        'uk': 'Чат з AI-асистентом',
        'de': 'Chat mit KI-Assistent'
    },
    'page_chat_subtitle': {
        'ru': 'Задавайте вопросы о вашем здоровье. ИИ использует ваши медицинские документы для ответов.',
        'en': 'Ask questions about your health. AI uses your medical documents to answer.',
        'uk': 'Ставте питання про ваше здоров\'я. AI використовує ваші медичні документи для відповідей.',
        'de': 'Stellen Sie Fragen zu Ihrer Gesundheit. KI verwendet Ihre medizinischen Dokumente für Antworten.'
    },
    'chat_greeting': {
        'ru': 'Привет! Я ваш персональный медицинский ассистент.',
        'en': 'Hello! I am your personal medical assistant.',
        'uk': 'Привіт! Я ваш персональний медичний асистент.',
        'de': 'Hallo! Ich bin Ihr persönlicher medizinischer Assistent.'
    },
    'chat_intro_text': {
        'ru': 'Я анализирую ваши документы, историю и симптомы. Задайте любой вопрос о здоровье — ответы будут персональными и контекстными.',
        'en': 'I analyze your documents, history, and symptoms. Ask any health question — answers will be personalized and contextual.',
        'uk': 'Я аналізую ваші документи, історію та симптоми. Поставте будь-яке питання про здоров\'я — відповіді будуть персональними та контекстними.',
        'de': 'Ich analysiere Ihre Dokumente, Krankengeschichte und Symptome. Stellen Sie eine Frage zur Gesundheit — die Antworten sind personalisiert und kontextbezogen.'
    },
    'chat_tips_title': {
        'ru': 'Чтобы получить максимально точные рекомендации:',
        'en': 'To get the most accurate recommendations:',
        'uk': 'Щоб отримати максимально точні рекомендації:',
        'de': 'Um die genauesten Empfehlungen zu erhalten:'
    },
    'chat_tip1_title': {
        'ru': '1. Заполните профиль.',
        'en': '1. Fill out your profile.',
        'uk': '1. Заповніть профіль.',
        'de': '1. Füllen Sie Ihr Profil aus.'
    },
    'chat_tip1_text': {
        'ru': 'Так мои ответы будут точнее и более персональными.',
        'en': 'This will make my answers more accurate and personalized.',
        'uk': 'Так мої відповіді будуть точнішими та більш персональними.',
        'de': 'So werden meine Antworten genauer und personalisierter.'
    },
    'chat_tip2_title': {
        'ru': '2. Проверьте медкарту.',
        'en': '2. Review your medical records.',
        'uk': '2. Перевірте медкарту.',
        'de': '2. Überprüfen Sie Ihre Krankenakte.'
    },
    'chat_tip2_text': {
        'ru': 'Выберите, какие документы будут учитываться при формировании ответа — просто переключайте тумблер «Учитывать в чате».',
        'en': 'Choose which documents should be considered in responses — just toggle "Consider in chat".',
        'uk': 'Виберіть, які документи будуть враховуватися при формуванні відповіді — просто перемикайте тумблер «Враховувати в чаті».',
        'de': 'Wählen Sie aus, welche Dokumente bei der Antwortbildung berücksichtigt werden — schalten Sie einfach "Im Chat berücksichtigen" um.'
    },
    'chat_placeholder': {
        'ru': 'Напишите ваш вопрос...',
        'en': 'Type your question...',
        'uk': 'Напишіть ваше питання...',
        'de': 'Geben Sie Ihre Frage ein...'
    },
    'btn_send': {
        'ru': 'Отправить',
        'en': 'Send',
        'uk': 'Відправити',
        'de': 'Senden'
    },
    'chat_examples_title': {
        'ru': 'Примеры вопросов',
        'en': 'Example questions',
        'uk': 'Приклади питань',
        'de': 'Beispielfragen'
    },
    'chat_example_1': {
        'ru': 'Какие анализы у меня в последнем документе?',
        'en': 'What tests are in my latest document?',
        'uk': 'Які аналізи у мене в останньому документі?',
        'de': 'Welche Tests sind in meinem letzten Dokument?'
    },
    'chat_example_2': {
        'ru': 'Есть ли у меня показатели вне нормы?',
        'en': 'Do I have any abnormal values?',
        'uk': 'Чи є у мене показники поза нормою?',
        'de': 'Habe ich abnormale Werte?'
    },
    'chat_example_3': {
        'ru': 'Что означает диагноз из последнего заключения?',
        'en': 'What does the diagnosis from the last report mean?',
        'uk': 'Що означає діагноз з останнього висновку?',
        'de': 'Was bedeutet die Diagnose aus dem letzten Bericht?'
    },
    'chat_example_4': {
        'ru': 'Какие рекомендации дал врач?',
        'en': 'What recommendations did the doctor give?',
        'uk': 'Які рекомендації дав лікар?',
        'de': 'Welche Empfehlungen hat der Arzt gegeben?'
    },
    
    # ============================================
    # 👤 СТРАНИЦА ПРОФИЛЯ
    # ============================================
    'page_profile_title': {
        'ru': 'Мой профиль',
        'en': 'My Profile',
        'uk': 'Мій профіль',
        'de': 'Mein Profil'
    },
    'page_profile_subtitle': {
        'ru': 'Управление вашей медицинской анкетой',
        'en': 'Manage your medical profile',
        'uk': 'Керування вашою медичною анкетою',
        'de': 'Verwalten Sie Ihr medizinisches Profil'
    },
    'profile_basic_info': {
        'ru': 'Основная информация',
        'en': 'Basic Information',
        'uk': 'Основна інформація',
        'de': 'Grundinformationen'
    },
    'profile_name': {
        'ru': 'Имя',
        'en': 'Name',
        'uk': 'Ім\'я',
        'de': 'Name'
    },
    'profile_email': {
        'ru': 'Email',
        'en': 'Email',
        'uk': 'Email',
        'de': 'E-Mail'
    },
    'profile_registered': {
        'ru': 'Зарегистрирован',
        'en': 'Registered',
        'uk': 'Зареєстровано',
        'de': 'Registriert'
    },
    'profile_medical_form': {
        'ru': 'Медицинская анкета',
        'en': 'Medical Form',
        'uk': 'Медична анкета',
        'de': 'Medizinisches Formular'
    },
    'profile_medical_form_desc': {
        'ru': 'Эта информация помогает ИИ давать более точные рекомендации',
        'en': 'This information helps AI provide more accurate recommendations',
        'uk': 'Ця інформація допомагає AI давати більш точні рекомендації',
        'de': 'Diese Informationen helfen der KI, genauere Empfehlungen zu geben'
    },
    'profile_birth_year': {
        'ru': 'Год рождения',
        'en': 'Birth Year',
        'uk': 'Рік народження',
        'de': 'Geburtsjahr'
    },
    'birth_year_invalid': {
        'ru': '⚠️ Введите корректный год рождения. Вам должно быть не менее 18 лет.',
        'en': '⚠️ Please enter a valid birth year. You must be at least 18 years old.',
        'uk': '⚠️ Введіть коректний рік народження. Вам має бути не менше 18 років.',
        'de': '⚠️ Bitte geben Sie ein gültiges Geburtsjahr ein. Sie müssen mindestens 18 Jahre alt sein.'
    },
    'profile_gender': {
        'ru': 'Пол',
        'en': 'Gender',
        'uk': 'Стать',
        'de': 'Geschlecht'
    },
    'profile_height': {
        'ru': 'Рост',
        'en': 'Height',
        'uk': 'Зріст',
        'de': 'Größe'
    },
    'profile_weight': {
        'ru': 'Вес',
        'en': 'Weight',
        'uk': 'Вага',
        'de': 'Gewicht'
    },
    'profile_chronic_conditions': {
        'ru': 'Хронические заболевания',
        'en': 'Chronic Conditions',
        'uk': 'Хронічні захворювання',
        'de': 'Chronische Erkrankungen'
    },
    'profile_allergies': {
        'ru': 'Аллергии',
        'en': 'Allergies',
        'uk': 'Алергії',
        'de': 'Allergien'
    },
    'profile_medications': {
        'ru': 'Принимаемые лекарства',
        'en': 'Medications taken',
        'uk': 'Ліки, що приймаються',
        'de': 'Eingenommene Medikamente'
    },
    'profile_lifestyle': {
        'ru': 'Образ жизни',
        'en': 'Lifestyle',
        'uk': 'Спосіб життя',
        'de': 'Lebensstil'
    },
    'profile_smoking': {
        'ru': 'Курение',
        'en': 'Smoking',
        'uk': 'Куріння',
        'de': 'Rauchen'
    },
    'profile_alcohol': {
        'ru': 'Алкоголь',
        'en': 'Alcohol',
        'uk': 'Алкоголь',
        'de': 'Alkohol'
    },
    'profile_physical_activity': {
        'ru': 'Активность',
        'en': 'Activity',
        'uk': 'Активність',
        'de': 'Aktivität'
    },
    'profile_how_to_fill': {
        'ru': 'Зачем заполнять анкету?',
        'en': 'Why fill out the form?',
        'uk': 'Навіщо заповнювати анкету?',
        'de': 'Warum sollte ich das Formular ausfüllen?'
    },
    
    'profile_fill_instruction': {
        'ru': 'Данные из анкеты используются ИИ наряду с вашими документами. Это позволяет анализировать ответы в контексте именно вашей ситуации и давать более персональные рекомендации.',
        'en': 'The data from your form is used by the AI alongside your documents. This helps analyze responses in the context of your situation and provide more personalized recommendations.',
        'uk': 'Дані з анкети використовуються ШІ разом із вашими документами. Це допомагає аналізувати відповіді у контексті саме вашої ситуації та надавати більш персональні рекомендації.',
        'de': 'Die Daten aus Ihrem Formular werden zusammen mit Ihren Dokumenten von der KI verwendet. Dadurch können Antworten im Kontext Ihrer Situation analysiert und persönlichere Empfehlungen gegeben werden.'
    },
    # ============================================
    # 🗑️ МОДАЛЬНОЕ ОКНО УДАЛЕНИЯ АККАУНТА
    # ============================================
    'profile_danger_zone': {
        'ru': 'Опасная зона',
        'en': 'Danger zone',
        'uk': 'Небезпечна зона',
        'de': 'Gefahrenzone'
    },
    'profile_delete_warning': {
        'ru': 'Удаление аккаунта приведёт к безвозвратной потере всех ваших данных, документов и истории чатов.',
        'en': 'Deleting your account will result in the irreversible loss of all your data, documents and chat history.',
        'uk': 'Видалення акаунту призведе до безповоротної втрати всіх ваших даних, документів та історії чатів.',
        'de': 'Das Löschen des Kontos führt zum unwiderruflichen Verlust aller Ihrer Daten, Dokumente und Chat-Verläufe.'
    },
    'profile_delete_account': {
        'ru': 'Удалить мой аккаунт',
        'en': 'Delete my account',
        'uk': 'Видалити мій акаунт',
        'de': 'Mein Konto löschen'
    },
    'profile_delete_account_confirm_title': {
        'ru': 'Внимание!',
        'en': 'Warning!',
        'uk': 'Увага!',
        'de': 'Achtung!'
    },
    'profile_delete_account_confirm_message': {
        'ru': 'Вы уверены что хотите удалить ваш аккаунт?',
        'en': 'Are you sure you want to delete your account?',
        'uk': 'Ви впевнені, що хочете видалити ваш акаунт?',
        'de': 'Sind Sie sicher, dass Sie Ihr Konto löschen möchten?'
    },
    'profile_will_be_deleted': {
        'ru': 'Будет удалено:',
        'en': 'Will be deleted:',
        'uk': 'Буде видалено:',
        'de': 'Wird gelöscht:'
    },
    'profile_delete_documents': {
        'ru': 'Все ваши документы',
        'en': 'All your documents',
        'uk': 'Всі ваші документи',
        'de': 'Alle Ihre Dokumente'
    },
    'profile_delete_chat_history': {
        'ru': 'История чата',
        'en': 'Chat history',
        'uk': 'Історія чату',
        'de': 'Chat-Verlauf'
    },
    'profile_delete_medical_questionnaire': {
        'ru': 'Медицинская анкета',
        'en': 'Medical questionnaire',
        'uk': 'Медична анкета',
        'de': 'Medizinischer Fragebogen'
    },
    'profile_delete_profile': {
        'ru': 'Профиль',
        'en': 'Profile',
        'uk': 'Профіль',
        'de': 'Profil'
    },
    'profile_action_irreversible': {
        'ru': 'Это действие НЕОБРАТИМО!',
        'en': 'This action is IRREVERSIBLE!',
        'uk': 'Ця дія НЕЗВОРОТНА!',
        'de': 'Diese Aktion ist UNWIDERRUFLICH!'
    },
    'common_cancel': {
        'ru': 'Отмена',
        'en': 'Cancel',
        'uk': 'Скасувати',
        'de': 'Abbrechen'
    },    
    'profile_not_specified': {
        'ru': 'Не указано',
        'en': 'Not specified',
        'uk': 'Не вказано',
        'de': 'Nicht angegeben'
    },
    'profile_height_unit': {
        'ru': 'см',
        'en': 'cm',
        'uk': 'см',
        'de': 'cm'
    },
    'profile_weight_unit': {
        'ru': 'кг',
        'en': 'kg',
        'uk': 'кг',
        'de': 'kg'
    },
    
    # ============================================
    # 🗑️ УДАЛЕНИЕ АККАУНТА
    # ============================================
    'confirm_delete_account_message': {
        'ru': 'Вы уверены что хотите удалить ваш аккаунт?',
        'en': 'Are you sure you want to delete your account?',
        'uk': 'Ви впевнені, що хочете видалити ваш акаунт?',
        'de': 'Sind Sie sicher, dass Sie Ihr Konto löschen möchten?'
    },
    'will_be_deleted': {
        'ru': 'Будут удалены',
        'en': 'Will be deleted',
        'uk': 'Буде видалено',
        'de': 'Wird gelöscht'
    },
    'all_documents': {
        'ru': 'Все ваши документы',
        'en': 'All your documents',
        'uk': 'Всі ваші документи',
        'de': 'Alle Ihre Dokumente'
    },
    'chat_history': {
        'ru': 'История чатов',
        'en': 'Chat history',
        'uk': 'Історія чатів',
        'de': 'Chat-Verlauf'
    },
    'medical_profile': {
        'ru': 'Медицинская анкета',
        'en': 'Medical profile',
        'uk': 'Медична анкета',
        'de': 'Medizinisches Profil'
    },
    'profile': {
        'ru': 'Профиль',
        'en': 'Profile',
        'uk': 'Профіль',
        'de': 'Profil'
    },
    'action_irreversible': {
        'ru': 'Это действие НЕОБРАТИМО',
        'en': 'This action is IRREVERSIBLE',
        'uk': 'Ця дія НЕЗВОРОТНА',
        'de': 'Diese Aktion ist UNWIDERRUFLICH'
    },
    'double_confirm_message': {
        'ru': 'Вы ТОЧНО уверены? Это действие нельзя отменить!',
        'en': 'Are you ABSOLUTELY sure? This cannot be undone!',
        'uk': 'Ви ТОЧНО впевнені? Цю дію не можна скасувати!',
        'de': 'Sind Sie ABSOLUT sicher? Dies kann nicht rückgängig gemacht werden!'
    },
    'subscriptions_and_payments': {
        'ru': 'Подписки и платежи',
        'en': 'Subscriptions and payments',
        'uk': 'Підписки та платежі',
        'de': 'Abonnements und Zahlungen'
    },
    'deleting': {
        'ru': 'Удаление',
        'en': 'Deleting',
        'uk': 'Видалення',
        'de': 'Löschen'
    },
    'account_deleted_success': {
        'ru': 'Ваш аккаунт успешно удалён. Все данные стерты.',
        'en': 'Your account has been successfully deleted. All data has been erased.',
        'uk': 'Ваш акаунт успішно видалено. Всі дані стерто.',
        'de': 'Ihr Konto wurde erfolgreich gelöscht. Alle Daten wurden gelöscht.'
    },
    'account_deletion_error': {
        'ru': 'Ошибка при удалении аккаунта. Попробуйте позже.',
        'en': 'Error deleting account. Please try later.',
        'uk': 'Помилка при видаленні акаунту. Спробуйте пізніше.',
        'de': 'Fehler beim Löschen des Kontos. Bitte versuchen Sie es später.'
    },
    
    # ============================================
    # 🎨 FOOTER
    # ============================================
    'footer_text': {
        'ru': 'Ваше здоровье - наш приоритет.',
        'en': 'Your health is our priority.',
        'uk': 'Ваше здоров\'я - наш пріоритет.',
        'de': 'Ihre Gesundheit ist unsere Priorität.'
    },
    'footer_powered': {
        'ru': 'Правовая информация',
        'en': 'Legal',
        'uk': 'Правова інформація',
        'de': 'Rechtliches'
    },
    
    # ============================================
    # 🌍 ВЫБОР ЯЗЫКА
    # ============================================
    'language_selector': {
        'ru': 'Язык',
        'en': 'Language',
        'uk': 'Мова',
        'de': 'Sprache'
    },
    'lang_ru': {
        'ru': 'Русский',
        'en': 'Russian',
        'uk': 'Російська',
        'de': 'Russisch'
    },
    'lang_en': {
        'ru': 'Английский',
        'en': 'English',
        'uk': 'Англійська',
        'de': 'Englisch'
    },
    'lang_uk': {
        'ru': 'Украинский',
        'en': 'Ukrainian',
        'uk': 'Українська',
        'de': 'Ukrainisch'
    },
    'lang_de': {
        'ru': 'Немецкий',
        'en': 'German',
        'uk': 'Німецька',
        'de': 'Deutsch'
    },
    
    # ============================================
    # 🔐 СТРАНИЦА ВХОДА (login.html)
    # ============================================
    'login_page_title': {
        'ru': 'Вход',
        'en': 'Login',
        'uk': 'Вхід',
        'de': 'Anmeldung'
    },
    'login_title': {
        'ru': 'Вход в систему',
        'en': 'Sign In',
        'uk': 'Вхід до системи',
        'de': 'Anmelden'
    },
    'login_subtitle': {
        'ru': 'Используйте ваш Google аккаунт для быстрого и безопасного входа',
        'en': 'Use your Google account for quick and secure sign in',
        'uk': 'Використовуйте ваш Google акаунт для швидкого та безпечного входу',
        'de': 'Verwenden Sie Ihr Google-Konto für eine schnelle und sichere Anmeldung'
    },
    'why_google_title': {
        'ru': 'Почему Google?',
        'en': 'Why Google?',
        'uk': 'Чому Google?',
        'de': 'Warum Google?'
    },
    'why_google_secure_title': {
        'ru': 'Безопасно',
        'en': 'Secure',
        'uk': 'Безпечно',
        'de': 'Sicher'
    },
    'why_google_secure_desc': {
        'ru': 'мы не храним ваш пароль',
        'en': 'we don\'t store your password',
        'uk': 'ми не зберігаємо ваш пароль',
        'de': 'wir speichern Ihr Passwort nicht'
    },
    'why_google_fast_title': {
        'ru': 'Быстро',
        'en': 'Fast',
        'uk': 'Швидко',
        'de': 'Schnell'
    },
    'why_google_fast_desc': {
        'ru': 'вход за несколько секунд',
        'en': 'sign in within seconds',
        'uk': 'вхід за кілька секунд',
        'de': 'Anmeldung in Sekunden'
    },
    'why_google_convenient_title': {
        'ru': 'Удобно',
        'en': 'Convenient',
        'uk': 'Зручно',
        'de': 'Bequem'
    },
    'why_google_convenient_desc': {
        'ru': 'используйте существующий аккаунт',
        'en': 'use your existing account',
        'uk': 'використовуйте існуючий акаунт',
        'de': 'verwenden Sie Ihr bestehendes Konto'
    },
    'why_google_reliable_title': {
        'ru': 'Надёжно',
        'en': 'Reliable',
        'uk': 'Надійно',
        'de': 'Zuverlässig'
    },
    'why_google_reliable_desc': {
        'ru': 'защита от Google',
        'en': 'protected by Google',
        'uk': 'захист від Google',
        'de': 'geschützt von Google'
    },
    'privacy_info': {
        'ru': 'Мы запрашиваем только ваше имя и email. Ваши медицинские данные защищены и не передаются третьим лицам.',
        'en': 'We only request your name and email. Your medical data is protected and not shared with third parties.',
        'uk': 'Ми запитуємо лише ваше ім\'я та email. Ваші медичні дані захищені та не передаються третім особам.',
        'de': 'Wir fordern nur Ihren Namen und Ihre E-Mail-Adresse an. Ihre medizinischen Daten sind geschützt und werden nicht an Dritte weitergegeben.'
    },

    # ============================================
    # ⚠️ УВЕДОМЛЕНИЯ И АЛЕРТЫ
    # ============================================
    'tip': {
        'ru': 'Совет',
        'en': 'Tip',
        'uk': 'Порада',
        'de': 'Tipp'
    },
    'success': {
        'ru': 'Успешно',
        'en': 'Success',
        'uk': 'Успішно',
        'de': 'Erfolgreich'
    },
    'error': {
        'ru': 'Ошибка',
        'en': 'Error',
        'uk': 'Помилка',
        'de': 'Fehler'
    },
    'warning': {
        'ru': 'Внимание',
        'en': 'Warning',
        'uk': 'Увага',
        'de': 'Warnung'
    },
    'language_changed': {
        'ru': 'Язык изменен',
        'en': 'Language changed',
        'uk': 'Мову змінено',
        'de': 'Sprache geändert'
    },
    
    # ============================================
    # 🔒 ОШИБКИ И СООБЩЕНИЯ API
    # ============================================
    'error_not_authorized': {
        'ru': 'Не авторизован. Войдите в систему.',
        'en': 'Not authorized. Please log in.',
        'uk': 'Не авторизовано. Увійдіть у систему.',
        'de': 'Nicht autorisiert. Bitte melden Sie sich an.'
    },
    'error_server': {
        'ru': 'Ошибка сервера. Попробуйте позже.',
        'en': 'Server error. Please try again later.',
        'uk': 'Помилка сервера. Спробуйте пізніше.',
        'de': 'Serverfehler. Bitte versuchen Sie es später erneut.'
    },
    'upload_connection_lost': {
        'ru': '⚠️ Требуется перезагрузка страницы для отображения анализа.',
        'en': '⚠️ Page reload required to display the analysis.',
        'uk': '⚠️ Потрібне оновлення сторінки для відображення аналізу.',
        'de': '⚠️ Seite neu laden erforderlich, um die Analyse anzuzeigen.'
    },
    'error_upload_failed': {
        'ru': 'Не удалось загрузить файл',
        'en': 'Failed to upload file',
        'uk': 'Не вдалося завантажити файл',
        'de': 'Datei konnte nicht hochgeladen werden'
    },
    'success_document_uploaded': {
        'ru': 'Документ успешно загружен',
        'en': 'Document uploaded successfully',
        'uk': 'Документ успішно завантажено',
        'de': 'Dokument erfolgreich hochgeladen'
    },
    'success_message_sent': {
        'ru': 'Сообщение отправлено',
        'en': 'Message sent',
        'uk': 'Повідомлення надіслано',
        'de': 'Nachricht gesendet'
    },

'free_limit_reached_title': {
    'ru': 'Бесплатный лимит исчерпан',
    'en': 'Free limit reached',
    'uk': 'Безкоштовний ліміт вичерпано',
    'de': 'Kostenloses Limit erreicht'
},
'free_limit_reached_text': {
    'ru': 'Вы использовали доступные бесплатные возможности.\n\nС активным планом вы продолжите получать:\n✓ персональные рекомендации AI ассистента\n✓ разборы медицинских документов\n✓ расширенные возможности чата',
    'en': 'You have used all available free features.\n\nWith an active plan you will continue to receive:\n✓ personalized AI assistant recommendations\n✓ medical document analysis\n✓ advanced chat features',
    'uk': 'Ви використали доступні безкоштовні можливості.\n\nЗ активним планом ви продовжите отримувати:\n✓ персональні рекомендації AI-асистента\n✓ розбір медичних документів\n✓ розширені можливості чату',
    'de': 'Sie haben alle verfügbaren kostenlosen Funktionen genutzt.\n\nMit einem aktiven Plan erhalten Sie weiterhin:\n✓ personalisierte KI-Assistent-Empfehlungen\n✓ medizinische Dokumentenanalyse\n✓ erweiterte Chat-Funktionen'
},
'view_plans_button': {
    'ru': 'Посмотреть тарифы',
    'en': 'View plans',
    'uk': 'Переглянути тарифи',
    'de': 'Tarife ansehen'
},
'close_button': {
    'ru': 'Закрыть',
    'en': 'Close',
    'uk': 'Закрити',
    'de': 'Schließen'
},

# ============================================
# 💳 СТРАНИЦА ПОДПИСОК
# ============================================
'page_subscription_title': {
    'ru': 'Подписка',
    'en': 'Subscription',
    'uk': 'Підписка',
    'de': 'Abonnement'
},
'pricing_title': {
    'ru': 'Выберите план',
    'en': 'Choose a plan',
    'uk': 'Оберіть план',
    'de': 'Wählen Sie einen Plan'
},
'security_title': {
    'ru': 'Безопасная оплата и управление подпиской',
    'en': 'Secure Payment and Subscription Management',
    'uk': 'Безпечна оплата та керування підпискою',
    'de': 'Sichere Zahlung und Abonnementverwaltung'
},
'security_text': {
    'ru': 'PulseBook использует Stripe — международный платежный провайдер уровня PCI DSS Level 1. Мы не храним данные банковских карт. Подписку можно отменить в любой момент, авто-продление отключается одним нажатием.',
    'en': 'PulseBook uses Stripe — an international payment provider with PCI DSS Level 1 certification. We do not store credit card data. You can cancel your subscription at any time, auto-renewal can be disabled with one click.',
    'uk': 'PulseBook використовує Stripe — міжнародний платіжний провайдер рівня PCI DSS Level 1. Ми не зберігаємо дані банківських карт. Підписку можна скасувати в будь-який момент, авто-продовження вимикається одним натисканням.',
    'de': 'PulseBook verwendet Stripe — einen internationalen Zahlungsanbieter mit PCI DSS Level 1-Zertifizierung. Wir speichern keine Kreditkartendaten. Sie können Ihr Abonnement jederzeit kündigen, die automatische Verlängerung kann mit einem Klick deaktiviert werden.'
},
'most_popular': {
    'ru': 'Самый популярный',
    'en': 'Most Popular',
    'uk': 'Найпопулярніший',
    'de': 'Am beliebtesten'
},
'active': {
    'ru': 'Активна',
    'en': 'Active',
    'uk': 'Активна',
    'de': 'Aktiv'
},
'month_short': {
    'ru': 'мес',
    'en': 'mo',
    'uk': 'міс',
    'de': 'Mon'
},
'billed_monthly': {
    'ru': 'Ежемесячно. Отмена в любое время.',
    'en': 'Billed monthly. Cancel anytime.',
    'uk': 'Щомісяця. Скасування в будь-який час.',
    'de': 'Monatlich abgerechnet. Jederzeit kündbar.'
},
'one_time_payment': {
    'ru': 'Разовый платеж',
    'en': 'One-time payment',
    'uk': 'Разовий платіж',
    'de': 'Einmalige Zahlung'
},
'get_started': {
    'ru': 'Оформить',
    'en': 'Get started',
    'uk': 'Оформити',
    'de': 'Loslegen'
},
'current_plan': {
    'ru': 'Текущий план',
    'en': 'Current Plan',
    'uk': 'Поточний план',
    'de': 'Aktueller Plan'
},
'ai_longterm_memory': {
    'ru': 'Расширенная память ИИ',
    'en': 'Extended AI memory',
    'uk': 'Розширена пам\'ять ШІ',
    'de': 'Erweiterte KI-Speicher'
},
'conversation_summaries': {
    'ru': 'Сводки разговоров',
    'en': 'Conversation Summaries',
    'uk': 'Зведення розмов',
    'de': 'Gesprächszusammenfassungen'
},
'chat_attachments': {
    'ru': 'Вложения в чате',
    'en': 'Chat attachments',
    'uk': 'Вкладення в чаті',
    'de': 'Chat-Anhänge'
},
'chat_history': {
    'ru': 'История чата',
    'en': 'Chat history',
    'uk': 'Історія чату',
    'de': 'Chat-Verlauf'
},
'premium_support': {
    'ru': 'Приоритетная поддержка',
    'en': 'Premium Support',
    'uk': 'Пріоритетна підтримка',
    'de': 'Premium-Support'
},
'valid_30_days': {
    'ru': 'Действует 30 дней',
    'en': 'Valid for 30 days',
    'uk': 'Діє 30 днів',
    'de': 'Gültig für 30 Tage'
},
'free_plan_note': {
    'ru': 'После использования лимитов загрузка новых документов будет недоступна. Чтобы продолжить — оформите Lite или Pro.',
    'en': 'After using the limits, uploading new documents will be unavailable. To continue — get Lite or Pro.',
    'uk': 'Після використання лімітів завантаження нових документів буде недоступне. Щоб продовжити — оформіть Lite або Pro.',
    'de': 'Nach der Nutzung der Limits ist das Hochladen neuer Dokumente nicht verfügbar. Um fortzufahren — holen Sie sich Lite oder Pro.'
},
'lite_plan_note': {
    'ru': 'Оптимальный выбор для большинства пользователей.',
    'en': 'Optimal choice for most users.',
    'uk': 'Оптимальний вибір для більшості користувачів.',
    'de': 'Optimale Wahl für die meisten Benutzer.'
},
'pro_plan_note': {
    'ru': 'Лучший вариант для пользователей, которые хотят максимум возможностей.',
    'en': 'Best option for users who want maximum capabilities.',
    'uk': 'Найкращий варіант для користувачів, які хочуть максимум можливостей.',
    'de': 'Beste Option für Benutzer, die maximale Möglichkeiten wünschen.'
},
'package_free_feature_1': {
    'ru': '1 медицинский документ',
    'en': '1 medical document',
    'uk': '1 медичний документ',
    'de': '1 medizinisches Dokument'
},

'package_free_feature_2': {
    'ru': '3 детальных консультаций',
    'en': '3 detailed consultations',
    'uk': '3 детальних консультацій',
    'de': '3 detaillierte Beratungen'
},
'package_free_feature_3': {
    'ru': '20 базовых ответов',
    'en': '20 basic responses',
    'uk': '20 базових відповідей',
    'de': '20 Basisantworten'
},
'free_plan_billing': {
    'ru': 'Разовые лимиты при регистрации',
    'en': 'One-time limits upon registration',
    'uk': 'Разові ліміти при реєстрації',
    'de': 'Einmalige Limits bei Registrierung'
},
'package_extra_name': {
    'ru': 'Дополнительный пакет',
    'en': 'Additional package',
    'uk': 'Додатковий пакет',
    'de': 'Zusatzpaket'
},

'package_extra_feature_1': {
    'ru': '2 медицинских документа',
    'en': '2 medical documents',
    'uk': '2 медичних документи',
    'de': '2 medizinische Dokumente'
},

'package_extra_feature_2': {
    'ru': '20 детальных консультаций',
    'en': '20 detailed consultations',
    'uk': '20 детальних консультацій',
    'de': '20 detaillierte Beratungen'
},

'package_extra_feature_3': {
    'ru': 'Действует 30 дней',
    'en': 'Valid for 30 days',
    'uk': 'Діє 30 днів',
    'de': 'Gültig für 30 Tage'
},

'package_basic_feature_1': {
    'ru': '5 медицинских документов в месяц',
    'en': '5 medical documents per month',
    'uk': '5 медичних документів на місяць',
    'de': '5 medizinische Dokumente pro Monat'
},

'package_basic_feature_2': {
    'ru': '50 детальных консультаций в месяц',
    'en': '50 detailed consultations per month',
    'uk': '50 детальних консультацій на місяць',
    'de': '50 detaillierte Beratungen pro Monat'
},

'package_basic_feature_3': {
    'ru': 'Повышенный лимит на базовые ответы',
    'en': 'Increased limit for basic responses',
    'uk': 'Підвищений ліміт на базові відповіді',
    'de': 'Erhöhtes Limit für Basisantworten'
},

'package_premium_feature_1': {
    'ru': '20 медицинских документов в месяц',
    'en': '20 medical documents per month',
    'uk': '20 медичних документів на місяць',
    'de': '20 medizinische Dokumente pro Monat'
},

'package_premium_feature_2': {
    'ru': '200 детальных консультаций в месяц',
    'en': '200 detailed consultations per month',
    'uk': '200 детальних консультацій на місяць',
    'de': '200 detaillierte Beratungen pro Monat'
},
'package_premium_feature_3': {
    'ru': 'Неограниченные базовые ответы',
    'en': 'Unlimited basic responses',
    'uk': 'Необмежені базові відповіді',
    'de': 'Unbegrenzte Basisantworten'
},
'package_basic_name': {
    'ru': 'Lite',
    'en': 'Lite',
    'uk': 'Lite',
    'de': 'Lite'
},

'package_premium_name': {
    'ru': 'Pro',
    'en': 'Pro',
    'uk': 'Pro',
    'de': 'Pro'
},
# 💎 Названия тарифов для отображения
'plan_free': {
    'ru': 'Бесплатный',
    'en': 'Free',
    'uk': 'Безкоштовний',
    'de': 'Kostenlos'
},

'plan_lite': {
    'ru': 'Lite',
    'en': 'Lite',
    'uk': 'Lite',
    'de': 'Lite'
},

'plan_pro': {
    'ru': 'Pro',
    'en': 'Pro',
    'uk': 'Pro',
    'de': 'Pro'
},
'mode_detailed_consultations': {
    'ru': 'Режим детальных консультаций',
    'en': 'Detailed Consultation Mode',
    'uk': 'Режим детальних консультацій',
    'de': 'Detaillierter Beratungsmodus'
},

'mode_basic_responses': {
    'ru': 'Режим базовых ответов',
    'en': 'Basic Response Mode',
    'uk': 'Режим базових відповідей',
    'de': 'Basis-Antwortmodus'
},

'mode_upgrade_to_detailed': {
    'ru': 'Обновить до детальных консультаций →',
    'en': 'Upgrade to detailed consultations →',
    'uk': 'Оновити до детальних консультацій →',
    'de': 'Auf detaillierte Beratungen upgraden →'
},
'medical_disclaimer': {
    'ru': 'PulseBook не заменяет консультацию врача. Ответы могут содержать ошибки.',
    'uk': 'PulseBook не замінює консультацію лікаря. Відповіді можуть містити помилки.',
    'en': 'PulseBook is not a substitute for medical advice. Responses may contain errors.',
    'de': 'PulseBook ersetzt keine ärztliche Beratung. Antworten können Fehler enthalten.'
},
'photo_requires_premium': {
    'ru': '⭐ Анализ фото доступен только с подпиской на детальные консультации',
    'en': '⭐ Photo analysis is available only with detailed consultations subscription',
    'uk': '⭐ Аналіз фото доступний тільки з підпискою на детальні консультації',
    'de': '⭐ Fotoanalyse ist nur mit einem Abonnement für detaillierte Beratungen verfügbar'
},
'ai_disclaimer': {
    "ru": "AI-анализ носит информационный характер и не является диагнозом или медицинским назначением. Выводы основаны только на загруженных данных и контексте, полнота которых влияет на точность интерпретации. Перед принятием медицинских решений проконсультируйтесь с врачом.",
    "en": "This AI-generated analysis is for informational purposes only and is not a diagnosis or medical prescription. Conclusions are based solely on the uploaded data and context, the completeness of which affects interpretation accuracy. Please consult a doctor before making medical decisions.",
    "uk": "AI-аналіз має інформаційний характер і не є діагнозом або медичним призначенням. Висновки ґрунтуються лише на завантажених даних і контексті, повнота яких впливає на точність інтерпретації. Перед прийняттям медичних рішень проконсультуйтеся з лікарем.",
    "de": "Diese KI-Analyse dient ausschließlich Informationszwecken und stellt keine Diagnose oder medizinische Verschreibung dar. Die Schlussfolgerungen basieren ausschließlich auf den hochgeladenen Daten und dem angegebenen Kontext, dessen Vollständigkeit die Genauigkeit der Interpretation beeinflusst. Bitte konsultieren Sie vor medizinischen Entscheidungen einen Arzt."
},
'photo_upload_button': {
    'ru': '📷 Загрузить фото',
    'en': '📷 Upload a photo',
    'uk': '📷 Завантажити фото',
    'de': '📷 Foto hochladen'
},

'photo_upload_description': {
    'ru': 'Поддерживается: PNG, JPG, JPEG, GIF, WEBP (макс. 5 МБ)',
    'en': 'Supported: PNG, JPG, JPEG, GIF, WEBP (max 5 MB)',
    'uk': 'Підтримується: PNG, JPG, JPEG, GIF, WEBP (макс. 5 МБ)',
    'de': 'Unterstützt: PNG, JPG, JPEG, GIF, WEBP (max. 5 MB)'
},
'edit': {
    'ru': 'Редактировать',
    'en': 'Edit',
    'uk': 'Редагувати',
    'de': 'Bearbeiten'
},
'save': {
    'ru': 'Сохранить',
    'en': 'Save',
    'uk': 'Зберегти',
    'de': 'Speichern'
},
'cancel': {
    'ru': 'Отмена',
    'en': 'Cancel',
    'uk': 'Скасувати',
    'de': 'Abbrechen'
},
'smoking_yes': {
    'ru': 'Да',
    'en': 'Yes',
    'uk': 'Так',
    'de': 'Ja'
},
'smoking_no': {
    'ru': 'Нет',
    'en': 'No',
    'uk': 'Ні',
    'de': 'Nein'
},
'smoking_vape': {
    'ru': 'Vape',
    'en': 'Vape',
    'uk': 'Vape',
    'de': 'Vape'
},
'alcohol_never': {
    'ru': 'Не употребляю',
    'en': 'Never',
    'uk': 'Не вживаю',
    'de': 'Nie'
},
'alcohol_sometimes': {
    'ru': 'Иногда',
    'en': 'Sometimes',
    'uk': 'Іноді',
    'de': 'Manchmal'
},
'alcohol_sometimes_hint': {
    'ru': 'Иногда (по праздникам или 1-2 раза в месяц)',
    'en': 'Sometimes (holidays or 1-2 times per month)',
    'uk': 'Іноді (по святах або 1-2 рази на місяць)',
    'de': 'Manchmal (an Feiertagen oder 1-2 Mal im Monat)'
},
'alcohol_often': {
    'ru': 'Часто',
    'en': 'Often',
    'uk': 'Часто',
    'de': 'Oft'
},
'alcohol_often_hint': {
    'ru': 'Часто (еженедельно или чаще)',
    'en': 'Often (weekly or more)',
    'uk': 'Часто (щотижня або частіше)',
    'de': 'Oft (wöchentlich oder öfter)'
},
'activity_none': {
    'ru': 'Нет активности',
    'en': 'No activity',
    'uk': 'Немає активності',
    'de': 'Keine Aktivität'
},
'activity_none_hint': {
    'ru': '❌ Нет активности (сидячий образ жизни)',
    'en': '❌ No activity (sedentary lifestyle)',
    'uk': '❌ Немає активності (сидячий спосіб життя)',
    'de': '❌ Keine Aktivität (sitzender Lebensstil)'
},
'activity_low': {
    'ru': 'Низкая',
    'en': 'Low',
    'uk': 'Низька',
    'de': 'Niedrig'
},
'activity_low_hint': {
    'ru': '🚶 Низкая (редкие прогулки)',
    'en': '🚶 Low (occasional walks)',
    'uk': '🚶 Низька (рідкісні прогулянки)',
    'de': '🚶 Niedrig (gelegentliche Spaziergänge)'
},
'activity_medium': {
    'ru': 'Средняя',
    'en': 'Medium',
    'uk': 'Середня',
    'de': 'Mittel'
},
'activity_medium_hint': {
    'ru': '🏃 Средняя (регулярные прогулки)',
    'en': '🏃 Medium (regular walks)',
    'uk': '🏃 Середня (регулярні прогулянки)',
    'de': '🏃 Mittel (regelmäßige Spaziergänge)'
},
'activity_high': {
    'ru': 'Высокая',
    'en': 'High',
    'uk': 'Висока',
    'de': 'Hoch'
},
'activity_high_hint': {
    'ru': '💪 Высокая (тренировки 3-5 раз в неделю)',
    'en': '💪 High (workouts 3-5 times per week)',
    'uk': '💪 Висока (тренування 3-5 разів на тиждень)',
    'de': '💪 Hoch (Training 3-5 Mal pro Woche)'
},
'activity_pro': {
    'ru': 'Профессиональная',
    'en': 'Professional',
    'uk': 'Професійна',
    'de': 'Professionell'
},
'activity_pro_hint': {
    'ru': '🏆 Профессиональная (ежедневные тренировки)',
    'en': '🏆 Professional (daily workouts)',
    'uk': '🏆 Професійна (щоденні тренування)',
    'de': '🏆 Professionell (tägliches Training)'
},
'profile_updated': {
    'ru': '✅ Профиль успешно обновлен',
    'en': '✅ Profile updated successfully',
    'uk': '✅ Профіль успішно оновлено',
    'de': '✅ Profil erfolgreich aktualisiert'
},
'error_updating': {
    'ru': '❌ Ошибка при обновлении профиля',
    'en': '❌ Error updating profile',
    'uk': '❌ Помилка при оновленні профілю',
    'de': '❌ Fehler beim Aktualisieren des Profils'
},
'name_required': {
    'ru': '❌ Имя обязательно для заполнения',
    'en': '❌ Name is required',
    'uk': '❌ Ім\'я обов\'язкове для заповнення',
    'de': '❌ Name ist erforderlich'
},
'gender_male': {
    'ru': 'Мужской',
    'en': 'Male',
    'uk': 'Чоловічий',
    'de': 'Männlich'
},
'gender_female': {
    'ru': 'Женский',
    'en': 'Female',
    'uk': 'Жіночий',
    'de': 'Weiblich'
},
'gender_other': {
    'ru': 'Другое',
    'en': 'Other',
    'uk': 'Інше',
    'de': 'Andere'
},

# === ОТЗЫВЫ ===
'testimonials_title': {
    'ru': 'Опыт наших пользователей',
    'en': 'User experience',
    'uk': 'Досвід наших користувачів',
    'de': 'Benutzererfahrung'
},

'testimonials_subtitle': {
    'ru': 'Реальные истории людей, которые используют PulseBook',
    'en': 'Real stories from people using PulseBook',
    'uk': 'Реальні історії людей, які використовують PulseBook',
    'de': 'Echte Geschichten von Menschen, die PulseBook nutzen'
},

'testimonial1_text': {
    'ru': 'Впервые понял, что означают показатели в моих анализах. ИИ объяснил всё простым языком без медицинского жаргона.',
    'en': 'Finally understood what the numbers in my tests mean. AI explained everything in simple terms without medical jargon.',
    'uk': 'Вперше зрозумів, що означають показники в моїх аналізах. ШІ пояснив все простою мовою без медичного жаргону.',
    'de': 'Endlich verstanden, was die Zahlen in meinen Tests bedeuten. KI hat alles einfach erklärt, ohne medizinisches Fachjargon.'
},

'testimonial1_author': {
    'ru': 'Алексей Иванов',
    'en': 'Alex Johnson',
    'uk': 'Олексій Іванов',
    'de': 'Alexander Schmidt'
},

'testimonial1_role': {
    'ru': '3 месяца с PulseBook',
    'en': '3 months with PulseBook',
    'uk': '3 місяці з PulseBook',
    'de': '3 Monate mit PulseBook'
},

'testimonial2_text': {
    'ru': 'Удобно хранить всю медицинскую историю в одном месте. Больше не теряю результаты анализов перед визитом к врачу.',
    'en': 'Convenient to keep all medical history in one place. No more losing test results before doctor visits.',
    'uk': 'Зручно зберігати всю медичну історію в одному місці. Більше не втрачаю результати аналізів перед візитом до лікаря.',
    'de': 'Praktisch, die gesamte Krankengeschichte an einem Ort aufzubewahren. Keine verlorenen Testergebnisse mehr vor Arztbesuchen.'
},

'testimonial2_author': {
    'ru': 'Мария Петрова',
    'en': 'Maria Peterson',
    'uk': 'Марія Петрова',
    'de': 'Maria Müller'
},

'testimonial2_role': {
    'ru': 'Премиум подписка',
    'en': 'Premium subscription',
    'uk': 'Преміум підписка',
    'de': 'Premium-Abonnement'
},

"extra_plan_description": {
    'ru': 'Дополнительные лимиты на 30 дней',
    'en': 'Additional limits for 30 days',
    'uk': 'Додаткові ліміти на 30 днів',
    'de': 'Zusätzliche Limits für 30 Tage'
},

"exit_app_hint": {
    "ru": "Нажмите ещё раз для выхода",
    "en": "Press again to exit",
    "uk": "Натисніть ще раз для виходу",
    "de": "Drücken Sie erneut zum Beenden"
},

# === FAQ ===
'faq_title': {
    'ru': 'Ответы на вопросы',
    'en': 'Frequently asked questions',
    'uk': 'Відповіді на питання',
    'de': 'Häufig gestellte Fragen'
},

'faq_q1': {
    'ru': 'Насколько безопасны мои данные?',
    'en': 'How secure is my data?',
    'uk': 'Наскільки безпечні мої дані?',
    'de': 'Wie sicher sind meine Daten?'
},

'faq_a1': {
    'ru': 'Мы используем шифрование уровня банков и соответствуем международным стандартам HIPAA и GDPR. Данные хранятся на защищённых серверах с постоянным мониторингом.',
    'en': 'We use bank-level encryption and comply with international HIPAA and GDPR standards. Data is stored on secure servers with constant monitoring.',
    'uk': 'Ми використовуємо шифрування рівня банків та відповідаємо міжнародним стандартам HIPAA та GDPR. Дані зберігаються на захищених серверах з постійним моніторингом.',
    'de': 'Wir verwenden Verschlüsselung auf Bankniveau und entsprechen internationalen HIPAA- und GDPR-Standards. Daten werden auf sicheren Servern mit ständiger Überwachung gespeichert.'
},

'faq_q2': {
    'ru': 'Заменяет ли ИИ врача?',
    'en': 'Does AI replace a doctor?',
    'uk': 'Чи замінює ШІ лікаря?',
    'de': 'Ersetzt KI einen Arzt?'
},

'faq_a2': {
    'ru': 'Нет. PulseBook — это инструмент для информирования, а не замена профессиональной медицинской помощи. При серьёзных симптомах обязательно обращайтесь к врачу.',
    'en': 'No. PulseBook is an information tool, not a replacement for professional medical care. Always consult a doctor for serious symptoms.',
    'uk': 'Ні. PulseBook — це інструмент для інформування, а не заміна професійної медичної допомоги. При серйозних симптомах обов\'язково звертайтесь до лікаря.',
    'de': 'Nein. PulseBook ist ein Informationswerkzeug, kein Ersatz für professionelle medizinische Versorgung. Konsultieren Sie bei ernsthaften Symptomen immer einen Arzt.'
},

'faq_q3': {
    'ru': 'Какие форматы файлов поддерживаются?',
    'en': 'What file formats are supported?',
    'uk': 'Які формати файлів підтримуються?',
    'de': 'Welche Dateiformate werden unterstützt?'
},

'faq_a3': {
    'ru': 'PDF, JPG, PNG, DICOM (медицинские снимки), а также текстовые документы. Система автоматически распознаёт содержимое.',
    'en': 'PDF, JPG, PNG, DICOM (medical images), and text documents. The system automatically recognizes content.',
    'uk': 'PDF, JPG, PNG, DICOM (медичні знімки), а також текстові документи. Система автоматично розпізнає вміст.',
    'de': 'PDF, JPG, PNG, DICOM (medizinische Bilder) und Textdokumente. Das System erkennt den Inhalt automatisch.'
},

'faq_q4': {
    'ru': 'Сколько стоит использование?',
    'en': 'How much does it cost?',
    'uk': 'Скільки коштує використання?',
    'de': 'Wie viel kostet die Nutzung?'
},

'faq_a4': {
    'ru': 'Базовый тариф бесплатный с ограничениями. Премиум от $9.99/месяц — безлимитные консультации, хранилище 50 ГБ, приоритетная поддержка.',
    'en': 'Basic plan is free with limitations. Premium from $9.99/month — unlimited consultations, 50 GB storage, priority support.',
    'uk': 'Базовий тариф безкоштовний з обмеженнями. Преміум від $9.99/місяць — безлімітні консультації, сховище 50 ГБ, пріоритетна підтримка.',
    'de': 'Basis-Tarif ist kostenlos mit Einschränkungen. Premium ab $9,99/Monat — unbegrenzte Beratungen, 50 GB Speicher, Priority-Support.'
},

# === ФИНАЛЬНЫЙ CTA ===
'cta_final_title': {
    'ru': 'Начните бесплатно',
    'en': 'Start for free',
    'uk': 'Почніть безкоштовно',
    'de': 'Kostenlos starten'
},

'cta_final_button': {
    'ru': 'Войти через Google',
    'en': 'Sign in with Google',
    'uk': 'Увійти через Google',
    'de': 'Mit Google anmelden'
},

'cta_final_note': {
    'ru': 'Без кредитной карты • Отмена в любой момент',
    'en': 'No credit card • Cancel anytime',
    'uk': 'Без кредитної картки • Скасування в будь-який момент',
    'de': 'Keine Kreditkarte • Jederzeit kündbar'
},

    # ============================================
    # 🔗 КНОПКА "ПОДКЛЮЧИТЬ TELEGRAM"
    # ============================================
    'connect_telegram_btn': {
        'ru': '🔗 Подключить Telegram',
        'en': '🔗 Connect Telegram',
        'uk': '🔗 Підключити Telegram',
        'de': '🔗 Telegram verbinden'
    },
    
    'telegram_connected': {
        'ru': '✅ Telegram подключен',
        'en': '✅ Telegram connected',
        'uk': '✅ Telegram підключено',
        'de': '✅ Telegram verbunden'
    },
    
    'connect_telegram_title': {
        'ru': 'Подключить Telegram бота',
        'en': 'Connect Telegram Bot',
        'uk': 'Підключити Telegram бота',
        'de': 'Telegram-Bot verbinden'
    },
    
    # ============================================
    # 📱 ИНСТРУКЦИИ ПО ПОДКЛЮЧЕНИЮ
    # ============================================
    'connect_instructions_title': {
        'ru': 'Как подключить Telegram?',
        'en': 'How to connect Telegram?',
        'uk': 'Як підключити Telegram?',
        'de': 'Wie verbinde ich Telegram?'
    },
    
    'connect_instructions_step1': {
        'ru': '1️⃣ Откройте эту страницу на устройстве, где установлен Telegram',
        'en': '1️⃣ Open this page on a device where Telegram is installed',
        'uk': '1️⃣ Відкрийте цю сторінку на пристрої, де встановлено Telegram',
        'de': '1️⃣ Öffnen Sie diese Seite auf einem Gerät, auf dem Telegram installiert ist'
    },
    
    'connect_instructions_step2': {
        'ru': '2️⃣ Нажмите кнопку ниже - откроется Telegram',
        'en': '2️⃣ Click the button below - Telegram will open',
        'uk': '2️⃣ Натисніть кнопку нижче - відкриється Telegram',
        'de': '2️⃣ Klicken Sie auf die Schaltfläche unten - Telegram wird geöffnet'
    },
    
    'connect_instructions_step3': {
        'ru': '3️⃣ Отправьте боту код из этой страницы',
        'en': '3️⃣ Send the code from this page to the bot',
        'uk': '3️⃣ Надішліть боту код з цієї сторінки',
        'de': '3️⃣ Senden Sie den Code von dieser Seite an den Bot'
    },
    
    'connect_instructions_warning': {
        'ru': '⚠️ Важно: Откройте страницу на устройстве с Telegram!',
        'en': '⚠️ Important: Open the page on a device with Telegram!',
        'uk': '⚠️ Важливо: Відкрийте сторінку на пристрої з Telegram!',
        'de': '⚠️ Wichtig: Öffnen Sie die Seite auf einem Gerät mit Telegram!'
    },
    
    # ============================================
    # 📋 КОД СВЯЗЫВАНИЯ
    # ============================================
    'your_link_code': {
        'ru': 'Ваш код связывания:',
        'en': 'Your link code:',
        'uk': 'Ваш код зв\'язування:',
        'de': 'Ihr Verknüpfungscode:'
    },
    
    'code_expires_in': {
        'ru': 'Код действителен {minutes} минут',
        'en': 'Code expires in {minutes} minutes',
        'uk': 'Код діє {minutes} хвилин',
        'de': 'Code läuft in {minutes} Minuten ab'
    },
    
    'copy_code': {
        'ru': 'Скопировать код',
        'en': 'Copy code',
        'uk': 'Скопіювати код',
        'de': 'Code kopieren'
    },
    
    'code_copied': {
        'ru': '✅ Код скопирован!',
        'en': '✅ Code copied!',
        'uk': '✅ Код скопійовано!',
        'de': '✅ Code kopiert!'
    },
    
    # ============================================
    # 🤖 КНОПКА ОТКРЫТЬ TELEGRAM
    # ============================================
    'open_telegram_bot': {
        'ru': '📱 Открыть Telegram бота',
        'en': '📱 Open Telegram Bot',
        'uk': '📱 Відкрити Telegram бота',
        'de': '📱 Telegram-Bot öffnen'
    },
    
    # ============================================
    # ✅ СООБЩЕНИЯ TELEGRAM БОТА
    # ============================================
    'bot_link_welcome': {
        'ru': '👋 Привет! Я вижу вы хотите подключить веб-версию к Telegram.\n\n📝 Пожалуйста, отправьте мне 6-значный код с веб-страницы.',
        'en': '👋 Hello! I see you want to connect the web version to Telegram.\n\n📝 Please send me the 6-digit code from the web page.',
        'uk': '👋 Привіт! Я бачу ви хочете підключити веб-версію до Telegram.\n\n📝 Будь ласка, надішліть мені 6-значний код з веб-сторінки.',
        'de': '👋 Hallo! Ich sehe, Sie möchten die Webversion mit Telegram verbinden.\n\n📝 Bitte senden Sie mir den 6-stelligen Code von der Webseite.'
    },
    
    'bot_code_format_error': {
        'ru': '❌ Неверный формат кода. Отправьте 6-значный код (только цифры).',
        'en': '❌ Invalid code format. Send a 6-digit code (numbers only).',
        'uk': '❌ Невірний формат коду. Надішліть 6-значний код (тільки цифри).',
        'de': '❌ Ungültiges Code-Format. Senden Sie einen 6-stelligen Code (nur Zahlen).'
    },
    
    'bot_code_not_found': {
        'ru': '❌ Код не найден или истёк.\n\nПожалуйста, создайте новый код на веб-странице.',
        'en': '❌ Code not found or expired.\n\nPlease create a new code on the web page.',
        'uk': '❌ Код не знайдено або закінчився.\n\nБудь ласка, створіть новий код на веб-сторінці.',
        'de': '❌ Code nicht gefunden oder abgelaufen.\n\nBitte erstellen Sie einen neuen Code auf der Webseite.'
    },
    
    'bot_code_already_used': {
        'ru': '❌ Этот код уже был использован.\n\nПожалуйста, создайте новый код на веб-странице.',
        'en': '❌ This code has already been used.\n\nPlease create a new code on the web page.',
        'uk': '❌ Цей код вже був використаний.\n\nБудь ласка, створіть новий код на веб-сторінці.',
        'de': '❌ Dieser Code wurde bereits verwendet.\n\nBitte erstellen Sie einen neuen Code auf der Webseite.'
    },
    
    # ============================================
    # 🔄 СООБЩЕНИЯ О СЛИЯНИИ
    # ============================================
    'bot_accounts_will_merge': {
        'ru': '⚠️ У вас уже есть аккаунт в Telegram!\n\n🔄 Если продолжить, ваши аккаунты будут объединены:\n\n✅ Все данные сохранятся\n✅ Подписка из веб-версии будет приоритетной\n✅ История сообщений объединится\n\nПродолжить?',
        'en': '⚠️ You already have a Telegram account!\n\n🔄 If you continue, your accounts will be merged:\n\n✅ All data will be preserved\n✅ Web subscription will take priority\n✅ Message history will be combined\n\nContinue?',
        'uk': '⚠️ У вас вже є акаунт в Telegram!\n\n🔄 Якщо продовжити, ваші акаунти будуть об\'єднані:\n\n✅ Всі дані збережуться\n✅ Підписка з веб-версії буде пріоритетною\n✅ Історія повідомлень об\'єднається\n\nПродовжити?',
        'de': '⚠️ Sie haben bereits ein Telegram-Konto!\n\n🔄 Wenn Sie fortfahren, werden Ihre Konten zusammengeführt:\n\n✅ Alle Daten werden gespeichert\n✅ Web-Abonnement hat Priorität\n✅ Nachrichtenverlauf wird kombiniert\n\nFortfahren?'
    },
    
    'bot_merge_confirm_yes': {
        'ru': '✅ Да, объединить',
        'en': '✅ Yes, merge',
        'uk': '✅ Так, об\'єднати',
        'de': '✅ Ja, zusammenführen'
    },
    
    'bot_merge_confirm_no': {
        'ru': '❌ Нет, отменить',
        'en': '❌ No, cancel',
        'uk': '❌ Ні, скасувати',
        'de': '❌ Nein, abbrechen'
    },
    
    'bot_merge_cancelled': {
        'ru': '❌ Связывание отменено.',
        'en': '❌ Linking cancelled.',
        'uk': '❌ Зв\'язування скасовано.',
        'de': '❌ Verknüpfung abgebrochen.'
    },
    
    # ============================================
    # 🎉 УСПЕШНОЕ ПОДКЛЮЧЕНИЕ
    # ============================================
    'bot_link_success': {
        'ru': '🎉 Отлично!\n\n✅ Теперь вы можете пользоваться обеими платформами с одним аккаунтом:\n\n• 🌐 Веб-версия\n• 📱 Telegram бот\n\nВсе ваши данные синхронизированы!',
        'en': '🎉 Great!\n\n✅ Now you can use both platforms with one account:\n\n• 🌐 Web version\n• 📱 Telegram bot\n\nAll your data is synchronized!',
        'uk': '🎉 Чудово!\n\n✅ Тепер ви можете користуватися обома платформами з одним акаунтом:\n\n• 🌐 Веб-версія\n• 📱 Telegram бот\n\nВсі ваші дані синхронізовані!',
        'de': '🎉 Großartig!\n\n✅ Jetzt können Sie beide Plattformen mit einem Konto nutzen:\n\n• 🌐 Webversion\n• 📱 Telegram-Bot\n\nAlle Ihre Daten sind synchronisiert!'
    },
    
    'bot_merge_success': {
        'ru': '🎉 Аккаунты успешно объединены!\n\n✅ Все данные сохранены:\n• История сообщений\n• Загруженные документы\n• Ваша подписка из веб-версии\n• Настройки и лекарства\n\nТеперь вы можете пользоваться обеими платформами!',
        'en': '🎉 Accounts successfully merged!\n\n✅ All data preserved:\n• Message history\n• Uploaded documents\n• Your web subscription\n• Settings and medications\n\nNow you can use both platforms!',
        'uk': '🎉 Акаунти успішно об\'єднано!\n\n✅ Всі дані збережено:\n• Історія повідомлень\n• Завантажені документи\n• Ваша підписка з веб-версії\n• Налаштування та ліки\n\nТепер ви можете користуватися обома платформами!',
        'de': '🎉 Konten erfolgreich zusammengeführt!\n\n✅ Alle Daten gespeichert:\n• Nachrichtenverlauf\n• Hochgeladene Dokumente\n• Ihr Web-Abonnement\n• Einstellungen und Medikamente\n\nJetzt können Sie beide Plattformen nutzen!'
    },
    
    # ============================================
    # ❌ ОШИБКИ
    # ============================================
    'error_linking': {
        'ru': '❌ Ошибка при связывании аккаунтов. Попробуйте позже.',
        'en': '❌ Error linking accounts. Please try later.',
        'uk': '❌ Помилка при зв\'язуванні акаунтів. Спробуйте пізніше.',
        'de': '❌ Fehler beim Verknüpfen der Konten. Bitte versuchen Sie es später.'
    },
    
    'error_generating_code': {
        'ru': '❌ Ошибка генерации кода. Обновите страницу.',
        'en': '❌ Error generating code. Refresh the page.',
        'uk': '❌ Помилка генерації коду. Оновіть сторінку.',
        'de': '❌ Fehler beim Generieren des Codes. Aktualisieren Sie die Seite.'
    },
    
    # ============================================
    # 💡 ПОДСКАЗКИ
    # ============================================
    'link_benefits_title': {
        'ru': '💡 Почему стоит подключить Telegram?',
        'en': '💡 Why connect Telegram?',
        'uk': '💡 Чому варто підключити Telegram?',
        'de': '💡 Warum Telegram verbinden?'
    },    
    'link_benefit_1': {
        'ru': 'Быстрый доступ к боту с телефона',
        'en': 'Quick bot access from phone',
        'uk': 'Швидкий доступ до бота з телефону',
        'de': 'Schneller Bot-Zugriff vom Telefon'
    },    
    'link_benefit_3': {
        'ru': 'Единая история на обеих платформах',
        'en': 'Unified history across platforms',
        'uk': 'Єдина історія на обох платформах',
        'de': 'Einheitliche Historie auf beiden Plattformen'
    },    
    'link_benefit_4': {
        'ru': 'Одна подписка на все устройства',
        'en': 'One subscription for all devices',
        'uk': 'Одна підписка на всі пристрої',
        'de': 'Ein Abonnement für alle Geräte'
    },
    'refresh_code': {
        'ru': '🔄 Обновить код',
        'en': '🔄 Refresh Code',
        'uk': '🔄 Оновити код',
        'de': '🔄 Code aktualisieren'
    },

'refreshing': {
    'ru': 'Обновление...',
    'en': 'Refreshing...',
    'uk': 'Оновлення...',
    'de': 'Aktualisierung...'
},
'waiting_connection': {
    'ru': 'Ожидание подключения...',
    'en': 'Waiting for connection...',
    'uk': 'Очікування підключення...',
    'de': 'Warten auf Verbindung...'
},
'telegram_link_description': {
    'ru': 'Получайте уведомления о приёме лекарств и консультируйтесь с AI прямо в Telegram.',
    'en': 'Get medication reminders and consult with AI directly in Telegram.',
    'uk': 'Отримуйте нагадування про прийом ліків та консультуйтеся з AI прямо в Telegram.',
    'de': 'Erhalten Sie Medikamentenerinnerungen und konsultieren Sie AI direkt in Telegram.'
},

'learn_more': {
    'ru': 'Узнать подробнее',
    'en': 'Learn more',
    'uk': 'Дізнатися більше',
    'de': 'Mehr erfahren'
},

'telegram_warning_device': {
    'ru': 'Откройте эту страницу на устройстве, где установлен Telegram',
    'en': 'Open this page on a device with Telegram installed',
    'uk': 'Відкрийте цю сторінку на пристрої, де встановлено Telegram',
    'de': 'Öffnen Sie diese Seite auf einem Gerät mit installiertem Telegram'
},

'telegram_warning_expires': {
    'ru': 'Ссылка для связывания действительна 10 минут',
    'en': 'Linking code is valid for 10 minutes',
    'uk': 'Посилання для зв\'язування дійсне 10 хвилин',
    'de': 'Verknüpfungscode ist 10 Minuten gültig'
},

'telegram_step_1': {
    'ru': '📱 Нажмите кнопку ниже',
    'en': '📱 Click the button below',
    'uk': '📱 Натисніть кнопку нижче',
    'de': '📱 Klicken Sie auf die Schaltfläche unten'
},

'telegram_step_2': {
    'ru': '🤖 Telegram откроется автоматически',
    'en': '🤖 Telegram will open automatically',
    'uk': '🤖 Telegram відкриється автоматично',
    'de': '🤖 Telegram wird automatisch geöffnet'
},

'telegram_step_3': {
    'ru': '✅ Нажмите START в боте',
    'en': '✅ Click START in the bot',
    'uk': '✅ Натисніть START в боті',
    'de': '✅ Klicken Sie auf START im Bot'
},

'link_expired': {
    'ru': '⏱️ Ссылка истекла',
    'en': '⏱️ Link expired',
    'uk': '⏱️ Посилання минуло',
    'de': '⏱️ Link abgelaufen'
},

'link_expired_refresh': {
    'ru': 'Пожалуйста, обновите страницу',
    'en': 'Please refresh the page',
    'uk': 'Будь ласка, оновіть сторінку',
    'de': 'Bitte aktualisieren Sie die Seite'
},
'back_to_dashboard': {
    'ru': 'Назад в кабинет',
    'en': 'Back to dashboard',
    'uk': 'Назад до кабінету',
    'de': 'Zurück zum Dashboard'
},
'profile_family_history': {
    'ru': 'Семейная история болезней',
    'en': 'Family medical history',
    'uk': 'Сімейна історія хвороб',
    'de': 'Familienkrankengeschichte'
},
'file_mime_type_mismatch': {
    'ru': '❌ Тип файла не соответствует содержимому. Возможно, файл переименован или повреждён.',
    'en': '❌ File type does not match content. The file may be renamed or corrupted.',
    'uk': '❌ Тип файлу не відповідає вмісту. Можливо, файл перейменовано або пошкоджено.',
    'de': '❌ Dateityp stimmt nicht mit Inhalt überein. Die Datei wurde möglicherweise umbenannt oder ist beschädigt.'
},
'file_validation_error': {
    'ru': '❌ Ошибка при проверке файла. Попробуйте другой файл.',
    'en': '❌ File validation error. Please try another file.',
    'uk': '❌ Помилка перевірки файлу. Спробуйте інший файл.',
    'de': '❌ Fehler bei der Dateivalidierung. Bitte versuchen Sie eine andere Datei.'
},
# ============================================
# 🔒 API ОШИБКИ И ЛИМИТЫ
# ============================================
'gpt4o_limit_exceeded': {
    'ru': '❌ Исчерпан лимит запросов к GPT-4. Пожалуйста, обновите подписку.',
    'en': '❌ GPT-4 query limit exceeded. Please upgrade your subscription.',
    'uk': '❌ Вичерпаноліміт запитів до GPT-4. Будь ласка, оновіть підписку.',
    'de': '❌ GPT-4-Abfragelimit überschritten. Bitte upgraden Sie Ihr Abonnement.'
},

'photo_too_large': {
    'ru': '❌ Фото слишком большое. Максимальный размер: 10 МБ.',
    'en': '❌ Photo too large. Maximum size: 10 MB.',
    'uk': '❌ Фото занадто велике. Максимальний розмір: 10 МБ.',
    'de': '❌ Foto zu groß. Maximale Größe: 10 MB.'
},

'photo_analysis_error': {
    'ru': '❌ Ошибка при анализе фото. Попробуйте другое изображение.',
    'en': '❌ Photo analysis error. Please try another image.',
    'uk': '❌ Помилка при аналізі фото. Спробуйте інше зображення.',
    'de': '❌ Fehler bei der Fotoanalyse. Bitte versuchen Sie ein anderes Bild.'
},

'photo_analysis_failed': {
    'ru': '❌ Не удалось проанализировать фото. Убедитесь, что изображение четкое и содержит медицинскую информацию.',
    'en': '❌ Failed to analyze photo. Make sure the image is clear and contains medical information.',
    'uk': '❌ Не вдалося проаналізувати фото. Переконайтеся, що зображення чітке та містить медичну інформацію.',
    'de': '❌ Fotoanalyse fehlgeschlagen. Stellen Sie sicher, dass das Bild klar ist und medizinische Informationen enthält.'
},

'stripe_session_creation_error': {
    'ru': '❌ Ошибка при создании платежной сессии. Попробуйте позже или обратитесь в поддержку.',
    'en': '❌ Error creating payment session. Please try again later or contact support.',
    'uk': '❌ Помилка при створенні платіжної сесії. Спробуйте пізніше або зверніться до підтримки.',
    'de': '❌ Fehler beim Erstellen der Zahlungssitzung. Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support.'
},
'document_toggle_error': {
    'ru': '❌ Ошибка при изменении статуса документа. Попробуйте позже.',
    'en': '❌ Error changing document status. Please try again later.',
    'uk': '❌ Помилка при зміні статусу документа. Спробуйте пізніше.',
    'de': '❌ Fehler beim Ändern des Dokumentstatus. Bitte versuchen Sie es später erneut.'
},
'waiting_for_telegram': {
    'ru': 'Ожидание подключения Telegram...',
    'en': 'Waiting for Telegram connection...',
    'uk': 'Очікування підключення Telegram...',
    'de': 'Warten auf Telegram-Verbindung...'
},
 # ============================================
    # 🩺 ИНТЕНТ-СТРАНИЦА: АНАЛИЗ КРОВИ
    # ============================================
    'blood_test_hero_title': {
        'ru': 'Поймите, что означают ваши анализы крови',
        'en': 'Understand What Your Blood Test Results Mean',
        'uk': 'Зрозумійте, що означають ваші аналізи крові',
        'de': 'Verstehen Sie, was Ihre Bluttestergebnisse bedeuten'
    },
    'blood_test_hero_subtitle_part1': {
        'ru': 'Загрузите анализ и получите чёткое объяснение',
        'en': 'Upload your blood test and get a clear explanation',
        'uk': 'Завантажте аналіз і отримайте чітке пояснення',
        'de': 'Laden Sie Ihren Bluttest hoch und erhalten Sie eine klare Erklärung'
    },
    'blood_test_hero_subtitle_part2': {
        'ru': 'что в норме, что нет и на что стоит обратить внимание',
        'en': 'of what’s normal, what’s not, and what matters',
        'uk': 'що в нормі, що ні та на що варто звернути увагу',
        'de': 'was normal ist, was nicht und worauf es ankommt'
    },
    'blood_test_btn_continue_google': {
        'ru': 'Продолжить с Google',
        'en': 'Continue with Google',
        'uk': 'Продовжити з Google',
        'de': 'Mit Google fortfahren'
    },
    'blood_test_btn_subtitle': {
        'ru': 'Без карты · Первый анализ — бесплатно',
        'en': 'No card · First analysis free',
        'uk': 'Без картки · Перший аналіз — безкоштовно',
        'de': 'Keine Karte · Erste Analyse kostenlos'
    },
    # ============================================
    # 🔬 VALUE PROOF БЛОК (ДО/ПОСЛЕ)
    # ============================================
    'value_proof_title': {
        'ru': 'От лабораторных результатов — к понятным медицинским выводам',
        'en': 'From lab results to clear medical insights',
        'uk': 'Від лабораторних результатів — до зрозумілих медичних висновків',
        'de': 'Von Laborergebnissen zu klaren medizinischen Erkenntnissen'
    },    
    'value_proof_subtitle': {
        'ru': 'Пример: результаты анализа крови',
        'en': 'Example shown: blood test results',
        'uk': 'Приклад: результати аналізу крові',
        'de': 'Beispiel: Ergebnisse der Blutuntersuchung'
    },
    'value_before_title': {
        'ru': 'До: бланк анализа крови',
        'en': 'Before: Blood Test Lab Report',
        'uk': 'До: бланк аналізу крові',
        'de': 'Vorher: Bluttest-Laborbericht'
    },
    'value_after_title': {
        'ru': 'После: клиническое объяснение',
        'en': 'After: Clinical Explanation',
        'uk': 'Після: клінічне пояснення',
        'de': 'Nachher: Klinische Erklärung'
    },
    'value_before_caption': {
        'ru': 'Цифры, референсы и термины — без пояснений',
        'en': 'Numbers, ranges and terms — no explanations',
        'uk': 'Цифри, референси і терміни — без пояснень',
        'de': 'Zahlen, Bereiche und Begriffe — ohne Erklärungen'
    },        
    'value_after_caption': {
        'ru': 'Структурированный разбор с фокусом на важное',
        'en': 'Structured analysis focused on what matters',
        'uk': 'Структурований розбір з фокусом на важливе',
        'de': 'Strukturierte Analyse mit Fokus auf das Wesentliche'
    },  
    'value_transformation_title': {
        'ru': 'Что вы получите',
        'en': 'What you get',
        'uk': 'Що ви отримаєте',
        'de': 'Was Sie erhalten'
    },    
    'what_you_get_summary_title': {
        'ru': 'Краткое резюме',
        'en': 'Summary',
        'uk': 'Коротке резюме',
        'de': 'Zusammenfassung'
    },

    'what_you_get_summary_1': {
        'ru': 'Клинический обзор и ключевые находки',
        'en': 'Clinical overview and key findings',
        'uk': 'Клінічний огляд та ключові знахідки',
        'de': 'Klinischer Überblick und wichtige Befunde'
    },

    'what_you_get_summary_2': {
        'ru': 'Интерпретация и практическое значение',
        'en': 'Interpretation and practical meaning',
        'uk': 'Інтерпретація та практичне значення',
        'de': 'Interpretation und praktische Bedeutung'
    },

    'what_you_get_summary_3': {
        'ru': 'Ограничения и контекст для наблюдения',
        'en': 'Limitations and follow-up context',
        'uk': 'Обмеження та контекст для спостереження',
        'de': 'Einschränkungen und Follow-up-Kontext'
    },

    'what_you_get_detailed_title': {
        'ru': 'Детальный анализ',
        'en': 'Detailed analysis',
        'uk': 'Детальний аналіз',
        'de': 'Detaillierte Analyse'
    },

    'what_you_get_detailed_1': {
        'ru': 'Клиническое рассуждение экспертного уровня',
        'en': 'Expert-level clinical reasoning',
        'uk': 'Клінічне міркування експертного рівня',
        'de': 'Klinische Argumentation auf Expertenebene'
    },

    'what_you_get_detailed_2': {
        'ru': 'Возможные интерпретации и паттерны',
        'en': 'Possible interpretations and patterns',
        'uk': 'Можливі інтерпретації та патерни',
        'de': 'Mögliche Interpretationen und Muster'
    },

    'what_you_get_detailed_3': {
        'ru': 'Углубленный контекст для сложных случаев',
        'en': 'Deeper context for complex cases',
        'uk': 'Поглиблений контекст для складних випадків',
        'de': 'Tieferer Kontext für komplexe Fälle'
    },    
    'value_cta_button': {
        'ru': 'Получить мой разбор',
        'en': 'Get My Analysis',
        'uk': 'Отримати мій розбір',
        'de': 'Meine Analyse erhalten'
    },    
    'privacy_block_title': {
        'ru': 'Конфиденциальность данных и безопасная обработка',
        'en': 'Data Privacy and Secure Processing',
        'uk': 'Конфіденційність даних та безпечна обробка',
        'de': 'Datenschutz und sichere Verarbeitung'
    },

    'privacy_block_text': {
        'ru': 'Ваши документы приватны по умолчанию и доступны только вам.',
        'en': 'Your documents are private by default and accessible only to you.',
        'uk': 'Ваші документи приватні за замовчуванням і доступні лише вам.',
        'de': 'Ihre Dokumente sind standardmäßig privat und nur für Sie zugänglich.'
    },
    'stats_live_indicator': {
        'ru': 'Статистика в реальном времени',
        'en': 'Live service statistics',
        'uk': 'Статистика в реальному часі',
        'de': 'Live-Servicestatistik'
    },
    'stats_users_label': {
        'ru': 'пользователей',
        'en': 'users joined',
        'uk': 'користувачів',
        'de': 'Benutzer beigetreten'
    },
    'stats_reports_label': {
        'ru': 'отчётов проанализировано',
        'en': 'reports analyzed',
        'uk': 'звітів проаналізовано',
        'de': 'Berichte analysiert'
    },
    'stats_ai_answers_label': {
        'ru': 'ответов ИИ',
        'en': 'AI answers',
        'uk': 'відповідей ШІ',
        'de': 'KI-Antworten'
    },
    'privacy_block_note_title': {
        'ru': 'Примечание о конфиденциальности',
        'en': 'Privacy note',
        'uk': 'Примітка про конфіденційність',
        'de': 'Datenschutzhinweis'
    },
    'privacy_block_note_text': {
        'ru': 'Ваши данные обрабатываются в соответствии с принципами защиты данных GDPR и хранятся на инфраструктуре, предоставляемой сервисами, прошедшими аудит SOC 2.',
        'en': 'Your data is handled in line with GDPR data protection principles and stored on infrastructure provided by SOC 2 audited service providers.',
        'uk': 'Ваші дані обробляються відповідно до принципів захисту даних GDPR та зберігаються на інфраструктурі, що надається сервісами, які пройшли аудит SOC 2.',
        'de': 'Ihre Daten werden gemäß den Datenschutzgrundsätzen der DSGVO verarbeitet und auf einer Infrastruktur gespeichert, die von SOC 2-auditierten Dienstleistern bereitgestellt wird.'
    },
    'funnel_cta_question': {
        'ru': 'Хотите понять, что это значит именно в вашем случае?',
        'uk': 'Хочете зрозуміти, що це означає саме у вашому випадку?',
        'en': 'Want to understand what this means for your specific case?',
        'de': 'Möchten Sie verstehen, was das in Ihrem Fall bedeutet?'
    },
    'funnel_cta_btn': {
        'ru': 'Обсудить мой результат',
        'uk': 'Обговорити мій результат',
        'en': 'Discuss my result',
        'de': 'Mein Ergebnis besprechen'
    },
    'funnel_cta_btn_2': {
        'ru': 'Ответить и продолжить разбор',
        'uk': 'Відповісти і продовжити розбір',
        'en': 'Answer and continue analysis',
        'de': 'Antworten und Analyse fortsetzen'
    },
    'funnel_specialist_title': {
        'ru': 'Клиническая интерпретация',
        'uk': 'Клінічна інтерпретація',
        'en': 'Clinical interpretation',
        'de': 'Klinische Interpretation'
    },
    'funnel_specialist_intro': {
        'ru': 'В подробном разборе:',
        'uk': 'У детальному розборі:',
        'en': 'In the detailed analysis:',
        'de': 'In der detaillierten Analyse:'
    },
    'funnel_specialist_li_1': {
        'ru': 'возможные причины изменений',
        'uk': 'можливі причини змін',
        'en': 'possible causes of changes',
        'de': 'mögliche Ursachen der Veränderungen'
    },
    'funnel_specialist_li_2': {
        'ru': 'как интерпретируются показатели',
        'uk': 'як інтерпретуються показники',
        'en': 'how the indicators are interpreted',
        'de': 'wie die Indikatoren interpretiert werden'
    },
    'funnel_specialist_li_3': {
        'ru': 'какие сценарии учитываются в медицинской практике',
        'uk': 'які сценарії враховуються в медичній практиці',
        'en': 'which scenarios are considered in medical practice',
        'de': 'welche Szenarien in der medizinischen Praxis berücksichtigt werden'
    },
    'funnel_specialist_btn': {
        'ru': 'Посмотреть полный разбор',
        'uk': 'Переглянути повний розбір',
        'en': 'See full analysis',
        'de': 'Vollständige Analyse ansehen'
    },
    'funnel_block_title': {
        'ru': 'Что это значит для вас',
        'uk': 'Що це означає для вас',
        'en': 'What this means for you',
        'de': 'Was das für Sie bedeutet'
    },
    'funnel_q_title': {
        'ru': 'Давайте уточним вашу ситуацию',
        'uk': 'Давайте уточнимо вашу ситуацію',
        'en': 'Let\'s clarify your situation',
        'de': 'Lassen Sie uns Ihre Situation klären'
    },
    'funnel_q_subtitle': {
        'ru': 'Давайте уточним пару деталей — это поможет точнее разобраться в результате',
        'uk': 'Давайте уточнимо кілька деталей — це допоможе точніше розібратися з результатом',
        'en': 'Let’s clarify a few details — this will help better understand your result',
        'de': 'Lassen Sie uns ein paar Details klären — das hilft, Ihr Ergebnis besser zu verstehen'
    },
    'tab_upload_document': {'ru': 'Загрузить документ', 'en': 'Upload Document', 'uk': 'Завантажити документ', 'de': 'Dokument hochladen'},
    'tab_my_documents': {'ru': 'Мои документы', 'en': 'My Documents', 'uk': 'Мої документи', 'de': 'Meine Dokumente'},
    'recent_documents': {'ru': 'Последние документы', 'en': 'Recent Documents', 'uk': 'Останні документи', 'de': 'Letzte Dokumente'},
    'search_placeholder': {'ru': 'Поиск по названию и описанию...', 'en': 'Search by title and description...', 'uk': 'Пошук за назвою та описом...', 'de': 'Suche nach Titel und Beschreibung...'},
    'doc_type_ecg':            {'ru': 'ЭКГ',              'en': 'ECG',           'uk': 'ЕКГ',              'de': 'EKG'},
    'doc_type_lab_results':    {'ru': 'Анализы',           'en': 'Lab Tests',     'uk': 'Аналізи',          'de': 'Analysen'},
    'doc_type_imaging':        {'ru': 'Снимки',            'en': 'Imaging',       'uk': 'Знімки',           'de': 'Bildgebung'},
    'doc_type_pathology':      {'ru': 'Патология',         'en': 'Pathology',     'uk': 'Патологія',        'de': 'Pathologie'},
    'doc_type_clinical_report':{'ru': 'Выписки',           'en': 'Clinical Report','uk': 'Виписки',         'de': 'Klinischer Bericht'},
    'doc_type_prescription':   {'ru': 'Рецепты',           'en': 'Prescriptions', 'uk': 'Рецепти',          'de': 'Rezepte'},
    'doc_type_generic':        {'ru': 'Прочее',            'en': 'Other',         'uk': 'Інше',             'de': 'Sonstiges'},
    'error_loading': {'ru': 'Ошибка загрузки', 'en': 'Loading error', 'uk': 'Помилка завантаження', 'de': 'Ladefehler'},
    'all_label': {'ru': 'Все', 'en': 'All', 'uk': 'Всі', 'de': 'Alle'},
    'tab_biomarkers': {
    'ru': 'Мои биомаркеры', 'en': 'My Biomarkers', 'uk': 'Мої біомаркери', 'de': 'Meine Biomarker'
    },
    'bm_loaded': {
        'ru': 'Загружено', 'en': 'Loaded', 'uk': 'Завантажено', 'de': 'Geladen'
    },
    'bm_normal': {
        'ru': 'В норме', 'en': 'Normal', 'uk': 'В нормі', 'de': 'Normal'
    },
    'bm_deviations': {
        'ru': 'Отклонений', 'en': 'Deviations', 'uk': 'Відхилень', 'de': 'Abweichungen'
    },
    'bm_status_normal': {
        'ru': 'Норма', 'en': 'Normal', 'uk': 'Норма', 'de': 'Normal'
    },
    'bm_status_high': {
        'ru': 'Высоко', 'en': 'High', 'uk': 'Високо', 'de': 'Hoch'
    },
    'bm_status_low': {
        'ru': 'Низко', 'en': 'Low', 'uk': 'Низько', 'de': 'Niedrig'
    },
    'bm_empty_title': {
        'ru': 'Нет данных о биомаркерах', 'en': 'No biomarker data', 'uk': 'Немає даних про біомаркери', 'de': 'Keine Biomarker-Daten'
    },
    'bm_empty_sub': {
        'ru': 'Загрузите результаты анализов, чтобы увидеть биомаркеры', 'en': 'Upload lab results to see your biomarkers', 'uk': 'Завантажте результати аналізів', 'de': 'Laden Sie Labordaten hoch'
    },
    'seo_type_blood': {'ru': 'Общий анализ крови', 'en': 'Complete Blood Count', 'uk': 'Загальний аналіз крові', 'de': 'Blutbild'},
    'seo_type_biochemistry': {'ru': 'Биохимия', 'en': 'Biochemistry', 'uk': 'Біохімія', 'de': 'Biochemie'},
    'seo_type_lipids': {'ru': 'Липидный профиль', 'en': 'Lipid Profile', 'uk': 'Ліпідний профіль', 'de': 'Lipidprofil'},
    'seo_type_liver': {'ru': 'Функция печени', 'en': 'Liver Function', 'uk': 'Функція печінки', 'de': 'Leberfunktion'},
    'seo_type_kidney': {'ru': 'Функция почек', 'en': 'Kidney Function', 'uk': 'Функція нирок', 'de': 'Nierenfunktion'},
    'seo_type_thyroid': {'ru': 'Щитовидная железа', 'en': 'Thyroid Panel', 'uk': 'Щитоподібна залоза', 'de': 'Schilddrüse'},
    'seo_type_cardiac': {'ru': 'Сердечные маркеры', 'en': 'Cardiac Markers', 'uk': 'Серцеві маркери', 'de': 'Herzmarker'},
    'seo_type_hormones': {'ru': 'Гормоны', 'en': 'Hormones', 'uk': 'Гормони', 'de': 'Hormone'},
    'seo_type_vitamins': {'ru': 'Витамины и минералы', 'en': 'Vitamins & Minerals', 'uk': 'Вітаміни та мінерали', 'de': 'Vitamine & Mineralien'},
    'seo_type_coagulation': {'ru': 'Свертывание крови', 'en': 'Coagulation', 'uk': 'Згортання крові', 'de': 'Gerinnung'},
    'seo_type_inflammation': {'ru': 'Воспаление и иммунитет', 'en': 'Inflammation & Immunity', 'uk': 'Запалення та імунітет', 'de': 'Entzündung & Immunität'},
    'seo_type_diabetes': {'ru': 'Углеводный обмен', 'en': 'Glucose Metabolism', 'uk': 'Вуглеводний обмін', 'de': 'Glukosestoffwechsel'},
    'seo_type_electrolytes': {'ru': 'Электролиты', 'en': 'Electrolytes', 'uk': 'Електроліти', 'de': 'Elektrolyte'},
    'seo_type_iron': {'ru': 'Обмен железа', 'en': 'Iron Metabolism', 'uk': 'Обмін заліза', 'de': 'Eisenstoffwechsel'},
    'seo_type_tumor_markers': {'ru': 'Онкомаркеры', 'en': 'Tumor Markers', 'uk': 'Онкомаркери', 'de': 'Tumormarker'},
    'seo_type_urine': {'ru': 'Анализ мочи', 'en': 'Urinalysis', 'uk': 'Аналіз сечі', 'de': 'Urinanalyse'},
    'seo_type_immunology': {'ru': 'Иммунологические анализы', 'en': 'Immunology Tests', 'uk': 'Імунологічні аналізи', 'de': 'Immunologische Tests'},
    # ══ Dashboard новый дизайн ══    
    'dashboard_medcard_title': {'ru': 'Медкарта', 'en': 'Medical Records', 'uk': 'Медкарта', 'de': 'Krankenakte'},
    'dashboard_consultations_title': {'ru': 'Консультации', 'en': 'Consultations', 'uk': 'Консультації', 'de': 'Beratungen'},
    'dashboard_last_chat_label': {'ru': 'Последний чат', 'en': 'Last Chat', 'uk': 'Останній чат', 'de': 'Letzter Chat'},
    'dashboard_open_general_chat': {'ru': 'Открыть общий чат', 'en': 'Open General Chat', 'uk': 'Відкрити загальний чат', 'de': 'Allgemeinen Chat öffnen'},
    'dashboard_tariff_limits_title': {'ru': 'Тарифы и лимиты', 'en': 'Plan & Limits', 'uk': 'Тарифи та ліміти', 'de': 'Tarif & Limits'},
    'dashboard_docs_label': {'ru': 'Документы', 'en': 'Documents', 'uk': 'Документи', 'de': 'Dokumente'},
    'dashboard_docs_count_label': {'ru': 'Документов', 'en': 'Documents', 'uk': 'Документів', 'de': 'Dokumente'},
    'dashboard_queries_label': {'ru': 'Консультации', 'en': 'Consultations', 'uk': 'Консультації', 'de': 'Beratungen'},
    'dashboard_limits_renew': {'ru': 'Лимиты обновятся', 'en': 'Limits renew on', 'uk': 'Ліміти оновляться', 'de': 'Limits erneuern sich am'},
    'dashboard_limits_permanent': {'ru': 'Бессрочно', 'en': 'No expiry', 'uk': 'Безстроково', 'de': 'Unbefristet'},
    'dashboard_upgrade_plan': {
        'ru': 'Получить больше лимитов →',
        'en': 'Get more limits →',
        'uk': 'Отримати більше лімітів →',
        'de': 'Mehr Limits erhalten →'
    },
    'dashboard_account_title': {'ru': 'Аккаунт', 'en': 'Account', 'uk': 'Акаунт', 'de': 'Konto'},
    'dashboard_install_app_label': {'ru': 'Установить приложение', 'en': 'Install App', 'uk': 'Встановити додаток', 'de': 'App installieren'},
    'dashboard_install_app_sub': {'ru': 'iOS · Android', 'en': 'iOS · Android', 'uk': 'iOS · Android', 'de': 'iOS · Android'},
    'dashboard_add_doc_btn': {'ru': 'Добавить документ', 'en': 'Add Document', 'uk': 'Додати документ', 'de': 'Dokument hinzufügen'},
    'dashboard_my_docs_btn': {'ru': 'Мои документы', 'en': 'My Documents', 'uk': 'Мої документи', 'de': 'Meine Dokumente'},
    'dashboard_my_biomarkers_btn': {'ru': 'Мои биомаркеры', 'en': 'My Biomarkers', 'uk': 'Мої біомаркери', 'de': 'Meine Biomarker'},
    'dashboard_biomarkers': {'ru': 'биомаркеров', 'en': 'biomarkers', 'uk': 'біомаркерів', 'de': 'Biomarker'},
    'chat_empty_state': {'ru': 'Нет активных чатов по документам', 'en': 'No active document chats', 'uk': 'Немає активних чатів по документах', 'de': 'Keine aktiven Dokument-Chats'},
    # ══ Онбординг новый ══
    'onboarding_start_label': {'ru': 'С чего начать?', 'en': 'Where to start?', 'uk': 'З чого почати?', 'de': 'Wo anfangen?'},
    'onboarding_ask_title': {'ru': 'Задать вопрос', 'en': 'Ask a Question', 'uk': 'Поставити запитання', 'de': 'Frage stellen'},
    'onboarding_ask_desc': {'ru': 'Спросите про симптомы, лекарства или результаты анализов', 'en': 'Ask about symptoms, medications or test results', 'uk': 'Запитайте про симптоми, ліки або результати аналізів', 'de': 'Fragen zu Symptomen, Medikamenten oder Testergebnissen'},
    'onboarding_trust_secure': {'ru': 'Данные защищены', 'en': 'Data secured', 'uk': 'Дані захищені', 'de': 'Daten geschützt'},
    'onboarding_trust_fast': {
        'ru': 'Анализ за пару минут',
        'en': 'Analysis in a couple of minutes',
        'uk': 'Аналіз за кілька хвилин',
        'de': 'Analyse in ein paar Minuten'
    },
    'onboarding_trust_ai': {
        'ru': 'Объясняем простым языком',
        'en': 'Explained in simple language',
        'uk': 'Пояснюємо простою мовою',
        'de': 'Einfach erklärt'
    },
    'onboarding_skip': {'ru': 'Пропустить, перейти в кабинет', 'en': 'Skip, go to dashboard', 'uk': 'Пропустити, перейти в кабінет', 'de': 'Überspringen, zum Dashboard'},
    'free_label': {'ru': 'Бесплатно', 'en': 'Free', 'uk': 'Безкоштовно', 'de': 'Kostenlos'},
    'onetime_tag': {'ru': 'Без подписки', 'en': 'No subscription', 'uk': 'Без підписки', 'de': 'Ohne Abo'},
    'onetime_title': {
        'ru': 'Попробовать без подписки',
        'en': 'Try without subscription',
        'uk': 'Спробувати без підписки',
        'de': 'Ohne Abo ausprobieren'
    },    
    'onetime_feature_2': {
        'ru': '10 детальных консультаций',
        'en': '10 detailed consultations',
        'uk': '10 детальних консультацій',
        'de': '10 detaillierte Beratungen'
    },
    'onetime_no_renewal': {
        'ru': 'Без авто-продления, оплата один раз.',
        'en': 'No auto-renewal, pay once.',
        'uk': 'Без автопоновлення, оплата один раз.',
        'de': 'Ohne automatische Verlängerung, einmalige Zahlung.'
    },
    'onetime_btn': {
        'ru': 'Попробовать →',
        'en': 'Try →',
        'uk': 'Спробувати →',
        'de': 'Ausprobieren →'
    },
    'upgrade_to': {
        'ru': 'Перейти на',
        'en': 'Switch to',
        'uk': 'Перейти на',
        'de': 'Zu',
    },    
    'btn_delete': {'ru': 'Удалить', 'en': 'Delete', 'uk': 'Видалити', 'de': 'Löschen'},
    'btn_chat': {'ru': 'Обсудить', 'en': 'Discuss', 'uk': 'Обговорити', 'de': 'Besprechen'},
    'toggle_included': {'ru': 'Учитывается', 'en': 'Included', 'uk': 'Враховується', 'de': 'Berücksichtigt'},
    'toggle_excluded': {'ru': 'Не учитывается', 'en': 'Excluded', 'uk': 'Не враховується', 'de': 'Nicht berücksichtigt'},
    'doc_section_document': {'ru': 'Документ', 'en': 'Document', 'uk': 'Документ', 'de': 'Dokument'},
    'doc_section_biomarkers': {'ru': 'Биомаркеры в документе', 'en': 'Biomarkers in document', 'uk': 'Біомаркери в документі', 'de': 'Biomarker im Dokument'},
    'doc_section_interpretation': {'ru': 'Медицинская интерпретация', 'en': 'Medical interpretation', 'uk': 'Медична інтерпретація', 'de': 'Medizinische Interpretation'},
    'doc_interpretation_label': {'ru': 'Заключение для специалиста', 'en': 'Specialist conclusion', 'uk': 'Висновок для спеціаліста', 'de': 'Fazit für Spezialisten'},
    'doc_interpretation_badge': {'ru': 'Медицинский язык', 'en': 'Medical language', 'uk': 'Медична мова', 'de': 'Medizinische Sprache'},
    'doc_section_discuss': {'ru': 'Обсудить документ', 'en': 'Discuss document', 'uk': 'Обговорити документ', 'de': 'Dokument besprechen'},
    'document_title_optional': {'ru': 'Название документа', 'en': 'Document title', 'uk': 'Назва документа', 'de': 'Dokumenttitel'},
    'document_date_label': {'ru': 'Дата документа', 'en': 'Document date', 'uk': 'Дата документа', 'de': 'Dokumentdatum'},
    'drop_zone_title': {
        'ru': 'Анализы, ЭКГ, снимки и другие меддокументы',
        'en': 'Lab tests, ECGs, scans and other medical documents',
        'uk': 'Аналізи, ЕКГ, знімки та інші меддокументи',
        'de': 'Analysen, EKGs, Scans und andere medizinische Dokumente',
    },
    'select_file_btn': {
        'ru': 'Выбрать файл',
        'en': 'Select file',
        'uk': 'Вибрати файл',
        'de': 'Datei auswählen',
    },
    'drop_max_size': {
        'ru': 'до 10 МБ',
        'en': 'up to 10 MB',
        'uk': 'до 10 МБ',
        'de': 'bis 10 MB',
    },
    'trust_only_you': {
        'ru': 'Только вы имеете доступ к документам',
        'en': 'Only you have access to your documents',
        'uk': 'Тільки ви маєте доступ до документів',
        'de': 'Nur Sie haben Zugang zu Ihren Dokumenten',
    },
    'trust_analysis_time': {
        'ru': 'Анализ за несколько минут',
        'en': 'Analysis in a few minutes',
        'uk': 'Аналіз за кілька хвилин',
        'de': 'Analyse in wenigen Minuten',
    },
    'bm_detail_history': {
        'ru': 'История измерений', 'en': 'Measurement history',
        'uk': 'Історія вимірювань', 'de': 'Messverlauf'
    },
    'bm_detail_no_history': {
        'ru': 'История пуста — данные не найдены', 'en': 'No data found',
        'uk': 'Історія порожня — даних немає', 'de': 'Keine Daten gefunden'
    },
    'bm_detail_about': {
        'ru': 'Что такое', 'en': 'About', 'uk': 'Що таке', 'de': 'Was ist'
    },
    'bm_detail_influences': {
        'ru': 'Что может влиять на показатель', 'en': 'What may affect this marker',
        'uk': 'Що може впливати на показник', 'de': 'Einflussfaktoren'
    },
    'bm_detail_related': {
        'ru': 'Связанные показатели', 'en': 'Related markers',
        'uk': 'Пов\'язані показники', 'de': 'Verwandte Marker'
    },
    'bm_detail_no_value': {
        'ru': 'Нет данных', 'en': 'No data', 'uk': 'Немає даних', 'de': 'Keine Daten'
    },
    'bm_detail_go_doc': {
        'ru': 'Открыть документ', 'en': 'Open document',
        'uk': 'Відкрити документ', 'de': 'Dokument öffnen'
    },
    'bm_detail_back': {
        'ru': 'Биомаркеры', 'en': 'Biomarkers', 'uk': 'Біомаркери', 'de': 'Biomarker'
    },
    'bm_detail_causes_high': {
        'ru': 'Причины повышения', 'en': 'Causes of high', 'uk': 'Причини підвищення', 'de': 'Ursachen erhöht'
    },
    'bm_detail_causes_low': {
        'ru': 'Причины понижения', 'en': 'Causes of low', 'uk': 'Причини зниження', 'de': 'Ursachen niedrig'
    },
    'bmd_detail_last_date': {
        'ru': 'Последнее измерение', 'en': 'Last measurement',
        'uk': 'Останнє вимірювання', 'de': 'Letzte Messung'
    },
    'bmd_detail_low': {
        'ru': 'Низко', 'en': 'Low', 'uk': 'Низько', 'de': 'Niedrig'
    },
    'bmd_detail_high': {
        'ru': 'Высоко', 'en': 'High', 'uk': 'Високо', 'de': 'Hoch'
    },
    'bmd_detail_no_history': {
        'ru': 'История пуста', 'en': 'No history yet',
        'uk': 'Історія порожня', 'de': 'Keine Historie'
    },
    'bmd_detail_no_history_sub': {
        'ru': 'Загрузите анализы, чтобы начать отслеживать этот показатель',
        'en': 'Upload lab results to start tracking this marker',
        'uk': 'Завантажте аналізи, щоб почати відстежувати цей показник',
        'de': 'Laden Sie Laborergebnisse hoch, um diesen Wert zu verfolgen'
    },
    'bmd_detail_influences_sub': {
        'ru': 'Не диагноз — это возможные причины отклонения. Подтверждает врач.',
        'en': 'Not a diagnosis — these are possible causes. A doctor should confirm.',
        'uk': 'Не діагноз — це можливі причини відхилення. Підтверджує лікар.',
        'de': 'Keine Diagnose — mögliche Ursachen. Ein Arzt sollte bestätigen.'
    },
    'bmd_detail_combinations': {
        'ru': 'в сочетании с другими показателями',
        'en': 'in combination with other markers',
        'uk': 'у поєднанні з іншими показниками',
        'de': 'in Kombination mit anderen Markern'
    },
    'bmd_detail_combinations_sub': {
        'ru': 'Один показатель редко говорит обо всём. Комбинации помогают сузить причину.',
        'en': 'One marker rarely tells the whole story. Combinations help narrow the cause.',
        'uk': 'Один показник рідко говорить про все. Комбінації допомагають звузити причину.',
        'de': 'Ein Wert allein sagt selten alles. Kombinationen helfen, die Ursache einzugrenzen.'
    },
    'bmd_detail_related_sub': {
        'ru': 'Эти биомаркеры обычно смотрят вместе. Нажмите, чтобы перейти.',
        'en': 'These markers are usually reviewed together. Click to navigate.',
        'uk': 'Ці маркери зазвичай переглядають разом. Натисніть, щоб перейти.',
        'de': 'Diese Marker werden meist gemeinsam betrachtet. Klicken zum Navigieren.'
    },
    'bmd_detail_history': {
        'ru': 'История измерений', 'en': 'Measurement history',
        'uk': 'Історія вимірювань', 'de': 'Messverlauf'
    },
    'bmd_detail_no_value': {
        'ru': 'Нет данных', 'en': 'No data',
        'uk': 'Немає даних', 'de': 'Keine Daten'
    },

    # ── App Onboarding (TWA/PWA) ──
    'app_onb_slide1_title': {
    'en': 'Upload a medical\ndocument',
    'de': 'Medizinisches\nDokument hochladen',
    'ru': 'Загрузите\nмедицинский документ',
    'uk': 'Завантажте\nмедичний документ',
    },

    'app_onb_slide1_sub': {
    'en': 'Understand what your test results,\nmedical reports and doctor notes mean.',
    'de': 'Verstehen Sie, was Ihre Analysen,\nBefunde und Arztberichte bedeuten.',
    'ru': 'Поймите, что означают ваши анализы,\nрезультаты обследований и заключения врачей.',
    'uk': 'Зрозумійте, що означають ваші аналізи,\nрезультати обстежень та висновки лікарів.',
    },
    'app_onb_slide2_title': {
    'en': 'Stop explaining\nyour history again and again',
    'de': 'Erklären Sie Ihre Krankengeschichte\nnicht immer wieder neu',
    'ru': 'Не объясняйте свою историю\nснова и снова',
    'uk': 'Не пояснюйте свою історію\nзнову і знову',
    },
    'app_onb_slide2_sub': {
    'en': 'Ask about test results, symptoms, or your health in general. PulseBook remembers your documents and previous conversations to provide answers tailored to your situation.',
    'de': 'Fragen Sie nach Analysewerten, Symptomen oder Ihrer Gesundheit. PulseBook merkt sich Ihre Dokumente und frühere Gespräche, um Antworten passend zu Ihrer Situation zu geben.',
    'ru': 'Спрашивайте о результатах анализов, симптомах и здоровье в целом. PulseBook помнит ваши документы и предыдущие консультации, чтобы давать ответы с учётом именно вашей ситуации.',
    'uk': 'Запитуйте про результати аналізів, симптоми та здоров’я загалом. PulseBook пам’ятає ваші документи та попередні консультації, щоб надавати відповіді з урахуванням саме вашої ситуації.',
    },
    'app_onb_slide3_title': {
        'en': 'Track your health\nover time',
        'de': 'Verfolgen Sie Ihre\nGesundheit im Zeitverlauf',
        'ru': 'Следите за здоровьем\nв динамике',
        'uk': 'Стежте за здоров’ям\nу динаміці',
    },

    'app_onb_slide3_sub': {
        'en': 'All documents and test results are organized into a timeline so you can see how your health changes over time',
        'de': 'Alle Dokumente und Testergebnisse werden in einer Zeitleiste organisiert, damit Sie Veränderungen im Zeitverlauf sehen können',
        'ru': 'Все анализы и документы выстраиваются в хронологию, чтобы вы могли видеть изменения показателей со временем',
        'uk': 'Усі аналізи та документи формують хронологію, щоб ви могли бачити зміни показників з часом',
    },
    
}




def t(key: str, lang: str = 'ru', **kwargs) -> str:
    """
    Получить перевод по ключу с поддержкой параметров
    
    Args:
        key: Ключ перевода (например, 'welcome')
        lang: Язык ('ru', 'en', 'uk', 'de')
        **kwargs: Дополнительные параметры для форматирования строки
    
    Returns:
        Переведенная строка или ключ, если перевод не найден
    
    Examples:
        >>> t('welcome', 'ru')
        'Добро пожаловать'
        >>> t('dashboard_welcome', 'en')
        'Welcome'
        >>> t('hello_name', 'ru', name='Иван')
        'Привет, Иван!'
    """
    # Проверяем что язык поддерживается
    if lang not in ['ru', 'en', 'uk', 'de']:
        lang = 'en'  # По умолчанию английский
    
    # Получаем перевод
    translation = TRANSLATIONS.get(key, {})
    text = translation.get(lang, key)
    
    # Если есть параметры для форматирования - применяем их
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            # Если форматирование не удалось - возвращаем как есть
            pass
    
    return text


def get_supported_languages():
    """Получить список поддерживаемых языков с флагами"""
    return [
        {'code': 'en', 'name': 'English', 'flag': '🇬🇧'},
        {'code': 'de', 'name': 'Deutsch', 'flag': '🇩🇪'},
        {'code': 'uk', 'name': 'Українська', 'flag': '🇺🇦'},
        {'code': 'ru', 'name': 'Русский', 'flag': '🇷🇺'}
    ]


def get_current_language(session):
    """
    Получить текущий язык из сессии Flask
    
    Args:
        session: Flask session объект
    
    Returns:
        Код языка ('ru', 'en', 'uk', 'de')
    """
    return session.get('language', 'en')


def set_language(session, lang_code: str):
    """
    Установить язык в сессию Flask
    
    Args:
        session: Flask session объект
        lang_code: Код языка ('ru', 'en', 'uk', 'de')
    """
    if lang_code in ['ru', 'en', 'uk', 'de']:
        session['language'] = lang_code
        session.modified = True