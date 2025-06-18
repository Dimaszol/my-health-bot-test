# Исправленная интеграция Gemini для медицинского анализа

import os  # ✅ ДОБАВЛЕН ИМПОРТ
import google.generativeai as genai
import asyncio
from PIL import Image
from typing import Tuple

class GeminiMedicalAnalyzer:
    """Анализатор медицинских изображений через Gemini API"""
    
    def __init__(self):
        """Инициализация с API ключом"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY не найден в .env файле!")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')  # ✅ Рекомендация Gemini для медицины
        print("✅ Gemini 1.5 Pro Latest инициализирован (оптимизирован для медицины)")
    
    async def analyze_medical_image(self, image_path: str, lang: str = "ru", custom_prompt: str = None) -> Tuple[str, str]:
        """
        Анализирует медицинское изображение
        
        Args:
            image_path: Путь к изображению
            lang: Язык ответа (ru, uk, en)
            custom_prompt: Кастомный промпт (если нужен)
            
        Returns:
            Tuple[analysis_text, error_message]
        """
        try:
            print(f"\n🧠 АНАЛИЗ ЧЕРЕЗ GEMINI:")
            print(f"📁 Файл: {image_path}")
            print(f"🌐 Язык: {lang}")
            
            # Проверяем существование файла
            if not os.path.exists(image_path):
                return "", f"Файл не найден: {image_path}"
            
            # Загружаем изображение
            image = Image.open(image_path)
            print(f"🖼️ Размер изображения: {image.size}")
            
            # Используем медицинский промпт
            prompt = custom_prompt or self._get_medical_prompt(lang)
            
            print(f"⏳ Отправляем запрос...")
            
            # Генерируем ответ асинхронно
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,        # Низкая для медицинской точности
                    max_output_tokens=4000, # Достаточно для детального анализа
                    candidate_count=1
                )
            )
            
            analysis = response.text
            
            print("\n" + "="*80)
            print("🤖 ОТВЕТ GEMINI:")
            print("="*80)
            print(analysis)
            print("="*80 + "\n")
            
            return analysis, ""
            
        except Exception as e:
            error_msg = f"Ошибка Gemini: {str(e)}"
            print(f"❌ {error_msg}")
            return "", error_msg
    
    def _get_medical_prompt(self, lang: str) -> str:
        """Медицинский промпт для анализа изображений (пока только русский)"""
        
        return """Ты опытный врач-диагност. Анализируй медицинские изображения профессионально и детально.

Проанализируй это медицинское изображение как врач:

1. **Тип исследования** - что это (ЭКГ, ЭЭГ, рентген, МРТ, УЗИ, анализы и т.д.)?

2. **Технические данные** - видимые параметры пациента и настройки

3. **Детальные находки** - что конкретно видно, измерения, показатели

4. **Патологические изменения** - отклонения от нормы, если есть

5. **Диагностическое заключение** - что это означает клинически

6. **Рекомендации** - что делать дальше, к какому врачу обратиться

Будь максимально конкретным и профессиональным. Укажи если нужна консультация специалиста."""

# ✅ ИСПРАВЛЕННАЯ функция для замены GPT Vision
async def send_to_gemini_vision(image_path: str, lang: str = "ru", prompt: str = None) -> Tuple[str, str]:
    """
    Замена send_to_gpt_vision на Gemini
    
    Args:
        image_path: Путь к изображению
        lang: Язык ответа
        prompt: Кастомный промпт
        
    Returns:
        Tuple[analysis_result, error_message]
    """
    try:
        analyzer = GeminiMedicalAnalyzer()
        return await analyzer.analyze_medical_image(image_path, lang, prompt)
    except Exception as e:
        return "", f"Ошибка анализа изображения: {str(e)}"

# ✅ ИСПРАВЛЕННАЯ комбинированная функция
async def analyze_medical_image_smart(image_path: str, lang: str = "ru", prompt: str = None) -> Tuple[str, str]:
    """
    Умная функция анализа: сначала Gemini, потом fallback (если нужен)
    
    Args:
        image_path: Путь к изображению
        lang: Язык ответа
        prompt: Кастомный промпт
        
    Returns:
        Tuple[analysis_result, error_message]
    """
    
    print("🎯 Пробуем Gemini (основной метод)...")
    
    # Сначала пробуем Gemini
    try:
        result, error = await send_to_gemini_vision(image_path, lang, prompt)
        if result and not error:
            print("✅ Gemini успешно проанализировал")
            return result, ""
        else:
            print(f"⚠️ Gemini вернул ошибку: {error}")
    except Exception as e:
        print(f"⚠️ Gemini недоступен: {e}")
    
    # Если Gemini не сработал, возвращаем информативную ошибку
    print("❌ Анализ изображения временно недоступен")
    error_msg = "Сервис анализа изображений временно недоступен. Попробуйте позже."
    return "", error_msg

# Для быстрого тестирования
async def test_gemini_analysis(image_path: str, lang: str = "ru"):
    """Быстрый тест Gemini анализа"""
    try:
        print(f"🧪 Тестируем анализ изображения: {image_path}")
        
        result, error = await send_to_gemini_vision(image_path, lang)
        
        if error:
            print(f"❌ Ошибка: {error}")
            return None
        else:
            print("✅ Анализ успешно завершен!")
            print("\n📋 РЕЗУЛЬТАТ:")
            print("-" * 50)
            print(result)
            print("-" * 50)
            return result
            
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        return None

# Функция для проверки доступных моделей
async def list_available_models():
    """Показывает список доступных моделей Gemini"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY не найден в .env файле!")
            return []
            
        genai.configure(api_key=api_key)
        
        print("🔍 Проверяем доступные модели Gemini...")
        models = genai.list_models()
        
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name)
                print(f"✅ {model.name}")
        
        return available_models
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка моделей: {e}")
        return []

# Пример использования
if __name__ == "__main__":
    async def main():
        # Сначала проверяем доступные модели
        await list_available_models()
        
        # Тест с примером изображения
        test_image = "test_medical_image.jpg"  # Замените на реальный путь
        
        if os.path.exists(test_image):
            await test_gemini_analysis(test_image, "ru")
        else:
            print("❌ Тестовое изображение не найдено")
            print("💡 Создайте файл test_medical_image.jpg для тестирования")
    
    # Запуск теста
    # asyncio.run(main())