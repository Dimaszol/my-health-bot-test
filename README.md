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