# webapp/translations.py
# 🌍 Система многоязычности для веб-приложения

"""
Простая система переводов для Flask веб-приложения.

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
        'uk': 'Медичний Асистент'
    },
    'hero_title': {
        'ru': 'Ваш личный медицинский ассистент',
        'en': 'Your Personal Medical Assistant',
        'uk': 'Ваш особистий медичний асистент'
    },
    'hero_subtitle': {
        'ru': 'Загружайте медицинские документы, общайтесь с ИИ-помощником и храните всю вашу медицинскую историю в одном месте',
        'en': 'Upload medical documents, chat with AI assistant and store all your medical history in one place',
        'uk': 'Завантажуйте медичні документи, спілкуйтеся з AI-помічником та зберігайте всю вашу медичну історію в одному місці'
    },
    'btn_get_started': {
        'ru': 'Начать работу',
        'en': 'Get Started',
        'uk': 'Почати роботу'
    },
    'btn_login': {
        'ru': 'Войти',
        'en': 'Login',
        'uk': 'Увійти'
    },
    'btn_login_google': {
        'ru': 'Войти через Google',
        'en': 'Login with Google',
        'uk': 'Увійти через Google'
    },
    'btn_logout': {
        'ru': 'Выход',
        'en': 'Logout',
        'uk': 'Вихід'
    },
    
    # ============================================
    # ✨ СЕКЦИЯ ВОЗМОЖНОСТЕЙ
    # ============================================
    'section_features': {
        'ru': 'Что вы можете делать',
        'en': 'What you can do',
        'uk': 'Що ви можете робити'
    },
    'feature_upload_title': {
        'ru': 'Загрузка документов',
        'en': 'Upload Documents',
        'uk': 'Завантаження документів'
    },
    'feature_upload_text': {
        'ru': 'Загружайте анализы, снимки, заключения врачей в форматах PDF, DOCX, изображения',
        'en': 'Upload tests, images, doctor reports in PDF, DOCX, image formats',
        'uk': 'Завантажуйте аналізи, знімки, висновки лікарів у форматах PDF, DOCX, зображення'
    },
    'feature_ai_title': {
        'ru': 'ИИ-консультант',
        'en': 'AI Consultant',
        'uk': 'AI-консультант'
    },
    'feature_ai_text': {
        'ru': 'Задавайте вопросы о вашем здоровье и получайте ответы на основе ваших документов',
        'en': 'Ask questions about your health and get answers based on your documents',
        'uk': 'Задавайте питання про ваше здоров\'я та отримуйте відповіді на основі ваших документів'
    },
    'feature_history_title': {
        'ru': 'История здоровья',
        'en': 'Health History',
        'uk': 'Історія здоров\'я'
    },
    'feature_history_text': {
        'ru': 'Вся ваша медицинская информация в одном месте, доступна в любое время',
        'en': 'All your medical information in one place, available anytime',
        'uk': 'Вся ваша медична інформація в одному місці, доступна в будь-який час'
    },
    
    # ============================================
    # 🔒 БЕЗОПАСНОСТЬ
    # ============================================
    'security_title': {
        'ru': 'Ваши данные в безопасности',
        'en': 'Your Data is Secure',
        'uk': 'Ваші дані в безпеці'
    },
    'security_text': {
        'ru': 'Мы используем шифрование данных, безопасную авторизацию через Google и храним информацию на защищённых серверах. Ваша медицинская информация доступна только вам.',
        'en': 'We use data encryption, secure Google authentication and store information on protected servers. Your medical information is accessible only to you.',
        'uk': 'Ми використовуємо шифрування даних, безпечну авторизацію через Google та зберігаємо інформацію на захищених серверах. Ваша медична інформація доступна лише вам.'
    },
    'cta_title': {
        'ru': 'Готовы начать заботиться о своём здоровье?',
        'en': 'Ready to start taking care of your health?',
        'uk': 'Готові почати піклуватися про своє здоров\'я?'
    },
    'cta_subtitle': {
        'ru': 'Вход занимает всего несколько секунд',
        'en': 'Login takes only a few seconds',
        'uk': 'Вхід займає лише кілька секунд'
    },
    
    # ============================================
    # 📊 ЛИЧНЫЙ КАБИНЕТ (dashboard.html)
    # ============================================
    'nav_dashboard': {
        'ru': 'Кабинет',
        'en': 'Dashboard',
        'uk': 'Кабінет'
    },
    'nav_chat': {
        'ru': 'Чат',
        'en': 'Chat',
        'uk': 'Чат'
    },
    'nav_documents': {
        'ru': 'Документы',
        'en': 'Documents',
        'uk': 'Документи'
    },
    'nav_profile': {
        'ru': 'Профиль',
        'en': 'Profile',
        'uk': 'Профіль'
    },
    'nav_home': {
        'ru': 'Главная',
        'en': 'Home',
        'uk': 'Головна'
    },
    'dashboard_welcome': {
        'ru': 'Добро пожаловать',
        'en': 'Welcome',
        'uk': 'Ласкаво просимо'
    },
    'dashboard_subtitle': {
        'ru': 'Ваш персональный медицинский кабинет',
        'en': 'Your Personal Medical Dashboard',
        'uk': 'Ваш персональний медичний кабінет'
    },
    'stats_documents_uploaded': {
        'ru': 'Загружено документов',
        'en': 'Documents Uploaded',
        'uk': 'Завантажено документів'
    },
    'stats_documents_left': {
        'ru': 'Осталось',
        'en': 'Remaining',
        'uk': 'Залишилось'
    },
    'stats_messages': {
        'ru': 'Сообщений с ИИ',
        'en': 'AI Messages',
        'uk': 'Повідомлень з AI'
    },
    'stats_queries_left': {
        'ru': 'Осталось запросов',
        'en': 'Queries Remaining',
        'uk': 'Залишилось запитів'
    },
    'stats_plan': {
        'ru': 'Текущий тариф',
        'en': 'Current Plan',
        'uk': 'Поточний тариф'
    },
    'btn_upgrade': {
        'ru': 'Улучшить',
        'en': 'Upgrade',
        'uk': 'Покращити'
    },
    
    # ============================================
    # 🚀 БЫСТРЫЕ ДЕЙСТВИЯ
    # ============================================
    'section_quick_actions': {
        'ru': 'Быстрые действия',
        'en': 'Quick Actions',
        'uk': 'Швидкі дії'
    },
    'action_chat_title': {
        'ru': 'Чат с ИИ-ассистентом',
        'en': 'Chat with AI Assistant',
        'uk': 'Чат з AI-асистентом'
    },
    'action_chat_text': {
        'ru': 'Задайте вопрос о вашем здоровье и получите ответ на основе ваших документов',
        'en': 'Ask a question about your health and get an answer based on your documents',
        'uk': 'Поставте питання про ваше здоров\'я та отримайте відповідь на основі ваших документів'
    },
    'action_upload_title': {
        'ru': 'Загрузить документ',
        'en': 'Upload Document',
        'uk': 'Завантажити документ'
    },
    'action_upload_text': {
        'ru': 'Загрузите анализы, снимки или заключения врачей',
        'en': 'Upload tests, images or doctor reports',
        'uk': 'Завантажте аналізи, знімки або висновки лікарів'
    },
    'action_profile_title': {
        'ru': 'Мой профиль',
        'en': 'My Profile',
        'uk': 'Мій профіль'
    },
    'action_profile_text': {
        'ru': 'Просмотрите и обновите вашу медицинскую анкету',
        'en': 'View and update your medical profile',
        'uk': 'Перегляньте та оновіть вашу медичну анкету'
    },
    
    # ============================================
    # 📄 ДОКУМЕНТЫ
    # ============================================
    'section_recent_documents': {
        'ru': 'Последние документы',
        'en': 'Recent Documents',
        'uk': 'Останні документи'
    },
    'document_uploaded': {
        'ru': 'Загружено',
        'en': 'Uploaded',
        'uk': 'Завантажено'
    },
    'document_uploaded_unknown': {
        'ru': 'Неизвестно',
        'en': 'Unknown',
        'uk': 'Невідомо'
    },
    'btn_view_all_documents': {
        'ru': 'Посмотреть все документы',
        'en': 'View All Documents',
        'uk': 'Переглянути всі документи'
    },
    'no_documents_tip': {
        'ru': 'У вас пока нет загруженных документов.',
        'en': 'You have no uploaded documents yet.',
        'uk': 'У вас поки немає завантажених документів.'
    },
    'no_documents_action': {
        'ru': 'Загрузите первый документ',
        'en': 'Upload your first document',
        'uk': 'Завантажте перший документ'
    },
    
    # ============================================
    # 💬 ЧАТ
    # ============================================
    'section_recent_chat': {
        'ru': 'Последняя беседа с ИИ',
        'en': 'Recent AI Conversation',
        'uk': 'Остання бесіда з AI'
    },
    'btn_continue_chat': {
        'ru': 'Продолжить беседу',
        'en': 'Continue Chat',
        'uk': 'Продовжити бесіду'
    },
    'no_chat_greeting': {
        'ru': 'Привет! Начните беседу с ИИ-ассистентом.',
        'en': 'Hello! Start a conversation with AI assistant.',
        'uk': 'Привіт! Почніть бесіду з AI-асистентом.'
    },
    'no_chat_action': {
        'ru': 'Задать первый вопрос',
        'en': 'Ask First Question',
        'uk': 'Поставити перше питання'
    },
    
    # ============================================
    # 🎨 FOOTER
    # ============================================
    'footer_text': {
        'ru': 'Ваше здоровье - наш приоритет.',
        'en': 'Your health is our priority.',
        'uk': 'Ваше здоров\'я - наш пріоритет.'
    },
    'footer_powered': {
        'ru': 'Работает на',
        'en': 'Powered by',
        'uk': 'Працює на'
    },
    
    # ============================================
    # 🌍 ВЫБОР ЯЗЫКА
    # ============================================
    'language_selector': {
        'ru': 'Язык',
        'en': 'Language',
        'uk': 'Мова'
    },
    'lang_ru': {
        'ru': 'Русский',
        'en': 'Russian',
        'uk': 'Російська'
    },
    'lang_en': {
        'ru': 'Английский',
        'en': 'English',
        'uk': 'Англійська'
    },
    'lang_uk': {
        'ru': 'Украинский',
        'en': 'Ukrainian',
        'uk': 'Українська'
    },
    
    # ============================================
    # ⚠️ УВЕДОМЛЕНИЯ И АЛЕРТЫ
    # ============================================
    'tip': {
        'ru': 'Совет',
        'en': 'Tip',
        'uk': 'Порада'
    },
    'success': {
        'ru': 'Успешно',
        'en': 'Success',
        'uk': 'Успішно'
    },
    'error': {
        'ru': 'Ошибка',
        'en': 'Error',
        'uk': 'Помилка'
    },
    'warning': {
        'ru': 'Внимание',
        'en': 'Warning',
        'uk': 'Увага'
    },
}


def t(key: str, lang: str = 'ru') -> str:
    """
    Получить перевод по ключу
    
    Args:
        key: Ключ перевода (например, 'welcome')
        lang: Язык ('ru', 'en', 'uk')
    
    Returns:
        Переведенная строка или ключ, если перевод не найден
    
    Examples:
        >>> t('welcome', 'ru')
        'Добро пожаловать'
        >>> t('welcome', 'en')
        'Welcome'
    """
    # Проверяем что язык поддерживается
    if lang not in ['ru', 'en', 'uk']:
        lang = 'ru'  # По умолчанию русский
    
    # Получаем перевод
    translation = TRANSLATIONS.get(key, {})
    
    # Возвращаем перевод или ключ если не найден
    return translation.get(lang, key)


def get_supported_languages():
    """Получить список поддерживаемых языков"""
    return [
        {'code': 'ru', 'name': 'Русский', 'flag': '🇷🇺'},
        {'code': 'en', 'name': 'English', 'flag': '🇬🇧'},
        {'code': 'uk', 'name': 'Українська', 'flag': '🇺🇦'}
    ]


def get_current_language(session):
    """
    Получить текущий язык из сессии Flask
    
    Args:
        session: Flask session объект
    
    Returns:
        Код языка ('ru', 'en', 'uk')
    """
    return session.get('language', 'ru')


def set_language(session, lang_code: str):
    """
    Установить язык в сессию Flask
    
    Args:
        session: Flask session объект
        lang_code: Код языка ('ru', 'en', 'uk')
    """
    if lang_code in ['ru', 'en', 'uk']:
        session['language'] = lang_code
        session.modified = True