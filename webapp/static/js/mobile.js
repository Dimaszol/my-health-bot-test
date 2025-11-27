// 📱 МОБИЛЬНОЕ МЕНЮ - JAVASCRIPT

document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================
    // 🍔 БУРГЕР-МЕНЮ
    // ============================================
    
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenuClose = document.getElementById('mobile-menu-close');
    const mobileMenu = document.getElementById('mobile-menu');
    const mobileMenuOverlay = document.getElementById('mobile-menu-overlay');
    const body = document.body;
    
    // Открытие меню
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            openMobileMenu();
        });
    }
    
    // Закрытие меню по кнопке закрытия
    if (mobileMenuClose) {
        mobileMenuClose.addEventListener('click', function() {
            closeMobileMenu();
        });
    }
    
    // Закрытие меню по клику на оверлей
    if (mobileMenuOverlay) {
        mobileMenuOverlay.addEventListener('click', function() {
            closeMobileMenu();
        });
    }
    
    // Закрытие меню при клике на пункт меню
    const mobileMenuLinks = document.querySelectorAll('.mobile-menu-items a');
    mobileMenuLinks.forEach(link => {
        link.addEventListener('click', function() {
            closeMobileMenu();
        });
    });
    
    // Функция открытия меню
    function openMobileMenu() {
        mobileMenu.classList.add('active');
        mobileMenuOverlay.classList.add('active');
        mobileMenuToggle.classList.add('active');
        body.style.overflow = 'hidden'; // Блокируем скролл страницы
    }
    
    // Функция закрытия меню
    function closeMobileMenu() {
        mobileMenu.classList.remove('active');
        mobileMenuOverlay.classList.remove('active');
        mobileMenuToggle.classList.remove('active');
        body.style.overflow = ''; // Возвращаем скролл
    }
    
    // Закрытие меню по Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
            closeMobileMenu();
        }
    });

    // ============================================
    // 👆 СВАЙПЫ ДЛЯ ОТКРЫТИЯ/ЗАКРЫТИЯ МЕНЮ
    // ============================================

    let touchStartX = 0;
    let touchEndX = 0;
    let touchStartY = 0;

    // Обработчики свайпа для всего документа
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        const touchEndY = e.changedTouches[0].screenY;
        
        // Проверяем что свайп горизонтальный (не вертикальный скролл)
        const verticalDiff = Math.abs(touchEndY - touchStartY);
        const horizontalDiff = Math.abs(touchEndX - touchStartX);
        
        if (horizontalDiff > verticalDiff && horizontalDiff > 50) {
            handleSwipe();
        }
    }, { passive: true });

    function handleSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        
        // Свайп вправо (открытие меню) - увеличиваем зону
        if (swipeDistance > 100 && touchStartX < 100 && !mobileMenu.classList.contains('active')) {
            openMobileMenu();
        }
        
        // Свайп влево (закрытие меню) - работает из любого места
        if (swipeDistance < -100 && mobileMenu.classList.contains('active')) {
            closeMobileMenu();
        }
    }
 
    // ============================================
    // 🎯 АКТИВНАЯ СТРАНИЦА В МЕНЮ
    // ============================================
    
    // Подсвечиваем текущую страницу в мобильном меню
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.mobile-menu-items a');
    
    menuLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.background = 'var(--background-light)';
            link.style.borderLeftColor = 'var(--primary-color)';
        }
    });
    
    // ============================================
    // 📏 ИСПРАВЛЕНИЕ 100vh НА iOS
    // ============================================
    
    // Исправляем проблему с 100vh на iOS (адресная строка)
    function setVH() {
        let vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }
    
    setVH();
    window.addEventListener('resize', setVH);
    window.addEventListener('orientationchange', setVH);
   
    // ============================================
    // 📊 VIBRATION FEEDBACK (для поддерживающих устройств)
    // ============================================
    
    // Добавляем вибрацию при нажатии на важные кнопки
    const vibrateButtons = document.querySelectorAll('.btn, .mobile-menu-btn');
    
    vibrateButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Проверяем поддержку вибрации
            if ('vibrate' in navigator) {
                navigator.vibrate(10); // Короткая вибрация 10мс
            }
        });
    });
    
    // ============================================
    // 🎨 ПЛАВНОЕ СКРЫТИЕ HEADER ПРИ СКРОЛЛЕ (опционально)
    // ============================================
    
    // Можно раскомментировать, если хочешь скрывать header при скролле вниз
    /*
    let lastScrollTop = 0;
    const header = document.querySelector('header');
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > lastScrollTop && scrollTop > 100) {
            // Скроллим вниз
            header.style.transform = 'translateY(-100%)';
        } else {
            // Скроллим вверх
            header.style.transform = 'translateY(0)';
        }
        
        lastScrollTop = scrollTop;
    }, { passive: true });
    */
    
    // ============================================
    // 📱 ОПРЕДЕЛЕНИЕ УСТРОЙСТВА
    // ============================================
    
    // Добавляем класс к body для определения типа устройства
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
    const isAndroid = /Android/i.test(navigator.userAgent);
    
    if (isMobile) {
        body.classList.add('is-mobile');
    }
    if (isIOS) {
        body.classList.add('is-ios');
    }
    if (isAndroid) {
        body.classList.add('is-android');
    }
    
    // ============================================
    // 🌐 ЛОГИРОВАНИЕ (для отладки)
    // ============================================
    
    // В production режиме закомментируй эту секцию
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('📱 Мобильное меню инициализировано');
        console.log('📏 Viewport height:', window.innerHeight);
        console.log('📐 Screen size:', window.screen.width + 'x' + window.screen.height);
        console.log('📱 Device:', isMobile ? 'Mobile' : 'Desktop');
    }
    
    // ============================================
    // 🚀 SERVICE WORKER (для PWA - опционально)
    // ============================================
    
    // Регистрируем service worker для PWA функциональности
    if ('serviceWorker' in navigator && window.location.protocol === 'https:') {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/static/sw.js')
                .then(function(registration) {
                    console.log('✅ Service Worker зарегистрирован:', registration.scope);
                })
                .catch(function(error) {
                    console.log('❌ Ошибка регистрации Service Worker:', error);
                });
        });
    }
    
    // ============================================
    // 💾 ОФФЛАЙН ИНДИКАТОР
    // ============================================
    
    // Показываем статус подключения
    function updateOnlineStatus() {
        if (!navigator.onLine) {
            // Можно показать уведомление об оффлайн режиме
            console.log('📵 Оффлайн режим');
        } else {
            console.log('✅ Онлайн режим');
        }
    }
    
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    
});

// ============================================
// 🎯 ЭКСПОРТИРУЕМ ФУНКЦИИ (если нужно)
// ============================================

window.mobileMenu = {
    open: function() {
        const event = new Event('click');
        document.getElementById('mobile-menu-toggle')?.dispatchEvent(event);
    },
    close: function() {
        const event = new Event('click');
        document.getElementById('mobile-menu-close')?.dispatchEvent(event);
    }
};