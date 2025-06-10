# test_server.py - Тестовый сервер для проверки подключения Make.com

from aiohttp import web
import json
import asyncio
from datetime import datetime

async def handle_webhook(request):
    """Обработчик webhook от Make.com"""
    try:
        # Получаем данные
        data = await request.json()
        
        # Логируем полученные данные
        print(f"🎯 Получен webhook в {datetime.now()}:")
        print(f"📨 Данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print(f"🌐 IP отправителя: {request.remote}")
        print("-" * 50)
        
        # Возвращаем успешный ответ
        response_data = {
            "status": "success",
            "message": "Webhook получен успешно!",
            "received_at": datetime.now().isoformat(),
            "data_received": data
        }
        
        return web.json_response(response_data)
        
    except Exception as e:
        print(f"❌ Ошибка обработки webhook: {e}")
        return web.json_response(
            {"status": "error", "message": str(e)}, 
            status=400
        )

async def handle_test(request):
    """Простой тестовый endpoint"""
    return web.json_response({
        "status": "ok",
        "message": "Сервер работает!",
        "timestamp": datetime.now().isoformat(),
        "your_ip": request.remote
    })

async def handle_root(request):
    """Главная страница для проверки в браузере"""
    html = """
    <html>
    <head><title>Webhook сервер работает!</title></head>
    <body>
        <h1>🎉 Webhook сервер запущен!</h1>
        <p><strong>Сервер работает корректно</strong></p>
        <p>Время: {timestamp}</p>
        <p>Ваш IP: {ip}</p>
        
        <h2>Доступные endpoints:</h2>
        <ul>
            <li><code>GET /</code> - эта страница</li>
            <li><code>GET /test</code> - тестовый JSON endpoint</li>
            <li><code>POST /webhook</code> - webhook для Make.com</li>
        </ul>
        
        <h2>Тест POST запроса:</h2>
        <button onclick="testWebhook()">Отправить тестовый webhook</button>
        <div id="result"></div>
        
        <script>
        async function testWebhook() {{
            try {{
                const response = await fetch('/webhook', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        test: true,
                        message: 'Тестовый webhook',
                        timestamp: new Date().toISOString()
                    }})
                }});
                const result = await response.json();
                document.getElementById('result').innerHTML = 
                    '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
            }} catch (e) {{
                document.getElementById('result').innerHTML = 'Ошибка: ' + e.message;
            }}
        }}
        </script>
    </body>
    </html>
    """.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ip=request.remote
    )
    return web.Response(text=html, content_type='text/html')

def create_app():
    """Создание приложения"""
    app = web.Application()
    
    # Добавляем маршруты
    app.router.add_get('/', handle_root)
    app.router.add_get('/test', handle_test)
    app.router.add_post('/webhook', handle_webhook)
    
    return app

async def main():
    """Главная функция запуска сервера"""
    
    # Настройки сервера
    HOST = '0.0.0.0'  # Слушаем на всех интерфейсах
    PORT = 8080
    
    print("🚀 Запуск webhook сервера...")
    print(f"🌐 Адрес: http://{HOST}:{PORT}")
    print(f"🏠 Локальный доступ: http://localhost:{PORT}")
    print(f"🌍 Сетевой доступ: http://192.168.1.190:{PORT}")
    print("=" * 60)
    print("📡 Ожидание webhook от Make.com...")
    print("🔍 Для проверки откройте в браузере: http://localhost:8080")
    print("=" * 60)
    
    # Создаем и запускаем приложение
    app = create_app()
    
    try:
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, HOST, PORT)
        await site.start()
        
        # Держим сервер запущенным
        print("✅ Сервер запущен успешно!")
        print("⏹️  Для остановки нажмите Ctrl+C")
        
        # Бесконечный цикл
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервера...")
        await runner.cleanup()
        print("✅ Сервер остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")