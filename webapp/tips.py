# webapp/tips.py
# Советы дня для dashboard

TIPS = {
    'ru': [
        "Загрузите все ваши медицинские документы — AI анализирует полную картину вашего здоровья и даёт более точные рекомендации.",
        "Выбирайте, учитывать ли документ при ответе AI — используйте тумблер «Учитывать в чате» в медкарте.",
        "Краткие выдержки под документами помогают быстро понять содержание анализа без открытия файла.",
        "Загружайте даже старые документы — AI учитывает всю вашу историю, а не только свежие данные.",
        "Заполните медицинский профиль полностью — хронические заболевания, операции и аллергии влияют на рекомендации AI.",
        "Обновляйте профиль, если меняются лекарства или состояние — AI использует эти данные при каждом ответе.",
        "При вопросах о симптомах указывайте длительность, интенсивность и факторы, которые усиливают или уменьшают проявления.",
        "Если спрашиваете про анализы, прикрепляйте оригинальный документ — AI точнее интерпретирует данные по файлу.",
        "При вопросах о лечении указывайте лекарства, которые вы уже принимаете — это важно для корректных рекомендаций.",
        "В Telegram можно быстро загружать документы прямо с телефона — удобно, когда вы в пути или не у компьютера.",
        "Аккаунт PulseBook работает и на сайте, и в Telegram — доступ к медданным есть с любого устройства.",
        "В Telegram доступна функция «Заметка в память» — добавляйте симптомы и наблюдения, AI будет учитывать их в дальнейших ответах.",
        "В Telegram можно вести список лекарств и включать напоминания о приёме — удобно для ежедневного контроля.",
    ],

    'en': [
        "Upload all your medical documents — AI sees the full picture and provides more accurate recommendations.",
        "Choose whether a document should be considered in chat responses — use the 'Include in chat' toggle in your medical record.",
        "Brief summaries under each document help you quickly understand its content without opening the file.",
        "Upload even older documents — AI takes your entire history into account, not only recent tests.",
        "Complete your medical profile — chronic conditions, surgeries and allergies influence AI recommendations.",
        "Update your profile if your medications or condition change — AI uses this data in every response.",
        "When asking about symptoms, specify duration, intensity and what worsens or eases them.",
        "When asking about test results, attach the original document — AI interprets files more accurately than text descriptions.",
        "When asking about treatment, mention all medications you are currently taking.",
        "In Telegram you can quickly upload documents directly from your phone — convenient when you're not at a computer.",
        "Your PulseBook account works both on the website and in Telegram — access your data from any device.",
        "Telegram offers 'Memory Notes' — add symptoms or observations, and AI will take them into account in future responses.",
        "In Telegram you can manage your medication list and enable reminders — useful for daily health control.",
    ],

    'uk': [
        "Завантажте всі ваші медичні документи — AI бачить повну картину здоров'я і дає точніші рекомендації.",
        "Вибирайте, чи враховувати документ у відповіді AI — використовуйте перемикач «Враховувати в чаті» у медкарті.",
        "Короткі витяги під документами допомагають швидко зрозуміти зміст без відкриття файлу.",
        "Завантажуйте навіть старі аналізи — AI враховує всю історію, а не лише нові дані.",
        "Заповніть медичний профіль повністю — хронічні хвороби, операції та алергії впливають на рекомендації AI.",
        "Оновлюйте профіль, якщо змінюються ліки або стан здоров’я — AI використовує ці дані у кожній відповіді.",
        "При питаннях про симптоми вказуйте тривалість, інтенсивність та фактори, що посилюють або послаблюють прояви.",
        "Якщо питаєте про аналізи, прикріплюйте оригінальний документ — AI точніше інтерпретує дані з файлу.",
        "При питаннях про лікування зазначайте ліки, які ви вже приймаєте.",
        "У Telegram можна швидко завантажувати документи прямо з телефону — зручно, коли ви не за комп’ютером.",
        "Ваш обліковий запис PulseBook працює і на сайті, і в Telegram — доступ до даних з будь-якого пристрою.",
        "У Telegram доступна функція «Нотатка в пам’ять» — додавайте симптоми та спостереження, AI враховуватиме їх у майбутніх відповідях.",
        "У Telegram можна вести список ліків та включати нагадування — корисно для щоденного контролю.",
    ],

    'de': [
        "Laden Sie alle Ihre medizinischen Dokumente hoch — die KI sieht das Gesamtbild und gibt präzisere Empfehlungen.",
        "Wählen Sie, ob ein Dokument in Chat-Antworten berücksichtigt werden soll — nutzen Sie den Schalter „Im Chat berücksichtigen“.",
        "Kurze Zusammenfassungen unter jedem Dokument helfen, den Inhalt schnell zu verstehen, ohne die Datei zu öffnen.",
        "Laden Sie auch ältere Dokumente hoch — die KI berücksichtigt Ihre gesamte Vorgeschichte.",
        "Füllen Sie Ihr medizinisches Profil vollständig aus — chronische Erkrankungen, Operationen und Allergien beeinflussen die KI-Empfehlungen.",
        "Aktualisieren Sie Ihr Profil, wenn sich Medikamente oder Ihr Gesundheitszustand ändern — die KI nutzt diese Angaben in jeder Antwort.",
        "Beschreiben Sie bei Symptomen Dauer, Intensität und auslösende Faktoren.",
        "Bei Fragen zu Laborwerten fügen Sie das Originaldokument bei — die KI interpretiert Dateien präziser als Textbeschreibungen.",
        "Bei Fragen zur Behandlung geben Sie Ihre aktuellen Medikamente an.",
        "Über Telegram können Sie Dokumente schnell direkt vom Handy hochladen — praktisch unterwegs.",
        "Ihr PulseBook-Konto funktioniert sowohl auf der Website als auch in Telegram — Zugriff von jedem Gerät.",
        "In Telegram gibt es „Gedächtnisnotizen“ — fügen Sie Symptome und Beobachtungen hinzu, die KI berücksichtigt sie in späteren Antworten.",
        "In Telegram können Sie Ihre Medikamentenliste verwalten und Erinnerungen aktivieren — hilfreich für den Alltag.",
    ]
}


def get_random_tip(lang='ru'):
    """Возвращает случайный совет на указанном языке"""
    import random
    tips = TIPS.get(lang, TIPS['ru'])
    return random.choice(tips)