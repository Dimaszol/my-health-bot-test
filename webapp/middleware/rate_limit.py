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

# 🍯 Honeypot: точные паттерны путей которые запрашивают только сканеры/боты
# Используем точное совпадение: path == pattern ИЛИ path начинается с /pattern/
HONEYPOT_PATTERNS = [
    # Env файлы
    '.env', '.env.bak', '.env.backup', '.env.save', '.env.old', '.env.prod',
    '.env.dev', '.env.local', '.env.example', '.env.sample', '.env.test',
    '.env.docker', '.env.travis', '.env.dist', '.env.php', '.flaskenv',
    'config.env', 'env.php', 'env.json', 'env.txt', 'env.list', 'env.bak',
    '.envrc', '.zshenv',

    # Git / VCS
    '.git', '.svn', '.hg',

    # AWS / Cloud
    '.aws', 'aws-credentials', 'aws.json', 'aws-config.js', 'aws.config.js',
    '.s3cfg',

    # PHP сканы
    'phpinfo.php', 'wp-config.php', 'wp-config-sample.php', 'xmlrpc.php',
    'config.php', 'info.php', 'test.php', 'shell.php', 'cmd.php',
    'adminer.php', 'phpmyadmin', 'eval-stdin.php',

    # Debug
    '_debugbar', 'debugbar', 'debug',

    # SSH / ключи
    'id_rsa', 'id_rsa.pub', '.ssh', '.htpasswd', '.bash_history',
    'secret.key', 'key.pem', 'cert.pem',

    # Бэкапы БД
    'database_backup.sql', 'db_backup', 'db.php', 'db.conf', 'sql.conf',

    # Admin
    'sqladmin.php', 'adminer.php',

    # Прочее
    'nginx.conf', 'httpd.conf', 'docker-compose.override.yml',
]

# ⏱️ Бан за honeypot на 10 минут
HONEYPOT_BAN_SECONDS = 600

# 🔢 Сколько honeypot-запросов за 5 минут = бан
HONEYPOT_THRESHOLD = 2
HONEYPOT_WINDOW = 300  # 5 минут

# 🧠 Максимум ключей в памяти (защита от memory leak при DDoS)
MAX_IPS_IN_MEMORY = 10000

# 🔍 Бан за массовые 404 (сканеры перебирают пути)
NOT_FOUND_THRESHOLD = 7   # 7 за минуту = сканер
NOT_FOUND_WINDOW = 60

