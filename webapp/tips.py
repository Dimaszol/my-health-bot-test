# webapp/tips.py
# Советы дня для dashboard

TIPS = {
    'ru': [
        "Загрузите все ваши медицинские документы, чтобы AI мог давать более точные рекомендации на основе полной картины вашего здоровья.",
        "Регулярно обновляйте список принимаемых лекарств в разделе 'Мои лекарства' для более точных консультаций.",
        "Заполните медицинскую анкету полностью — это поможет AI учитывать ваши хронические заболевания и аллергии.",
        "Используйте заметки в память для важных симптомов и реакций на лечение — AI будет учитывать их в будущих консультациях.",
        "Подключите Telegram бот для удобного доступа к консультациям прямо из мессенджера.",
    ],
    'en': [
        "Upload all your medical documents so AI can provide more accurate recommendations based on your complete health picture.",
        "Regularly update your medication list in 'My Medications' for more accurate consultations.",
        "Complete your medical profile fully — it helps AI consider your chronic conditions and allergies.",
        "Use memory notes for important symptoms and treatment reactions — AI will consider them in future consultations.",
        "Connect Telegram bot for convenient access to consultations directly from messenger.",
    ],
    'uk': [
        "Завантажте всі ваші медичні документи, щоб AI міг давати більш точні рекомендації на основі повної картини вашого здоров'я.",
        "Регулярно оновлюйте список ліків у розділі 'Мої ліки' для більш точних консультацій.",
        "Заповніть медичну анкету повністю — це допоможе AI враховувати ваші хронічні захворювання та алергії.",
        "Використовуйте нотатки в пам'ять для важливих симптомів та реакцій на лікування — AI враховуватиме їх у майбутніх консультаціях.",
        "Підключіть Telegram бот для зручного доступу до консультацій прямо з месенджера.",
    ],
    'de': [
        "Laden Sie alle Ihre medizinischen Dokumente hoch, damit die KI genauere Empfehlungen basierend auf Ihrem vollständigen Gesundheitsbild geben kann.",
        "Aktualisieren Sie regelmäßig Ihre Medikamentenliste in 'Meine Medikamente' für genauere Konsultationen.",
        "Füllen Sie Ihr medizinisches Profil vollständig aus — es hilft der KI, Ihre chronischen Erkrankungen und Allergien zu berücksichtigen.",
        "Verwenden Sie Gedächtnisnotizen für wichtige Symptome und Behandlungsreaktionen — die KI wird sie in zukünftigen Konsultationen berücksichtigen.",
        "Verbinden Sie Telegram-Bot für bequemen Zugriff auf Konsultationen direkt aus dem Messenger.",
    ]
}

def get_random_tip(lang='ru'):
    """Возвращает случайный совет на указанном языке"""
    import random
    tips = TIPS.get(lang, TIPS['ru'])
    return random.choice(tips)