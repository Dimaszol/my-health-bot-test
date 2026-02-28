# faq_texts.py - Тексты для FAQ раздела

FAQ_TEXTS = {
    "ru": {
        # Главное меню FAQ
        "faq_main_title": "❓ FAQ - Помощь по боту\n\nВыберите интересующий раздел:",
        
        # Кнопки главного меню
        "faq_getting_started": "🚀 Начало работы",
        "faq_subscriptions": "💎 Подписки и лимиты",
        "faq_documents": "📄 Загрузка документов",
        "faq_notes": "📝 Заметки и память",
        "faq_medications": "💊 График лекарств",
        "faq_security": "🔒 Безопасность данных",
        "faq_profile": "⚙️ Меню Настройки",
        "faq_support": "📞 Поддержка",
        
        # Содержимое разделов
        "faq_getting_started_content": """          <b>Как получить максимум от бота?</b>

    📄 <b>Загружайте документы и снимки</b> — каждый файл анализируется и становится частью вашей медицинской истории. Чем больше данных загрузите, тем точнее будут мои рекомендации и ответы!

    👤 <b>Заполните подробную анкету</b> — вы получите персонализированные советы именно для вашей ситуации.

    📝 <b>Добавляйте заметки в память</b> — записывайте симптомы, наблюдения, результаты визитов к врачам, всю эту информацию. Я помогаю отслеживать динамику здоровья, находить связи между разными событиями.

    💊 <b>Ведите график лекарств</b> — добавляйте принимаемые препараты с временем приема. Я буду учитывать их при ответах, а вы сможете всегда посмотреть свой график.

                <b>Что это дает?</b>
    - Получаете ответы с учетом ИМЕННО вашей ситуации
    - Видите полную картину своего здоровья в одном месте  
    - Можете подготовиться к визиту к врачу с готовыми вопросами
    - Отслеживаете изменения в анализах и самочувствии

⚠️ <b>Помните:</b> Я — ваш медицинский помощник, а не замена врача!""",

        "faq_subscriptions_content": """            <b>Выберите подходящий план:</b>

🆓 <b>Бесплатный план</b>
    - 1 загрузка документов/снимков (разово)
    - 3 детальных консультаций (разово)
    - 25 базовых ответов (разово)

📦 <b>Базовый план ($3.99/месяц)</b>  
    - 5 загрузок документов/снимков
    - 50 детальных консультаций
    - 100 вопросов в день

⭐ <b>Премиум план ($9.99/месяц)</b>
    - 20 загрузок документов/снимков  
    - 200 детальных консультаций
    - 100 вопросов в день

💊 <b>Экстра пакет ($1.99)</b>
    - 2 загрузки документов/снимков
    - 20 детальных консультаций
    - Разовая покупка на 30 дней

            <b>В чем разница ответов?</b>
💬 <b>Базовые ответы</b> — модель, которая дает более короткие ответы

🩺 <b>Детальные консультации</b> — использую продвинутую модель, которая:
    - Лучше анализирует связи в вашей медицинской истории
    - Дает более глубокие и развернутые ответы
    - <b>Позволяет задавать вопросы с фотографиями</b> (сыпь, травмы, препараты, симптомы)
    - Учитывает больше контекста из ваших документов

            <b>Как работает оплата?</b>
    - 🔄 Подписка автоматически продлевается каждый месяц
    - ⏸️ Можете отменить в любой момент в настройках
    - 📉 Если автопродление не прошло (заблокирована карта) — переходите на бесплатный план, но все данные остаются!""",

        "faq_documents_content": """        <b>Что можно загружать через "📄 Загрузить документ"?</b>

🔬 <b>Любые медицинские документы (PDF):</b>
    - Результаты анализов крови, мочи, биохимии
    - Выписки из больниц и поликлиник  
    - Заключения специалистов (кардиолог, эндокринолог и др.)
    - Назначения и рецепты врачей
    - Медицинские справки и заключения
    - Протоколы операций и процедур
    - История болезни

📸 <b>Профессиональные медицинские снимки (JPG, PNG):</b>
    - Рентгеновские снимки всех органов
    - УЗИ исследования  
    - МРТ и КТ снимки
    - ЭКГ кардиограммы
    - Результаты эндоскопии
    - Снимки из медицинских аппаратов

        <b>Как происходит анализ?</b>
🤖 Бот автоматически определяет тип документа и анализирует как профессионал:
    - <b>Анализы</b> → извлекает все показатели и сравнивает с нормами
    - <b>Снимки</b> → анализирует как врач визуализации (напр. радиолог, кардиолог, маммолог... в зависимости от типа снимка)  
    - <b>Выписки</b> → выделяет диагнозы, назначения и рекомендации

        <b>Технические моменты:</b>
    - Максимум 5 МБ на файл
    - PDF анализируется первые 5 страниц (для оптимальной работы)
   
    💡 <b>Чем больше медицинских документов загрузите, тем точнее я буду понимать вашу ситуацию и давать персональные рекомендации!</b>

            ⚠️ <b>Для вопросов с фото</b>
Просто отправьте в чат фото и задайте вопрос:
    - Дерматологические проблемы (сыпь, родинки)
    - Фото препаратов для идентификации  
    - Травмы и внешние симптомы
    - Любые фото для медицинского анализа
⚠️ВНИМАНИЕ: вопрос по фото это не детальный анализ снимка с сохранением в мою память, если у вас есть медицинский снимок - воспользуйтесь кнопкой "Загрузить документ" для детального анализа.""",

        "faq_notes_content": """         <b>Как работает система памяти?</b>

🧠 <b>Что происходит с вашими заметками:</b>
    - Каждая заметка анализируется и заносится в память
    - При ваших вопросах я ищу нужные заметки в зависимости от вашего вопроса и учитываю их в ответе
    - Чем подробнее заметки, тем точнее мои рекомендации

📝 <b>Что стоит записывать:</b>
    - Результаты визитов к врачам
    - Реакции на лекарства и процедуры
    - Особенности образа жизни
    - Любые данные, которые нужно запомнить (напр. вы можете внести свой номер страхования, и потом спросить в чате и я его напомню)
            
📊 <b>Лимиты на заметки:</b>
    🆓 Бесплатно: 5 заметок в неделю
    💎 Подписчики: 10 заметок в день

💡 <b>Совет:</b> Одна подробная заметка лучше нескольких коротких!
Обязательно следите за актуальностью данных в памяти, через пункт  "Мои документы" """,

        "faq_medications_content": """      <b>Как добавлять лекарства?</b>

🤖 <b>Умное добавление:</b>
    • "Добавь метформин за завтраком" → бот автоматически добавит время
    • "Удали аспирин" → убирает препарат
    • "Удали все" → очищает весь график
    • "Добавь омепразол в 19:30" → точное время


📋 <b>Что учитывается:</b>
    - При ответах я всегда помню ваши текущие лекарства
    - Учитываю при анализе симптомов

❗ <b>Важно:</b> График носит справочный характер. Дозировки и изменения — только с врачом!""",

        "faq_security_content": """     <b>Как защищены ваши данные?</b>

🛡️ <b>Техническая защита:</b>
    - Все данные шифруются при передаче и хранении
    - Серверы соответствуют медицинским стандартам безопасности
    - Доступ только у вас — даже разработчики не видят содержимое
    - Данные обрабатываются анонимно, без привязки к личности
            
📋 <b>Политика хранения:</b>
    - Медицинские документы — до удаления вами
    - История чата — для улучшения ответов
    - Можете удалить ВСЕ данные через настройки
    - Все хранится в зашифрованом виде и доступно только вам

🇪🇺 <b>GDPR:</b>
    - Полное соблюдение европейских стандартов
    - Право на доступ, исправление и удаление данных
    - <a href="https://bit.ly/pulsebook-privacy">Политика конфиденциальности</a>

⚠️ <b>Помните:</b> PulseBook — это помощник, не замена врача!""",

        "faq_profile_content": """        <b>👤 Профиль</b>
Здесь вы можете редактировать свои данные:
    - Анкету
    - Язык интерфейса

💡 <b>Чем подробнее профиль, тем персональнее мои ответы!</b>

            <b>💎 Подписка</b>
Управление тарифными планами:
    - Просмотр текущих лимитов
    - Оформление подписки (Базовый/Премиум)
    - Покупка дополнительных пакетов
    - Отмена подписки

            <b>🗑️ Удаление данных</b>
⚠️ <b>ВНИМАНИЕ:</b> Полное удаление профиля:
    - Удаляются ВСЕ медицинские данные (необратимо)
    - Автоматически отменяются все подписки
    - История переписки стирается навсегда
    - Восстановление невозможно

            ✏️ <b>Как попасть в настройки:</b>
Нажмите ⚙️ Настройки в главном меню""",

        "faq_support_content": """          <b>Если возникли проблемы:</b>

🔧 <b>Технические вопросы:</b>
    - Проблемы с загрузкой документов
    - Ошибки в работе бота
    - Вопросы по подпискам и платежам

💬 <b>Медицинские вопросы:</b>
    - Помощь в интерпретации ответов
    - Рекомендации по использованию
    - Предложения по улучшению

📧 <b>Контакты:</b>
    - Напишите /support
    ⏰ Ответ в течении 72 часов 

🚨 <b>В экстренных случаях:</b>
    Обращайтесь к врачу или в скорую помощь! 
    PulseBook не заменяет врача или экстренной медицинской помощи.

💡 <b>Предложения:</b>
    Мы всегда рады услышать ваши идеи по улучшению бота!""",
    },

    "uk": {
        # Главное меню FAQ
        "faq_main_title": "❓ FAQ - Допомога з ботом\n\nОберіть цікавий розділ:",
        
        # Кнопки главного меню
        "faq_getting_started": "🚀 Початок роботи",
        "faq_subscriptions": "💎 Підписки та ліміти",
        "faq_documents": "📄 Завантаження документів",
        "faq_notes": "📝 Нотатки та пам'ять",
        "faq_medications": "💊 Графік ліків",
        "faq_security": "🔒 Безпека даних",
        "faq_profile": "⚙️ Меню Налаштування",
        "faq_support": "📞 Підтримка",
        
        # Содержимое разделов
        "faq_getting_started_content": """          <b>Як отримати максимум від бота?</b>

    📄 <b>Завантажуйте документи та знімки</b> — кожен файл аналізується та стає частиною вашої медичної історії. Чим більше даних завантажите, тим точніші будуть мої рекомендації та відповіді!

    👤 <b>Заповніть детальну анкету</b> — ви отримаєте персоналізовані поради саме для вашої ситуації.

    📝 <b>Додавайте нотатки в пам'ять</b> — записуйте симптоми, спостереження, результати візитів до лікарів, всю цю інформацію. Я допомагаю відстежувати динаміку здоров'я, знаходити зв'язки між різними подіями.

    💊 <b>Ведіть графік ліків</b> — додавайте препарати, що приймаєте, з часом прийому. Я буду враховувати їх при відповідях, а ви зможете завжди подивитися свій графік.

                <b>Що це дає?</b>
    - Отримуєте відповіді з урахуванням САМЕ вашої ситуації
    - Бачите повну картину свого здоров'я в одному місці  
    - Можете підготуватися до візиту до лікаря з готовими питаннями
    - Відстежуєте зміни в аналізах та самопочутті

⚠️ <b>Пам'ятайте:</b> Я — ваш медичний помічник, а не заміна лікаря!""",

        "faq_subscriptions_content": """            <b>Оберіть підходящий план:</b>

🆓 <b>Безкоштовний план</b>
    - 1 завантаження документів/знімків (одноразово)
    - 3 детальні консультації (одноразово)
    - 25 базових відповідей (одноразово)

📦 <b>Базовий план ($3.99/місяць)</b>
    - 5 завантажень документів/знімків
    - 50 детальних консультацій
    - 100 запитань на день

⭐ <b>Преміум план ($9.99/місяць)</b>
    - 20 завантажень документів/знімків
    - 200 детальних консультацій
    - 100 запитань на день

💊 <b>Екстра пакет ($1.99)</b>
    - 2 завантаження документів/знімків
    - 20 детальних консультацій
    - Одноразова покупка на 30 днів

            <b>У чому різниця відповідей?</b>
💬 <b>Базові відповіді</b> — модель, яка дає більш короткі відповіді

🩺 <b>Детальні консультації</b> — використовую продвинуту модель, яка:
    - Краще аналізує зв'язки у вашій медичній історії
    - Дає більш глибокі та розгорнуті відповіді
    - <b>Дозволяє ставити питання з фотографіями</b> (висип, травми, препарати, симптоми)
    - Враховує більше контексту з ваших документів

            <b>Як працює оплата?</b>
    - 🔄 Підписка автоматично продовжується щомісяця
    - ⏸️ Можете скасувати будь-коли в налаштуваннях
    - 📉 Якщо автопродовження не пройшло (заблокована картка) — переходите на безкоштовний план, але всі дані залишаються!""",

        "faq_documents_content": """        <b>Що можна завантажувати через "📄 Завантажити документ"?</b>

🔬 <b>Будь-які медичні документи (PDF):</b>
    - Результати аналізів крові, сечі, біохімії
    - Виписки з лікарень та поліклінік  
    - Висновки спеціалістів (кардіолог, ендокринолог та ін.)
    - Призначення та рецепти лікарів
    - Медичні довідки та висновки
    - Протоколи операцій та процедур
    - Історія хвороби

📸 <b>Професійні медичні знімки (JPG, PNG):</b>
    - Рентгенівські знімки всіх органів
    - УЗД дослідження  
    - МРТ та КТ знімки
    - ЕКГ кардіограми
    - Результати ендоскопії
    - Знімки з медичних апаратів

        <b>Як відбувається аналіз?</b>
🤖 Бот автоматично визначає тип документа та аналізує як професіонал:
    - <b>Аналізи</b> → витягує всі показники та порівнює з нормами
    - <b>Знімки</b> → аналізує як лікар візуалізації (напр. радіолог, кардіолог, мамолог... залежно від типу знімка)  
    - <b>Виписки</b> → виділяє діагнози, призначення та рекомендації

        <b>Технічні моменти:</b>
    - Максимум 5 МБ на файл
    - PDF аналізується перші 5 сторінок (для оптимальної роботи)
   
    💡 <b>Чим більше медичних документів завантажите, тим точніше я буду розуміти вашу ситуацію та давати персональні рекомендації!</b>

            ⚠️ <b>Для питань з фото</b>
Просто надішліть у чат фото та поставте питання:
    - Дерматологічні проблеми (висип, родимки)
    - Фото препаратів для ідентифікації  
    - Травми та зовнішні симптоми
    - Будь-які фото для медичного аналізу
⚠️УВАГА: питання по фото це не детальний аналіз знімка з збереженням в мою пам'ять, якщо у вас є медичний знімок - скористайтеся кнопкою "Завантажити документ" для детального аналізу.""",

        "faq_notes_content": """         <b>Як працює система пам'яті?</b>

🧠 <b>Що відбувається з вашими нотатками:</b>
    - Кожна нотатка аналізується та заноситься в пам'ять
    - При ваших питаннях я шукаю потрібні нотатки залежно від вашого питання та враховую їх у відповіді
    - Чим детальніші нотатки, тим точніші мої рекомендації

📝 <b>Що варто записувати:</b>
    - Результати візитів до лікарів
    - Реакції на ліки та процедури
    - Особливості способу життя
    - Будь-які дані, які потрібно запам'ятати (напр. ви можете внести свій номер страхування, і потім запитати в чаті і я його нагадаю)
            
📊 <b>Ліміти на нотатки:</b>
    🆓 Безкоштовно: 5 нотаток на тиждень
    💎 Підписники: 10 нотаток на день

💡 <b>Порада:</b> Одна детальна нотатка краще кількох коротких!
Обов'язково стежте за актуальністю даних в пам'яті, через пункт  "Мої документи" """,

        "faq_medications_content": """      <b>Як додавати ліки?</b>

🤖 <b>Розумне додавання:</b>
    • "Додай метформін за сніданком" → бот автоматично додасть час
    • "Видали аспірин" → прибирає препарат
    • "Видали все" → очищає весь графік
    • "Додай омепразол о 19:30" → точний час


📋 <b>Що враховується:</b>
    - При відповідях я завжди пам'ятаю ваші поточні ліки
    - Враховую при аналізі симптомів

❗ <b>Важливо:</b> Графік носить довідковий характер. Дозування та зміни — тільки з лікарем!""",

        "faq_security_content": """     <b>Як захищені ваші дані?</b>

🛡️ <b>Технічний захист:</b>
    - Всі дані шифруються при передачі та зберіганні
    - Сервери відповідають медичним стандартам безпеки
    - Доступ тільки у вас — навіть розробники не бачать вміст
    - Дані обробляються анонімно, без прив'язки до особистості
            
📋 <b>Політика зберігання:</b>
    - Медичні документи — до видалення вами
    - Історія чату — для покращення відповідей
    - Можете видалити ВСІ дані через налаштування
    - Все зберігається в зашифрованому вигляді та доступне тільки вам

🇪🇺 <b>GDPR:</b>
    - Повне дотримання європейських стандартів
    - Право на доступ, виправлення та видалення даних
    - <a href="https://bit.ly/pulsebook-privacy">Політика конфіденційності</a>

⚠️ <b>Пам'ятайте:</b> PulseBook — це помічник, не заміна лікаря!""",

        "faq_profile_content": """        <b>👤 Профіль</b>
Тут ви можете редагувати свої дані:
    - Анкету
    - Мову інтерфейсу

💡 <b>Чим детальніший профіль, тим персональніші мої відповіді!</b>

            <b>💎 Підписка</b>
Управління тарифними планами:
    - Перегляд поточних лімітів
    - Оформлення підписки (Базовий/Преміум)
    - Покупка додаткових пакетів
    - Скасування підписки

            <b>🗑️ Видалення даних</b>
⚠️ <b>УВАГА:</b> Повне видалення профілю:
    - Видаляються ВСІ медичні дані (незворотно)
    - Автоматично скасовуються всі підписки
    - Історія листування стирається назавжди
    - Відновлення неможливе

            ✏️ <b>Як потрапити в налаштування:</b>
Натисніть ⚙️ Налаштування в головному меню""",

        "faq_support_content": """          <b>Якщо виникли проблеми:</b>

🔧 <b>Технічні питання:</b>
    - Проблеми з завантаженням документів
    - Помилки в роботі бота
    - Питання з підписками та платежами

💬 <b>Медичні питання:</b>
    - Допомога в інтерпретації відповідей
    - Рекомендації з використання
    - Пропозиції з покращення

📧 <b>Контакти:</b>
    - Напишіть /support
    ⏰ Відповідь протягом 72 годин 

🚨 <b>В екстрених випадках:</b>
    Звертайтеся до лікаря або в швидку допомогу! 
    PulseBook не замінює лікаря або екстрену медичну допомогу.

💡 <b>Пропозиції:</b>
    Ми завжди раді почути ваші ідеї з покращення бота!""",
    },

    "en": {
        # FAQ Main Menu
        "faq_main_title": "❓ FAQ - Bot Help\n\nSelect a section of interest:",
        
        # Main Menu Buttons
        "faq_getting_started": "🚀 Getting Started",
        "faq_subscriptions": "💎 Subscriptions & Limits",
        "faq_documents": "📄 Document Upload",
        "faq_notes": "📝 Notes & Memory",
        "faq_medications": "💊 Medication Schedule",
        "faq_security": "🔒 Data Security",
        "faq_profile": "⚙️ Settings Menu",
        "faq_support": "📞 Support",
        
        # Section Content
        "faq_getting_started_content": """          <b>How to get the most from the bot?</b>

    📄 <b>Upload documents and images</b> — each file is analyzed and becomes part of your medical history. The more data you upload, the more accurate my recommendations and responses will be!

    👤 <b>Fill out a detailed profile</b> — you will receive personalized advice exactly for your situation.

    📝 <b>Add notes to memory</b> — record symptoms, observations, doctor visit results, all this information. I help track health dynamics, find connections between different events.

    💊 <b>Keep a medication schedule</b> — add medications you're taking with timing. I will consider them in responses, and you can always view your schedule.

                <b>What does this give you?</b>
    - Get answers considering EXACTLY your situation
    - See a complete picture of your health in one place  
    - Prepare for doctor visits with ready questions
    - Track changes in tests and well-being

⚠️ <b>Remember:</b> I am your medical assistant, not a doctor replacement!""",

        "faq_subscriptions_content": """            <b>Choose the right plan:</b>

🆓 <b>Free Plan</b>
    - 1 document/image upload (one-time)
    - 3 detailed consultations (one-time)
    - 25 basic responses (one-time)

📦 <b>Basic Plan ($3.99/month)</b>
    - 5 document/image uploads
    - 50 detailed consultations
    - 100 questions per day

⭐ <b>Premium Plan ($9.99/month)</b>
    - 20 document/image uploads
    - 200 detailed consultations
    - 100 questions per day

💊 <b>Extra Package ($1.99)</b>
    - 2 document/image uploads
    - 20 detailed consultations
    - One-time purchase valid for 30 days

            <b>What's the difference in responses?</b>
💬 <b>Basic answers</b> — model that gives shorter responses

🩺 <b>Detailed consultations</b> — I use advanced model that:
    - Better analyzes connections in your medical history
    - Gives deeper and more comprehensive responses
    - <b>Allows questions with photos</b> (rash, injuries, medications, symptoms)
    - Considers more context from your documents

            <b>How does payment work?</b>
    - 🔄 Subscription automatically renews monthly
    - ⏸️ You can cancel anytime in settings
    - 📉 If auto-renewal fails (blocked card) — you switch to free plan, but all data remains!""",

        "faq_documents_content": """        <b>What can be uploaded via "📄 Upload Document"?</b>

🔬 <b>Any medical documents (PDF):</b>
    - Blood, urine, biochemistry test results
    - Hospital and clinic discharge summaries  
    - Specialist conclusions (cardiologist, endocrinologist, etc.)
    - Doctor prescriptions and orders
    - Medical certificates and conclusions
    - Surgery and procedure protocols
    - Medical history

📸 <b>Professional medical images (JPG, PNG):</b>
    - X-ray images of all organs
    - Ultrasound studies  
    - MRI and CT scans
    - ECG cardiograms
    - Endoscopy results
    - Medical device images

        <b>How does analysis work?</b>
🤖 Bot automatically determines document type and analyzes professionally:
    - <b>Lab tests</b> → extracts all indicators and compares with norms
    - <b>Images</b> → analyzes as imaging specialist (e.g. radiologist, cardiologist, mammologist... depending on image type)  
    - <b>Discharge summaries</b> → highlights diagnoses, prescriptions and recommendations

        <b>Technical details:</b>
    - Maximum 5 MB per file
    - PDF analyzes first 5 pages (for optimal performance)
   
    💡 <b>The more medical documents you upload, the better I'll understand your situation and provide personal recommendations!</b>

            ⚠️ <b>For questions with photos</b>
Simply send a photo in chat and ask a question:
    - Dermatological problems (rash, moles)
    - Photos of medications for identification  
    - Injuries and external symptoms
    - Any photos for medical analysis
⚠️WARNING: photo questions are not detailed image analysis with saving to my memory, if you have a medical image - use "Upload Document" button for detailed analysis.""",

        "faq_notes_content": """         <b>How does the memory system work?</b>

🧠 <b>What happens with your notes:</b>
    - Each note is analyzed and stored in memory
    - When you ask questions, I search for relevant notes based on your question and consider them in responses
    - The more detailed the notes, the more accurate my recommendations

📝 <b>What to record:</b>
    - Doctor visit results
    - Reactions to medications and procedures
    - Lifestyle features
    - Any data you need to remember (e.g. you can enter your insurance number, then ask in chat and I'll remind you)
            
📊 <b>Note limits:</b>
    🆓 Free: 5 notes per week
    💎 Subscribers: 10 notes per day

💡 <b>Tip:</b> One detailed note is better than several short ones!
Be sure to keep memory data current, via "My Documents" section """,

        "faq_medications_content": """      <b>How to add medications?</b>

🤖 <b>Smart adding:</b>
    • "Add metformin with breakfast" → bot automatically adds time
    • "Remove aspirin" → removes medication
    • "Remove all" → clears entire schedule
    • "Add omeprazole at 19:30" → exact time


📋 <b>What's considered:</b>
    - In responses I always remember your current medications
    - Consider when analyzing symptoms

❗ <b>Important:</b> Schedule is for reference only. Dosages and changes — only with a doctor!""",

        "faq_security_content": """     <b>How is your data protected?</b>

🛡️ <b>Technical protection:</b>
    - All data is encrypted during transmission and storage
    - Servers comply with medical security standards
    - Access only by you — even developers can't see content
    - Data is processed anonymously, without personal identification
            
📋 <b>Storage policy:</b>
    - Medical documents — until deleted by you
    - Chat history — to improve responses
    - You can delete ALL data via settings
    - Everything is stored encrypted and accessible only to you

🇪🇺 <b>GDPR:</b>
    - Full compliance with European standards
    - Right to access, correction and data deletion
    - <a href="https://bit.ly/pulsebook-privacy">Privacy Policy</a>

⚠️ <b>Remember:</b> PulseBook is an assistant, not a doctor replacement!""",

        "faq_profile_content": """        <b>👤 Profile</b>
Here you can edit your data:
    - Profile questionnaire
    - Interface language

💡 <b>The more detailed the profile, the more personalized my responses!</b>

            <b>💎 Subscription</b>
Tariff plan management:
    - View current limits
    - Subscribe (Basic/Premium)
    - Purchase additional packages
    - Cancel subscription

            <b>🗑️ Data deletion</b>
⚠️ <b>WARNING:</b> Complete profile deletion:
    - ALL medical data is deleted (irreversible)
    - All subscriptions are automatically cancelled
    - Chat history is permanently erased
    - Recovery is impossible

            ✏️ <b>How to access settings:</b>
Click ⚙️ Settings in main menu""",

        "faq_support_content": """          <b>If you have problems:</b>

🔧 <b>Technical questions:</b>
    - Document upload problems
    - Bot operation errors
    - Subscription and payment questions

💬 <b>Medical questions:</b>
    - Help interpreting responses
    - Usage recommendations
    - Improvement suggestions

📧 <b>Contacts:</b>
    - Write to /support
    ⏰ Response within 72 hours 

🚨 <b>In emergency cases:</b>
    Contact a doctor or emergency services! 
    PulseBook does not replace a doctor or emergency medical care.

💡 <b>Suggestions:</b>
    We're always happy to hear your ideas for improving the bot!""",
    },

    "de": {
        # FAQ Hauptmenü
        "faq_main_title": "❓ FAQ - Bot-Hilfe\n\nWählen Sie einen Bereich aus:",
        
        # Hauptmenü-Buttons
        "faq_getting_started": "🚀 Erste Schritte",
        "faq_subscriptions": "💎 Abonnements & Limits",
        "faq_documents": "📄 Dokument-Upload",
        "faq_notes": "📝 Notizen & Gedächtnis",
        "faq_medications": "💊 Medikamenten-Plan",
        "faq_security": "🔒 Datensicherheit",
        "faq_profile": "⚙️ Einstellungsmenü",
        "faq_support": "📞 Support",
        
        # Bereichsinhalte
        "faq_getting_started_content": """          <b>Wie holen Sie das Beste aus dem Bot heraus?</b>

    📄 <b>Laden Sie Dokumente und Bilder hoch</b> — jede Datei wird analysiert und wird Teil Ihrer Krankengeschichte. Je mehr Daten Sie hochladen, desto genauer werden meine Empfehlungen und Antworten!

    👤 <b>Füllen Sie ein detailliertes Profil aus</b> — Sie erhalten personalisierte Ratschläge genau für Ihre Situation.

    📝 <b>Fügen Sie Notizen zum Gedächtnis hinzu</b> — notieren Sie Symptome, Beobachtungen, Arztbesuch-Ergebnisse, all diese Informationen. Ich helfe dabei, Gesundheitsdynamiken zu verfolgen und Verbindungen zwischen verschiedenen Ereignissen zu finden.

    💊 <b>Führen Sie einen Medikamenten-Plan</b> — fügen Sie eingenommene Medikamente mit Zeitangaben hinzu. Ich berücksichtige sie in Antworten, und Sie können Ihren Plan jederzeit ansehen.

                <b>Was bringt Ihnen das?</b>
    - Erhalten Sie Antworten unter Berücksichtigung GENAU Ihrer Situation
    - Sehen Sie ein vollständiges Bild Ihrer Gesundheit an einem Ort  
    - Bereiten Sie sich auf Arztbesuche mit fertigen Fragen vor
    - Verfolgen Sie Veränderungen in Tests und Wohlbefinden

⚠️ <b>Denken Sie daran:</b> Ich bin Ihr medizinischer Assistent, kein Arzt-Ersatz!""",

        "faq_subscriptions_content": """            <b>Wählen Sie den passenden Plan:</b>

🆓 <b>Kostenloser Plan</b>
    - 1 Dokument-/Bild-Upload (einmalig)
    - 3 detaillierte Beratungen (einmalig)
    - 25 Basisantworten (einmalig)

📦 <b>Basisplan ($3.99/Monat)</b>
    - 5 Dokument-/Bild-Uploads
    - 50 detaillierte Beratungen
    - 100 Fragen pro Tag

⭐ <b>Premium-Plan ($9.99/Monat)</b>
    - 20 Dokument-/Bild-Uploads
    - 200 detaillierte Beratungen
    - 100 Fragen pro Tag

💊 <b>Extra-Paket ($1.99)</b>
    - 2 Dokument-/Bild-Uploads
    - 20 detaillierte Beratungen
    - Einmaliger Kauf für 30 Tage gültig

            <b>Was ist der Unterschied bei den Antworten?</b>
💬 <b>Einfache Antworten</b> — Modell, das kürzere Antworten gibt

🩺 <b>Detaillierte Konsultationen</b> — ich verwende ein fortgeschrittenes Modell, das:
    - Verbindungen in Ihrer Krankengeschichte besser analysiert
    - Tiefere und umfassendere Antworten gibt
    - <b>Fragen mit Fotos ermöglicht</b> (Ausschlag, Verletzungen, Medikamente, Symptome)
    - Mehr Kontext aus Ihren Dokumenten berücksichtigt

            <b>Wie funktioniert die Zahlung?</b>
    - 🔄 Abonnement verlängert sich automatisch monatlich
    - ⏸️ Sie können jederzeit in den Einstellungen kündigen
    - 📉 Wenn die automatische Verlängerung fehlschlägt (gesperrte Karte) — wechseln Sie zum kostenlosen Plan, aber alle Daten bleiben erhalten!""",

        "faq_documents_content": """        <b>Was kann über "📄 Dokument hochladen" hochgeladen werden?</b>

🔬 <b>Beliebige medizinische Dokumente (PDF):</b>
    - Blut-, Urin-, Biochemie-Testergebnisse
    - Krankenhaus- und Klinik-Entlassungsberichte  
    - Facharzt-Befunde (Kardiologe, Endokrinologe, etc.)
    - Arztrezepte und Verordnungen
    - Medizinische Bescheinigungen und Befunde
    - Operations- und Verfahrensprotokolle
    - Krankengeschichte

📸 <b>Professionelle medizinische Bilder (JPG, PNG):</b>
    - Röntgenbilder aller Organe
    - Ultraschall-Untersuchungen  
    - MRT- und CT-Aufnahmen
    - EKG-Kardiogramme
    - Endoskopie-Ergebnisse
    - Bilder von medizinischen Geräten

        <b>Wie funktioniert die Analyse?</b>
🤖 Der Bot bestimmt automatisch den Dokumenttyp und analysiert professionell:
    - <b>Labortests</b> → extrahiert alle Indikatoren und vergleicht mit Normen
    - <b>Bilder</b> → analysiert als Bildgebungsspezialist (z.B. Radiologe, Kardiologe, Mammologe... je nach Bildtyp)  
    - <b>Entlassungsberichte</b> → hebt Diagnosen, Verschreibungen und Empfehlungen hervor

        <b>Technische Details:</b>
    - Maximum 5 MB pro Datei
    - PDF analysiert erste 5 Seiten (für optimale Leistung)
   
    💡 <b>Je mehr medizinische Dokumente Sie hochladen, desto besser verstehe ich Ihre Situation und gebe persönliche Empfehlungen!</b>

            ⚠️ <b>Für Fragen mit Fotos</b>
Senden Sie einfach ein Foto im Chat und stellen Sie eine Frage:
    - Dermatologische Probleme (Ausschlag, Muttermale)
    - Fotos von Medikamenten zur Identifikation  
    - Verletzungen und äußere Symptome
    - Beliebige Fotos für medizinische Analyse
⚠️WARNUNG: Foto-Fragen sind keine detaillierte Bildanalyse mit Speicherung in meinem Gedächtnis, wenn Sie ein medizinisches Bild haben - nutzen Sie die "Dokument hochladen" Schaltfläche für detaillierte Analyse.""",

        "faq_notes_content": """         <b>Wie funktioniert das Gedächtnissystem?</b>

🧠 <b>Was passiert mit Ihren Notizen:</b>
    - Jede Notiz wird analysiert und im Gedächtnis gespeichert
    - Bei Ihren Fragen suche ich relevante Notizen basierend auf Ihrer Frage und berücksichtige sie in Antworten
    - Je detaillierter die Notizen, desto genauer meine Empfehlungen

📝 <b>Was zu notieren ist:</b>
    - Arztbesuch-Ergebnisse
    - Reaktionen auf Medikamente und Verfahren
    - Lebensstil-Besonderheiten
    - Beliebige Daten, die Sie sich merken müssen (z.B. können Sie Ihre Versicherungsnummer eingeben und dann im Chat fragen, ich erinnere Sie daran)
            
📊 <b>Notiz-Limits:</b>
    🆓 Kostenlos: 5 Notizen pro Woche
    💎 Abonnenten: 10 Notizen pro Tag

💡 <b>Tipp:</b> Eine detaillierte Notiz ist besser als mehrere kurze!
Achten Sie darauf, Gedächtnisdaten aktuell zu halten, über den Abschnitt "Meine Dokumente" """,

        "faq_medications_content": """      <b>Wie Medikamente hinzufügen?</b>

🤖 <b>Intelligentes Hinzufügen:</b>
    • "Metformin zum Frühstück hinzufügen" → Bot fügt automatisch Zeit hinzu
    • "Aspirin entfernen" → entfernt Medikament
    • "Alles entfernen" → löscht gesamten Plan
    • "Omeprazol um 19:30 hinzufügen" → genaue Zeit


📋 <b>Was berücksichtigt wird:</b>
    - Bei Antworten erinnere ich mich immer an Ihre aktuellen Medikamente
    - Berücksichtige bei Symptom-Analyse

❗ <b>Wichtig:</b> Der Plan dient nur zur Referenz. Dosierungen und Änderungen — nur mit einem Arzt!""",

        "faq_security_content": """     <b>Wie sind Ihre Daten geschützt?</b>

🛡️ <b>Technischer Schutz:</b>
    - Alle Daten werden bei Übertragung und Speicherung verschlüsselt
    - Server entsprechen medizinischen Sicherheitsstandards
    - Zugang nur für Sie — selbst Entwickler können Inhalte nicht sehen
    - Daten werden anonym verarbeitet, ohne persönliche Identifikation
            
📋 <b>Speicher-Richtlinie:</b>
    - Medizinische Dokumente — bis zur Löschung durch Sie
    - Chat-Verlauf — zur Verbesserung der Antworten
    - Sie können ALLE Daten über Einstellungen löschen
    - Alles wird verschlüsselt gespeichert und ist nur für Sie zugänglich

🇪🇺 <b>DSGVO:</b>
    - Vollständige Einhaltung europäischer Standards
    - Recht auf Zugang, Korrektur und Datenlöschung
    - <a href="https://bit.ly/pulsebook-privacy">Datenschutzrichtlinie</a>

⚠️ <b>Denken Sie daran:</b> PulseBook ist ein Assistent, kein Arzt-Ersatz!""",

        "faq_profile_content": """        <b>👤 Profil</b>
Hier können Sie Ihre Daten bearbeiten:
    - Profil-Fragebogen
    - Interface-Sprache

💡 <b>Je detaillierter das Profil, desto personalisierter meine Antworten!</b>

            <b>💎 Abonnement</b>
Tarif-Plan-Verwaltung:
    - Aktuelle Limits anzeigen
    - Abonnement abschließen (Basic/Premium)
    - Zusätzliche Pakete kaufen
    - Abonnement kündigen

            <b>🗑️ Datenlöschung</b>
⚠️ <b>WARNUNG:</b> Vollständige Profil-Löschung:
    - ALLE medizinischen Daten werden gelöscht (unumkehrbar)
    - Alle Abonnements werden automatisch gekündigt
    - Chat-Verlauf wird dauerhaft gelöscht
    - Wiederherstellung ist unmöglich

            ✏️ <b>Wie zu den Einstellungen gelangen:</b>
Klicken Sie ⚙️ Einstellungen im Hauptmenü""",

        "faq_support_content": """          <b>Bei Problemen:</b>

🔧 <b>Technische Fragen:</b>
    - Probleme beim Dokument-Upload
    - Bot-Betriebsfehler
    - Fragen zu Abonnements und Zahlungen

💬 <b>Medizinische Fragen:</b>
    - Hilfe bei der Interpretation von Antworten
    - Nutzungsempfehlungen
    - Verbesserungsvorschläge

📧 <b>Kontakte:</b>
    - Schreiben Sie an /support
    ⏰ Antwort innerhalb von 72 Stunden 

🚨 <b>In Notfällen:</b>
    Wenden Sie sich an einen Arzt oder Notdienst! 
    PulseBook ersetzt keinen Arzt oder Notfallmedizin.

💡 <b>Vorschläge:</b>
    Wir freuen uns immer über Ihre Ideen zur Verbesserung des Bots!""",
    },
}


def get_faq_text(key: str, lang: str = "ru") -> str:
    """Получить текст FAQ по ключу и языку"""
    try:
        return FAQ_TEXTS[lang][key]
    except KeyError:
        # Fallback на русский если нет перевода
        return FAQ_TEXTS["ru"].get(key, f"❌ Текст не найден: {key}")