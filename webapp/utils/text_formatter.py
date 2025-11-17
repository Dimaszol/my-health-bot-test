# webapp/utils/text_formatter.py
"""
🎨 Форматирование текста для веб-интерфейса
Преобразует Markdown в безопасный HTML для отображения в браузере
"""

import re
import html


def format_for_web(text: str) -> str:
    """
    Преобразует Markdown текст в HTML для веб-интерфейса
    
    Что делает:
    - **текст** → <strong>текст</strong> (жирный)
    - *текст* → <em>текст</em> (курсив)
    - `код` → <code>код</code> (моноширинный)
    - ### Заголовок → <h3>Заголовок</h3>
    - - пункт → <li>пункт</li> (списки)
    - \n\n → <br><br> (переносы строк)
    
    Args:
        text: Исходный текст от GPT в Markdown формате
        
    Returns:
        Отформатированный HTML текст (безопасный)
    """
    
    if not text:
        return ""
    
    
    
    # 2️⃣ Преобразуем Markdown ЗАГОЛОВКИ в HTML
    # ### Заголовок → <h3>Заголовок</h3>
    text = re.sub(r'^### (.+)$', r'<h3 style="color: #00c9a7; font-weight: 600; margin-top: 1rem;">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2 style="color: #00c9a7; font-weight: 600; margin-top: 1rem;">\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1 style="color: #00c9a7; font-weight: 700; margin-top: 1rem;">\1</h1>', text, flags=re.MULTILINE)
    
    # 3️⃣ Преобразуем ЖИРНЫЙ текст
    # **текст** → <strong>текст</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # 4️⃣ Преобразуем КУРСИВ
    # *текст* → <em>текст</em>
    # (используем (?<!\*) чтобы не задеть уже обработанный жирный текст)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)', r'<em>\1</em>', text)
    
    # 5️⃣ Преобразуем КОД
    # `код` → <code>код</code>
    text = re.sub(
        r'`(.+?)`', 
        r'<code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace;">\1</code>', 
        text
    )
    
    # 6️⃣ Преобразуем СПИСКИ
    # - пункт → <li>пункт</li>
    # Сначала находим все пункты списка
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        # Проверяем, это пункт списка?
        if re.match(r'^[\-\*•]\s+(.+)', line):
            # Извлекаем текст пункта (без маркера)
            item_text = re.sub(r'^[\-\*•]\s+', '', line)
            
            # Если это первый пункт - открываем <ul>
            if not in_list:
                formatted_lines.append('<ul style="margin-left: 1.5rem; margin-top: 0.5rem;">')
                in_list = True
            
            # Добавляем пункт списка
            formatted_lines.append(f'<li style="margin-bottom: 0.3rem;">{item_text}</li>')
        else:
            # Если была открыта ul - закрываем
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            
            # Добавляем обычную строку
            formatted_lines.append(line)
    
    # Если список не был закрыт - закрываем
    if in_list:
        formatted_lines.append('</ul>')
    
    # Склеиваем обратно
    text = '\n'.join(formatted_lines)
    
    # 7️⃣ Преобразуем ПЕРЕНОСЫ СТРОК
    text = re.sub(r'\n\n+', '<br>', text)  # Двойной перенос → один <br>
    text = re.sub(r'\n', ' ', text)  # Одиночные переносы в пробел
    
    # 8️⃣ УБИРАЕМ лишние пробелы
    text = re.sub(r'\s+', ' ', text)  # Множественные пробелы в один
    text = text.strip()
    
    return text


def format_error_message(error_text: str) -> str:
    """
    Форматирует сообщения об ошибках для веб-интерфейса
    
    Args:
        error_text: Текст ошибки
        
    Returns:
        HTML с красным предупреждением
    """
    return f'''
    <div style="
        background: #fee; 
        border-left: 4px solid #f44336; 
        padding: 1rem; 
        border-radius: 8px;
        color: #c62828;
    ">
        <strong>⚠️ Ошибка:</strong> {html.escape(error_text)}
    </div>
    '''


def format_success_message(message: str) -> str:
    """
    Форматирует успешные сообщения для веб-интерфейса
    
    Args:
        message: Текст сообщения
        
    Returns:
        HTML с зелёным уведомлением
    """
    return f'''
    <div style="
        background: #e8f5e9; 
        border-left: 4px solid #4caf50; 
        padding: 1rem; 
        border-radius: 8px;
        color: #2e7d32;
    ">
        <strong>✅ Успешно:</strong> {html.escape(message)}
    </div>
    '''