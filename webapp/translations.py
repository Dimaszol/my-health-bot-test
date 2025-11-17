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
        'ru': 'Ваш умный помощник для',
        'en': 'Your Smart Assistant for',
        'uk': 'Ваш розумний помічник для',
        'de': 'Ihr intelligenter Assistent für'
    },
    'hero_main_title_highlight': {
        'ru': 'управления здоровьем',
        'en': 'Health Management',
        'uk': 'управління здоров\'ям',
        'de': 'Gesundheitsmanagement'
    },
    'hero_main_title_part2': {
        'ru': '',
        'en': '',
        'uk': '',
        'de': ''
    },
    'hero_description': {
        'ru': 'Храните медицинские документы в одном месте. Получайте мгновенный анализ и консультации от ИИ-ассистента. Контролируйте своё здоровье с помощью современных технологий.',
        'en': 'Store medical documents in one place. Get instant analysis and consultations from an AI assistant. Take control of your health with modern technology.',
        'uk': 'Зберігайте медичні документи в одному місці. Отримуйте миттєвий аналіз та консультації від ШІ-асистента. Контролюйте своє здоров\'я за допомогою сучасних технологій.',
        'de': 'Speichern Sie medizinische Dokumente an einem Ort. Erhalten Sie sofortige Analysen und Beratung von einem KI-Assistenten. Kontrollieren Sie Ihre Gesundheit mit moderner Technologie.'
    },
    'btn_try_free': {
        'ru': 'Попробовать бесплатно',
        'en': 'Try for free',
        'uk': 'Спробувати безкоштовно',
        'de': 'Kostenlos testen'
    },
    'btn_learn_more': {
        'ru': 'Узнать больше',
        'en': 'Learn more',
        'uk': 'Дізнатися більше',
        'de': 'Mehr erfahren'
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
    'menu_features': {
        'ru': 'Возможности',
        'en': 'Features',
        'uk': 'Можливості',
        'de': 'Funktionen'
    },
    'menu_security': {
        'ru': 'Безопасность',
        'en': 'Security',
        'uk': 'Безпека',
        'de': 'Sicherheit'
    },
    
    # ============================================
    # ✨ СЕКЦИЯ ВОЗМОЖНОСТЕЙ
    # ============================================
    'section_features': {
        'ru': 'Что вы можете делать',
        'en': 'What you can do',
        'uk': 'Що ви можете робити',
        'de': 'Was Sie tun können'
    },
    'features_subtitle': {
        'ru': 'Мощные AI-инструменты для управления вашим здоровьем',
        'en': 'Powerful AI tools for managing your health',
        'uk': 'Потужні AI-інструменти для управління вашим здоров\'ям',
        'de': 'Leistungsstarke KI-Tools zur Verwaltung Ihrer Gesundheit'
    },
    'feature_upload_title': {
        'ru': 'Анализ документов',
        'en': 'Document Analysis',
        'uk': 'Аналіз документів',
        'de': 'Dokumentenanalyse'
    },
    'feature_upload_text': {
        'ru': 'Загружайте анализы, снимки, заключения врачей в форматах PDF, DOCX, изображения. AI автоматически извлечет все важные данные.',
        'en': 'Upload tests, images, doctor reports in PDF, DOCX, image formats. AI automatically extracts all important data.',
        'uk': 'Завантажуйте аналізи, знімки, висновки лікарів у форматах PDF, DOCX, зображення. AI автоматично витягне всі важливі дані.',
        'de': 'Laden Sie Tests, Bilder, Arztberichte in PDF-, DOCX-, Bildformaten hoch. KI extrahiert automatisch alle wichtigen Daten.'
    },
    'feature_upload_list1': {
        'ru': 'Результаты анализов крови, мочи',
        'en': 'Blood and urine test results',
        'uk': 'Результати аналізів крові, сечі',
        'de': 'Blut- und Urintestergebnisse'
    },
    'feature_upload_list2': {
        'ru': 'Рентген, МРТ, УЗИ снимки',
        'en': 'X-ray, MRI, ultrasound images',
        'uk': 'Рентген, МРТ, УЗД знімки',
        'de': 'Röntgen-, MRT-, Ultraschallbilder'
    },
    'feature_upload_list3': {
        'ru': 'Выписки и заключения врачей',
        'en': 'Medical reports and doctor conclusions',
        'uk': 'Виписки та висновки лікарів',
        'de': 'Arztberichte und Schlussfolgerungen'
    },
    'feature_upload_list4': {
        'ru': 'Подробный анализ документов',
        'en': 'Detailed document analysis',
        'uk': 'Детальний аналіз документів',
        'de': 'Detaillierte Dokumentenanalyse'
    },
    'feature_ai_title': {
        'ru': 'ИИ-консультант',
        'en': 'AI Consultant',
        'uk': 'AI-консультант',
        'de': 'KI-Berater'
    },
    'feature_ai_title_247': {
        'ru': 'AI-консультант 24/7',
        'en': 'AI Consultant 24/7',
        'uk': 'AI-консультант 24/7',
        'de': 'KI-Berater 24/7'
    },
    'feature_ai_text': {
        'ru': 'Задавайте вопросы о вашем здоровье и получайте ответы на основе ваших документов. ИИ анализирует вашу историю.',
        'en': 'Ask questions about your health and get answers based on your documents. AI analyzes your history.',
        'uk': 'Ставте питання про ваше здоров\'я та отримуйте відповіді на основі ваших документів. ШІ аналізує вашу історію.',
        'de': 'Stellen Sie Fragen zu Ihrer Gesundheit und erhalten Sie Antworten basierend auf Ihren Dokumenten. KI analysiert Ihre Geschichte.'
    },
    'feature_ai_list1': {
        'ru': 'Мгновенные ответы на вопросы',
        'en': 'Instant answers to questions',
        'uk': 'Миттєві відповіді на питання',
        'de': 'Sofortige Antworten auf Fragen'
    },
    'feature_ai_list2': {
        'ru': 'Персональный анализ на основе ваших данных',
        'en': 'Personalized analysis based on your data',
        'uk': 'Персональний аналіз на основі ваших даних',
        'de': 'Personalisierte Analyse basierend auf Ihren Daten'
    },
    'feature_ai_list3': {
        'ru': 'Понятные объяснения терминов',
        'en': 'Clear explanations of terms',
        'uk': 'Зрозумілі пояснення термінів',
        'de': 'Klare Erklärungen von Begriffen'
    },
    'feature_history_title': {
        'ru': 'Медицинская карта',
        'en': 'Medical Record',
        'uk': 'Медична карта',
        'de': 'Krankenakte'
    },
    'feature_history_text': {
        'ru': 'Вся ваша медицинская история в одном месте, доступна в любое время. Отслеживайте динамику показателей.',
        'en': 'All your medical history in one place, accessible anytime. Track your health metrics dynamics.',
        'uk': 'Вся ваша медична історія в одному місці, доступна в будь-який час. Відстежуйте динаміку показників.',
        'de': 'Ihre gesamte Krankengeschichte an einem Ort, jederzeit zugänglich. Verfolgen Sie die Dynamik Ihrer Gesundheitskennzahlen.'
    },
    'feature_history_list1': {
        'ru': 'Хронология всех документов',
        'en': 'Timeline of all documents',
        'uk': 'Хронологія всіх документів',
        'de': 'Zeitleiste aller Dokumente'
    },
    'feature_history_list2': {
        'ru': 'Все загруженные данные используются ИИ для ответов',
        'en': 'All uploaded data is used by AI for answers',
        'uk': 'Всі завантажені дані використовуються ШІ для відповідей',
        'de': 'Alle hochgeladenen Daten werden von der KI für Antworten verwendet'
    },
    'feature_history_list3': {
        'ru': 'Чем больше PulseBook знает о вас, тем точнее рекомендации',
        'en': 'The more PulseBook knows about you, the more accurate the recommendations',
        'uk': 'Чим більше PulseBook знає про вас, тим точніші рекомендації',
        'de': 'Je mehr PulseBook über Sie weiß, desto genauer sind die Empfehlungen'
    },
    'menu_faq': {
        'ru': 'FAQ',
        'en': 'FAQ',
        'uk': 'FAQ',
        'de': 'FAQ'
    },
    # ============================================
    # 🔒 БЕЗОПАСНОСТЬ
    # ============================================
    'security_title': {
        'ru': 'Ваши данные в полной безопасности',
        'en': 'Your data is completely secure',
        'uk': 'Ваші дані в повній безпеці',
        'de': 'Ihre Daten sind vollständig sicher'
    },
    'security_description': {
        'ru': 'Мы используем шифрование данных, безопасную авторизацию через Google и храним информацию на защищённых серверах. Ваша медицинская информация доступна только вам.',
        'en': 'We use data encryption, secure Google authentication and store information on protected servers. Your medical information is accessible only to you.',
        'uk': 'Ми використовуємо шифрування даних, безпечну авторизацію через Google і зберігаємо інформацію на захищених серверах. Ваша медична інформація доступна тільки вам.',
        'de': 'Wir verwenden Datenverschlüsselung, sichere Google-Authentifizierung und speichern Informationen auf geschützten Servern. Ihre medizinischen Informationen sind nur für Sie zugänglich.'
    },
    'security_note_title': {
        'ru': 'Примечание о конфиденциальности',
        'en': 'Privacy Note',
        'uk': 'Примітка про конфіденційність',
        'de': 'Datenschutzhinweis'
    },
    'security_note_text': {
        'ru': 'Ваши данные конфиденциальны и защищены стандартами SOC 2, HIPAA и GDPR.',
        'en': 'Your data is confidential and protected by SOC 2, HIPAA and GDPR standards.',
        'uk': 'Ваші дані конфіденційні та захищені стандартами SOC 2, HIPAA і GDPR.',
        'de': 'Ihre Daten sind vertraulich und durch SOC 2-, HIPAA- und GDPR-Standards geschützt.'
    },
    
    # ============================================
    # 📈 СТАТИСТИКА
    # ============================================
    'stats_trust_title': {
        'ru': 'Нам доверяют тысячи пользователей',
        'en': 'Thousands of users trust us',
        'uk': 'Нам довіряють тисячі користувачів',
        'de': 'Tausende von Benutzern vertrauen uns'
    },
    'stats_active_users': {
        'ru': 'Активных пользователей',
        'en': 'Active users',
        'uk': 'Активних користувачів',
        'de': 'Aktive Benutzer'
    },
    'stats_documents_analyzed': {
        'ru': 'Проанализированных документов',
        'en': 'Documents analyzed',
        'uk': 'Проаналізованих документів',
        'de': 'Analysierte Dokumente'
    },
    'stats_ai_consultations': {
        'ru': 'AI-консультаций',
        'en': 'AI consultations',
        'uk': 'AI-консультацій',
        'de': 'KI-Beratungen'
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
        'ru': 'Присоединяйтесь к тысячам пользователей, которые уже управляют своим здоровьем с помощью AI',
        'en': 'Join thousands of users who are already managing their health with AI',
        'uk': 'Приєднуйтесь до тисяч користувачів, які вже керують своїм здоров\'ям за допомогою AI',
        'de': 'Schließen Sie sich Tausenden von Benutzern an, die ihre Gesundheit bereits mit KI verwalten'
    },
    'cta_button': {
        'ru': 'Начать бесплатно 🚀',
        'en': 'Start for free 🚀',
        'uk': 'Почати безкоштовно 🚀',
        'de': 'Kostenlos starten 🚀'
    },
    'cta_note': {
        'ru': 'Регистрация занимает всего 30 секунд • Не требуется кредитная карта',
        'en': 'Registration takes only 30 seconds • No credit card required',
        'uk': 'Реєстрація займає всього 30 секунд • Не потрібна кредитна картка',
        'de': 'Registrierung dauert nur 30 Sekunden • Keine Kreditkarte erforderlich'
    },
    
    # ============================================
    # 🏥 DASHBOARD (Личный кабинет)
    # ============================================
    'dashboard_welcome': {
        'ru': 'Добро пожаловать',
        'en': 'Welcome',
        'uk': 'Ласкаво просимо',
        'de': 'Willkommen'
    },
    'dashboard_subtitle': {
        'ru': 'Ваш персональный медицинский кабинет',
        'en': 'Your personal medical dashboard',
        'uk': 'Ваш особистий медичний кабінет',
        'de': 'Ihr persönliches medizinisches Dashboard'
    },
    'stats_documents_uploaded': {
        'ru': 'Загружено документов',
        'en': 'Documents Uploaded',
        'uk': 'Завантажено документів',
        'de': 'Hochgeladene Dokumente'
    },
    'stats_documents_left': {
        'ru': 'Осталось',
        'en': 'Remaining',
        'uk': 'Залишилось',
        'de': 'Verbleibend'
    },
    'stats_messages': {
        'ru': 'Сообщений с AI',
        'en': 'AI Messages',
        'uk': 'Повідомлень з AI',
        'de': 'KI-Nachrichten'
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
    'btn_upload_document': {
        'ru': 'Загрузить документ',
        'en': 'Upload Document',
        'uk': 'Завантажити документ',
        'de': 'Dokument hochladen'
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
    'tip_upload_docs': {
        'ru': 'Загрузите все ваши медицинские документы, чтобы AI мог давать более точные рекомендации на основе полной картины вашего здоровья.',
        'en': 'Upload all your medical documents so AI can provide more accurate recommendations based on your complete health picture.',
        'uk': 'Завантажте всі ваші медичні документи, щоб AI міг давати більш точні рекомендації на основі повної картини вашого здоров\'я.',
        'de': 'Laden Sie alle Ihre medizinischen Dokumente hoch, damit die KI genauere Empfehlungen basierend auf Ihrem vollständigen Gesundheitsbild geben kann.'
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
    'progress_upload': {
        'ru': '📤 Загружаем файл...',
        'en': '📤 Uploading file...',
        'uk': '📤 Завантажуємо файл...',
        'de': '📤 Datei wird hochgeladen...'
    },
    'progress_extract': {
        'ru': '📝 Извлекаем текст через AI...',
        'en': '📝 Extracting text via AI...',
        'uk': '📝 Витягуємо текст через AI...',
        'de': '📝 Text wird per KI extrahiert...'
    },
    'progress_analyze': {
        'ru': '🔍 Анализируем содержимое...',
        'en': '🔍 Analyzing content...',
        'uk': '🔍 Аналізуємо вміст...',
        'de': '🔍 Inhalt wird analysiert...'
    },
    'progress_save': {
        'ru': '💾 Сохраняем в базу данных...',
        'en': '💾 Saving to database...',
        'uk': '💾 Зберігаємо в базу даних...',
        'de': '💾 In Datenbank speichern...'
    },
    'progress_completed': {
        'ru': '✅ Документ успешно обработан!',
        'en': '✅ Document processed successfully!',
        'uk': '✅ Документ успішно оброблено!',
        'de': '✅ Dokument erfolgreich verarbeitet!'
    },
    'progress_step_upload': {
        'ru': 'Загрузка файла',
        'en': 'File upload',
        'uk': 'Завантаження файлу',
        'de': 'Datei-Upload'
    },
    'progress_step_extract': {
        'ru': 'Извлечение текста',
        'en': 'Text extraction',
        'uk': 'Витягування тексту',
        'de': 'Textextraktion'
    },
    'progress_step_analyze': {
        'ru': 'Анализ AI',
        'en': 'AI Analysis',
        'uk': 'Аналіз AI',
        'de': 'KI-Analyse'
    },
    'progress_step_save': {
        'ru': 'Сохранение',
        'en': 'Saving',
        'uk': 'Збереження',
        'de': 'Speichern'
    },
    'progress_please_wait': {
        'ru': 'Пожалуйста, подождите...',
        'en': 'Please wait...',
        'uk': 'Будь ласка, зачекайте...',
        'de': 'Bitte warten...'
    },
    # ============================================
    # 📄 СТРАНИЦА ДОКУМЕНТОВ
    # ============================================
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
        'ru': 'Мои документы',
        'en': 'My Documents',
        'uk': 'Мої документи',
        'de': 'Meine Dokumente'
    },
    'page_documents_subtitle': {
        'ru': 'Загрузите медицинские файлы, чтобы PulseBook знал ваш контекст и отвечал точнее',
        'en': 'Upload your medical files so PulseBook can understand your context and respond more accurately',
        'uk': 'Завантажте медичні файли, щоб PulseBook розумів ваш контекст і відповідав точніше',
        'de': 'Laden Sie Ihre medizinischen Dateien hoch, damit PulseBook Ihren Kontext versteht und genauer antwortet'
    },
    
    'document_title_optional': {
        'ru': 'Название документа (необязательно)',
        'en': 'Document title (optional)',
        'uk': 'Назва документа (необов\'язково)',
        'de': 'Dokumententitel (optional)'
    },
    'document_title_placeholder': {
        'ru': 'Например: Анализ крови от 15.01.2025',
        'en': 'Example: Blood test from 15.01.2025',
        'uk': 'Наприклад: Аналіз крові від 15.01.2025',
        'de': 'Beispiel: Bluttest vom 15.01.2025'
    },
    'select_file': {
        'ru': 'Выберите файл',
        'en': 'Select file',
        'uk': 'Виберіть файл',
        'de': 'Datei auswählen'
    },
    'supported_formats': {
        'ru': 'Поддерживаемые форматы: PDF, DOCX, TXT, JPG, PNG (макс. 10 МБ)',
        'en': 'Supported formats: PDF, DOCX, TXT, JPG, PNG (max. 10 MB)',
        'uk': 'Підтримувані формати: PDF, DOCX, TXT, JPG, PNG (макс. 10 МБ)',
        'de': 'Unterstützte Formate: PDF, DOCX, TXT, JPG, PNG (max. 10 MB)'
    },
    'uploaded_documents': {
        'ru': 'Загруженные документы',
        'en': 'Uploaded documents',
        'uk': 'Завантажені документи',
        'de': 'Hochgeladene Dokumente'
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
    'document_delete': {
        'ru': 'Удалить',
        'en': 'Delete',
        'uk': 'Видалити',
        'de': 'Löschen'
    },
    'no_documents_yet': {
        'ru': 'У вас пока нет документов',
        'en': 'You have no documents yet',
        'uk': 'У вас поки немає документів',
        'de': 'Sie haben noch keine Dokumente'
    },
    'no_documents_action': {
        'ru': 'Загрузите ваш первый медицинский документ используя форму выше',
        'en': 'Upload your first medical document using the form above',
        'uk': 'Завантажте ваш перший медичний документ, використовуючи форму вище',
        'de': 'Laden Sie Ihr erstes medizinisches Dokument mit dem obigen Formular hoch'
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
        'ru': 'Показать',
        'uk': 'Показати',
        'en': 'Show',
        'de': 'Anzeigen'
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
    'chat_start_conversation': {
        'ru': 'Начните разговор — задайте мне любой вопрос о вашем здоровье',
        'en': 'Start a conversation — ask me any question about your health',
        'uk': 'Почніть розмову — поставте мені будь-яке питання про ваше здоров\'я',
        'de': 'Starten Sie ein Gespräch — stellen Sie mir eine Frage zu Ihrer Gesundheit'
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
        'ru': 'Физическая активность',
        'en': 'Physical activity',
        'uk': 'Фізична активність',
        'de': 'Körperliche Aktivität'
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
    'common_delete': {
        'ru': 'Удалить',
        'en': 'Delete',
        'uk': 'Видалити',
        'de': 'Löschen'
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
        'ru': 'Работает на',
        'en': 'Powered by',
        'uk': 'Працює на',
        'de': 'Betrieben von'
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
# ============================================
# 💳 СТРАНИЦА ПОДПИСОК
# ============================================

'pricing_title': {
    'ru': 'Тарифные планы PulseBook',
    'en': 'PulseBook Pricing Plans',
    'uk': 'Тарифні плани PulseBook',
    'de': 'PulseBook Preispläne'
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
    'ru': 'Долгосрочная память ИИ',
    'en': 'AI long-term memory',
    'uk': 'Довгострокова пам\'ять ШІ',
    'de': 'KI-Langzeitgedächtnis'
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
'package_extra_name': {
    'ru': 'Дополнительный пакет',
    'en': 'Additional package',
    'uk': 'Додатковий пакет',
    'de': 'Zusatzpaket'
},

'package_extra_feature_1': {
    'ru': '3 медицинских документа',
    'en': '3 medical documents',
    'uk': '3 медичних документи',
    'de': '3 medizinische Dokumente'
},

'package_extra_feature_2': {
    'ru': '30 детальных консультаций',
    'en': '30 detailed consultations',
    'uk': '30 детальних консультацій',
    'de': '30 detaillierte Beratungen'
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
    'ru': '100 детальных консультаций в месяц',
    'en': '100 detailed consultations per month',
    'uk': '100 детальних консультацій на місяць',
    'de': '100 detaillierte Beratungen pro Monat'
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
    'ru': '400 детальных консультаций в месяц',
    'en': '400 detailed consultations per month',
    'uk': '400 детальних консультацій на місяць',
    'de': '400 detaillierte Beratungen pro Monat'
},

'package_premium_feature_3': {
    'ru': 'Повышенный лимит на базовые ответы',
    'en': 'Increased limit for basic responses',
    'uk': 'Підвищений ліміт на базові відповіді',
    'de': 'Erhöhtes Limit für Basisantworten'
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
    'ru': 'Этот AI-анализ носит информационный характер и может содержать ошибки. Не является диагнозом или назначением. Перед принятием решений проконсультируйтесь с врачом.',
    'en': 'This AI-generated analysis is for informational purposes only and may contain errors. It is not a diagnosis or prescription. Please consult a doctor before making any decisions.',
    'uk': 'Цей AI-аналіз носить інформаційний характер і може містити помилки. Не є діагнозом або призначенням. Перед прийняттям рішень проконсультуйтеся з лікарем.',
    'de': 'Diese KI-Analyse dient nur zu Informationszwecken und kann Fehler enthalten. Es ist keine Diagnose oder Verschreibung. Bitte konsultieren Sie einen Arzt, bevor Sie Entscheidungen treffen.'
},
'btn_delete_document': {
    'ru': 'Удалить',
    'en': 'Delete',
    'uk': 'Видалити',
    'de': 'Löschen'
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
# === HERO СЕКЦИЯ (улучшенные тексты) ===
'hero_main_title_part1': {
    'ru': 'Медицинская помощь',
    'en': 'Medical assistance',
    'uk': 'Медична допомога',
    'de': 'Medizinische Hilfe'
},

'hero_main_title_highlight': {
    'ru': 'на основе ИИ',
    'en': 'powered by AI',
    'uk': 'на основі ШІ',
    'de': 'mit KI-Unterstützung'
},

'hero_main_title_part2': {
    'ru': 'доступная каждому',
    'en': 'accessible to everyone',
    'uk': 'доступна кожному',
    'de': 'für jeden zugänglich'
},

'hero_description': {
    'ru': 'Храните медицинские документы в одном месте. Получайте мгновенный анализ и консультации от ИИ-ассистента. Контролируйте своё здоровье с помощью современных технологий.',
    'en': 'Store medical documents in one place. Get instant analysis and consultations from AI assistant. Take control of your health with modern technology.',
    'uk': 'Зберігайте медичні документи в одному місці. Отримуйте миттєвий аналіз та консультації від ШІ-асистента. Контролюйте своє здоров\'я за допомогою сучасних технологій.',
    'de': 'Speichern Sie medizinische Dokumente an einem Ort. Erhalten Sie sofortige Analysen und Beratungen vom KI-Assistenten. Kontrollieren Sie Ihre Gesundheit mit moderner Technologie.'
},

# === КАК ЭТО РАБОТАЕТ ===
'how_it_works_title': {
    'ru': 'Три шага до результата',
    'en': 'Three steps to results',
    'uk': 'Три кроки до результату',
    'de': 'Drei Schritte zum Ergebnis'
},

'how_it_works_subtitle': {
    'ru': 'Простой процесс для получения медицинской информации',
    'en': 'Simple process to get medical information',
    'uk': 'Простий процес для отримання медичної інформації',
    'de': 'Einfacher Prozess für medizinische Informationen'
},

'step1_title': {
    'ru': 'Загрузка документов',
    'en': 'Upload documents',
    'uk': 'Завантаження документів',
    'de': 'Dokumente hochladen'
},

'step1_text': {
    'ru': 'Загрузите анализы, снимки или заключения врачей. Поддерживаются все популярные форматы файлов.',
    'en': 'Upload tests, images or medical reports. All popular file formats are supported.',
    'uk': 'Завантажте аналізи, знімки або висновки лікарів. Підтримуються всі популярні формати файлів.',
    'de': 'Laden Sie Tests, Bilder oder Arztberichte hoch. Alle gängigen Dateiformate werden unterstützt.'
},

'step2_title': {
    'ru': 'Автоматический анализ',
    'en': 'Automatic analysis',
    'uk': 'Автоматичний аналіз',
    'de': 'Automatische Analyse'
},

'step2_text': {
    'ru': 'ИИ обрабатывает документы и формирует структурированный медицинский профиль за секунды.',
    'en': 'AI processes documents and creates a structured medical profile in seconds.',
    'uk': 'ШІ обробляє документи та формує структурований медичний профіль за секунди.',
    'de': 'KI verarbeitet Dokumente und erstellt in Sekunden ein strukturiertes Gesundheitsprofil.'
},

'step3_title': {
    'ru': 'Персональные рекомендации',
    'en': 'Personalized recommendations',
    'uk': 'Персональні рекомендації',
    'de': 'Personalisierte Empfehlungen'
},

'step3_text': {
    'ru': 'Задавайте вопросы ИИ-ассистенту и получайте понятные объяснения в любое время.',
    'en': 'Ask questions to AI assistant and get clear explanations anytime.',
    'uk': 'Ставте питання ШІ-асистенту та отримуйте зрозумілі пояснення в будь-який час.',
    'de': 'Stellen Sie dem KI-Assistenten Fragen und erhalten Sie jederzeit verständliche Erklärungen.'
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
        'ru': '📱 Быстрый доступ к боту с телефона',
        'en': '📱 Quick bot access from phone',
        'uk': '📱 Швидкий доступ до бота з телефону',
        'de': '📱 Schneller Bot-Zugriff vom Telefon'
    },
    
    'link_benefit_2': {
        'ru': '🔔 Уведомления о приёме лекарств',
        'en': '🔔 Medication reminders',
        'uk': '🔔 Нагадування про прийом ліків',
        'de': '🔔 Medikamentenerinnerungen'
    },
    
    'link_benefit_3': {
        'ru': '☁️ Единая история на обеих платформах',
        'en': '☁️ Unified history across platforms',
        'uk': '☁️ Єдина історія на обох платформах',
        'de': '☁️ Einheitliche Historie auf beiden Plattformen'
    },
    
    'link_benefit_4': {
        'ru': '🎯 Одна подписка на все устройства',
        'en': '🎯 One subscription for all devices',
        'uk': '🎯 Одна підписка на всі пристрої',
        'de': '🎯 Ein Abonnement für alle Geräte'
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