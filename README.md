# 🧠 Health Assistant Bot

Телеграм-бот для анализа медицинских документов с использованием GPT-4, построенный на PostgreSQL и pgvector для векторного поиска.

## 🚀 Возможности

- 📄 Загрузка и анализ медицинских документов (PDF, DOCX, TXT, изображения)
- 🤖 Интеграция с OpenAI GPT-4o для медицинских консультаций
- 🔍 Векторный поиск по истории пользователя через PostgreSQL + pgvector
- 👤 Детальные профили пациентов с медицинской историей
- 💬 Автоматические сводки разговоров каждые 5 сообщений
- 💳 Система подписок и лимитов через Stripe
- 🖼️ Анализ медицинских изображений через Google Gemini
- 🌐 Мультиязычная поддержка (русский/украинский/английский)

## 🛠️ Технологический стек

- **Backend**: Python 3.8+, aiogram 3.x
- **База данных**: PostgreSQL с pgvector расширением
- **AI**: OpenAI GPT-4o, Google Gemini Vision
- **Платежи**: Stripe Integration
- **Деплой**: Готов для Docker/Kubernetes

## ⚙️ Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```env
# 🤖 Telegram
BOT_TOKEN=your_telegram_bot_token

# 🧠 OpenAI
OPENAI_API_KEY=your_openai_api_key

# 🗄️ PostgreSQL (Supabase)
DATABASE_URL=postgresql://user:password@host:port/database

# 💳 Stripe (опционально)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# 🔍 Gemini Vision (опционально)
GEMINI_API_KEY=your_gemini_api_key
```

## 🗄️ Структура базы данных (PostgreSQL)

### Основные таблицы:
- **users** - профили пользователей и медицинская анкета
- **documents** - загруженные медицинские документы
- **document_vectors** - векторные эмбеддинги для поиска
- **chat_history** - история сообщений
- **conversation_summary** - автоматические сводки разговоров
- **user_limits** - лимиты и подписки пользователей
- **transactions** - история платежей через Stripe

## 🚀 Установка и запуск

1. **Клонирование:**
```bash
git clone https://github.com/your_username/health-assistant-bot.git
cd health-assistant-bot
```

2. **Виртуальное окружение:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Зависимости:**
```bash
pip install -r requirements.txt
```

4. **Конфигурация:**
- Создайте PostgreSQL базу (рекомендуется Supabase)
- Скопируйте `.env.example` в `.env`
- Заполните все необходимые API ключи

5. **Запуск:**
```bash
python main.py
```

## 📦 Основные модули

- `main.py` - точка входа и Telegram handlers
- `db_postgresql.py` - работа с PostgreSQL
- `vector_db_postgresql.py` - векторный поиск через pgvector
- `gpt.py` - интеграция с OpenAI API
- `upload.py` - обработка загруженных файлов
- `subscription_manager.py` - система подписок и лимитов
- `error_handler.py` - централизованная обработка ошибок

## 🛡️ Безопасность

- ✅ Секретные ключи в `.env` (исключены из Git)
- ✅ Валидация загружаемых файлов
- ✅ Rate limiting для предотвращения злоупотреблений
- ✅ Безопасная работа с пользовательскими данными
- ✅ Логирование всех операций

## 🔄 Миграция с предыдущих версий

Проект перенесен с SQLite/ChromaDB на PostgreSQL/pgvector для лучшей масштабируемости.

## 🎯 Планы развития

- 🌐 Web-интерфейс (FastAPI + React)
- 📱 Мобильное приложение
- 🐳 Docker контейнеризация
- ☁️ Облачное развертывание
- 📊 Analytics dashboard
- 🔗 API для интеграций

## 📄 Лицензия

MIT License - см. файл LICENSE

## 🤝 Контрибуция

1. Fork проекта
2. Создайте feature branch
3. Commit изменения
4. Push в branch
5. Создайте Pull Request