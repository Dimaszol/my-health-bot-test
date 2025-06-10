# test_external.py - Тест внешнего доступа к серверу

import requests
import json

def test_external_access():
    """Тестирует доступ к серверу по внешнему IP"""
    
    external_ip = "152.37.121.201"
    port = 8080
    
    # URL для тестирования
    urls = [
        f"http://localhost:{port}/test",
        f"http://192.168.1.190:{port}/test", 
        f"http://{external_ip}:{port}/test"
    ]
    
    print("🧪 Тестирование доступности сервера...")
    print("=" * 50)
    
    for url in urls:
        try:
            print(f"🔍 Тестируем: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ УСПЕХ! Ответ: {data['message']}")
                print(f"   Ваш IP с сервера: {data.get('your_ip', 'неизвестно')}")
            else:
                print(f"❌ Ошибка HTTP {response.status_code}")
                
        except requests.exceptions.ConnectTimeout:
            print(f"⏰ ТАЙМАУТ - сервер не отвечает")
        except requests.exceptions.ConnectionError:
            print(f"🚫 НЕ ПОДКЛЮЧАЕТСЯ - проверьте проброс портов")
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
        
        print("-" * 30)
    
    print("\n💡 Интерпретация результатов:")
    print("✅ localhost - сервер работает локально")
    print("✅ 192.168.x.x - доступ в локальной сети")
    print("✅ внешний IP - проброс портов настроен правильно")
    print("❌ внешний IP - нужно настроить проброс портов в роутере")

def test_webhook_post():
    """Тестирует POST запрос к webhook"""
    
    external_ip = "152.37.121.201"
    port = 8080
    url = f"http://{external_ip}:{port}/webhook"
    
    test_data = {
        "user_id": 123456,
        "event_type": "subscription_renewed",
        "package_id": "basic_sub",
        "message": "Тест от Python скрипта"
    }
    
    print(f"\n🚀 Тестируем POST запрос к webhook...")
    print(f"📡 URL: {url}")
    print(f"📨 Данные: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            url, 
            json=test_data,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Webhook работает! Ответ:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки webhook: {e}")

if __name__ == "__main__":
    # Сначала тестируем GET запросы
    test_external_access()
    
    # Потом тестируем POST webhook
    test_webhook_post()
    
    print(f"\n🔧 Что делать дальше:")
    print(f"1. Если все ✅ - можно настраивать Make.com")
    print(f"2. Если внешний IP ❌ - настройте проброс портов")
    print(f"3. URL для Make.com: http://152.37.121.201:8080/webhook")