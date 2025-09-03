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
        """Получить исторические данные за указанное количество дней"""
        try:
            conn = await get_db_connection()
            
            start_date = date.today() - timedelta(days=days)
            
            rows = await conn.fetch("""
                SELECT * FROM garmin_daily_data 
                WHERE user_id = $1 
                AND data_date >= $2
                ORDER BY data_date DESC
            """, user_id, start_date)
            
            await release_db_connection(conn)
            
            # Преобразуем в список словарей
            historical_data = []
            for row in rows:
                row_dict = dict(row)
                # Преобразуем дату в строку для JSON
                row_dict['data_date'] = row_dict['data_date'].strftime('%Y-%m-%d')
                historical_data.append(row_dict)
            
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

    async def _prepare_analysis_context(self, daily_data: Dict, historical_data: List[Dict], 
                                      user_profile: Dict, lang: str) -> Dict:
        """Подготовить контекст для AI анализа"""
        
        # Анализируем тренды
        trends = self._calculate_trends(daily_data, historical_data)
        
        # Форматируем данные за текущий день
        current_day_summary = self._format_current_day_data(daily_data)
        
        # Форматируем исторические данные
        historical_summary = self._format_historical_data(historical_data)
        
        return {
            'language': lang,
            'analysis_date': daily_data.get('data_date', date.today() - timedelta(days=1)),
            'user_profile': user_profile,
            'current_day': current_day_summary,
            'historical_data': historical_summary,
            'trends': trends,
            'data_quality': self._assess_data_quality(daily_data, historical_data)
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
        """Форматировать данные текущего дня для AI"""
        data_parts = []
        
        # Сон
        if daily_data.get('sleep_duration_minutes'):
            hours = daily_data['sleep_duration_minutes'] // 60
            minutes = daily_data['sleep_duration_minutes'] % 60
            data_parts.append(f"Сон: {hours}ч {minutes}мин")
            
            if daily_data.get('sleep_deep_minutes'):
                deep_hours = daily_data['sleep_deep_minutes'] // 60
                deep_mins = daily_data['sleep_deep_minutes'] % 60
                data_parts.append(f"Глубокий сон: {deep_hours}ч {deep_mins}мин")
        
        # Активность
        if daily_data.get('steps'):
            data_parts.append(f"Шаги: {daily_data['steps']:,}")
        
        if daily_data.get('calories'):
            data_parts.append(f"Калории: {daily_data['calories']}")
        
        # Пульс
        if daily_data.get('resting_heart_rate'):
            data_parts.append(f"Пульс покоя: {daily_data['resting_heart_rate']} уд/мин")
        
        # Стресс и восстановление
        if daily_data.get('stress_avg'):
            data_parts.append(f"Средний стресс: {daily_data['stress_avg']}/100")
        
        if daily_data.get('body_battery_max') and daily_data.get('body_battery_min'):
            data_parts.append(f"Body Battery: {daily_data['body_battery_max']}% → {daily_data['body_battery_min']}%")
        
        # SpO2 и дыхание
        if daily_data.get('spo2_avg'):
            data_parts.append(f"SpO2: {daily_data['spo2_avg']:.1f}%")
        
        if daily_data.get('respiration_avg'):
            data_parts.append(f"Дыхание: {daily_data['respiration_avg']:.1f} вдохов/мин")
        
        # Готовность к тренировкам
        if daily_data.get('training_readiness'):
            data_parts.append(f"Готовность к тренировкам: {daily_data['training_readiness']}/100")
        
        return "; ".join(data_parts) if data_parts else "Недостаточно данных"

    def _format_historical_data(self, historical: List[Dict]) -> str:
        """Форматировать исторические данные для AI"""
        if not historical:
            return "Исторических данных нет"
        
        summary_parts = []
        
        # Средние значения за неделю
        avg_sleep = self._calculate_average(historical, 'sleep_duration_minutes')
        if avg_sleep:
            hours = int(avg_sleep) // 60
            minutes = int(avg_sleep) % 60
            summary_parts.append(f"Средний сон за неделю: {hours}ч {minutes}мин")
        
        avg_steps = self._calculate_average(historical, 'steps')
        if avg_steps:
            summary_parts.append(f"Средние шаги: {int(avg_steps):,}")
        
        avg_stress = self._calculate_average(historical, 'stress_avg')
        if avg_stress:
            summary_parts.append(f"Средний стресс: {int(avg_stress)}/100")
        
        avg_rhr = self._calculate_average(historical, 'resting_heart_rate')
        if avg_rhr:
            summary_parts.append(f"Средний пульс покоя: {int(avg_rhr)} уд/мин")
        
        # Количество дней с данными
        summary_parts.append(f"Данных за {len(historical)} дней")
        
        return "; ".join(summary_parts)

    def _calculate_average(self, data: List[Dict], field: str) -> Optional[float]:
        """Вычислить среднее значение поля"""
        values = [item[field] for item in data if item.get(field) is not None]
        return sum(values) / len(values) if values else None

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
        """Построить system prompt для AI анализа"""
        
        if lang == "ru":
            return """Ты опытный врач-терапевт и специалист по превентивной медицине. 
            
Анализируй данные здоровья от умных часов и давай персональные рекомендации.

ОБЯЗАТЕЛЬНЫЕ ПРИНЦИПЫ:
• Анализируй все показатели комплексно - ищи связи между сном, стрессом, активностью
• Учитывай медицинский профиль пациента и принимаемые лекарства
• Сравнивай с нормами для возраста и пола
• Выявляй тренды - улучшение/ухудшение показателей
• Давай конкретные, выполнимые рекомендации
• При отклонениях от нормы - предлагай обратиться к врачу

СТРУКТУРА ОТВЕТА:
1. Краткая оценка общего состояния
2. Анализ ключевых показателей (сон, активность, восстановление, стресс)
3. Выявленные проблемы или риски
4. Конкретные рекомендации для улучшения
5. Оценка прогресса по сравнению с предыдущими днями

Отвечай на русском языке, дружелюбно, но профессионально."""

        elif lang == "uk":
            return """Ти досвідчений лікар-терапевт та фахівець з превентивної медицини.

Аналізуй дані здоров'я від розумного годинника та давай персональні рекомендації.

ОБОВ'ЯЗКОВІ ПРИНЦИПИ:
• Аналізуй всі показники комплексно - шукай зв'язки між сном, стресом, активністю
• Враховуй медичний профіль пацієнта та ліки, що приймає
• Порівнюй з нормами для віку та статі  
• Виявляй тренди - покращення/погіршення показників
• Давай конкретні, виконувані рекомендації
• При відхиленнях від норми - пропонуй звернутися до лікаря

Відповідай українською мовою, доброзичливо, але професійно."""

        else:  # English
            return """You are an experienced physician and preventive medicine specialist.

Analyze health data from smartwatch and provide personalized recommendations.

MANDATORY PRINCIPLES:
• Analyze all indicators comprehensively - look for connections between sleep, stress, activity
• Consider patient's medical profile and medications
• Compare with age and gender norms
• Identify trends - improvement/deterioration of indicators  
• Give specific, actionable recommendations
• For deviations from norm - suggest consulting a doctor

Respond in English, friendly but professionally."""

    def _build_user_prompt(self, context: Dict) -> str:
        """Построить user prompt с данными для анализа"""
        
        analysis_date = context['analysis_date']
        if isinstance(analysis_date, date):
            date_str = analysis_date.strftime('%Y-%m-%d')
        else:
            date_str = str(analysis_date)
        
        prompt = f"""МЕДИЦИНСКИЙ АНАЛИЗ ДАННЫХ ЗДОРОВЬЯ

📅 ДАТА АНАЛИЗА: {date_str}

👤 МЕДИЦИНСКИЙ ПРОФИЛЬ ПАЦИЕНТА:
{context['user_profile']['profile_text']}

💊 ПРИНИМАЕМЫЕ ЛЕКАРСТВА:
{context['user_profile']['medications']}

📊 ДАННЫЕ ЗА ТЕКУЩИЙ ДЕНЬ:
{context['current_day']}

📈 ИСТОРИЧЕСКИЕ ДАННЫЕ (за неделю):
{context['historical_data']}

🔍 ВЫЯВЛЕННЫЕ ТРЕНДЫ:
• Сон: {context['trends'].get('sleep_trend', 'неизвестно')}
• Активность: {context['trends'].get('activity_trend', 'неизвестно')}
• Стресс: {context['trends'].get('stress_trend', 'неизвестно')}  
• Восстановление: {context['trends'].get('recovery_trend', 'неизвестно')}

📋 КАЧЕСТВО ДАННЫХ: {context['data_quality']}

ЗАДАНИЕ:
Проведи комплексный медицинский анализ всех показателей. Дай персональные рекомендации для улучшения здоровья и качества жизни. Учти медицинский профиль и принимаемые лекарства.

Ответ структурируй в удобном для чтения формате с эмодзи."""
        
        return prompt

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