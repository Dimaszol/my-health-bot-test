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
    'hero_main_title_part1': {
        'ru': 'Ваша',
        'en': 'Your',
        'uk': 'Ваша',
        'de': 'Ihre'
    },
    'hero_main_title_highlight': {
        'ru': 'AI-платформа',
        'en': 'AI-platform',
        'uk': 'AI-платформа',
        'de': 'KI-Plattform'
    },
    'hero_main_title_part2': {
        'ru': 'для управления здоровьем',
        'en': 'for health management',
        'uk': 'для управління здоров\'ям',
        'de': 'für Gesundheitsmanagement'
    },
    'hero_description': {
        'ru': 'Для пациентов, врачей и медицинских компаний: Medical Assistant предоставляет надежные AI-инструменты там, где они нужны больше всего.',
        'en': 'For patients, doctors and medical companies: Medical Assistant provides reliable AI tools where they are needed most.',
        'uk': 'Для пацієнтів, лікарів та медичних компаній: Medical Assistant надає надійні AI-інструменти там, де вони потрібні найбільше.',
        'de': 'Für Patienten, Ärzte und medizinische Unternehmen: Medical Assistant bietet zuverlässige KI-Tools dort, wo sie am meisten benötigt werden.'
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
        'en': 'Upload tests, images, doctor reports in PDF, DOCX, image formats. AI will automatically extract all important data.',
        'uk': 'Завантажуйте аналізи, знімки, висновки лікарів у форматах PDF, DOCX, зображення. AI автоматично витягне всі важливі дані.',
        'de': 'Laden Sie Tests, Bilder, Arztberichte in PDF-, DOCX- und Bildformaten hoch. KI extrahiert automatisch alle wichtigen Daten.'
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
        'en': 'Medical reports and conclusions',
        'uk': 'Виписки та висновки лікарів',
        'de': 'Arztberichte und Schlussfolgerungen'
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
        'ru': 'Задавайте вопросы о вашем здоровье и получайте ответы на основе ваших документов. GPT-4 анализирует вашу историю.',
        'en': 'Ask health questions and get answers based on your documents. GPT-4 analyzes your history.',
        'uk': 'Ставте питання про ваше здоров\'я та отримуйте відповіді на основі ваших документів. GPT-4 аналізує вашу історію.',
        'de': 'Stellen Sie Gesundheitsfragen und erhalten Sie Antworten basierend auf Ihren Dokumenten. GPT-4 analysiert Ihre Geschichte.'
    },
    'feature_ai_list1': {
        'ru': 'Мгновенные ответы на вопросы',
        'en': 'Instant answers to questions',
        'uk': 'Миттєві відповіді на питання',
        'de': 'Sofortige Antworten auf Fragen'
    },
    'feature_ai_list2': {
        'ru': 'Анализ на основе ваших данных',
        'en': 'Analysis based on your data',
        'uk': 'Аналіз на основі ваших даних',
        'de': 'Analyse basierend auf Ihren Daten'
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
        'ru': 'Вся ваша медицинская информация в одном месте, доступна в любое время. Отслеживайте динамику показателей.',
        'en': 'All your medical information in one place, accessible anytime. Track metrics dynamics.',
        'uk': 'Вся ваша медична інформація в одному місці, доступна в будь-який час. Відстежуйте динаміку показників.',
        'de': 'Alle Ihre medizinischen Informationen an einem Ort, jederzeit zugänglich. Verfolgen Sie die Dynamik der Kennzahlen.'
    },
    'feature_history_list1': {
        'ru': 'Хронология всех документов',
        'en': 'Timeline of all documents',
        'uk': 'Хронологія всіх документів',
        'de': 'Zeitleiste aller Dokumente'
    },
    'feature_history_list2': {
        'ru': 'Графики изменения анализов',
        'en': 'Test results trend charts',
        'uk': 'Графіки зміни аналізів',
        'de': 'Trenddiagramme der Testergebnisse'
    },
    'feature_history_list3': {
        'ru': 'Экспорт данных для врача',
        'en': 'Data export for doctor',
        'uk': 'Експорт даних для лікаря',
        'de': 'Datenexport für Arzt'
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
        'ru': 'Улучшить план',
        'en': 'Upgrade Plan',
        'uk': 'Покращити план',
        'de': 'Plan upgraden'
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
        'ru': 'Управляйте вашими медицинскими файлами',
        'en': 'Manage your medical files',
        'uk': 'Керуйте вашими медичними файлами',
        'de': 'Verwalten Sie Ihre medizinischen Dateien'
    },
    'upload_new_document': {
        'ru': 'Загрузить новый документ',
        'en': 'Upload new document',
        'uk': 'Завантажити новий документ',
        'de': 'Neues Dokument hochladen'
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
        'ru': 'Как заполнить анкету?',
        'en': 'How to fill out the form?',
        'uk': 'Як заповнити анкету?',
        'de': 'Wie fülle ich das Formular aus?'
    },
    'profile_fill_instruction': {
        'ru': 'Если вы зарегистрировались через веб-сайт, анкета пока пустая. Вы можете заполнить её через Telegram-бота или мы добавим форму редактирования позже.',
        'en': 'If you registered through the website, the form is still empty. You can fill it out via the Telegram bot or we will add an editing form later.',
        'uk': 'Якщо ви зареєструвалися через веб-сайт, анкета поки порожня. Ви можете заповнити її через Telegram-бота або ми додамо форму редагування пізніше.',
        'de': 'Wenn Sie sich über die Website registriert haben, ist das Formular noch leer. Sie können es über den Telegram-Bot ausfüllen oder wir werden später ein Bearbeitungsformular hinzufügen.'
    },
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
    'delete_feature_coming_soon': {
        'ru': 'Функция удаления аккаунта будет добавлена позже',
        'en': 'Account deletion feature will be added later',
        'uk': 'Функція видалення акаунту буде додана пізніше',
        'de': 'Kontolöschfunktion wird später hinzugefügt'
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
'pricing_subtitle': {
    'ru': 'Для людей, использующих PulseBook для управления своим здоровьем',
    'en': 'For individuals using PulseBook to manage their personal health',
    'uk': 'Для людей, які використовують PulseBook для керування своїм здоров\'ям',
    'de': 'Für Personen, die PulseBook zur Verwaltung ihrer persönlichen Gesundheit nutzen'
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
    'ru': 'Начать',
    'en': 'Get Started',
    'uk': 'Почати',
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
    'ru': 'Базовый',
    'en': 'Basic',
    'uk': 'Базовий',
    'de': 'Basis'
},

'package_premium_name': {
    'ru': 'Премиум',
    'en': 'Premium',
    'uk': 'Преміум',
    'de': 'Premium'
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
}
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
        lang = 'ru'  # По умолчанию русский
    
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
        {'code': 'ru', 'name': 'Русский', 'flag': '🇷🇺'},
        {'code': 'uk', 'name': 'Українська', 'flag': '🇺🇦'},
        {'code': 'en', 'name': 'English', 'flag': '🇬🇧'},
        {'code': 'de', 'name': 'Deutsch', 'flag': '🇩🇪'}
    ]


def get_current_language(session):
    """
    Получить текущий язык из сессии Flask
    
    Args:
        session: Flask session объект
    
    Returns:
        Код языка ('ru', 'en', 'uk', 'de')
    """
    return session.get('language', 'ru')


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