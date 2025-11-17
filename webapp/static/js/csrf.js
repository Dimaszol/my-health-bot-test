// webapp/static/js/csrf.js
// 🛡️ Утилита для получения CSRF токена из cookies

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getCSRFToken() {
    return getCookie('csrf_token');
}

// ✅ Автоматически добавляем CSRF токен ко всем fetch запросам
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    // Только для POST, PUT, DELETE, PATCH
    if (options.method && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(options.method.toUpperCase())) {
        options.headers = options.headers || {};
        options.headers['X-CSRF-Token'] = getCSRFToken();
    }
    return originalFetch(url, options);
};