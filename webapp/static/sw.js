// 📱 Service Worker для PWA с обработкой suspend-режима
const CACHE_NAME = 'pulsebook-v5';
const urlsToCache = [
  '/static/css/style.css',
  '/static/css/mobile.css',
  '/static/js/app.js',
  '/static/js/mobile.js',
  '/static/favicon.svg'
];

// Установка SW - кэшируем основные файлы
self.addEventListener('install', (event) => {
  self.skipWaiting(); // ← добавь эту строку
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('✅ Кэш открыт');
        return cache.addAll(urlsToCache);
      })
  );
});

// Активация SW - удаляем старые кэши
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Удаляем старый кэш:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim()) // ← и эту строку
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // HTML страницы — всегда из сети (чтобы не терять query параметры)
  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request));
    return;
  }
  
  // Статика — сначала кэш, потом сеть
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        return response || fetch(event.request);
      })
  );
});