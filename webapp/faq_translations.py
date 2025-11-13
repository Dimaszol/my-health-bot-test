# webapp/faq_translations.py
# ❓ Переводы для FAQ страницы

"""
Система переводов для FAQ страницы с поддержкой 4 языков:
- Русский (ru) 🇷🇺
- Украинский (uk) 🇺🇦
- Английский (en) 🇬🇧
- Немецкий (de) 🇩🇪
"""

FAQ_TRANSLATIONS = {
    # ============================================
    # 📋 ОБЩИЕ ЭЛЕМЕНТЫ FAQ
    # ============================================
    'faq_title': {
        'ru': 'Часто задаваемые вопросы',
        'en': 'Frequently Asked Questions',
        'uk': 'Часті питання',
        'de': 'Häufig gestellte Fragen'
    },
    'faq_subtitle': {
        'ru': 'Найдите ответы на популярные вопросы о PulseBook',
        'en': 'Find answers to popular questions about PulseBook',
        'uk': 'Знайдіть відповіді на популярні питання про PulseBook',
        'de': 'Finden Sie Antworten auf häufige Fragen zu PulseBook'
    },
    
    # ============================================
    # 1️⃣ О PULSEBOOK
    # ============================================
    'faq_about_title': {
        'ru': 'О PulseBook',
        'en': 'About PulseBook',
        'uk': 'Про PulseBook',
        'de': 'Über PulseBook'
    },
    'faq_about_content': {
        'ru': '''
<p><strong>PulseBook — это не просто еще один AI-ассистент.</strong></p>

<p>Это первая медицинская платформа, где работает <strong>консилиум ведущих AI-моделей</strong> — OpenAI, Google Gemini и Claude объединены в единый алгоритм для максимально точного анализа ваших медицинских данных.</p>

<h4>Почему это важно?</h4>

<p>• <strong>Перекрестная проверка:</strong> Каждый документ анализируется несколькими моделями, что снижает риск пропущенных деталей</p>

<p>• <strong>Работа как единое целое:</strong> Алгоритм настроен так, что все модели работают синхронно, дополняя сильные стороны друг друга для получения наиболее точного результата</p>

<p>• <strong>Медицинская специализация:</strong> Алгоритм специально обучен работать с медицинскими документами, терминологией и контекстом здоровья</p>

<h4>Ваши преимущества:</h4>

<p>✓ Все медицинские документы в одном месте<br>
✓ Мгновенный анализ от "консилиума" AI-моделей<br>
✓ Персонализированные рекомендации на основе вашей истории<br>
✓ Полная конфиденциальность и соответствие HIPAA/GDPR</p>

<p><strong>PulseBook — это ваш умный медицинский помощник, который всегда с вами.</strong></p>
''',
        'en': '''
<p><strong>PulseBook is not just another AI assistant.</strong></p>

<p>It's the first medical platform with a <strong>consortium of leading AI models</strong> — OpenAI, Google Gemini, and Claude combined into a single algorithm for the most accurate analysis of your medical data.</p>

<h4>Why is this important?</h4>

<p>• <strong>Cross-verification:</strong> Each document is analyzed by multiple models, reducing the risk of missed details</p>

<p>• <strong>Working as one:</strong> The algorithm is configured so all models work synchronously, complementing each other's strengths for the most accurate result</p>

<p>• <strong>Medical specialization:</strong> The algorithm is specially trained to work with medical documents, terminology, and health context</p>

<h4>Your benefits:</h4>

<p>✓ All medical documents in one place<br>
✓ Instant analysis from AI model "consortium"<br>
✓ Personalized recommendations based on your history<br>
✓ Full confidentiality and HIPAA/GDPR compliance</p>

<p><strong>PulseBook is your smart medical assistant, always with you.</strong></p>
''',
        'uk': '''
<p><strong>PulseBook — це не просто ще один AI-асистент.</strong></p>

<p>Це перша медична платформа, де працює <strong>консиліум провідних AI-моделей</strong> — OpenAI, Google Gemini та Claude об'єднані в єдиний алгоритм для максимально точного аналізу ваших медичних даних.</p>

<h4>Чому це важливо?</h4>

<p>• <strong>Перехресна перевірка:</strong> Кожен документ аналізується декількома моделями, що знижує ризик пропущених деталей</p>

<p>• <strong>Робота як єдине ціле:</strong> Алгоритм налаштований так, що всі моделі працюють синхронно, доповнюючи сильні сторони одна одної для отримання найточнішого результату</p>

<p>• <strong>Медична спеціалізація:</strong> Алгоритм спеціально навчений працювати з медичними документами, термінологією та контекстом здоров'я</p>

<h4>Ваші переваги:</h4>

<p>✓ Всі медичні документи в одному місці<br>
✓ Миттєвий аналіз від "консиліуму" AI-моделей<br>
✓ Персоналізовані рекомендації на основі вашої історії<br>
✓ Повна конфіденційність та відповідність HIPAA/GDPR</p>

<p><strong>PulseBook — це ваш розумний медичний помічник, який завжди з вами.</strong></p>
''',
        'de': '''
<p><strong>PulseBook ist nicht nur ein weiterer KI-Assistent.</strong></p>

<p>Es ist die erste medizinische Plattform mit einem <strong>Konsortium führender KI-Modelle</strong> — OpenAI, Google Gemini und Claude kombiniert in einem einzigen Algorithmus für die genaueste Analyse Ihrer medizinischen Daten.</p>

<h4>Warum ist das wichtig?</h4>

<p>• <strong>Kreuzverifizierung:</strong> Jedes Dokument wird von mehreren Modellen analysiert, wodurch das Risiko übersehener Details verringert wird</p>

<p>• <strong>Als Einheit arbeiten:</strong> Der Algorithmus ist so konfiguriert, dass alle Modelle synchron arbeiten und die Stärken des anderen ergänzen, um das genaueste Ergebnis zu erzielen</p>

<p>• <strong>Medizinische Spezialisierung:</strong> Der Algorithmus ist speziell darauf trainiert, mit medizinischen Dokumenten, Terminologie und Gesundheitskontext zu arbeiten</p>

<h4>Ihre Vorteile:</h4>

<p>✓ Alle medizinischen Dokumente an einem Ort<br>
✓ Sofortige Analyse vom KI-Modell-"Konsortium"<br>
✓ Personalisierte Empfehlungen basierend auf Ihrer Geschichte<br>
✓ Vollständige Vertraulichkeit und HIPAA/GDPR-Konformität</p>

<p><strong>PulseBook ist Ihr intelligenter medizinischer Assistent, immer bei Ihnen.</strong></p>
'''
    },
    
    # ============================================
    # 2️⃣ НАЧАЛО РАБОТЫ
    # ============================================
    'faq_getting_started_title': {
        'ru': '🚀 Начало работы',
        'en': '🚀 Getting Started',
        'uk': '🚀 Початок роботи',
        'de': '🚀 Erste Schritte'
    },
    'faq_getting_started_content': {
        'ru': '''
<h4>Как начать пользоваться PulseBook?</h4>

<p>Всего 3 простых шага отделяют вас от персонального AI-помощника:</p>

<p><strong>1. Регистрация через Google</strong><br>
Войдите на сайт используя свой Google аккаунт — это быстро и безопасно. Никаких сложных форм и подтверждений email.</p>

<p><strong>2. Заполните базовый профиль</strong><br>
Укажите основную информацию о себе: возраст, пол, рост, вес, хронические заболевания и аллергии. Чем больше PulseBook знает о вас, тем точнее будут рекомендации.</p>

<p><strong>3. Загрузите первые документы</strong><br>
Добавьте анализы, снимки или заключения врачей в любом формате (PDF, DOCX, изображения). AI автоматически извлечет все важные данные.</p>

<h4>Готово! Теперь вы можете:</h4>

<p>✓ Задавать вопросы о своем здоровье в чате<br>
✓ Получать анализ загруженных документов<br>
✓ Отслеживать динамику показателей здоровья<br>
✓ Создавать заметки о самочувствии</p>

<p><strong>💡 Совет:</strong> Начните с загрузки последних анализов крови — это даст AI хорошую базу для персонализированных рекомендаций.</p>
''',
        'en': '''
<h4>How to start using PulseBook?</h4>

<p>Just 3 simple steps separate you from your personal AI assistant:</p>

<p><strong>1. Register via Google</strong><br>
Sign in using your Google account — it's fast and secure. No complex forms or email confirmations.</p>

<p><strong>2. Fill in basic profile</strong><br>
Provide basic information about yourself: age, gender, height, weight, chronic diseases, and allergies. The more PulseBook knows about you, the more accurate the recommendations.</p>

<p><strong>3. Upload first documents</strong><br>
Add test results, images, or doctor's reports in any format (PDF, DOCX, images). AI will automatically extract all important data.</p>

<h4>Done! Now you can:</h4>

<p>✓ Ask questions about your health in chat<br>
✓ Get analysis of uploaded documents<br>
✓ Track health metrics dynamics<br>
✓ Create wellness notes</p>

<p><strong>💡 Tip:</strong> Start by uploading your latest blood tests — this will give AI a good foundation for personalized recommendations.</p>
''',
        'uk': '''
<h4>Як почати користуватися PulseBook?</h4>

<p>Всього 3 прості кроки відділяють вас від персонального AI-помічника:</p>

<p><strong>1. Реєстрація через Google</strong><br>
Увійдіть на сайт використовуючи свій Google акаунт — це швидко і безпечно. Ніяких складних форм і підтверджень email.</p>

<p><strong>2. Заповніть базовий профіль</strong><br>
Вкажіть основну інформацію про себе: вік, стать, зріст, вага, хронічні захворювання та алергії. Чим більше PulseBook знає про вас, тим точніші рекомендації.</p>

<p><strong>3. Завантажте перші документи</strong><br>
Додайте аналізи, знімки або висновки лікарів у будь-якому форматі (PDF, DOCX, зображення). AI автоматично витягне всі важливі дані.</p>

<h4>Готово! Тепер ви можете:</h4>

<p>✓ Ставити питання про своє здоров'я в чаті<br>
✓ Отримувати аналіз завантажених документів<br>
✓ Відстежувати динаміку показників здоров'я<br>
✓ Створювати нотатки про самопочуття</p>

<p><strong>💡 Порада:</strong> Почніть із завантаження останніх аналізів крові — це дасть AI хорошу базу для персоналізованих рекомендацій.</p>
''',
        'de': '''
<h4>Wie beginnt man mit PulseBook?</h4>

<p>Nur 3 einfache Schritte trennen Sie von Ihrem persönlichen KI-Assistenten:</p>

<p><strong>1. Registrierung über Google</strong><br>
Melden Sie sich mit Ihrem Google-Konto an — schnell und sicher. Keine komplexen Formulare oder E-Mail-Bestätigungen.</p>

<p><strong>2. Grundprofil ausfüllen</strong><br>
Geben Sie grundlegende Informationen über sich an: Alter, Geschlecht, Größe, Gewicht, chronische Krankheiten und Allergien. Je mehr PulseBook über Sie weiß, desto genauer die Empfehlungen.</p>

<p><strong>3. Erste Dokumente hochladen</strong><br>
Fügen Sie Testergebnisse, Bilder oder Arztberichte in jedem Format hinzu (PDF, DOCX, Bilder). KI extrahiert automatisch alle wichtigen Daten.</p>

<h4>Fertig! Jetzt können Sie:</h4>

<p>✓ Fragen zu Ihrer Gesundheit im Chat stellen<br>
✓ Analyse hochgeladener Dokumente erhalten<br>
✓ Dynamik von Gesundheitskennzahlen verfolgen<br>
✓ Wellness-Notizen erstellen</p>

<p><strong>💡 Tipp:</strong> Beginnen Sie mit dem Hochladen Ihrer neuesten Bluttests — dies gibt der KI eine gute Grundlage für personalisierte Empfehlungen.</p>
'''
    },
    
    # ============================================
    # 3️⃣ ПОДПИСКИ И ТАРИФЫ
    # ============================================
    'faq_subscriptions_title': {
        'ru': '💳 Подписки и тарифы',
        'en': '💳 Subscriptions and Plans',
        'uk': '💳 Підписки та тарифи',
        'de': '💳 Abonnements und Tarife'
    },
    'faq_subscriptions_content': {
        'ru': '''
<h4>Какие тарифные планы доступны?</h4>

<p>PulseBook предлагает гибкую систему тарифов под любые потребности:</p>

<p><strong>🆓 Бесплатный тариф</strong></p>
<ul>
<li>10 детальных консультаций</li>
<li>2 загрузки и анализа документа</li>
<li>50 базовых ответов в неделю</li>
<li>Хранение медицинской истории</li>
<li>Доступ ко всем функциям профиля</li>
</ul>

<p><strong>⭐ Lite (Базовый)</strong></p>
<ul>
<li>100 детальных консультаций</li>
<li>5 загрузки и анализа документа</li>
<li>100 базовых ответов в день</li>
<li>Максимальная память в чате</li>
<li>Персональные рекомендации на основе истории</li>
<li>Приоритетная поддержка и обработка документов</li>
</ul>

<p><strong>💎 Pro (Премиум)</strong></p>
<ul>
<li>400 детальных консультаций</li>
<li>До 20 документов</li>
<li>100 базовых ответов в день</li>
<li>Максимальная память в чате</li>
<li>Персональные рекомендации на основе истории</li>
<li>Приоритетная поддержка и обработка документов</li>
</ul>

<hr>

<h4>В чем разница между базовым ответом и детальной консультацией?</h4>

<p><strong>Базовый ответ</strong> — быстрый ответ от одной AI-модели.</p>

<p><strong>Детальная консультация</strong> — работает "консилиум" из нескольких ведущих AI-моделей (OpenAI, Gemini, Claude). Используется для:</p>
<ul>
<li>Глубокого анализа медицинских документов</li>
<li>Сложных вопросов о здоровье</li>
<li>Персонализированных рекомендаций на основе вашей истории</li>
<li>Перекрестной проверки информации для максимальной точности</li>
</ul>

<hr>

<h4>Как оплатить?</h4>

<p>Мы принимаем оплату через Stripe — безопасный международный платежный сервис. Поддерживаются карты Visa, Mastercard и другие популярные способы оплаты.</p>

<p><strong>💡 Совет:</strong> Начните с бесплатного тарифа, чтобы оценить возможности платформы, а затем выберите подходящий план.</p>
''',
        'en': '''
<h4>What subscription plans are available?</h4>

<p>PulseBook offers flexible pricing for any needs:</p>

<p><strong>🆓 Free Plan</strong></p>
<ul>
<li>10 detailed consultations</li>
<li>2 document uploads and analyses</li>
<li>50 basic answers per week</li>
<li>Medical history storage</li>
<li>Access to all profile features</li>
</ul>

<p><strong>⭐ Lite (Basic)</strong></p>
<ul>
<li>100 detailed consultations</li>
<li>5 document uploads and analyses</li>
<li>100 basic answers per day</li>
<li>Maximum chat memory</li>
<li>Personalized recommendations based on history</li>
<li>Priority support and document processing</li>
</ul>

<p><strong>💎 Pro (Premium)</strong></p>
<ul>
<li>400 detailed consultations</li>
<li>Up to 20 documents</li>
<li>100 basic answers per day</li>
<li>Maximum chat memory</li>
<li>Personalized recommendations based on history</li>
<li>Priority support and document processing</li>
</ul>

<hr>

<h4>What's the difference between basic answer and detailed consultation?</h4>

<p><strong>Basic answer</strong> — quick response from one AI model.</p>

<p><strong>Detailed consultation</strong> — a "consortium" of several leading AI models (OpenAI, Gemini, Claude) working together. Used for:</p>
<ul>
<li>In-depth analysis of medical documents</li>
<li>Complex health questions</li>
<li>Personalized recommendations based on your history</li>
<li>Cross-verification for maximum accuracy</li>
</ul>

<hr>

<h4>How to pay?</h4>

<p>We accept payments through Stripe — a secure international payment service. Visa, Mastercard, and other popular payment methods are supported.</p>

<p><strong>💡 Tip:</strong> Start with the free plan to evaluate the platform, then choose the right plan.</p>
''',
        'uk': '''
<h4>Які тарифні плани доступні?</h4>

<p>PulseBook пропонує гнучку систему тарифів під будь-які потреби:</p>

<p><strong>🆓 Безкоштовний тариф</strong></p>
<ul>
<li>10 детальних консультацій</li>
<li>2 завантаження та аналізу документа</li>
<li>50 базових відповідей на тиждень</li>
<li>Зберігання медичної історії</li>
<li>Доступ до всіх функцій профілю</li>
</ul>

<p><strong>⭐ Lite (Базовий)</strong></p>
<ul>
<li>100 детальних консультацій</li>
<li>5 завантажень та аналізів документа</li>
<li>100 базових відповідей на день</li>
<li>Максимальна пам'ять в чаті</li>
<li>Персональні рекомендації на основі історії</li>
<li>Пріоритетна підтримка та обробка документів</li>
</ul>

<p><strong>💎 Pro (Преміум)</strong></p>
<ul>
<li>400 детальних консультацій</li>
<li>До 20 документів</li>
<li>100 базових відповідей на день</li>
<li>Максимальна пам'ять в чаті</li>
<li>Персональні рекомендації на основі історії</li>
<li>Пріоритетна підтримка та обробка документів</li>
</ul>

<hr>

<h4>У чому різниця між базовою відповіддю та детальною консультацією?</h4>

<p><strong>Базова відповідь</strong> — швидка відповідь від однієї AI-моделі.</p>

<p><strong>Детальна консультація</strong> — працює "консиліум" з кількох провідних AI-моделей (OpenAI, Gemini, Claude). Використовується для:</p>
<ul>
<li>Глибокого аналізу медичних документів</li>
<li>Складних питань про здоров'я</li>
<li>Персоналізованих рекомендацій на основі вашої історії</li>
<li>Перехресної перевірки інформації для максимальної точності</li>
</ul>

<hr>

<h4>Як оплатити?</h4>

<p>Ми приймаємо оплату через Stripe — безпечний міжнародний платіжний сервіс. Підтримуються карти Visa, Mastercard та інші популярні способи оплати.</p>

<p><strong>💡 Порада:</strong> Почніть з безкоштовного тарифу, щоб оцінити можливості платформи, а потім виберіть відповідний план.</p>
''',
        'de': '''
<h4>Welche Abonnementpläne sind verfügbar?</h4>

<p>PulseBook bietet flexible Preise für jeden Bedarf:</p>

<p><strong>🆓 Kostenloser Plan</strong></p>
<ul>
<li>10 detaillierte Beratungen</li>
<li>2 Dokument-Uploads und Analysen</li>
<li>50 Basisantworten pro Woche</li>
<li>Speicherung der Krankengeschichte</li>
<li>Zugriff auf alle Profilfunktionen</li>
</ul>

<p><strong>⭐ Lite (Basic)</strong></p>
<ul>
<li>100 detaillierte Beratungen</li>
<li>5 Dokument-Uploads und Analysen</li>
<li>100 Basisantworten pro Tag</li>
<li>Maximales Chat-Gedächtnis</li>
<li>Personalisierte Empfehlungen basierend auf Historie</li>
<li>Prioritätsunterstützung und Dokumentenverarbeitung</li>
</ul>

<p><strong>💎 Pro (Premium)</strong></p>
<ul>
<li>400 detaillierte Beratungen</li>
<li>Bis zu 20 Dokumente</li>
<li>100 Basisantworten pro Tag</li>
<li>Maximales Chat-Gedächtnis</li>
<li>Personalisierte Empfehlungen basierend auf Historie</li>
<li>Prioritätsunterstützung und Dokumentenverarbeitung</li>
</ul>

<hr>

<h4>Was ist der Unterschied zwischen Basisantwort und detaillierter Beratung?</h4>

<p><strong>Basisantwort</strong> — schnelle Antwort von einem KI-Modell.</p>

<p><strong>Detaillierte Beratung</strong> — ein "Konsortium" mehrerer führender KI-Modelle (OpenAI, Gemini, Claude) arbeitet zusammen. Verwendet für:</p>
<ul>
<li>Tiefgehende Analyse medizinischer Dokumente</li>
<li>Komplexe Gesundheitsfragen</li>
<li>Personalisierte Empfehlungen basierend auf Ihrer Geschichte</li>
<li>Kreuzverifizierung für maximale Genauigkeit</li>
</ul>

<hr>

<h4>Wie bezahlen?</h4>

<p>Wir akzeptieren Zahlungen über Stripe — einen sicheren internationalen Zahlungsdienst. Visa, Mastercard und andere beliebte Zahlungsmethoden werden unterstützt.</p>

<p><strong>💡 Tipp:</strong> Beginnen Sie mit dem kostenlosen Plan, um die Plattform zu bewerten, und wählen Sie dann den richtigen Plan.</p>
'''
    },
    
    # ============================================
    # 4️⃣ ДОКУМЕНТЫ
    # ============================================
    'faq_documents_title': {
        'ru': '📄 Документы',
        'en': '📄 Documents',
        'uk': '📄 Документи',
        'de': '📄 Dokumente'
    },
    'faq_documents_content': {
        'ru': '''
<h4>Как работать с медицинскими документами?</h4>

<p>PulseBook позволяет хранить и анализировать все ваши медицинские документы в одном месте.</p>

<h4>Какие документы можно загружать?</h4>

<p>✓ Результаты анализов крови, мочи, биохимии<br>
✓ Рентгеновские снимки, МРТ, КТ, УЗИ<br>
✓ Выписки из больниц и заключения врачей<br>
✓ Рецепты и назначения<br>
✓ Результаты обследований и диагностики</p>

<h4>Поддерживаемые форматы:</h4>

<p>PDF, DOCX, JPG, PNG и другие популярные форматы изображений и документов.</p>

<h4>Как загрузить документ?</h4>

<p>1. Перейдите в раздел "Документы"<br>
2. Нажмите кнопку "Загрузить документ"<br>
3. Выберите файл с вашего устройства<br>
4. AI автоматически проанализирует документ и извлечет все важные данные</p>

<h4>Что происходит после загрузки?</h4>

<p>AI автоматически:</p>
<ul>
<li>Извлекает все показатели и данные из документа</li>
<li>Сохраняет информацию в вашу медицинскую карту</li>
<li>Использует эти данные для персонализированных ответов в чате</li>
<li>Отслеживает динамику изменения показателей</li>
</ul>

<h4>Доступ к вашим документам:</h4>

<p>✓ Все документы доступны с любого устройства — компьютера, планшета или телефона<br>
✓ Вы никогда не потеряете важные медицинские данные<br>
✓ Можете скачать любой документ в любое время<br>
✓ Удобный просмотр и поиск по всей истории документов</p>

<p><strong>💡 Совет:</strong> Загружайте документы сразу после получения результатов анализов — так AI будет иметь актуальную информацию о вашем здоровье.</p>

<h4>Безопасность:</h4>

<p>Все документы хранятся в зашифрованном виде и доступны только вам. Мы соблюдаем стандарты HIPAA и GDPR.</p>
''',
        'en': '''
<h4>How to work with medical documents?</h4>

<p>PulseBook allows you to store and analyze all your medical documents in one place.</p>

<h4>What documents can be uploaded?</h4>

<p>✓ Blood, urine, biochemistry test results<br>
✓ X-rays, MRI, CT, ultrasound images<br>
✓ Hospital discharge summaries and doctor reports<br>
✓ Prescriptions and appointments<br>
✓ Examination and diagnostic results</p>

<h4>Supported formats:</h4>

<p>PDF, DOCX, JPG, PNG and other popular image and document formats.</p>

<h4>How to upload a document?</h4>

<p>1. Go to "Documents" section<br>
2. Click "Upload document" button<br>
3. Select file from your device<br>
4. AI will automatically analyze the document and extract all important data</p>

<h4>What happens after upload?</h4>

<p>AI automatically:</p>
<ul>
<li>Extracts all metrics and data from the document</li>
<li>Saves information to your medical record</li>
<li>Uses this data for personalized chat responses</li>
<li>Tracks dynamics of metric changes</li>
</ul>

<h4>Access to your documents:</h4>

<p>✓ All documents accessible from any device — computer, tablet, or phone<br>
✓ You'll never lose important medical data<br>
✓ Can download any document anytime<br>
✓ Convenient viewing and search through entire document history</p>

<p><strong>💡 Tip:</strong> Upload documents immediately after receiving test results — so AI will have current information about your health.</p>

<h4>Security:</h4>

<p>All documents are stored encrypted and accessible only to you. We comply with HIPAA and GDPR standards.</p>
''',
        'uk': '''
<h4>Як працювати з медичними документами?</h4>

<p>PulseBook дозволяє зберігати та аналізувати всі ваші медичні документи в одному місці.</p>

<h4>Які документи можна завантажувати?</h4>

<p>✓ Результати аналізів крові, сечі, біохімії<br>
✓ Рентгенівські знімки, МРТ, КТ, УЗД<br>
✓ Виписки з лікарень та висновки лікарів<br>
✓ Рецепти та призначення<br>
✓ Результати обстежень та діагностики</p>

<h4>Підтримувані формати:</h4>

<p>PDF, DOCX, JPG, PNG та інші популярні формати зображень та документів.</p>

<h4>Як завантажити документ?</h4>

<p>1. Перейдіть до розділу "Документи"<br>
2. Натисніть кнопку "Завантажити документ"<br>
3. Виберіть файл з вашого пристрою<br>
4. AI автоматично проаналізує документ та витягне всі важливі дані</p>

<h4>Що відбувається після завантаження?</h4>

<p>AI автоматично:</p>
<ul>
<li>Витягує всі показники та дані з документа</li>
<li>Зберігає інформацію у вашу медичну карту</li>
<li>Використовує ці дані для персоналізованих відповідей у чаті</li>
<li>Відстежує динаміку зміни показників</li>
</ul>

<h4>Доступ до ваших документів:</h4>

<p>✓ Всі документи доступні з будь-якого пристрою — комп'ютера, планшета або телефону<br>
✓ Ви ніколи не втратите важливі медичні дані<br>
✓ Можете завантажити будь-який документ у будь-який час<br>
✓ Зручний перегляд та пошук по всій історії документів</p>

<p><strong>💡 Порада:</strong> Завантажуйте документи відразу після отримання результатів аналізів — так AI матиме актуальну інформацію про ваше здоров'я.</p>

<h4>Безпека:</h4>

<p>Всі документи зберігаються в зашифрованому вигляді та доступні тільки вам. Ми дотримуємося стандартів HIPAA та GDPR.</p>
''',
        'de': '''
<h4>Wie arbeitet man mit medizinischen Dokumenten?</h4>

<p>PulseBook ermöglicht es Ihnen, alle Ihre medizinischen Dokumente an einem Ort zu speichern und zu analysieren.</p>

<h4>Welche Dokumente können hochgeladen werden?</h4>

<p>✓ Blut-, Urin-, Biochemie-Testergebnisse<br>
✓ Röntgen-, MRT-, CT-, Ultraschallbilder<br>
✓ Krankenhaus-Entlassungsberichte und Arztberichte<br>
✓ Rezepte und Termine<br>
✓ Untersuchungs- und Diagnoseergebnisse</p>

<h4>Unterstützte Formate:</h4>

<p>PDF, DOCX, JPG, PNG und andere beliebte Bild- und Dokumentformate.</p>

<h4>Wie lädt man ein Dokument hoch?</h4>

<p>1. Gehen Sie zum Abschnitt "Dokumente"<br>
2. Klicken Sie auf die Schaltfläche "Dokument hochladen"<br>
3. Wählen Sie eine Datei von Ihrem Gerät aus<br>
4. KI analysiert automatisch das Dokument und extrahiert alle wichtigen Daten</p>

<h4>Was passiert nach dem Hochladen?</h4>

<p>KI automatisch:</p>
<ul>
<li>Extrahiert alle Metriken und Daten aus dem Dokument</li>
<li>Speichert Informationen in Ihrer Krankenakte</li>
<li>Verwendet diese Daten für personalisierte Chat-Antworten</li>
<li>Verfolgt die Dynamik von Metrikänderungen</li>
</ul>

<h4>Zugriff auf Ihre Dokumente:</h4>

<p>✓ Alle Dokumente von jedem Gerät aus zugänglich — Computer, Tablet oder Telefon<br>
✓ Sie verlieren niemals wichtige medizinische Daten<br>
✓ Können jedes Dokument jederzeit herunterladen<br>
✓ Bequemes Ansehen und Durchsuchen der gesamten Dokumentenhistorie</p>

<p><strong>💡 Tipp:</strong> Laden Sie Dokumente sofort nach Erhalt der Testergebnisse hoch — so hat die KI aktuelle Informationen über Ihre Gesundheit.</p>

<h4>Sicherheit:</h4>

<p>Alle Dokumente werden verschlüsselt gespeichert und sind nur für Sie zugänglich. Wir erfüllen HIPAA- und GDPR-Standards.</p>
'''
    },
    
    # ============================================
    # 5️⃣ ПРОФИЛЬ
    # ============================================
    'faq_profile_title': {
        'ru': '👤 Профиль',
        'en': '👤 Profile',
        'uk': '👤 Профіль',
        'de': '👤 Profil'
    },
    'faq_profile_content': {
        'ru': '''
<h4>Зачем заполнять профиль?</h4>

<p>Профиль — это основа для персонализированных рекомендаций от AI. Чем больше PulseBook знает о вас, тем точнее будут ответы и анализ документов.</p>

<h4>Какую информацию нужно указать?</h4>

<p><strong>Основные данные:</strong></p>
<ul>
<li>Имя</li>
<li>Год рождения</li>
<li>Пол</li>
<li>Рост и вес</li>
</ul>

<p><strong>Медицинская информация:</strong></p>
<ul>
<li>Хронические заболевания</li>
<li>Аллергии и непереносимости</li>
<li>Постоянные медикаменты</li>
</ul>

<p><strong>Образ жизни:</strong></p>
<ul>
<li>Уровень физической активности</li>
<li>Курение и употребление алкоголя</li>
<li>Особенности питания</li>
</ul>

<h4>Зачем это нужно?</h4>

<p>✓ AI учитывает ваши особенности при анализе документов<br>
✓ Рекомендации становятся персонализированными под ваш профиль<br>
✓ Система предупреждает о возможных противопоказаниях<br>
✓ Отслеживание динамики показателей с учетом вашего возраста и состояния</p>

<h4>Как обновить профиль?</h4>

<p>1. Перейдите в раздел "Профиль"<br>
2. Нажмите кнопку "Редактировать"<br>
3. Внесите изменения<br>
4. Сохраните данные</p>

<h4>Конфиденциальность:</h4>

<p>Все данные профиля защищены и используются только для улучшения качества рекомендаций. Мы никогда не передаем вашу информацию третьим лицам.</p>

<p><strong>💡 Совет:</strong> Обновляйте данные о весе, медикаментах и заболеваниях при изменениях — это поможет AI давать более актуальные рекомендации.</p>
''',
        'en': '''
<h4>Why fill in the profile?</h4>

<p>Profile is the foundation for personalized AI recommendations. The more PulseBook knows about you, the more accurate the answers and document analysis.</p>

<h4>What information needs to be provided?</h4>

<p><strong>Basic data:</strong></p>
<ul>
<li>Name</li>
<li>Year of birth</li>
<li>Gender</li>
<li>Height and weight</li>
</ul>

<p><strong>Medical information:</strong></p>
<ul>
<li>Chronic diseases</li>
<li>Allergies and intolerances</li>
<li>Regular medications</li>
</ul>

<p><strong>Lifestyle:</strong></p>
<ul>
<li>Physical activity level</li>
<li>Smoking and alcohol consumption</li>
<li>Dietary features</li>
</ul>

<h4>Why is this needed?</h4>

<p>✓ AI considers your characteristics when analyzing documents<br>
✓ Recommendations become personalized to your profile<br>
✓ System warns about possible contraindications<br>
✓ Tracking metric dynamics considering your age and condition</p>

<h4>How to update profile?</h4>

<p>1. Go to "Profile" section<br>
2. Click "Edit" button<br>
3. Make changes<br>
4. Save data</p>

<h4>Privacy:</h4>

<p>All profile data is protected and used only to improve recommendation quality. We never share your information with third parties.</p>

<p><strong>💡 Tip:</strong> Update weight, medication, and disease data when changes occur — this will help AI provide more relevant recommendations.</p>
''',
        'uk': '''
<h4>Навіщо заповнювати профіль?</h4>

<p>Профіль — це основа для персоналізованих рекомендацій від AI. Чим більше PulseBook знає про вас, тим точніші відповіді та аналіз документів.</p>

<h4>Яку інформацію потрібно вказати?</h4>

<p><strong>Основні дані:</strong></p>
<ul>
<li>Ім'я</li>
<li>Рік народження</li>
<li>Стать</li>
<li>Зріст та вага</li>
</ul>

<p><strong>Медична інформація:</strong></p>
<ul>
<li>Хронічні захворювання</li>
<li>Алергії та непереносимості</li>
<li>Постійні медикаменти</li>
</ul>

<p><strong>Спосіб життя:</strong></p>
<ul>
<li>Рівень фізичної активності</li>
<li>Куріння та вживання алкоголю</li>
<li>Особливості харчування</li>
</ul>

<h4>Навіщо це потрібно?</h4>

<p>✓ AI враховує ваші особливості при аналізі документів<br>
✓ Рекомендації стають персоналізованими під ваш профіль<br>
✓ Система попереджає про можливі протипоказання<br>
✓ Відстеження динаміки показників з урахуванням вашого віку та стану</p>

<h4>Як оновити профіль?</h4>

<p>1. Перейдіть до розділу "Профіль"<br>
2. Натисніть кнопку "Редагувати"<br>
3. Внесіть зміни<br>
4. Збережіть дані</p>

<h4>Конфіденційність:</h4>

<p>Всі дані профілю захищені та використовуються тільки для покращення якості рекомендацій. Ми ніколи не передаємо вашу інформацію третім особам.</p>

<p><strong>💡 Порада:</strong> Оновлюйте дані про вагу, медикаменти та захворювання при змінах — це допоможе AI давати більш актуальні рекомендації.</p>
''',
        'de': '''
<h4>Warum das Profil ausfüllen?</h4>

<p>Das Profil ist die Grundlage für personalisierte KI-Empfehlungen. Je mehr PulseBook über Sie weiß, desto genauer die Antworten und Dokumentenanalyse.</p>

<h4>Welche Informationen müssen angegeben werden?</h4>

<p><strong>Basisdaten:</strong></p>
<ul>
<li>Name</li>
<li>Geburtsjahr</li>
<li>Geschlecht</li>
<li>Größe und Gewicht</li>
</ul>

<p><strong>Medizinische Informationen:</strong></p>
<ul>
<li>Chronische Krankheiten</li>
<li>Allergien und Unverträglichkeiten</li>
<li>Regelmäßige Medikamente</li>
</ul>

<p><strong>Lebensstil:</strong></p>
<ul>
<li>Körperliche Aktivitätsniveau</li>
<li>Rauchen und Alkoholkonsum</li>
<li>Ernährungsbesonderheiten</li>
</ul>

<h4>Warum ist das notwendig?</h4>

<p>✓ KI berücksichtigt Ihre Merkmale bei der Dokumentenanalyse<br>
✓ Empfehlungen werden auf Ihr Profil personalisiert<br>
✓ System warnt vor möglichen Kontraindikationen<br>
✓ Verfolgung der Metrikdynamik unter Berücksichtigung Ihres Alters und Zustands</p>

<h4>Wie aktualisiert man das Profil?</h4>

<p>1. Gehen Sie zum Abschnitt "Profil"<br>
2. Klicken Sie auf die Schaltfläche "Bearbeiten"<br>
3. Nehmen Sie Änderungen vor<br>
4. Daten speichern</p>

<h4>Privatsphäre:</h4>

<p>Alle Profildaten sind geschützt und werden nur zur Verbesserung der Empfehlungsqualität verwendet. Wir geben Ihre Informationen niemals an Dritte weiter.</p>

<p><strong>💡 Tipp:</strong> Aktualisieren Sie Gewichts-, Medikamenten- und Krankheitsdaten bei Änderungen — dies hilft der KI, relevantere Empfehlungen zu geben.</p>
'''
    },
    
    # ============================================
    # 6️⃣ БЕЗОПАСНОСТЬ
    # ============================================
    'faq_security_title': {
        'ru': '🔒 Безопасность',
        'en': '🔒 Security',
        'uk': '🔒 Безпека',
        'de': '🔒 Sicherheit'
    },
    'faq_security_content': {
        'ru': '''
<h4>Как PulseBook защищает ваши данные?</h4>

<p>Безопасность медицинских данных — наш главный приоритет. Мы используем передовые технологии защиты информации.</p>

<h4>Шифрование данных:</h4>

<p>✓ Все данные шифруются при передаче (SSL/TLS)<br>
✓ Документы хранятся в зашифрованном виде на серверах<br>
✓ Доступ к данным имеете только вы</p>

<h4>Соответствие стандартам:</h4>

<p>✓ <strong>HIPAA</strong> — американский стандарт защиты медицинских данных<br>
✓ <strong>GDPR</strong> — европейский регламент по защите персональных данных<br>
✓ <strong>SOC 2 Type II</strong> — международная сертификация безопасности</p>

<h4>Авторизация:</h4>

<ul>
<li>Вход через Google OAuth — надежная система аутентификации</li>
<li>Никто не имеет доступа к вашим данным без авторизации</li>
<li>Автоматический выход при длительной неактивности</li>
</ul>

<h4>Обработка данных AI:</h4>

<p>✓ AI анализирует данные в защищенной среде<br>
✓ Ваши документы не используются для обучения моделей<br>
✓ Вся информация остается конфиденциальной</p>

<h4>Контроль над данными:</h4>

<p>✓ Вы можете удалить любой документ в любое время<br>
✓ Полное удаление аккаунта и всех данных по запросу<br>
✓ Экспорт всех ваших данных в любой момент</p>

<p><strong>💡 Помните:</strong> Мы никогда не попросим вас отправить пароль или личные данные по email или в чате. Будьте бдительны!</p>
''',
        'en': '''
<h4>How does PulseBook protect your data?</h4>

<p>Medical data security is our top priority. We use advanced information protection technologies.</p>

<h4>Data encryption:</h4>

<p>✓ All data is encrypted during transmission (SSL/TLS)<br>
✓ Documents are stored encrypted on servers<br>
✓ Only you have access to the data</p>

<h4>Compliance with standards:</h4>

<p>✓ <strong>HIPAA</strong> — American standard for protecting medical data<br>
✓ <strong>GDPR</strong> — European regulation on personal data protection<br>
✓ <strong>SOC 2 Type II</strong> — international security certification</p>

<h4>Authorization:</h4>

<ul>
<li>Login via Google OAuth — reliable authentication system</li>
<li>No one has access to your data without authorization</li>
<li>Automatic logout after prolonged inactivity</li>
</ul>

<h4>AI data processing:</h4>

<p>✓ AI analyzes data in a secure environment<br>
✓ Your documents are not used for model training<br>
✓ All information remains confidential</p>

<h4>Data control:</h4>

<p>✓ You can delete any document at any time<br>
✓ Complete account and all data deletion on request<br>
✓ Export all your data at any time</p>

<p><strong>💡 Remember:</strong> We will never ask you to send passwords or personal data via email or chat. Stay vigilant!</p>
''',
        'uk': '''
<h4>Як PulseBook захищає ваші дані?</h4>

<p>Безпека медичних даних — наш головний пріоритет. Ми використовуємо передові технології захисту інформації.</p>

<h4>Шифрування даних:</h4>

<p>✓ Всі дані шифруються при передачі (SSL/TLS)<br>
✓ Документи зберігаються в зашифрованому вигляді на серверах<br>
✓ Доступ до даних маєте тільки ви</p>

<h4>Відповідність стандартам:</h4>

<p>✓ <strong>HIPAA</strong> — американський стандарт захисту медичних даних<br>
✓ <strong>GDPR</strong> — європейський регламент захисту персональних даних<br>
✓ <strong>SOC 2 Type II</strong> — міжнародна сертифікація безпеки</p>

<h4>Авторизація:</h4>

<ul>
<li>Вхід через Google OAuth — надійна система автентифікації</li>
<li>Ніхто не має доступу до ваших даних без авторизації</li>
<li>Автоматичний вихід при тривалій неактивності</li>
</ul>

<h4>Обробка даних AI:</h4>

<p>✓ AI аналізує дані в захищеному середовищі<br>
✓ Ваші документи не використовуються для навчання моделей<br>
✓ Вся інформація залишається конфіденційною</p>

<h4>Контроль над даними:</h4>

<p>✓ Ви можете видалити будь-який документ у будь-який час<br>
✓ Повне видалення акаунта та всіх даних на запит<br>
✓ Експорт всіх ваших даних у будь-який момент</p>

<p><strong>💡 Пам'ятайте:</strong> Ми ніколи не попросимо вас надіслати пароль або особисті дані електронною поштою або в чаті. Будьте пильні!</p>
''',
        'de': '''
<h4>Wie schützt PulseBook Ihre Daten?</h4>

<p>Medizinische Datensicherheit ist unsere oberste Priorität. Wir verwenden fortschrittliche Informationsschutztechnologien.</p>

<h4>Datenverschlüsselung:</h4>

<p>✓ Alle Daten werden während der Übertragung verschlüsselt (SSL/TLS)<br>
✓ Dokumente werden verschlüsselt auf Servern gespeichert<br>
✓ Nur Sie haben Zugriff auf die Daten</p>

<h4>Einhaltung von Standards:</h4>

<p>✓ <strong>HIPAA</strong> — amerikanischer Standard zum Schutz medizinischer Daten<br>
✓ <strong>GDPR</strong> — europäische Verordnung zum Schutz personenbezogener Daten<br>
✓ <strong>SOC 2 Type II</strong> — internationale Sicherheitszertifizierung</p>

<h4>Autorisierung:</h4>

<ul>
<li>Anmeldung über Google OAuth — zuverlässiges Authentifizierungssystem</li>
<li>Niemand hat ohne Autorisierung Zugriff auf Ihre Daten</li>
<li>Automatische Abmeldung nach längerer Inaktivität</li>
</ul>

<h4>KI-Datenverarbeitung:</h4>

<p>✓ KI analysiert Daten in einer sicheren Umgebung<br>
✓ Ihre Dokumente werden nicht für Modelltraining verwendet<br>
✓ Alle Informationen bleiben vertraulich</p>

<h4>Datenkontrolle:</h4>

<p>✓ Sie können jedes Dokument jederzeit löschen<br>
✓ Vollständige Löschung des Kontos und aller Daten auf Anfrage<br>
✓ Export aller Ihrer Daten jederzeit</p>

<p><strong>💡 Denken Sie daran:</strong> Wir werden Sie niemals bitten, Passwörter oder persönliche Daten per E-Mail oder Chat zu senden. Seien Sie wachsam!</p>
'''
    },
    
    # ============================================
    # 7️⃣ ПОДДЕРЖКА
    # ============================================
    'faq_support_title': {
        'ru': '💬 Поддержка',
        'en': '💬 Support',
        'uk': '💬 Підтримка',
        'de': '💬 Support'
    },
    'faq_support_content': {
        'ru': '''
<h4>Как получить помощь?</h4>

<p>Мы всегда готовы помочь вам разобраться с любыми вопросами по использованию PulseBook.</p>

<h4>Способы связи:</h4>

<p><strong>📧 Email поддержка:</strong> support@pulsebook.health<br>
Ответим в течение 24 часов (для Pro подписчиков — приоритетная обработка)</p>

<p><strong>💬 Чат поддержки:</strong><br>
Напишите в чат внутри платформы — наша команда ответит как можно быстрее</p>

<p><strong>🌐 FAQ раздел:</strong><br>
Большинство вопросов уже освещены в этом разделе — используйте поиск или просмотрите другие категории</p>

<h4>По каким вопросам можно обратиться?</h4>

<p>✓ Технические проблемы с загрузкой документов<br>
✓ Вопросы по тарифам и оплате<br>
✓ Помощь в настройке профиля<br>
✓ Проблемы с доступом к аккаунту<br>
✓ Предложения по улучшению сервиса</p>

<h4>Важно знать:</h4>

<p>⚠️ <strong>PulseBook — это информационный сервис, а не замена визита к врачу.</strong> AI-рекомендации носят справочный характер.</p>

<p>⚠️ <strong>При острых состояниях, сильной боли или ухудшении самочувствия — немедленно обратитесь к врачу или вызовите скорую помощь.</strong></p>

<p><strong>💡 Совет:</strong> Перед обращением в поддержку попробуйте найти ответ в FAQ — это быстрее и удобнее!</p>

<h4>Мы ценим ваши отзывы!</h4>

<p>Поделитесь своим опытом использования PulseBook — это поможет нам стать лучше и полезнее для вас.</p>
''',
        'en': '''
<h4>How to get help?</h4>

<p>We're always ready to help you with any questions about using PulseBook.</p>

<h4>Contact methods:</h4>

<p><strong>📧 Email support:</strong> support@pulsebook.health<br>
We'll respond within 24 hours (Pro subscribers get priority processing)</p>

<p><strong>💬 Support chat:</strong><br>
Write in the chat inside the platform — our team will respond as quickly as possible</p>

<p><strong>🌐 FAQ section:</strong><br>
Most questions are already covered in this section — use search or browse other categories</p>

<h4>What questions can you contact us about?</h4>

<p>✓ Technical issues with document uploads<br>
✓ Questions about plans and payment<br>
✓ Help setting up profile<br>
✓ Account access problems<br>
✓ Service improvement suggestions</p>

<h4>Important to know:</h4>

<p>⚠️ <strong>PulseBook is an information service, not a replacement for a doctor visit.</strong> AI recommendations are for reference only.</p>

<p>⚠️ <strong>For acute conditions, severe pain, or worsening health — immediately see a doctor or call emergency services.</strong></p>

<p><strong>💡 Tip:</strong> Before contacting support, try finding the answer in FAQ — it's faster and more convenient!</p>

<h4>We value your feedback!</h4>

<p>Share your experience using PulseBook — this helps us become better and more useful for you.</p>
''',
        'uk': '''
<h4>Як отримати допомогу?</h4>

<p>Ми завжди готові допомогти вам розібратися з будь-якими питаннями щодо використання PulseBook.</p>

<h4>Способи зв'язку:</h4>

<p><strong>📧 Email підтримка:</strong> support@pulsebook.health<br>
Відповімо протягом 24 годин (для Pro підписників — пріоритетна обробка)</p>

<p><strong>💬 Чат підтримки:</strong><br>
Напишіть у чат всередині платформи — наша команда відповість якомога швидше</p>

<p><strong>🌐 Розділ FAQ:</strong><br>
Більшість питань вже висвітлені в цьому розділі — використовуйте пошук або перегляньте інші категорії</p>

<h4>З яких питань можна звернутися?</h4>

<p>✓ Технічні проблеми із завантаженням документів<br>
✓ Питання щодо тарифів та оплати<br>
✓ Допомога в налаштуванні профілю<br>
✓ Проблеми з доступом до акаунта<br>
✓ Пропозиції щодо покращення сервісу</p>

<h4>Важливо знати:</h4>

<p>⚠️ <strong>PulseBook — це інформаційний сервіс, а не заміна візиту до лікаря.</strong> AI-рекомендації носять довідковий характер.</p>

<p>⚠️ <strong>При гострих станах, сильному болю або погіршенні самопочуття — негайно зверніться до лікаря або викличте швидку допомогу.</strong></p>

<p><strong>💡 Порада:</strong> Перед зверненням до підтримки спробуйте знайти відповідь у FAQ — це швидше та зручніше!</p>

<h4>Ми цінуємо ваші відгуки!</h4>

<p>Поділіться своїм досвідом використання PulseBook — це допоможе нам стати кращими та кориснішими для вас.</p>
''',
        'de': '''
<h4>Wie erhält man Hilfe?</h4>

<p>Wir sind immer bereit, Ihnen bei Fragen zur Nutzung von PulseBook zu helfen.</p>

<h4>Kontaktmethoden:</h4>

<p><strong>📧 Email-Support:</strong> support@pulsebook.health<br>
Wir antworten innerhalb von 24 Stunden (Pro-Abonnenten erhalten vorrangige Bearbeitung)</p>

<p><strong>💬 Support-Chat:</strong><br>
Schreiben Sie im Chat innerhalb der Plattform — unser Team antwortet so schnell wie möglich</p>

<p><strong>🌐 FAQ-Bereich:</strong><br>
Die meisten Fragen werden bereits in diesem Bereich behandelt — verwenden Sie die Suche oder durchsuchen Sie andere Kategorien</p>

<h4>Zu welchen Fragen können Sie uns kontaktieren?</h4>

<p>✓ Technische Probleme beim Hochladen von Dokumenten<br>
✓ Fragen zu Plänen und Zahlung<br>
✓ Hilfe beim Einrichten des Profils<br>
✓ Probleme mit dem Kontozugriff<br>
✓ Verbesserungsvorschläge für den Service</p>

<h4>Wichtig zu wissen:</h4>

<p>⚠️ <strong>PulseBook ist ein Informationsdienst, kein Ersatz für einen Arztbesuch.</strong> KI-Empfehlungen sind nur zur Information.</p>

<p>⚠️ <strong>Bei akuten Zuständen, starken Schmerzen oder Verschlechterung des Gesundheitszustands — suchen Sie sofort einen Arzt auf oder rufen Sie den Notdienst an.</strong></p>

<p><strong>💡 Tipp:</strong> Versuchen Sie vor dem Kontakt mit dem Support, die Antwort in den FAQ zu finden — es ist schneller und bequemer!</p>

<h4>Wir schätzen Ihr Feedback!</h4>

<p>Teilen Sie Ihre Erfahrungen mit PulseBook — dies hilft uns, besser und nützlicher für Sie zu werden.</p>
'''
    }
}


def get_faq_translation(key: str, lang: str = 'ru') -> str:
    """
    Получить перевод FAQ по ключу
    
    Args:
        key: Ключ перевода (например, 'faq_title')
        lang: Язык ('ru', 'en', 'uk', 'de')
    
    Returns:
        Переведенная строка или ключ, если перевод не найден
    """
    # Проверяем что язык поддерживается
    if lang not in ['ru', 'en', 'uk', 'de']:
        lang = 'ru'  # По умолчанию русский
    
    # Получаем перевод
    translation = FAQ_TRANSLATIONS.get(key, {})
    return translation.get(lang, key)