# garmin_analyzer.py - AI анализ данных здоровья от Garmin

import logging
import json
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List, Any

from garmin_connector import garmin_connector
from db_postgresql import get_db_connection, release_db_connection, get_user_language
from gpt import ask_doctor_gemini
from save_utils import format_user_profile

logger = logging.getLogger(__name__)

# ================================
# ОСНОВНОЙ КЛАСС АНАЛИЗАТОРА
# ================================

class GarminAnalyzer:
    """Класс для AI анализа данных здоровья от Garmin"""
    
    def __init__(self):
        pass
    
    async def create_health_analysis(self, user_id: int, daily_data: Dict) -> Optional[Dict]:
        """Создать полный анализ здоровья на основе данных Garmin"""
        try:
            logger.info(f"🧠 Начинаю AI анализ для пользователя {user_id}")
            
            # Получаем язык пользователя
            lang = await get_user_language(user_id)
            
            # Шаг 1: Собираем исторические данные за неделю
            historical_data = await self._get_historical_data(user_id, days=7)
            
            # Шаг 2: Получаем медицинский профиль пользователя
            user_profile = await self._get_user_medical_profile(user_id)
            
            # Шаг 3: Формируем структурированные данные
            analysis_context = await self._prepare_analysis_context(
                daily_data, historical_data, user_profile, lang
            )
            
            # Шаг 4: Создаем AI анализ с помощью GPT-5
            ai_response = await self._generate_ai_analysis(analysis_context, lang)
            
            if not ai_response:
                logger.error(f"❌ AI не смог создать анализ для {user_id}")
                return None
            
            # Шаг 5: Парсим и структурируем ответ
            analysis_result = await self._parse_ai_response(ai_response, daily_data)
            
            # Шаг 6: Сохраняем анализ в БД
            saved = await self._save_analysis_to_db(user_id, analysis_result)
            
            if saved:
                logger.info(f"✅ AI анализ для пользователя {user_id} создан и сохранен")
                return analysis_result
            else:
                logger.error(f"❌ Не удалось сохранить анализ для {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания анализа для {user_id}: {e}")
            return None

    async def _get_historical_data(self, user_id: int, days: int = 7) -> List[Dict]:
        """
        Получить исторические данные ИСКЛЮЧАЯ последние 1 день
       
       
        """
        try:
            conn = await get_db_connection()
            
           
            end_date = date.today() - timedelta(days=1)      
            start_date = date.today() - timedelta(days=days)  
            
            rows = await conn.fetch("""
                SELECT * FROM garmin_daily_data 
                WHERE user_id = $1 
                AND data_date >= $2
                AND data_date <= $3
                ORDER BY data_date DESC
            """, user_id, start_date, end_date)
            
            await release_db_connection(conn)
            
            # Преобразуем в список словарей
            historical_data = []
            for row in rows:
                row_dict = dict(row)
                # Преобразуем дату в СТРОКУ (другие методы ожидают строку)
                if isinstance(row_dict['data_date'], date):
                    row_dict['data_date'] = row_dict['data_date'].strftime('%Y-%m-%d')
                historical_data.append(row_dict)
            
            logger.info(f"📊 Получено {len(historical_data)} дней исторических данных")
            return historical_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения исторических данных: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return []

    async def _get_user_medical_profile(self, user_id: int) -> Dict:
        """Получить медицинский профиль пользователя"""
        try:
            profile_text = await format_user_profile(user_id)
            
            # 🔧 ИСПРАВЛЕНИЕ: Используем asyncpg подход
            conn = await get_db_connection()
            
            result = await conn.fetchrow("""
                SELECT medications FROM users WHERE user_id = $1
            """, user_id)
            
            await release_db_connection(conn)
            
            medications = result['medications'] if result and result['medications'] else "Не принимает лекарства"
            
            return {
                'profile_text': profile_text,
                'medications': medications
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения медицинского профиля: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return {'profile_text': 'Профиль не заполнен', 'medications': 'Не указаны'}
        
    async def _get_last_analysis(self, user_id: int) -> Optional[str]:
        """Получить текст последнего анализа для контекста"""
        try:
            conn = await get_db_connection()
            
            # Получаем последний анализ (не сегодняшний)
            last_analysis = await conn.fetchrow("""
                SELECT analysis_date, analysis_text, recommendations
                FROM garmin_analysis_history
                WHERE user_id = $1 
                AND analysis_date < CURRENT_DATE
                ORDER BY analysis_date DESC
                LIMIT 1
            """, user_id)
            
            await release_db_connection(conn)
            
            if not last_analysis:
                return None
                
            # Форматируем для промпта
            date_str = last_analysis['analysis_date'].strftime('%Y-%m-%d')
            text = last_analysis['analysis_text']
            
            # НОВАЯ ЛОГИКА ОБРЕЗКИ: первые 1000 + последние 500 символов
            if len(text) > 1500:
                # Берем начало (общая оценка, ключевые наблюдения)
                beginning = text[:1000]
                
                # Берем конец (рекомендации)
                ending = text[-500:]
                
                # Объединяем с разделителем
                text = f"{beginning}\n\n[...]\n\n{ending}"
            
            formatted = f"""📅 Дата: {date_str}

    {text}"""
            
            return formatted
            
        except Exception as e:
            logger.error(f"Ошибка получения последнего анализа: {e}")
            return None

    async def _prepare_analysis_context(self, daily_data: Dict, historical_data: List[Dict], 
                                  user_profile: Dict, lang: str) -> Dict:
        """Подготовить контекст для AI анализа"""
        
        # Форматируем данные за текущий день
        current_day_summary = self._format_current_day_data(daily_data)
        
        # Форматируем исторические данные ПОДРОБНО (день за днем)
        historical_summary = self._format_historical_data(historical_data)
        
        # НОВОЕ: Получаем последний анализ
        user_id = daily_data.get('user_id')
        last_analysis = await self._get_last_analysis(user_id) if user_id else None
        
        return {
            'language': lang,
            'analysis_date': daily_data.get('data_date', date.today() - timedelta(days=1)),
            'user_profile': user_profile,
            'current_day': current_day_summary,
            'historical_data': historical_summary,
            'last_analysis': last_analysis  # НОВОЕ ПОЛЕ
        }

    def _calculate_trends(self, current: Dict, historical: List[Dict]) -> Dict:
        """Вычислить тренды показателей здоровья"""
        trends = {}
        
        try:
            if len(historical) < 2:
                return {
                    'sleep_trend': 'insufficient_data',
                    'activity_trend': 'insufficient_data', 
                    'stress_trend': 'insufficient_data',
                    'recovery_trend': 'insufficient_data'
                }
            
            # Тренд сна (сравниваем последние 3 дня с предыдущими 3)
            recent_sleep = []
            older_sleep = []
            
            for i, day in enumerate(historical):
                if day.get('sleep_duration_minutes'):
                    if i < 3:
                        recent_sleep.append(day['sleep_duration_minutes'])
                    elif i < 6:
                        older_sleep.append(day['sleep_duration_minutes'])
            
            if recent_sleep and older_sleep:
                recent_avg = sum(recent_sleep) / len(recent_sleep)
                older_avg = sum(older_sleep) / len(older_sleep)
                
                if recent_avg > older_avg + 30:  # Больше на 30 минут
                    trends['sleep_trend'] = 'improving'
                elif recent_avg < older_avg - 30:
                    trends['sleep_trend'] = 'declining'
                else:
                    trends['sleep_trend'] = 'stable'
            
            # Аналогично для других показателей
            trends.update(self._calculate_activity_trend(historical))
            trends.update(self._calculate_stress_trend(historical))
            trends.update(self._calculate_recovery_trend(historical))
            
            return trends
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета трендов: {e}")
            return {'sleep_trend': 'unknown', 'activity_trend': 'unknown', 
                   'stress_trend': 'unknown', 'recovery_trend': 'unknown'}

    def _calculate_activity_trend(self, historical: List[Dict]) -> Dict:
        """Вычислить тренд активности"""
        recent_steps = []
        older_steps = []
        
        for i, day in enumerate(historical):
            if day.get('steps'):
                if i < 3:
                    recent_steps.append(day['steps'])
                elif i < 6:
                    older_steps.append(day['steps'])
        
        if recent_steps and older_steps:
            recent_avg = sum(recent_steps) / len(recent_steps)
            older_avg = sum(older_steps) / len(older_steps)
            
            if recent_avg > older_avg * 1.1:  # Больше на 10%
                return {'activity_trend': 'improving'}
            elif recent_avg < older_avg * 0.9:
                return {'activity_trend': 'declining'}
            else:
                return {'activity_trend': 'stable'}
        
        return {'activity_trend': 'insufficient_data'}

    def _calculate_stress_trend(self, historical: List[Dict]) -> Dict:
        """Вычислить тренд стресса"""
        recent_stress = []
        older_stress = []
        
        for i, day in enumerate(historical):
            if day.get('stress_avg'):
                if i < 3:
                    recent_stress.append(day['stress_avg'])
                elif i < 6:
                    older_stress.append(day['stress_avg'])
        
        if recent_stress and older_stress:
            recent_avg = sum(recent_stress) / len(recent_stress)
            older_avg = sum(older_stress) / len(older_stress)
            
            if recent_avg < older_avg - 10:  # Стресс снизился
                return {'stress_trend': 'improving'}
            elif recent_avg > older_avg + 10:
                return {'stress_trend': 'declining'}
            else:
                return {'stress_trend': 'stable'}
        
        return {'stress_trend': 'insufficient_data'}

    def _calculate_recovery_trend(self, historical: List[Dict]) -> Dict:
        """Вычислить тренд восстановления (Body Battery)"""
        recent_recovery = []
        older_recovery = []
        
        for i, day in enumerate(historical):
            if day.get('body_battery_max'):
                if i < 3:
                    recent_recovery.append(day['body_battery_max'])
                elif i < 6:
                    older_recovery.append(day['body_battery_max'])
        
        if recent_recovery and older_recovery:
            recent_avg = sum(recent_recovery) / len(recent_recovery)
            older_avg = sum(older_recovery) / len(older_recovery)
            
            if recent_avg > older_avg + 5:  # Body Battery улучшается
                return {'recovery_trend': 'improving'}
            elif recent_avg < older_avg - 5:
                return {'recovery_trend': 'declining'}
            else:
                return {'recovery_trend': 'stable'}
        
        return {'recovery_trend': 'insufficient_data'}

    def _format_current_day_data(self, daily_data: Dict) -> str:
        """
        Форматировать данные текущего дня для AI в JSON формате
        
        НОВАЯ ЛОГИКА:
        - Передаём ВСЕ непустые поля (не null)
        - Исключаем только технические поля (id, user_id, sync_timestamp, idx)
        - Формат: чистый JSON для удобства AI
        """
        try:
            # Технические поля которые не нужны для анализа
            exclude_fields = {
                'id', 'idx', 'user_id', 'sync_timestamp', 
                'data_quality', 'activities_data'  # JSON поля исключаем
            }
            
            # Фильтруем: убираем технические поля и null значения
            filtered_data = {}
            for key, value in daily_data.items():
                if key not in exclude_fields and value is not None:
                    filtered_data[key] = value
            
            if not filtered_data:
                return "Недостаточно данных"
            
            # Форматируем в красивый JSON
            json_str = json.dumps(filtered_data, ensure_ascii=False, indent=2)
            
            return f"```json\n{json_str}\n```"
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования текущего дня: {e}")
            return "Ошибка обработки данных"

    def _format_historical_data(self, historical: List[Dict]) -> str:
        """
        Форматировать исторические данные для AI в JSON формате
        
        НОВАЯ ЛОГИКА:
        - Передаём историю ДЕНЬ ЗА ДНЁМ в виде массива JSON объектов
        - Каждый день содержит ВСЕ непустые поля
        - Исключаем только технические поля
        - Сортируем от старых дат к новым (хронологический порядок)
        """
        try:
            if not historical:
                return "Исторических данных нет"
            
            # Технические поля которые не нужны для анализа
            exclude_fields = {
                'id', 'idx', 'user_id', 'sync_timestamp',
                'data_quality', 'activities_data'
            }
            
            # Сортируем от старых к новым (для хронологии)
            sorted_history = sorted(
                historical, 
                key=lambda x: x.get('data_date', '1970-01-01')
            )
            
            # Фильтруем каждый день
            filtered_days = []
            for day in sorted_history:
                filtered_day = {}
                for key, value in day.items():
                    if key not in exclude_fields and value is not None:
                        filtered_day[key] = value
                
                if filtered_day:  # Добавляем только если есть данные
                    filtered_days.append(filtered_day)
            
            if not filtered_days:
                return "Недостаточно исторических данных"
            
            # Форматируем в красивый JSON массив
            json_str = json.dumps(filtered_days, ensure_ascii=False, indent=2)
            
            return f"```json\n{json_str}\n```"
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования исторических данных: {e}")
            return "Ошибка обработки данных"

    def _assess_data_quality(self, daily_data: Dict, historical: List[Dict]) -> str:
        """Оценить качество данных"""
        quality_scores = []
        
        # Проверяем наличие основных показателей
        if daily_data.get('sleep_duration_minutes'):
            quality_scores.append(1)
        if daily_data.get('steps'):
            quality_scores.append(1) 
        if daily_data.get('resting_heart_rate'):
            quality_scores.append(1)
        if daily_data.get('stress_avg'):
            quality_scores.append(1)
        if daily_data.get('body_battery_max'):
            quality_scores.append(1)
        
        quality_percent = (sum(quality_scores) / 5) * 100
        
        if quality_percent >= 80:
            return "excellent"
        elif quality_percent >= 60:
            return "good"
        elif quality_percent >= 40:
            return "fair"
        else:
            return "poor"

    async def _generate_ai_analysis(self, context: Dict, lang: str) -> Optional[str]:
        """Генерировать AI анализ с помощью GPT-5"""
        try:
            system_prompt = self._build_system_prompt(lang)
            user_prompt = self._build_user_prompt(context)
            
            # Используем функцию ask_doctor_gemini (GPT-5) для анализа
            ai_response = await ask_doctor_gemini(
                system_prompt=system_prompt,
                full_prompt=user_prompt,
                lang=lang
            )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI анализа: {e}")
            return None

    def _build_system_prompt(self, lang: str) -> str:
        """Построить system prompt для AI анализа (оптимизированная версия)"""
        
        # Языковые инструкции
        lang_instructions = {
            'ru': 'КРИТИЧЕСКИ ВАЖНО: Отвечай ТОЛЬКО на русском языке.',
            'uk': 'КРИТИЧНО ВАЖЛИВО: Відповідай ТІЛЬКИ українською мовою.',
            'en': 'CRITICAL: Respond ONLY in English.',
            'de': 'KRITISCH WICHTIG: Antworten Sie NUR auf Deutsch.'
        }
        
        lang_instruction = lang_instructions.get(lang, lang_instructions['ru'])
        
        return f"""{lang_instruction}

    Ты опытный врач-терапевт, который ведет долгосрочное медицинское наблюдение за пациентами через данные с умных часов.

    🎯 ТВОЯ РОЛЬ:
    • Анализируешь данные здоровья (сон, активность, стресс, восстановление)
    • Отслеживаешь динамику показателей день за днем
    • Даешь персонализированные рекомендации
    • Поддерживаешь мотивацию пациента

    ⚠️ ОБЯЗАТЕЛЬНЫЕ ПРИНЦИПЫ:
    • Твой ответ должен быть МАКСИМУМ 3000 символов (включая эмодзи)
    • Анализируй показатели КОМПЛЕКСНО - ищи связи между сном, стрессом, активностью
    • Учитывай медицинский профиль пациента и принимаемые лекарства
    • Сравнивай с нормами для возраста и пола
    • Будь КОНКРЕТНЫМ: не "больше спать", а "ложиться в 22:30"
    • ХВАЛИ прогресс - это мотивирует пациента
    • При отклонениях от нормы - рекомендуй обратиться к врачу

    📋 СТРУКТУРА ТВОЕГО ОТВЕТА:
    1. Оценка выполнения предыдущих рекомендаций (если были) - 2-3 предложения
    2. Динамика за неделю - выявленные тренды и паттерны - 3-4 предложения
    3. Анализ текущего дня - что хорошо, что требует внимания - 2-3 предложения
    4. Конкретные рекомендации на сегодня и ближайшую неделю - 4-5 пунктов

    💡 СТИЛЬ ОБЩЕНИЯ:
    Дружелюбный, поддерживающий, профессиональный. Как врач, который знает своего пациента и искренне заботится о его здоровье."""

    def _build_user_prompt(self, context: Dict) -> str:
        """Построить user prompt с данными для анализа (НОВАЯ ВЕРСИЯ)"""
        
        analysis_date = context['analysis_date']
        if isinstance(analysis_date, date):
            date_str = analysis_date.strftime('%Y-%m-%d')
        else:
            date_str = str(analysis_date)
        
        # Базовые блоки
        prompt_parts = [
            "МЕДИЦИНСКИЙ АНАЛИЗ ДАННЫХ ЗДОРОВЬЯ",
            f"\n📅 ДАТА АНАЛИЗА: {date_str}",
            f"\n👤 МЕДИЦИНСКИЙ ПРОФИЛЬ ПАЦИЕНТА:\n{context['user_profile']['profile_text']}",
            f"\n💊 ПРИНИМАЕМЫЕ ЛЕКАРСТВА:\n{context['user_profile']['medications']}",
            f"\n📊 ДАННЫЕ ЗА ТЕКУЩИЙ ДЕНЬ:\n{context['current_day']}",
            f"\n📈 ДАННЫЕ ЗА ПРЕДЫДУЩИЕ 7 ДНЕЙ:\n{context['historical_data']}"
        ]
        
        # НОВОЕ: Добавляем последний анализ если есть
        if context.get('last_analysis'):
            prompt_parts.append(f"\n📋 ПРЕДЫДУЩИЙ АНАЛИЗ И РЕКОМЕНДАЦИИ:\n{context['last_analysis']}")
        
        # Задание для AI
        if context.get('last_analysis'):
            task = """
    ЗАДАНИЕ:
    Ты продолжаешь медицинское наблюдение за пациентом. 

    1. Посмотри на ПРЕДЫДУЩИЙ АНАЛИЗ - какие рекомендации ты давал
    2. Проанализируй ДАННЫЕ ЗА 7 ДНЕЙ - как менялись показатели, есть ли тренды
    3. Оцени ТЕКУЩИЙ ДЕНЬ - выполнил ли пациент рекомендации, улучшились ли показатели
    4. Дай НОВЫЕ РЕКОМЕНДАЦИИ с учетом динамики

    ВАЖНО: 
    - Отметь выполнение/невыполнение предыдущих рекомендаций
    - Похвали за улучшения показателей
    - Если тренд негативный - мягко укажи на это и скорректируй рекомендации
    - Учитывай медицинский профиль и лекарства

    Ответ структурируй с эмодзи, дружелюбно и конструктивно."""
        else:
            task = """
    ЗАДАНИЕ:
    Это первый анализ для пациента.

    1. Проанализируй данные за 7 дней - выяви тренды и паттерны
    2. Оцени текущее состояние здоровья
    3. Дай персональные рекомендации с учетом медицинского профиля

    Ответ структурируй с эмодзи, дружелюбно и понятно."""
        
        prompt_parts.append(task)
        
        return "\n".join(prompt_parts)

    async def _parse_ai_response(self, ai_response: str, daily_data: Dict) -> Dict:
        """Парсить и структурировать ответ от AI"""
        try:
            # Вычисляем общий балл здоровья на основе данных
            health_score = self._calculate_health_score(daily_data)
            
            # Извлекаем тренды из данных (базовая логика)
            trends = self._extract_basic_trends(daily_data)
            
            # Формируем структурированный результат
            analysis_result = {
                'analysis_date': daily_data.get('data_date', date.today() - timedelta(days=1)),
                'analysis_text': ai_response,
                'health_score': health_score,
                'recommendations': self._extract_recommendations(ai_response),
                'sleep_trend': trends.get('sleep_trend', 'stable'),
                'activity_trend': trends.get('activity_trend', 'stable'),
                'stress_trend': trends.get('stress_trend', 'stable'),
                'recovery_trend': trends.get('recovery_trend', 'stable'),
                'gpt_model_used': 'gpt-5-chat-latest',
                'created_at': datetime.now()
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга AI ответа: {e}")
            return {
                'analysis_date': daily_data.get('data_date', date.today() - timedelta(days=1)),
                'analysis_text': ai_response,
                'health_score': 50.0,
                'recommendations': "Продолжайте следить за здоровьем",
                'created_at': datetime.now()
            }

    def _calculate_health_score(self, daily_data: Dict) -> float:
        """Вычислить общий балл здоровья (0-100)"""
        try:
            score_components = []
            
            # Сон (30% от общего балла)
            if daily_data.get('sleep_duration_minutes'):
                sleep_hours = daily_data['sleep_duration_minutes'] / 60
                if 7 <= sleep_hours <= 9:
                    sleep_score = 100
                elif 6 <= sleep_hours <= 10:
                    sleep_score = 80
                elif 5 <= sleep_hours <= 11:
                    sleep_score = 60
                else:
                    sleep_score = 40
                score_components.append(sleep_score * 0.3)
            
            # Активность (25% от общего балла)
            if daily_data.get('steps'):
                steps = daily_data['steps']
                if steps >= 10000:
                    activity_score = 100
                elif steps >= 7500:
                    activity_score = 80
                elif steps >= 5000:
                    activity_score = 60
                else:
                    activity_score = 40
                score_components.append(activity_score * 0.25)
            
            # Стресс (20% от общего балла)
            if daily_data.get('stress_avg'):
                stress = daily_data['stress_avg']
                if stress <= 25:
                    stress_score = 100
                elif stress <= 50:
                    stress_score = 80
                elif stress <= 75:
                    stress_score = 60
                else:
                    stress_score = 40
                score_components.append(stress_score * 0.2)
            
            # Body Battery (15% от общего балла)
            if daily_data.get('body_battery_max'):
                battery = daily_data['body_battery_max']
                if battery >= 80:
                    battery_score = 100
                elif battery >= 60:
                    battery_score = 80
                elif battery >= 40:
                    battery_score = 60
                else:
                    battery_score = 40
                score_components.append(battery_score * 0.15)
            
            # Пульс покоя (10% от общего балла)
            if daily_data.get('resting_heart_rate'):
                rhr = daily_data['resting_heart_rate']
                if 50 <= rhr <= 70:
                    rhr_score = 100
                elif 40 <= rhr <= 80:
                    rhr_score = 80
                elif 35 <= rhr <= 90:
                    rhr_score = 60
                else:
                    rhr_score = 40
                score_components.append(rhr_score * 0.1)
            
            # Если нет достаточно данных, возвращаем средний балл
            if not score_components:
                return 50.0
            
            # Нормализуем на фактическое количество компонентов
            total_weight = sum([0.3, 0.25, 0.2, 0.15, 0.1][:len(score_components)])
            final_score = sum(score_components) / total_weight * 100
            
            return round(min(max(final_score, 0), 100), 1)
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета балла здоровья: {e}")
            return 50.0

    def _extract_basic_trends(self, daily_data: Dict) -> Dict:
        """Извлечь базовые тренды из данных"""
        # Это упрощенная версия - в реальности тренды вычисляются в _calculate_trends
        return {
            'sleep_trend': 'stable',
            'activity_trend': 'stable', 
            'stress_trend': 'stable',
            'recovery_trend': 'stable'
        }

    def _extract_recommendations(self, ai_response: str) -> str:
        """Извлечь рекомендации из ответа AI"""
        # Простое извлечение - ищем секцию с рекомендациями
        try:
            lines = ai_response.split('\n')
            recommendations = []
            
            in_recommendations_section = False
            for line in lines:
                line = line.strip()
                
                # Ищем секцию рекомендаций
                if any(keyword in line.lower() for keyword in ['рекомендац', 'советы', 'предложен', 'recommendation']):
                    in_recommendations_section = True
                    continue
                
                if in_recommendations_section:
                    # Прекращаем если дошли до следующей секции
                    if line.startswith('##') or line.startswith('**') or line.startswith('---'):
                        break
                    
                    if line and not line.startswith('#'):
                        recommendations.append(line)
            
            if recommendations:
                return '\n'.join(recommendations[:5])  # Максимум 5 рекомендаций
            else:
                # Если не нашли секцию, берем последние строки
                return '\n'.join([line for line in lines[-5:] if line.strip()])
                
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения рекомендаций: {e}")
            return "Продолжайте следить за здоровьем!"

    async def _save_analysis_to_db(self, user_id: int, analysis_result: Dict) -> bool:
        """Сохранить анализ в базу данных"""
        try:
            # 🔧 ИСПРАВЛЕНИЕ: Используем asyncpg подход
            conn = await get_db_connection()
            
            await conn.execute("""
                INSERT INTO garmin_analysis_history 
                (user_id, analysis_date, analysis_text, health_score, 
                recommendations, sleep_trend, activity_trend, stress_trend, 
                recovery_trend, gpt_model_used)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (user_id, analysis_date)
                DO UPDATE SET 
                    analysis_text = EXCLUDED.analysis_text,
                    health_score = EXCLUDED.health_score,
                    recommendations = EXCLUDED.recommendations,
                    sleep_trend = EXCLUDED.sleep_trend,
                    activity_trend = EXCLUDED.activity_trend,
                    stress_trend = EXCLUDED.stress_trend,
                    recovery_trend = EXCLUDED.recovery_trend,
                    gpt_model_used = EXCLUDED.gpt_model_used
            """, 
            user_id,
            analysis_result['analysis_date'],
            analysis_result['analysis_text'],
            analysis_result['health_score'],
            analysis_result.get('recommendations', ''),
            analysis_result.get('sleep_trend', 'stable'),
            analysis_result.get('activity_trend', 'stable'),
            analysis_result.get('stress_trend', 'stable'),
            analysis_result.get('recovery_trend', 'stable'),
            analysis_result.get('gpt_model_used', 'gpt-4o'))
            
            await release_db_connection(conn)
            
            logger.info(f"✅ Анализ сохранен в БД для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения анализа в БД: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return False

    async def get_analysis_history(self, user_id: int, days: int = 7) -> List[Dict]:
        """Получить историю анализов пользователя"""
        try:
            conn = await get_db_connection()
            cursor = conn
            
            cursor.execute("""
                SELECT * FROM garmin_analysis_history
                WHERE user_id = %s
                ORDER BY analysis_date DESC
                LIMIT %s
            """, (user_id, days))
            
            rows = cursor.fetchall()
            conn.close()
            await release_db_connection(conn)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения истории анализов: {e}")
            return []

# ================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ================================

garmin_analyzer = GarminAnalyzer()