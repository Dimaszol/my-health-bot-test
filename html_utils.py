import re

def fix_unclosed_html_tags(text: str) -> str:
    """
    Исправляет незакрытые HTML теги в тексте
    
    Telegram требует чтобы все теги были закрыты:
    - <b>текст</b>
    - <i>текст</i>
    - <code>текст</code>
    - <pre>текст</pre>
    """
    
    # Список поддерживаемых тегов в Telegram HTML
    tags = ['b', 'i', 'code', 'pre', 'u', 's', 'a']
    
    for tag in tags:
        # Считаем открывающие и закрывающие теги
        open_count = len(re.findall(f'<{tag}(?:\\s[^>]*)?>', text))
        close_count = len(re.findall(f'</{tag}>', text))
        
        # Если есть незакрытые теги - закрываем их в конце
        if open_count > close_count:
            diff = open_count - close_count
            text += f'</{tag}>' * diff
        
        # Если есть лишние закрывающие - удаляем их
        elif close_count > open_count:
            diff = close_count - open_count
            # Удаляем последние лишние закрывающие теги
            for _ in range(diff):
                text = text[::-1].replace(f'>/{tag}<'[::-1], '', 1)[::-1]
    
    return text


def safe_html_for_telegram(text: str) -> str:
    """
    Полная очистка HTML для Telegram
    
    1. Убирает неподдерживаемые теги
    2. Исправляет незакрытые теги
    3. Экранирует спецсимволы
    """
    
    # 1. Убираем неподдерживаемые теги (оставляем только b, i, code, pre, u, s, a)
    # Удаляем теги которые Telegram не поддерживает
    unsupported_tags = ['strong', 'em', 'span', 'div', 'p', 'br', 'h1', 'h2', 'h3', 'ul', 'li']
    
    for tag in unsupported_tags:
        # Заменяем <strong> на <b>
        if tag == 'strong':
            text = re.sub(f'<{tag}(?:\\s[^>]*)?>', '<b>', text)
            text = text.replace(f'</{tag}>', '</b>')
        # Заменяем <em> на <i>
        elif tag == 'em':
            text = re.sub(f'<{tag}(?:\\s[^>]*)?>', '<i>', text)
            text = text.replace(f'</{tag}>', '</i>')
        # Заменяем <br> на перенос строки
        elif tag == 'br':
            text = re.sub(f'<{tag}\\s*/?>', '\n', text)
        # Просто удаляем остальные
        else:
            text = re.sub(f'<{tag}(?:\\s[^>]*)?>', '', text)
            text = text.replace(f'</{tag}>', '')
    
    # 2. Исправляем незакрытые теги
    text = fix_unclosed_html_tags(text)
    
    # 3. Убираем множественные пробелы и переносы
    text = re.sub(r'\n{3,}', '\n\n', text)  # Макс 2 переноса подряд
    text = re.sub(r' {2,}', ' ', text)  # Макс 1 пробел подряд
    
    return text.strip()