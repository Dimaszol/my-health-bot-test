# webapp/utils/context.py
"""
Контекст для шаблонов (общий для app.py и роутеров)
"""
from fastapi import Request
from webapp.translations import t, get_supported_languages
from webapp.utils.flash import get_flashed_messages


def get_template_context(request: Request) -> dict:
    """
    Возвращает базовый контекст для всех шаблонов
    (аналог context_processor в Flask)
    """
    # ✅ ОПРЕДЕЛЯЕМ ЯЗЫК ПО URL (для SEO-страниц)
    path = request.url.path
    
    if path.startswith('/de/') or path == '/de':
        lang = 'de'
    elif path.startswith('/ru/') or path == '/ru':
        lang = 'ru'
    elif path.startswith('/uk/') or path == '/uk':
        lang = 'uk'
    else:
        # ⚠️ ДЛЯ СЛУЖЕБНЫХ СТРАНИЦ (login, dashboard) - берём из session
        lang = request.session.get('language', 'en')
    
    # 💱 Определяем валюту пользователя
    from webapp.utils.currency import get_ui_currency, get_currency_symbol
    
    # Получаем country из сессии (устанавливается при логине)
    user_country = request.session.get('country', None)
    currency = get_ui_currency(user_country)
    currency_symbol = get_currency_symbol(currency)

    # ✅ ВЫЧИСЛЯЕМ base_path (путь без языкового префикса)
    if path.startswith('/de/') or path.startswith('/ru/') or path.startswith('/uk/'):
        base_path = path[3:]  # Убираем "/de", "/ru", "/uk"
    elif path in ['/de', '/ru', '/uk']:
        base_path = ''
    else:
        base_path = path
    
    # ✅ ПРАВИЛЬНАЯ РЕАЛИЗАЦИЯ get_flashed_messages
    def _get_flashed_messages(**kwargs):
        """Wrapper для передачи в шаблон"""
        return get_flashed_messages(request, **kwargs)
    
    return {
        'request': request,
        'session': request.session,
        'lang': lang,
        'base_path': base_path,
        't': t,
        'supported_languages': get_supported_languages(),
        'get_flashed_messages': _get_flashed_messages,
        'currency': currency,
        'currency_symbol': currency_symbol
    }