# webapp/middleware/rate_limit.py
# 🛡️ Middleware для защиты от DoS/DDoS атак через Rate Limiting

import time
from typing import Dict, List, Tuple
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware для ограничения количества запросов с одного IP-адреса
    
    🔒 Защита от:
    - DoS/DDoS атак
    - Перебора паролей
    - Спама в чат
    - Злоупотребления API
    
    📊 Лимиты (снижены для безопасности):
    - Обычные страницы: 30 запросов/минуту
    - Чат с AI: 5 запросов/минуту
    - Загрузка файлов: 3 запроса/минуту
    - Авторизация: 5 попыток/минуту
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # 📊 Хранилище запросов: {IP: {endpoint: [timestamps]}}
        self.requests: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        
        # 🕐 Время жизни записей (5 минут)
        self.cleanup_interval = 300
        self.last_cleanup = time.time()
        
        # ⚙️ ПРАВИЛА ЛИМИТОВ (endpoint_pattern, requests_per_minute)
        self.rate_limits = [
            ('/api/chat', 5),           # Чат с AI - 5 запросов/мин
            ('/api/upload', 3),         # Загрузка файлов - 3 запроса/мин
            ('/auth/google', 5),        # Авторизация Google - 5 попыток/мин
            ('/api/profile', 10),       # Обновление профиля - 10 запросов/мин
            ('/api/', 20),              # Все остальные API - 20 запросов/мин
            ('/', 30)                   # Обычные страницы - 30 запросов/мин
        ]
        
        # 🌍 Мультиязычные сообщения об ошибках
        self.error_messages = {
            'en': 'Too many requests. Please wait {seconds} seconds.',
            'ru': 'Слишком много запросов. Подождите {seconds} секунд.',
            'uk': 'Забагато запитів. Зачекайте {seconds} секунд.',
            'es': 'Demasiadas solicitudes. Espera {seconds} segundos.',
            'fr': 'Trop de requêtes. Attendez {seconds} secondes.',
            'de': 'Zu viele Anfragen. Warten Sie {seconds} Sekunden.',
            'it': 'Troppe richieste. Attendi {seconds} secondi.',
            'pt': 'Muitas solicitações. Aguarde {seconds} segundos.'
        }
    
    def get_client_ip(self, request: Request) -> str:
        """
        Получить реальный IP клиента (учитывая прокси/CDN)
        
        🔍 Проверяем заголовки в порядке приоритета:
        1. X-Forwarded-For (если за прокси/CloudFlare)
        2. X-Real-IP (nginx)
        3. request.client.host (прямое подключение)
        """
        # Railway/CloudFlare передают реальный IP в X-Forwarded-For
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            # Берём первый IP из списка (реальный клиент)
            return forwarded.split(',')[0].strip()
        
        # Nginx передаёт в X-Real-IP
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Прямое подключение
        return request.client.host if request.client else 'unknown'
    
    def get_rate_limit(self, path: str) -> Tuple[str, int]:
        """
        Определить лимит для конкретного endpoint
        
        Возвращает: (название_лимита, запросов_в_минуту)
        """
        for pattern, limit in self.rate_limits:
            if path.startswith(pattern):
                return (pattern, limit)
        
        # По умолчанию - самый строгий лимит
        return ('default', 30)
    
    def cleanup_old_requests(self):
        """
        Очистка старых записей для экономии памяти
        Вызывается каждые 5 минут
        """
        current_time = time.time()
        cutoff_time = current_time - 300  # 5 минут назад
        
        # Удаляем старые IP
        ips_to_remove = []
        for ip, endpoints in list(self.requests.items()):
            # Очищаем старые timestamps в каждом endpoint
            for endpoint, timestamps in list(endpoints.items()):
                # Оставляем только последние 5 минут
                endpoints[endpoint] = [ts for ts in timestamps if ts > cutoff_time]
                
                # Если endpoint пустой - удаляем его
                if not endpoints[endpoint]:
                    del endpoints[endpoint]
            
            # Если у IP нет активных endpoints - удаляем IP
            if not endpoints:
                ips_to_remove.append(ip)
        
        for ip in ips_to_remove:
            del self.requests[ip]
        
        logger.info(f"🧹 Rate limit cleanup: удалено {len(ips_to_remove)} неактивных IP")
    
    def get_error_message(self, request: Request, wait_seconds: int) -> str:
        """
        Получить сообщение об ошибке на языке пользователя
        """
        # Определяем язык из сессии или заголовка
        lang = 'en'
        
        # Пытаемся получить язык из сессии
        try:
            if hasattr(request, 'session') and 'language' in request.session:
                lang = request.session.get('language', 'en')
        except:
            pass
        
        # Если язык не поддерживается - используем английский
        if lang not in self.error_messages:
            lang = 'en'
        
        return self.error_messages[lang].format(seconds=wait_seconds)
    
    async def dispatch(self, request: Request, call_next):
        """
        Обработка каждого запроса
        """
        # 🧹 Периодическая очистка старых записей
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self.cleanup_old_requests()
            self.last_cleanup = current_time
        
        # 🔍 Получаем IP клиента
        client_ip = self.get_client_ip(request)
        
        # 📍 Определяем путь и лимит
        path = request.url.path
        endpoint_pattern, limit = self.get_rate_limit(path)
        
        # 📊 Получаем историю запросов для этого IP и endpoint
        timestamps = self.requests[client_ip][endpoint_pattern]
        
        # 🕐 Оставляем только запросы за последнюю минуту
        one_minute_ago = current_time - 60
        recent_requests = [ts for ts in timestamps if ts > one_minute_ago]
        
        # ✅ Проверяем лимит
        if len(recent_requests) >= limit:
            # ❌ ПРЕВЫШЕН ЛИМИТ!
            
            # Вычисляем через сколько секунд можно повторить запрос
            oldest_request = min(recent_requests)
            wait_seconds = int(60 - (current_time - oldest_request)) + 1
            
            # Получаем мультиязычное сообщение
            error_message = self.get_error_message(request, wait_seconds)
            
            # 📝 Логируем для безопасности (без личных данных)
            logger.warning(
                f"🚫 Rate limit exceeded | "
                f"IP: {client_ip[:10]}... | "
                f"Endpoint: {endpoint_pattern} | "
                f"Limit: {limit}/min | "
                f"Current: {len(recent_requests)}"
            )
            
            # Возвращаем ошибку 429
            return JSONResponse(
                status_code=429,
                content={
                    'success': False,
                    'error': error_message,
                    'retry_after': wait_seconds
                },
                headers={
                    'Retry-After': str(wait_seconds),
                    'X-RateLimit-Limit': str(limit),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(int(oldest_request + 60))
                }
            )
        
        # ✅ Лимит не превышен - записываем запрос
        self.requests[client_ip][endpoint_pattern] = recent_requests + [current_time]
        
        # 📤 Добавляем заголовки с информацией о лимите
        response = await call_next(request)
        
        # Добавляем заголовки о rate limit
        response.headers['X-RateLimit-Limit'] = str(limit)
        response.headers['X-RateLimit-Remaining'] = str(limit - len(recent_requests) - 1)
        
        return response


# 🔧 Удобная функция для добавления middleware в FastAPI
def add_rate_limit_middleware(app):
    """
    Добавить Rate Limit Middleware в FastAPI приложение
    
    Использование:
        from webapp.middleware.rate_limit import add_rate_limit_middleware
        
        app = FastAPI()
        add_rate_limit_middleware(app)
    """
    app.add_middleware(RateLimitMiddleware)
    logger.info("✅ Rate Limit Middleware активирован")