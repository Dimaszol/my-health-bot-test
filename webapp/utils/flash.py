# webapp/utils/flash.py
"""
Flash-сообщения для FastAPI (аналог Flask flash)
"""
from typing import List, Tuple
from fastapi import Request
from fastapi.responses import RedirectResponse

def flash(request: Request, message: str, category: str = 'info'):
    """
    Добавляет flash-сообщение в сессию
    
    Args:
        request: FastAPI Request объект
        message: Текст сообщения
        category: Категория ('success', 'error', 'warning', 'info')
    
    Использование:
        flash(request, 'Вы успешно вошли!', 'success')
        flash(request, 'Ошибка входа', 'error')
    """
    if '_flashes' not in request.session:
        request.session['_flashes'] = []
    request.session['_flashes'].append((category, message))


def get_flashed_messages(request: Request, with_categories: bool = False) -> List:
    """
    Получает и удаляет flash-сообщения из сессии
    
    Args:
        request: FastAPI Request объект
        with_categories: Возвращать ли категории
    
    Returns:
        Если with_categories=True: [(category, message), ...]
        Если with_categories=False: [message, ...]
    """
    flashes = request.session.pop('_flashes', [])
    
    if with_categories:
        return flashes
    else:
        return [message for category, message in flashes]
    
def redirect_with_flash(request: Request, url: str, message_key: str, category: str = "info"):
    """
    Редирект с flash-сообщением
    
    Args:
        request: FastAPI Request объект
        url: URL для редиректа
        message_key: Ключ сообщения для перевода
        category: Категория (info, success, warning, error)
    """
    flash(request, message_key, category)
    return RedirectResponse(url=url, status_code=302)