# admin_limits.py - Упрощенная админ-панель для управления лимитами

import sqlite3
from datetime import datetime, timedelta

class LimitsAdmin:
    def __init__(self):
        self.db_path = "users.db"
    
    def get_user_limits(self, user_id: int):
        """Показать текущие лимиты пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем информацию о пользователе
            cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
            user_info = cursor.fetchone()
            
            if not user_info:
                print(f"❌ Пользователь {user_id} не найден")
                conn.close()
                return
            
            # Получаем лимиты
            cursor.execute("""
                SELECT documents_left, gpt4o_queries_left, subscription_type, 
                       subscription_expires_at, created_at, updated_at
                FROM user_limits 
                WHERE user_id = ?
            """, (user_id,))
            
            limits = cursor.fetchone()
            
            print(f"\n👤 ПОЛЬЗОВАТЕЛЬ: {user_info[0]} (ID: {user_id})")
            print("=" * 50)
            
            if limits:
                docs, queries, sub_type, expires, created, updated = limits
                print(f"📄 Документы: {docs}")
                print(f"🤖 GPT-4o запросы: {queries}")
                print(f"💳 Тип подписки: {sub_type}")
                print(f"⏰ Истекает: {expires or 'Не установлено'}")
                print(f"📅 Создано: {created}")
                print(f"🔄 Обновлено: {updated}")
            else:
                print("❌ Лимиты не установлены")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def set_limits(self, user_id: int, documents: int, gpt4o_queries: int):
        """Изменить только количество документов и запросов (тип подписки остается)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем существует ли пользователь
            cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
            user_info = cursor.fetchone()
            if not user_info:
                print(f"❌ Пользователь {user_id} не найден в системе")
                conn.close()
                return
            
            # Получаем текущие данные подписки
            cursor.execute("""
                SELECT subscription_type, subscription_expires_at, created_at
                FROM user_limits WHERE user_id = ?
            """, (user_id,))
            
            current_data = cursor.fetchone()
            
            if current_data:
                # Обновляем только лимиты, оставляя тип подписки и дату
                current_type, current_expires, created_at = current_data
                
                cursor.execute("""
                    UPDATE user_limits 
                    SET documents_left = ?, 
                        gpt4o_queries_left = ?, 
                        updated_at = ?
                    WHERE user_id = ?
                """, (documents, gpt4o_queries, datetime.now().isoformat(), user_id))
                
                print(f"\n✅ Лимиты обновлены для пользователя {user_id} ({user_info[0]}):")
                print(f"📄 Документы: {documents}")
                print(f"🤖 GPT-4o запросы: {gpt4o_queries}")
                print(f"💳 Тип: {current_type} (не изменен)")
                print(f"⏰ Истекает: {current_expires or 'Не установлено'} (не изменено)")
                
            else:
                # Создаем новую запись с базовыми настройками
                expires_at = datetime.now() + timedelta(days=30)
                
                cursor.execute("""
                    INSERT INTO user_limits 
                    (user_id, documents_left, gpt4o_queries_left, subscription_type, 
                     subscription_expires_at, created_at, updated_at)
                    VALUES (?, ?, ?, 'one_time', ?, ?, ?)
                """, (
                    user_id, documents, gpt4o_queries,
                    expires_at.isoformat(),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                print(f"\n✅ Лимиты созданы для пользователя {user_id} ({user_info[0]}):")
                print(f"📄 Документы: {documents}")
                print(f"🤖 GPT-4o запросы: {gpt4o_queries}")
                print(f"💳 Тип: one_time (по умолчанию)")
                print(f"⏰ Действительно до: {expires_at.strftime('%Y-%m-%d %H:%M')}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def reset_limits(self, user_id: int):
        """Сбросить только количество документов и запросов до нуля (подписка остается)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем существует ли пользователь
            cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
            user_info = cursor.fetchone()
            if not user_info:
                print(f"❌ Пользователь {user_id} не найден в системе")
                conn.close()
                return
            
            # Получаем текущие данные подписки
            cursor.execute("""
                SELECT subscription_type, subscription_expires_at, created_at
                FROM user_limits WHERE user_id = ?
            """, (user_id,))
            
            current_data = cursor.fetchone()
            
            if current_data:
                # Сбрасываем только лимиты, оставляя подписку
                current_type, current_expires, created_at = current_data
                
                cursor.execute("""
                    UPDATE user_limits 
                    SET documents_left = 0, 
                        gpt4o_queries_left = 0, 
                        updated_at = ?
                    WHERE user_id = ?
                """, (datetime.now().isoformat(), user_id))
                
                print(f"🔄 Лимиты пользователя {user_id} ({user_info[0]}) сброшены до нуля")
                print(f"📄 Документы: 0")
                print(f"🤖 GPT-4o запросы: 0")
                print(f"💳 Тип: {current_type} (не изменен)")
                print(f"⏰ Истекает: {current_expires or 'Не установлено'} (не изменено)")
                
            else:
                # Создаем новую запись с нулевыми лимитами
                cursor.execute("""
                    INSERT INTO user_limits 
                    (user_id, documents_left, gpt4o_queries_left, subscription_type, created_at, updated_at)
                    VALUES (?, 0, 0, 'free', ?, ?)
                """, (user_id, datetime.now().isoformat(), datetime.now().isoformat()))
                
                print(f"🔄 Созданы нулевые лимиты для пользователя {user_id} ({user_info[0]})")
                print(f"📄 Документы: 0")
                print(f"🤖 GPT-4o запросы: 0")
                print(f"💳 Тип: free (по умолчанию)")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def list_all_users(self):
        """Показать всех пользователей с лимитами"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.user_id, u.name, 
                       COALESCE(l.documents_left, 0) as docs,
                       COALESCE(l.gpt4o_queries_left, 0) as queries,
                       COALESCE(l.subscription_type, 'free') as type,
                       l.subscription_expires_at
                FROM users u
                LEFT JOIN user_limits l ON u.user_id = l.user_id
                ORDER BY u.user_id
            """)
            
            users = cursor.fetchall()
            
            print(f"\n👥 ВСЕ ПОЛЬЗОВАТЕЛИ ({len(users)}):")
            print("=" * 80)
            print(f"{'ID':<12} {'Имя':<20} {'Док.':<6} {'GPT-4o':<8} {'Тип':<12} {'Истекает':<15}")
            print("-" * 80)
            
            for user_id, name, docs, queries, sub_type, expires in users:
                expires_str = expires[:10] if expires else "—"
                name_short = (name[:17] + "...") if name and len(name) > 20 else (name or "Без имени")
                print(f"{user_id:<12} {name_short:<20} {docs:<6} {queries:<8} {sub_type:<12} {expires_str:<15}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def main():
    admin = LimitsAdmin()
    
    print("🔧 АДМИН ПАНЕЛЬ УПРАВЛЕНИЯ ЛИМИТАМИ")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. Показать лимиты пользователя")
        print("2. Изменить лимиты")
        print("3. Сбросить лимиты")
        print("4. Показать всех пользователей")
        print("0. Выход")
        
        choice = input("\nВведите номер: ").strip()
        
        if choice == "0":
            print("👋 До свидания!")
            break
            
        elif choice == "1":
            try:
                user_id = int(input("Введите ID пользователя: "))
                admin.get_user_limits(user_id)
            except ValueError:
                print("❌ Введите корректный ID пользователя")
            
        elif choice == "2":
            try:
                user_id = int(input("Введите ID пользователя: "))
                documents = int(input("Количество документов: "))
                gpt4o_queries = int(input("Количество GPT-4o запросов: "))
                
                admin.set_limits(user_id, documents, gpt4o_queries)
                
            except ValueError:
                print("❌ Введите корректные числовые значения")
            
        elif choice == "3":
            try:
                user_id = int(input("Введите ID пользователя: "))
                admin.reset_limits(user_id)
            except ValueError:
                print("❌ Введите корректный ID пользователя")
            
        elif choice == "4":
            admin.list_all_users()
            
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    main()