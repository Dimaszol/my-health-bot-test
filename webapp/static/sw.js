// 📱 Service Worker для PWA с обработкой suspend-режима
const CACHE_NAME = 'pulsebook-v2';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/css/mobile.css',
  '/static/js/app.js',
  '/static/js/mobile.js',
  '/static/favicon.svg'
];

// Установка SW - кэшируем основные файлы
self.addEventListener('install', (event) => {
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
    })
  );
});

// Перехват запросов - сначала кэш, потом сеть
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        return response || fetch(event.request);
      })
  );
});

// ✅ НОВОЕ: Перехват уведомлений при ошибках
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  // Если это уведомление о готовности документа - открываем страницу
  if (event.notification.tag === 'document-ready') {
    const documentId = event.notification.data?.documentId;
    const url = documentId 
      ? `/dashboard/documents?new_doc_id=${documentId}`
      : '/dashboard/documents';
    
    event.waitUntil(
      clients.openWindow(url)
    );
  }
});

// ✅ НОВОЕ: Показываем красивое уведомление вместо ошибки
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'DOCUMENT_UPLOAD_COMPLETE') {
    // ✅ Получаем переведённые тексты из сообщения
    const title = event.data.title || '✅ Документ готов!';
    const body = event.data.body || 'Анализ завершён. Нажмите чтобы посмотреть результат.';
    const actionTitle = event.data.actionTitle || 'Открыть документ';
    
    // Показываем уведомление
    self.registration.showNotification(title, {
      body: body,
      icon: '/static/favicon.svg',
      badge: '/static/favicon.svg',
      tag: 'document-ready',
      requireInteraction: true,
      data: {
        documentId: event.data.documentId
      },
      actions: [
        {
          action: 'view',
          title: actionTitle
        }
      ]
    });
  }
});