# webapp/legal_translations.py
# Юридические документы для PulseBook Health
# Языки: English, Deutsch, Українська, Русский | UK GDPR compliant

LEGAL_TRANSLATIONS = {
    'legal_last_updated': {'en': 'Last updated: {date}', 'de': 'Zuletzt aktualisiert: {date}', 'uk': 'Останнє оновлення: {date}', 'ru': 'Последнее обновление: {date}'},
    'legal_back_home': {'en': '← Back to Home', 'de': '← Zurück zur Startseite', 'uk': '← Назад на головну', 'ru': '← Назад на главную'},
    
    'privacy_title': {'en': 'Privacy Policy', 'de': 'Datenschutzerklärung', 'uk': 'Політика конфіденційності', 'ru': 'Политика конфиденциальности'},
    'privacy_intro': {
        'en': '<p>Welcome to <strong>PulseBook Health</strong>. We protect your privacy per UK GDPR and Data Protection Act 2018.</p><p><strong>Data Controller:</strong> PulseBook, UK sole trader.</p>',
        'de': '<p>Willkommen bei <strong>PulseBook Health</strong>. Wir schützen Ihre Daten gemäß UK GDPR und Data Protection Act 2018.</p><p><strong>Datenverantwortlicher:</strong> PulseBook, UK Einzelunternehmer.</p>',
        'uk': '<p>Ласкаво просимо до <strong>PulseBook Health</strong>. Ми захищаємо вашу конфіденційність згідно UK GDPR та Закону про захист даних 2018.</p><p><strong>Контролер:</strong> PulseBook, UK приватний підприємець.</p>',
        'ru': '<p>Добро пожаловать в <strong>PulseBook Health</strong>. Мы защищаем конфиденциальность согласно UK GDPR и Закону о защите данных 2018.</p><p><strong>Контролер:</strong> PulseBook, UK частный предприниматель.</p>'
    },
    
    'privacy_h1': {'en': '1. Information We Collect', 'de': '1. Gesammelte Daten', 'uk': '1. Зібрані дані', 'ru': '1. Собираемые данные'},
    'privacy_collected': {
        'en': '<h3>Account Info</h3><p>Google OAuth: email, name, photo. Telegram: ID, username.</p><h3>Health Data</h3><p>Medical history, AI chats, uploaded documents, health goals.</p><h3>Payments</h3><p>Via Stripe (we don\'t store card details).</p><h3>Technical</h3><p>Device info, IP, usage logs.</p>',
        'de': '<h3>Kontodaten</h3><p>Google OAuth: E-Mail, Name, Foto. Telegram: ID, Benutzername.</p><h3>Gesundheitsdaten</h3><p>Krankengeschichte, KI-Chats, Dokumente, Gesundheitsziele.</p><h3>Zahlungen</h3><p>Via Stripe (keine Kartendaten gespeichert).</p><h3>Technisch</h3><p>Gerät, IP, Nutzung.</p>',
        'uk': '<h3>Дані акаунта</h3><p>Google OAuth: email, ім\'я, фото. Telegram: ID, username.</p><h3>Медичні дані</h3><p>Історія, AI-чати, документи, цілі.</p><h3>Платежі</h3><p>Через Stripe (не зберігаємо картки).</p><h3>Технічне</h3><p>Пристрій, IP, логи.</p>',
        'ru': '<h3>Данные аккаунта</h3><p>Google OAuth: email, имя, фото. Telegram: ID, username.</p><h3>Медицинские</h3><p>История, AI-чаты, документы, цели.</p><h3>Платежи</h3><p>Через Stripe (карты не храним).</p><h3>Техническое</h3><p>Устройство, IP, логи.</p>'
    },
    
    'privacy_h2': {'en': '2. How We Use Data', 'de': '2. Datennutzung', 'uk': '2. Використання', 'ru': '2. Использование'},
    'privacy_usage': {
        'en': '<ul><li>Provide AI health services</li><li>Manage accounts</li><li>Process payments (Stripe)</li><li>Improve service</li><li>Send updates</li><li>Legal compliance</li></ul>',
        'de': '<ul><li>KI-Gesundheitsdienste</li><li>Kontoverwaltung</li><li>Zahlungen (Stripe)</li><li>Service verbessern</li><li>Updates senden</li><li>Rechtliche Konformität</li></ul>',
        'uk': '<ul><li>AI здоров\'я сервіси</li><li>Управління</li><li>Платежі (Stripe)</li><li>Покращення</li><li>Оновлення</li><li>Юридичне</li></ul>',
        'ru': '<ul><li>AI здоровье сервисы</li><li>Управление</li><li>Платежи (Stripe)</li><li>Улучшение</li><li>Обновления</li><li>Юридическое</li></ul>'
    },
    
    'privacy_h3': {'en': '3. Third-Party Services', 'de': '3. Drittanbieter', 'uk': '3. Сторонні сервіси', 'ru': '3. Сторонние'},
    'privacy_thirdparty': {
        'en': '<p><strong>OpenAI:</strong> AI analysis (no training on your data)<br><strong>Google Gemini:</strong> Enhanced analysis<br><strong>Stripe:</strong> Payments<br><strong>Supabase:</strong> Encrypted database (GDPR, SOC2)<br><strong>Railway:</strong> Secure hosting<br><strong>Google OAuth:</strong> Authentication</p>',
        'de': '<p><strong>OpenAI:</strong> KI-Analyse (keine Trainingsdaten)<br><strong>Google Gemini:</strong> Erweiterte Analyse<br><strong>Stripe:</strong> Zahlungen<br><strong>Supabase:</strong> Verschlüsselte DB (DSGVO, SOC2)<br><strong>Railway:</strong> Hosting<br><strong>Google OAuth:</strong> Authentifizierung</p>',
        'uk': '<p><strong>OpenAI:</strong> AI аналіз (не навчається)<br><strong>Google Gemini:</strong> Розширений<br><strong>Stripe:</strong> Платежі<br><strong>Supabase:</strong> Шифрована БД (GDPR, SOC2)<br><strong>Railway:</strong> Хостинг<br><strong>Google OAuth:</strong> Автентифікація</p>',
        'ru': '<p><strong>OpenAI:</strong> AI анализ (не обучается)<br><strong>Google Gemini:</strong> Расширенный<br><strong>Stripe:</strong> Платежи<br><strong>Supabase:</strong> Шифрованная БД (GDPR, SOC2)<br><strong>Railway:</strong> Хостинг<br><strong>Google OAuth:</strong> Аутентификация</p>'
    },
    
    'privacy_h4': {'en': '4. Security', 'de': '4. Sicherheit', 'uk': '4. Безпека', 'ru': '4. Безопасность'},
    'privacy_security': {
        'en': '<ul><li>SSL/TLS encryption</li><li>Strict access controls</li><li>Regular backups</li><li>24/7 monitoring</li></ul><p class="text-warning">No method is 100% secure.</p>',
        'de': '<ul><li>SSL/TLS Verschlüsselung</li><li>Strikte Zugangskontrollen</li><li>Regelmäßige Backups</li><li>24/7 Überwachung</li></ul><p class="text-warning">Keine Methode ist 100% sicher.</p>',
        'uk': '<ul><li>SSL/TLS шифрування</li><li>Суворий контроль</li><li>Регулярні бекапи</li><li>24/7 моніторинг</li></ul><p class="text-warning">Немає 100% безпеки.</p>',
        'ru': '<ul><li>SSL/TLS шифрование</li><li>Строгий контроль</li><li>Регулярные бэкапы</li><li>24/7 мониторинг</li></ul><p class="text-warning">Нет 100% безопасности.</p>'
    },
    
    'privacy_h5': {'en': '5. Your Rights (UK GDPR)', 'de': '5. Ihre Rechte', 'uk': '5. Ваші права', 'ru': '5. Ваши права'},
    'privacy_rights': {
        'en': '<ul><li><strong>Access:</strong> Get your data copy</li><li><strong>Rectification:</strong> Fix errors</li><li><strong>Erasure:</strong> Delete data</li><li><strong>Portability:</strong> Export data</li><li><strong>Object:</strong> Stop processing</li><li><strong>Restrict:</strong> Limit use</li></ul><p>Contact: <a href="mailto:support@pulsebook.health">support@pulsebook.health</a> (30-day response)</p><p>Complain to ICO: <a href="https://ico.org.uk" target="_blank">ico.org.uk</a></p>',
        'de': '<ul><li><strong>Zugang:</strong> Datenkopie erhalten</li><li><strong>Berichtigung:</strong> Fehler korrigieren</li><li><strong>Löschung:</strong> Daten löschen</li><li><strong>Übertragbarkeit:</strong> Daten exportieren</li><li><strong>Widerspruch:</strong> Verarbeitung stoppen</li><li><strong>Einschränkung:</strong> Nutzung begrenzen</li></ul><p>Kontakt: <a href="mailto:support@pulsebook.health">support@pulsebook.health</a> (30 Tage)</p><p>Beschwerde bei ICO: <a href="https://ico.org.uk" target="_blank">ico.org.uk</a></p>',
        'uk': '<ul><li><strong>Доступ:</strong> Копія даних</li><li><strong>Виправлення:</strong> Виправити помилки</li><li><strong>Видалення:</strong> Видалити дані</li><li><strong>Переносність:</strong> Експорт</li><li><strong>Заперечення:</strong> Зупинити</li><li><strong>Обмеження:</strong> Лімітувати</li></ul><p>Контакт: <a href="mailto:support@pulsebook.health">support@pulsebook.health</a> (30 днів)</p><p>Скарга до ICO: <a href="https://ico.org.uk" target="_blank">ico.org.uk</a></p>',
        'ru': '<ul><li><strong>Доступ:</strong> Копия данных</li><li><strong>Исправление:</strong> Исправить ошибки</li><li><strong>Удаление:</strong> Удалить данные</li><li><strong>Переносимость:</strong> Экспорт</li><li><strong>Возражение:</strong> Остановить</li><li><strong>Ограничение:</strong> Лимитировать</li></ul><p>Контакт: <a href="mailto:support@pulsebook.health">support@pulsebook.health</a> (30 дней)</p><p>Жалоба в ICO: <a href="https://ico.org.uk" target="_blank">ico.org.uk</a></p>'
    },
    
    'privacy_h6': {'en': '6. Medical Disclaimer', 'de': '6. Medizinischer Haftungsausschluss', 'uk': '6. Медичний дисклеймер', 'ru': '6. Медицинский дисклеймер'},
    'privacy_medical_disclaimer': {
        'en': '<div class="alert alert-danger"><h4>⚠️ IMPORTANT</h4><p><strong>NOT a medical device</strong> (not MHRA regulated)</p><ul><li>NOT professional medical advice</li><li>Always consult doctors</li><li>Never delay care</li><li>Emergency: 999 (UK) / 112 (EU)</li></ul></div>',
        'de': '<div class="alert alert-danger"><h4>⚠️ WICHTIG</h4><p><strong>KEIN Medizinprodukt</strong> (nicht MHRA reguliert)</p><ul><li>KEINE ärztliche Beratung</li><li>Immer Ärzte konsultieren</li><li>Nie Versorgung verzögern</li><li>Notfall: 112</li></ul></div>',
        'uk': '<div class="alert alert-danger"><h4>⚠️ ВАЖЛИВО</h4><p><strong>НЕ медичний пристрій</strong> (не MHRA)</p><ul><li>НЕ медична консультація</li><li>Завжди консультуйте лікарів</li><li>Не відкладайте допомогу</li><li>Екстрено: 103</li></ul></div>',
        'ru': '<div class="alert alert-danger"><h4>⚠️ ВАЖНО</h4><p><strong>НЕ медицинское устройство</strong> (не MHRA)</p><ul><li>НЕ медицинская консультация</li><li>Всегда консультируйте врачей</li><li>Не откладывайте помощь</li><li>Экстренно: 103</li></ul></div>'
    },
    
    'privacy_contact': {
        'en': '<p><strong>Email:</strong> <a href="mailto:support@pulsebook.health">support@pulsebook.health</a><br><strong>Controller:</strong> PulseBook, UK<br>Response: 30 days</p>',
        'de': '<p><strong>E-Mail:</strong> <a href="mailto:support@pulsebook.health">support@pulsebook.health</a><br><strong>Verantwortlicher:</strong> PulseBook, UK<br>Antwort: 30 Tage</p>',
        'uk': '<p><strong>Email:</strong> <a href="mailto:support@pulsebook.health">support@pulsebook.health</a><br><strong>Контролер:</strong> PulseBook, UK<br>Відповідь: 30 днів</p>',
        'ru': '<p><strong>Email:</strong> <a href="mailto:support@pulsebook.health">support@pulsebook.health</a><br><strong>Контролер:</strong> PulseBook, UK<br>Ответ: 30 дней</p>'
    },
    
    'terms_title': {'en': 'Terms of Service', 'de': 'Nutzungsbedingungen', 'uk': 'Умови використання', 'ru': 'Условия использования'},
    'terms_intro': {
        'en': '<p>By using PulseBook, you agree to these Terms. Must be 18+. UK-operated service.</p>',
        'de': '<p>Durch Nutzung von PulseBook stimmen Sie zu. 18+ erforderlich. UK-Service.</p>',
        'uk': '<p>Використовуючи PulseBook, ви погоджуєтесь. Потрібно 18+. UK-сервіс.</p>',
        'ru': '<p>Используя PulseBook, вы соглашаетесь. Требуется 18+. UK-сервис.</p>'
    },
    
    'terms_medical_disclaimer': {
        'en': '<div class="alert alert-danger"><h4>⚠️ CRITICAL</h4><p><strong>NOT MEDICAL DEVICE</strong> (not MHRA regulated)<br><strong>NOT MEDICAL ADVICE</strong></p><ul><li>Consult healthcare providers</li><li>Never delay care</li><li>Emergency: 999/112</li><li>No doctor-patient relationship</li><li>AI may err</li></ul><p><strong>YOU ACCEPT THESE LIMITS</strong></p></div>',
        'de': '<div class="alert alert-danger"><h4>⚠️ KRITISCH</h4><p><strong>KEIN MEDIZINPRODUKT</strong> (nicht MHRA)<br><strong>KEINE MEDIZINISCHE BERATUNG</strong></p><ul><li>Gesundheitsdienstleister konsultieren</li><li>Nie Versorgung verzögern</li><li>Notfall: 112</li><li>Keine Arzt-Patienten-Beziehung</li><li>KI kann irren</li></ul><p><strong>SIE AKZEPTIEREN DIES</strong></p></div>',
        'uk': '<div class="alert alert-danger"><h4>⚠️ КРИТИЧНО</h4><p><strong>НЕ МЕДПРИСТРІЙ</strong> (не MHRA)<br><strong>НЕ МЕДКОНСУЛЬТАЦІЯ</strong></p><ul><li>Консультуйте лікарів</li><li>Не відкладайте</li><li>Екстрено: 103</li><li>Немає відносин лікар-пацієнт</li><li>AI може помилятись</li></ul><p><strong>ВИ ПРИЙМАЄТЕ ЦЕ</strong></p></div>',
        'ru': '<div class="alert alert-danger"><h4>⚠️ КРИТИЧНО</h4><p><strong>НЕ МЕДУСТРОЙСТВО</strong> (не MHRA)<br><strong>НЕ МЕДКОНСУЛЬТАЦИЯ</strong></p><ul><li>Консультируйте врачей</li><li>Не откладывайте</li><li>Экстренно: 103</li><li>Нет отношений врач-пациент</li><li>AI может ошибаться</li></ul><p><strong>ВЫ ПРИНИМАЕТЕ ЭТО</strong></p></div>'
    },
    
    'terms_law': {
        'en': '<p>Governed by <strong>England & Wales</strong> law. Disputes in English/Welsh courts.</p>',
        'de': '<p>Geregelt durch <strong>England & Wales</strong> Recht. Streitigkeiten in englischen/walisischen Gerichten.</p>',
        'uk': '<p>Регулюється законами <strong>Англії та Уельсу</strong>. Спори в англійських/валлійських судах.</p>',
        'ru': '<p>Регулируется законами <strong>Англии и Уэльса</strong>. Споры в английских/валлийских судах.</p>'
    },
}

def tl(key, lang='en', **kwargs):
    """Get legal translation"""
    if lang not in ['ru','en','uk','de']: lang='en'
    text = LEGAL_TRANSLATIONS.get(key,{}).get(lang,key)
    if kwargs:
        try: text=text.format(**kwargs)
        except: pass
    return text