# profile_manager.py - НОВЫЙ ФАЙЛ, создать в корне проекта

from db_postgresql import get_user_profile, update_user_field, t, set_user_language
import logging

logger = logging.getLogger(__name__)

class ProfileManager:
    """Класс для управления профилем пользователя"""
    
    @staticmethod
    async def get_profile_text(user_id: int, lang: str) -> str:
        """Получить текст профиля для отображения"""
        try:
            profile = await get_user_profile(user_id)
            
            # Формируем текст профиля
            profile_lines = [t("profile_title", lang)]
            
            # Имя
            name = profile.get("name") or t("profile_not_specified", lang)
            profile_lines.append(t("profile_name", lang, name=name))
            
            # Рост
            height = profile.get("height_cm")
            height_text = f"{height}" if height else t("profile_not_specified", lang)
            profile_lines.append(t("profile_height", lang, height=height_text))
            
            # Вес
            weight = profile.get("weight_kg")
            weight_text = f"{weight}" if weight else t("profile_not_specified", lang)
            profile_lines.append(t("profile_weight", lang, weight=weight_text))
            
            # Аллергии
            allergies = profile.get("allergies") or t("profile_not_specified", lang)
            profile_lines.append(t("profile_allergies", lang, allergies=allergies))
            
            # Курение
            smoking = profile.get("smoking") or t("profile_not_specified", lang)
            profile_lines.append(t("profile_smoking", lang, smoking=smoking))
            
            # Алкоголь
            alcohol = profile.get("alcohol") or t("profile_not_specified", lang)
            profile_lines.append(t("profile_alcohol", lang, alcohol=alcohol))
            
            # ✅ ИСПРАВЛЕНИЕ: Правильное отображение активности с эмодзи
            activity = profile.get("physical_activity")
            if activity:
                # Добавляем эмодзи к значению активности для красивого отображения
                activity_with_emoji = ProfileManager._add_activity_emoji(activity, lang)
                profile_lines.append(t("profile_activity", lang, activity=activity_with_emoji))
            else:
                profile_lines.append(t("profile_activity", lang, activity=t("profile_not_specified", lang)))
            
            # Язык
            language_names = {"ru": "Русский", "uk": "Українська", "en": "English"}
            current_lang = language_names.get(lang, lang)
            profile_lines.append(t("profile_language", lang, language=current_lang))
            
            return "\n\n".join(profile_lines)
            
        except Exception as e:
            logger.error(f"Ошибка получения профиля для пользователя {user_id}: {e}")
            return t("profile_load_error", lang)

    @staticmethod 
    def _add_activity_emoji(activity: str, lang: str) -> str:
        """Добавляет эмодзи к значению активности для красивого отображения"""
        if not activity:
            return activity
        
        print(f"🔧 DEBUG _add_activity_emoji: activity='{activity}', lang='{lang}'")
        
        # Маппинг активности к эмодзи (учитываем разные языки)
        emoji_mapping = {
            # Русские варианты
            "Нет активности": "❌ Нет активности",
            "Низкая": "🚶 Низкая",
            "Средняя": "🏃 Средняя", 
            "Высокая": "💪 Высокая",
            "Профессиональная": "🏆 Профессиональная",
            
            # Английские варианты
            "No activity": "❌ No activity",
            "Low": "🚶 Low",
            "Medium": "🏃 Medium",
            "High": "💪 High", 
            "Professional": "🏆 Professional"
        }
        
        result = emoji_mapping.get(activity, activity)
        print(f"🔧 DEBUG _add_activity_emoji result: '{result}'")
        return result
    
    @staticmethod
    async def update_field(user_id: int, field: str, value: str, lang: str) -> tuple[bool, str]:
        """
        Обновить поле профиля
        
        Returns:
            (успех, сообщение)
        """
        try:
            # Валидация и обработка значений
            processed_value = ProfileManager._process_field_value(field, value, lang)
            
            if processed_value is None:
                return False, ProfileManager._get_validation_error(field, lang)
            
            # Специальная обработка языка
            if field == "language":
                await set_user_language(user_id, processed_value)
                logger.info(f"Язык пользователя {user_id} изменен на {processed_value}")
                return True, t("profile_updated", processed_value)  # Сообщение на новом языке
            
            # Обновляем поле в базе
            success = await update_user_field(user_id, field, processed_value)
            
            if success:
                logger.info(f"Поле {field} пользователя {user_id} обновлено на: {processed_value}")
                return True, t("profile_updated", lang)
            else:
                return False, t("profile_update_error", lang)
                
        except Exception as e:
            logger.error(f"Ошибка обновления поля {field} для пользователя {user_id}: {e}")
            return False, t("profile_update_error", lang)
    
    @staticmethod
    def _process_field_value(field: str, value: str, lang: str):
        """Обработка и валидация значения поля"""
        value = value.strip()
        
        if field == "name":
            if len(value) < 1 or len(value) > 100:
                return None
            return value
            
        elif field == "height_cm":
            try:
                height = int(value)
                if 100 <= height <= 250:
                    return height
                return None
            except ValueError:
                return None
                
        elif field == "weight_kg":
            try:
                weight = float(value)
                if 30 <= weight <= 300:
                    return weight
                return None
            except ValueError:
                return None
                
        elif field == "allergies":
            if len(value) < 1 or len(value) > 200:
                return None
            return value
            
        elif field == "physical_activity":
            # ✅ ИСПРАВЛЕНИЕ: нормализуем активность
            return ProfileManager._normalize_activity_value(value, lang)
                
        elif field in ["smoking", "alcohol"]:
            return value  # Эти поля приходят уже валидированными из кнопок
            
        elif field == "language":
            if value in ["ru", "uk", "en"]:
                return value
            return None
            
        return value
    
    @staticmethod
    def _get_validation_error(field: str, lang: str) -> str:
        """Получить сообщение об ошибке валидации"""
        if field == "height_cm":
            return t("invalid_height", lang)
        elif field == "weight_kg":
            return t("invalid_weight", lang)
        else:
            return t("invalid_value", lang)
        
    @staticmethod
    def _normalize_activity_value(value: str, lang: str) -> str:
        """Нормализует значение активности к единому формату"""
        if not value:
            return value
        
        # Убираем эмодзи и лишние пробелы
        clean_value = value.strip()
        for emoji in ["❌", "🚶", "🏃", "💪", "🏆"]:
            clean_value = clean_value.replace(emoji, "").strip()
        
        # Маппинг различных вариантов к единому формату
        activity_mapping = {
            # Русские варианты
            "нет активности": "Нет активности",
            "низкая": "Низкая", 
            "средняя": "Средняя",
            "высокая": "Высокая",
            "профессиональная": "Профессиональная",
            
            # Украинские варианты  
            "відсутня активність": "Нет активности",
            "низька": "Низкая",
            "середня": "Средняя", 
            "висока": "Высокая",
            "професійна": "Профессиональная",
            
            # Английские варианты
            "no activity": "No activity",
            "low": "Low",
            "medium": "Medium", 
            "high": "High",
            "professional": "Professional"
        }
        
        normalized = activity_mapping.get(clean_value.lower(), clean_value)
        return normalized

# Маппинг значений для кнопок на читаемые значения
CHOICE_MAPPINGS = {
    "smoking": {
        "smoking_yes": {"ru": "Да", "uk": "Так", "en": "Yes"},
        "smoking_no": {"ru": "Нет", "uk": "Ні", "en": "No"},
        "smoking_vape": {"ru": "Vape", "uk": "Vape", "en": "Vape"}
    },
    "alcohol": {
        "alcohol_never": {"ru": "Не употребляю", "uk": "Не вживаю", "en": "Never"},
        "alcohol_sometimes": {"ru": "Иногда", "uk": "Іноді", "en": "Sometimes"},
        "alcohol_often": {"ru": "Часто", "uk": "Часто", "en": "Often"}
    },
    "physical_activity": {
        "activity_none": {"ru": "Нет активности", "uk": "Відсутня активність", "en": "No activity"},
        "activity_low": {"ru": "Низкая", "uk": "Низька", "en": "Low"},
        "activity_medium": {"ru": "Средняя", "uk": "Середня", "en": "Medium"},
        "activity_high": {"ru": "Высокая", "uk": "Висока", "en": "High"},
        "activity_pro": {"ru": "Профессиональная", "uk": "Професійна", "en": "Professional"}
    }
}