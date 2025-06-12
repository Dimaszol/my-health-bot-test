Структура БД: 

📋 Таблица: users
  - user_id (INTEGER)
  - name (TEXT)
  - created_at (DATETIME)
  - birth_year (INTEGER)
  - gender (TEXT)
  - height_cm (INTEGER)
  - weight_kg (REAL)
  - chronic_conditions (TEXT)
  - medications (TEXT)
  - allergies (TEXT)
  - smoking (TEXT)
  - alcohol (TEXT)
  - physical_activity (TEXT)
  - family_history (TEXT)
  - last_updated (DATETIME)
  - language (TEXT)

📋 Таблица: sqlite_sequence
  - name ()
  - seq ()

📋 Таблица: chat_history
  - id (INTEGER)
  - user_id (INTEGER)
  - role (TEXT)
  - message (TEXT)
  - timestamp (DATETIME)

📋 Таблица: conversation_summary
  - id (INTEGER)
  - user_id (INTEGER)
  - summary_text (TEXT)
  - last_message_id (INTEGER)
  - updated_at (DATETIME)

📋 Таблица: documents
  - id (INTEGER)
  - user_id (INTEGER)
  - title (TEXT)
  - file_path (TEXT)
  - file_type (TEXT)
  - raw_text (TEXT)
  - summary (TEXT)
  - confirmed (BOOLEAN)
  - uploaded_at (DATETIME)
  - vector_id (TEXT)

📋 Таблица: medications
  - id (INTEGER)
  - user_id (INTEGER)
  - name (TEXT)
  - time (TEXT)
  - label (TEXT)

📋 Таблица: user_limits
  - user_id (INTEGER)
  - documents_left (INTEGER)
  - gpt4o_queries_left (INTEGER)
  - subscription_type (TEXT)
  - subscription_expires_at (DATETIME)
  - created_at (DATETIME)
  - updated_at (DATETIME)

📋 Таблица: transactions
  - id (INTEGER)
  - user_id (INTEGER)
  - stripe_session_id (TEXT)
  - amount_usd (REAL)
  - package_type (TEXT)
  - status (TEXT)
  - payment_method (TEXT)
  - created_at (DATETIME)
  - completed_at (DATETIME)
  - package_id (TEXT)
  - documents_granted (INTEGER)
  - queries_granted (INTEGER)

📋 Таблица: subscription_packages
  - id (TEXT)
  - name (TEXT)
  - price_usd (REAL)
  - documents_included (INTEGER)
  - gpt4o_queries_included (INTEGER)
  - type (TEXT)
  - is_active (BOOLEAN)
  - created_at (DATETIME)

📋 Таблица: user_subscriptions
  - id (INTEGER)
  - user_id (INTEGER)
  - stripe_subscription_id (TEXT)
  - package_id (TEXT)
  - status (TEXT)
  - created_at (DATETIME)
  - cancelled_at (DATETIME)

# 🧠 Health Assistant Bot

Телеграм-бот, который анализирует медицинские документы, извлекает важную информацию и позволяет пользователю задавать вопросы своему "виртуальному врачу", powered by GPT-4.

## 🚀 Возможности

- 📄 Загрузка PDF, DOCX, TXT и других медицинских файлов
- 🤖 Интеграция с OpenAI GPT-4 и GPT-4o-mini
- 🔍 Векторный поиск по истории пользователя (ChromaDB)
- 🧾 Профили пациентов, анализ истории, интерпретация отчётов
- 🧠 Поддержка персонализированных ответов на медицинские вопросы
- 💳 Подписка на расширенные функции (GPT-4)

## 🛠️ Установка

1. Клонируй репозиторий:
```bash
git clone https://github.com/your_username/your_repo_name.git
cd your_repo_name
Установи зависимости:

bash
Копировать
Редактировать
pip install -r requirements.txt
Создай файл .env на основе .env.example и добавь свои ключи.

Запусти бота:

bash
Копировать
Редактировать
python main.py
⚙️ .env переменные
Создай .env с такими переменными:

env
Копировать
Редактировать
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
CHROMA_OPENAI_API_KEY=your_chroma_api_key
📦 Структура проекта
main.py — запуск бота

upload.py — загрузка и разбор файлов

gpt.py — вызов GPT-4 / GPT-4o

db.py и db_pool.py — работа с SQLite

vector_db.py и vector_utils.py — ChromaDB для поиска

registration.py, documents.py — работа с пользователями и файлами

error_handler.py — централизованная обработка ошибок

🛡️ Безопасность
Токены и ключи не хранятся в репозитории

Базы и логи исключены через .gitignore

Валидация файлов и ограничение расширений