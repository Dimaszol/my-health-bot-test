// 🚀 MEDICAL ASSISTANT - JAVASCRIPT
// Современные интерактивные эффекты в стиле Docus.ai

document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================
    // ✨ ПЛАВНАЯ ПРОКРУТКА ДЛЯ ЯКОРНЫХ ССЫЛОК
    // ============================================
    
    const smoothScrollLinks = document.querySelectorAll('a[href^="#"]');
    
    smoothScrollLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Пропускаем пустые якоря
            if (href === '#') return;
            
            e.preventDefault();
            
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // ============================================
    // 👀 АНИМАЦИЯ ПРИ ПОЯВЛЕНИИ ЭЛЕМЕНТОВ
    // ============================================
    
    // Функция для проверки видимости элемента
    function isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Добавляем класс для анимации при скролле
    const fadeElements = document.querySelectorAll('.card, .stat-card');
    
    function checkFadeElements() {
        fadeElements.forEach(el => {
            if (isElementInViewport(el)) {
                el.classList.add('fade-in', 'visible');
            }
        });
    }
    
    // Проверяем при загрузке и скролле
    checkFadeElements();
    window.addEventListener('scroll', checkFadeElements);
    
    // ============================================
    // 💬 ЧАТ: Автопрокрутка вниз
    // ============================================
    
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        // Прокручиваем вниз при загрузке
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Плавная прокрутка при добавлении новых сообщений
        const observer = new MutationObserver(() => {
            chatContainer.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        });
        
        observer.observe(chatContainer, { childList: true, subtree: true });
    }
    
    // ============================================
    // 📝 ЧАТ: Отправка сообщений
    // ============================================
    
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const typingIndicator = document.getElementById('typing-indicator');
    
    if (chatForm && messageInput) {
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Добавляем сообщение пользователя
            addMessageToChat('user', message);
            
            // Очищаем input
            messageInput.value = '';
            
            // Показываем индикатор печатания
            if (typingIndicator) {
                typingIndicator.style.display = 'block';
            }
            
            try {
                // Отправляем запрос на сервер (AJAX)
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                // Скрываем индикатор
                if (typingIndicator) {
                    typingIndicator.style.display = 'none';
                }
                
                // Добавляем ответ AI
                if (data.response) {
                    addMessageToChat('ai', data.response);
                }
                
            } catch (error) {
                console.error('Ошибка отправки сообщения:', error);
                
                // Скрываем индикатор
                if (typingIndicator) {
                    typingIndicator.style.display = 'none';
                }
                
                // Показываем сообщение об ошибке
                addMessageToChat('ai', 'Извините, произошла ошибка. Пожалуйста, попробуйте снова.');
            }
        });
    }
    
    // Функция добавления сообщения в чат
    function addMessageToChat(role, text) {
        if (!chatContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        // ✅ КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ:
        // Для AI используем innerHTML (отображает HTML теги)
        // Для пользователя используем textContent (безопасность)
        if (role === 'ai') {
            bubble.innerHTML = text;  // ✅ AI сообщения с HTML
        } else {
            bubble.textContent = text;  // ✅ Сообщения пользователя - только текст
        }
        
        const time = document.createElement('div');
        time.className = 'message-time';
        const now = new Date();
        time.textContent = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.appendChild(bubble);
        messageDiv.appendChild(time);
        chatContainer.appendChild(messageDiv);
    }
    
    // ============================================
    // 📤 ЗАГРУЗКА ФАЙЛОВ: Drag & Drop
    // ============================================
    
    const fileUploadArea = document.getElementById('file-upload-area');
    
    if (fileUploadArea) {
        // Предотвращаем стандартное поведение drag & drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Подсветка при наведении файла
        ['dragenter', 'dragover'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, () => {
                fileUploadArea.classList.add('highlight');
            });
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, () => {
                fileUploadArea.classList.remove('highlight');
            });
        });
        
        // Обработка drop
        fileUploadArea.addEventListener('drop', handleDrop);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        }
        
        function handleFiles(files) {
            ([...files]).forEach(uploadFile);
        }
        
        function uploadFile(file) {
            console.log('Загружаем файл:', file.name);
            // Здесь добавьте логику загрузки файла на сервер
        }
    }
    
    // ============================================
    // 🔔 УВЕДОМЛЕНИЯ: Автоматическое скрытие
    // ============================================
    
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(20px)';
            
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        }, 5000);
    });
    
    // ============================================
    // 🎨 КНОПКИ: Эффект ripple при клике
    // ============================================
    
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple-effect');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // ============================================
    // 📊 СТАТИСТИКА: Анимация счетчиков
    // ============================================
    
    function animateCounter(element, target, duration = 1000) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = target.toLocaleString('ru-RU');
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current).toLocaleString('ru-RU');
            }
        }, 16);
    }
    
    // Запускаем анимацию для всех счетчиков
    const statNumbers = document.querySelectorAll('.stat-number');
    
    const observerOptions = {
        threshold: 0.5
    };
    
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseInt(entry.target.textContent.replace(/[^\d]/g, ''));
                if (!isNaN(target)) {
                    animateCounter(entry.target, target);
                }
                statsObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    statNumbers.forEach(stat => {
        statsObserver.observe(stat);
    });
    
    // ============================================
    // 🌓 ТЕМНАЯ ТЕМА (опционально)
    // ============================================
    
    const themeToggle = document.getElementById('theme-toggle');
    
    if (themeToggle) {
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-theme', currentTheme);
        
        themeToggle.addEventListener('click', () => {
            const theme = document.body.getAttribute('data-theme');
            const newTheme = theme === 'light' ? 'dark' : 'light';
            
            document.body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
    
    // ============================================
    // 🔍 ПОИСК В РЕАЛЬНОМ ВРЕМЕНИ (для документов)
    // ============================================
    
    const searchInput = document.getElementById('search-documents');
    
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const documents = document.querySelectorAll('.document-item');
            
            documents.forEach(doc => {
                const text = doc.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    doc.style.display = 'block';
                } else {
                    doc.style.display = 'none';
                }
            });
        });
    }
    
    // ============================================
    // 📱 МОБИЛЬНОЕ МЕНЮ
    // ============================================
    
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const navMenu = document.querySelector('nav ul');
    
    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('show-mobile-menu');
        });
    }
    
    // ============================================
    // ✅ ВАЛИДАЦИЯ ФОРМ
    // ============================================
    
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = form.querySelectorAll('input[required], textarea[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.style.borderColor = '#dc3545';
                    
                    // Убираем красную границу при вводе
                    input.addEventListener('input', function() {
                        this.style.borderColor = '';
                    }, { once: true });
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Пожалуйста, заполните все обязательные поля');
            }
        });
    });
    
    // ============================================
    // 🎉 ПРИВЕТСТВИЕ ДЛЯ НОВЫХ ПОЛЬЗОВАТЕЛЕЙ
    // ============================================
    
    const isNewUser = localStorage.getItem('visited');
    
    if (!isNewUser && window.location.pathname === '/dashboard') {
        // Показываем приветственное сообщение
        setTimeout(() => {
            showWelcomeToast();
            localStorage.setItem('visited', 'true');
        }, 500);
    }
    
    function showWelcomeToast() {
        const toast = document.createElement('div');
        toast.className = 'alert alert-success';
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.style.maxWidth = '400px';
        toast.innerHTML = `
            <h4>🎉 Добро пожаловать!</h4>
            <p>Начните с загрузки вашего первого медицинского документа</p>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
    
    // ============================================
    // 🔒 БЕЗОПАСНОСТЬ: Предотвращение консоли в продакшене
    // ============================================
    
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        // Отключаем console в production (опционально)
        // console.log = function() {};
        // console.warn = function() {};
        // console.error = function() {};
    }
    
    console.log('✅ Medical Assistant - JavaScript загружен успешно!');
});

// ============================================
// 🎨 CSS ДЛЯ RIPPLE ЭФФЕКТА
// ============================================

const style = document.createElement('style');
style.textContent = `
    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.5);
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .highlight {
        background: rgba(0, 201, 167, 0.1);
        border-color: var(--primary-color) !important;
    }
`;
document.head.appendChild(style);