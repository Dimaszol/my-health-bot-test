# corrected_security_test.py - ИСПРАВЛЕННЫЙ тест безопасности

from db import update_user_field

def test_sql_injection():
    """Тест SQL инъекций"""
    print("🧪 Тест 1: SQL инъекция")
    try:
        result = update_user_field(123, 'name', "'; DROP TABLE users; --")
        # Если функция вернула True - это плохо (атака прошла)
        if result:
            print("❌ SQL инъекция ПРОШЛА - это ПЛОХО!")
        else:
            print("✅ SQL инъекция заблокирована - функция вернула False")
    except Exception as e:
        # Если исключение - это хорошо (атака заблокирована)
        print(f"✅ SQL инъекция заблокирована исключением: {str(e)[:50]}")

def test_forbidden_field():
    """Тест запрещенных полей"""
    print("\n🧪 Тест 2: Запрещенное поле")
    try:
        result = update_user_field(123, 'admin', 'true')
        if result:
            print("❌ Запрещенное поле ОБНОВЛЕНО - это ПЛОХО!")
        else:
            print("✅ Запрещенное поле заблокировано - функция вернула False")
    except Exception as e:
        print(f"✅ Запрещенное поле заблокировано исключением: {str(e)[:50]}")

def test_invalid_user_id():
    """Тест некорректного user_id"""
    print("\n🧪 Тест 3: Некорректный user_id")
    try:
        result = update_user_field(-1, 'name', 'test')
        if result:
            print("❌ Некорректный ID ПРИНЯТ - это ПЛОХО!")
        else:
            print("✅ Некорректный ID заблокирован - функция вернула False")
    except Exception as e:
        print(f"✅ Некорректный ID заблокирован исключением: {str(e)[:50]}")

def test_normal_operation():
    """Тест нормальной работы"""
    print("\n🧪 Тест 4: Нормальная работа")
    try:
        result = update_user_field(123, 'name', 'Иван')
        if result:
            print("✅ Нормальное обновление прошло успешно")
        else:
            print("⚠️ Нормальное обновление не прошло (возможно, пользователь не существует)")
    except Exception as e:
        print(f"❌ Ошибка при нормальном обновлении: {e}")

def main():
    print("🛡️ ИСПРАВЛЕННЫЙ ТЕСТ БЕЗОПАСНОСТИ")
    print("=" * 50)
    
    test_sql_injection()
    test_forbidden_field()
    test_invalid_user_id()
    test_normal_operation()
    
    print("\n" + "=" * 50)
    print("📊 ИНТЕРПРЕТАЦИЯ:")
    print("✅ = Защита работает правильно")
    print("❌ = Найдена уязвимость")
    print("⚠️ = Требует внимания")

if __name__ == "__main__":
    main()