# 🚨 Path traversal / LFI паттерны
TRAVERSAL_PATTERNS = [
    '../', '..\\', '%2e%2e', '%252e', '..%c0%af', '..%af',
    '/etc/passwd', 'file://', 'http://127', 'http://localhost',
    'http://ip6-localhost', '169.254.169.254',
]

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware для ограничения количества запросов

    🔒 Защита от:
    - DoS/DDoS атак
    - Перебора паролей
    - Спама в чат
    - Сканеров уязвимостей (honeypot с порогом)
    """

    def __init__(self, app):
        super().__init__(app)

        # 📊 Хранилище запросов: {key: {endpoint: [timestamps]}}
        self.requests: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

        # 🍯 Счётчик honeypot-запросов: {key: [timestamps]}
        self.honeypot_hits: Dict[str, List[float]] = defaultdict(list)

        # 🚫 Забаненные ключи: {key: unban_timestamp}
        self.banned_keys: Dict[str, float] = {}

        # 🔁 Счётчик повторных нарушений: {key: [timestamps]}
        self.rate_violations: Dict[str, List[float]] = defaultdict(list)

        # 🔍 Счётчик 404-ответов: {key: [timestamps]}
        self.not_found_hits: Dict[str, List[float]] = defaultdict(list)

        # 🕐 Время жизни записей (5 минут)
        self.cleanup_interval = 300
        self.last_cleanup = time.time()

        # ⚙️ ПРАВИЛА ЛИМИТОВ (endpoint_pattern, requests_per_minute)
        self.rate_limits = [
            ('/api/chat', 5),
            ('/api/upload', 3),
            ('/api/analyze-photo', 3),
            ('/auth/google', 5),
            ('/api/profile', 10),
            ('/api/check-auth', 200),
            ('/api/toggle-document-confirmed/', 100),
            ('/api/delete-document/', 50),
            ('/api/rename-document/', 50),
            ('/api/check-document-status/', 100),
            ('/api/', 20),
            ('/', 60),
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

    def _get_key(self, request: Request) -> str:
        """Ключ идентификации: IP + User-Agent (защита от shared IP / NAT)"""
        ip = self.get_client_ip(request)
        ua = request.headers.get('User-Agent', '')[:50]
        return f"{ip}|{ua}"

    def get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        return request.client.host if request.client else 'unknown'

    def get_rate_limit(self, path: str) -> Tuple[str, int]:
        for pattern, limit in self.rate_limits:
            if path.startswith(pattern):
                return (pattern, limit)
        return ('default', 30)

    def is_honeypot_path(self, path: str) -> bool:
        """
        Точная проверка пути.
        НЕ срабатывает на /api/get-config или /api/user-credentials-check
        """
        path_lower = path.lower().lstrip('/')
        for pattern in HONEYPOT_PATTERNS:
            p = pattern.lower().lstrip('/')
            if path_lower == p or path_lower.startswith(p + '/'):
                return True
        return False

    def check_and_update_honeypot(self, key: str, current_time: float) -> bool:
        """
        Возвращает True если надо банить.
        Банит только после HONEYPOT_THRESHOLD запросов за HONEYPOT_WINDOW секунд.
        """
        window_start = current_time - HONEYPOT_WINDOW
        hits = [t for t in self.honeypot_hits[key] if t > window_start]
        hits.append(current_time)
        self.honeypot_hits[key] = hits
        return len(hits) >= HONEYPOT_THRESHOLD

    def is_banned(self, key: str, current_time: float) -> bool:
        unban_time = self.banned_keys.get(key)
        if unban_time and current_time < unban_time:
            return True
        if unban_time:
            del self.banned_keys[key]
        return False

    def cleanup_old_requests(self):
        current_time = time.time()
        cutoff_time = current_time - 300

        ips_to_remove = []
        for key, endpoints in list(self.requests.items()):
            for endpoint, timestamps in list(endpoints.items()):
                endpoints[endpoint] = [ts for ts in timestamps if ts > cutoff_time]
                if not endpoints[endpoint]:
                    del endpoints[endpoint]
            if not endpoints:
                ips_to_remove.append(key)

        for key in ips_to_remove:
            del self.requests[key]

        # Очищаем honeypot hits
        for key in list(self.honeypot_hits.keys()):
            self.honeypot_hits[key] = [t for t in self.honeypot_hits[key] if t > cutoff_time]
            if not self.honeypot_hits[key]:
                del self.honeypot_hits[key]

        # Очищаем violations
        for key in list(self.rate_violations.keys()):
            self.rate_violations[key] = [t for t in self.rate_violations[key] if t > cutoff_time]
            if not self.rate_violations[key]:
                del self.rate_violations[key]

        # Очищаем not_found hits
        for key in list(self.not_found_hits.keys()):
            self.not_found_hits[key] = [t for t in self.not_found_hits[key] if t > cutoff_time]
            if not self.not_found_hits[key]:
                del self.not_found_hits[key]

        # Очищаем истёкшие баны
        expired_bans = [k for k, t in self.banned_keys.items() if current_time > t]
        for key in expired_bans:
            del self.banned_keys[key]

        logger.debug(f"Rate limit cleanup: removed {len(ips_to_remove)} inactive, {len(expired_bans)} expired bans")

    def _check_memory_limit(self):
        """Защита от memory leak при DDoS"""
        if len(self.requests) > MAX_IPS_IN_MEMORY:
            keys = list(self.requests.keys())
            to_remove = keys[:len(keys) // 5]  # удаляем старые 20%
            for key in to_remove:
                del self.requests[key]
            logger.warning(f"Memory limit reached, cleared {len(to_remove)} oldest entries")

    def get_error_message(self, request: Request, wait_seconds: int) -> str:
        lang = 'en'
        try:
            if hasattr(request, 'session') and 'language' in request.session:
                lang = request.session.get('language', 'en')
        except:
            pass
        if lang not in self.error_messages:
            lang = 'en'
        return self.error_messages[lang].format(seconds=wait_seconds)

    async def dispatch(self, request: Request, call_next):
        current_time = time.time()

        # 🧹 Периодическая очистка
        if current_time - self.last_cleanup > self.cleanup_interval:
            self.cleanup_old_requests()
            self.last_cleanup = current_time

        # 🧠 Защита памяти
        self._check_memory_limit()

        client_ip = self.get_client_ip(request)
        key = self._get_key(request)
        path = request.url.path

        # 🚨 Path traversal / LFI в query parameters
        query_string = str(request.url.query).lower()        
        if any(p in query_string for p in TRAVERSAL_PATTERNS):
            should_ban = self.check_and_update_honeypot(key, current_time)
            if should_ban:
                already_banned = key in self.banned_keys
                self.banned_keys[key] = current_time + HONEYPOT_BAN_SECONDS
                if not already_banned:
                    logger.warning(f"Path traversal attempt banned | IP: {client_ip[:10]}...")
            return JSONResponse(status_code=400, content={'detail': 'Bad Request'})

        # 🍯 Honeypot: точная проверка + порог 2 запроса за 5 минут
        if self.is_honeypot_path(path):
            should_ban = self.check_and_update_honeypot(key, current_time)
            if should_ban:
                already_banned = key in self.banned_keys
                self.banned_keys[key] = current_time + HONEYPOT_BAN_SECONDS
                if not already_banned:
                    logger.warning(f"Scanner banned | IP: {client_ip[:10]}...")
            return JSONResponse(status_code=404, content={'detail': 'Not Found'})

        # 🚫 Проверка существующего бана
        if self.is_banned(key, current_time):
            return JSONResponse(status_code=429, content={'detail': 'Too Many Requests'})

        # 📍 Rate limit
        endpoint_pattern, limit = self.get_rate_limit(path)
        timestamps = self.requests[key][endpoint_pattern]
        one_minute_ago = current_time - 60
        recent_requests = [ts for ts in timestamps if ts > one_minute_ago]

        if len(recent_requests) >= limit:
            oldest_request = min(recent_requests)
            wait_seconds = int(60 - (current_time - oldest_request)) + 1
            error_message = self.get_error_message(request, wait_seconds)

            if len(recent_requests) == limit:
                logger.warning(
                    f"Rate limit reached | IP: {client_ip[:10]}... | "
                    f"Endpoint: {endpoint_pattern} | Limit: {limit}/min"
                )
                # 🚫 Автобан за повторные нарушения
                violations = self.rate_violations[key]
                violations = [ts for ts in violations if ts > current_time - 300]
                violations.append(current_time)
                self.rate_violations[key] = violations
                if len(violations) >= 10:
                    self.banned_keys[key] = current_time + HONEYPOT_BAN_SECONDS
                    logger.warning(f"Repeat violator auto-banned | IP: {client_ip[:10]}...")

            return JSONResponse(
                status_code=429,
                content={'success': False, 'error': error_message, 'retry_after': wait_seconds},
                headers={
                    'Retry-After': str(wait_seconds),
                    'X-RateLimit-Limit': str(limit),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(int(oldest_request + 60))
                }
            )

        self.requests[key][endpoint_pattern] = recent_requests + [current_time]

        response = await call_next(request)

        # 🔍 Считаем 404 — баним сканеры
        if response.status_code == 404:
            window_start = current_time - NOT_FOUND_WINDOW
            hits = [t for t in self.not_found_hits[key] if t > window_start]
            hits.append(current_time)
            self.not_found_hits[key] = hits
            if len(hits) >= NOT_FOUND_THRESHOLD:
                if key not in self.banned_keys:
                    self.banned_keys[key] = current_time + HONEYPOT_BAN_SECONDS
                    logger.warning(f"Scanner banned (404s) | IP: {client_ip[:10]}...")

        response.headers['X-RateLimit-Limit'] = str(limit)
        response.headers['X-RateLimit-Remaining'] = str(limit - len(recent_requests) - 1)
        return response


def add_rate_limit_middleware(app):
    app.add_middleware(RateLimitMiddleware)
    logger.info("Rate limit middleware activated")