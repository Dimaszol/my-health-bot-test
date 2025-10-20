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
    lang = request.session.get('language', 'ru')
    
    # ✅ ПРАВИЛЬНАЯ РЕАЛИЗАЦИЯ get_flashed_messages
    def _get_flashed_messages(**kwargs):
        """Wrapper для передачи в шаблон"""
        return get_flashed_messages(request, **kwargs)
    
    return {
        'request': request,
        'session': request.session,
        'lang': lang,
        't': t,
        'supported_languages': get_supported_languages(),
        'get_flashed_messages': _get_flashed_messages
    }