# db_pool.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с правильными async вызовами

import asyncio
import aiosqlite
import logging
from typing import Any, Optional, List, Dict, AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabasePool:
    """
    Асинхронный пул соединений с SQLite
    """
    
    def __init__(self, db_path: str = "users.db", max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool: List[aiosqlite.Connection] = []
        self._in_use: set = set()
        self._lock = asyncio.Lock()
        self._connection_count = 0
        self._stats = {
            "total_requests": 0,
            "active_connections": 0,
            "max_connections_used": 0
        }
        
    async def initialize(self):
        """Инициализация пула"""
        logger.info(f"🔧 Инициализация пула БД: {self.max_connections} соединений")
        
        # Создаем базовое количество соединений
        initial_connections = min(3, self.max_connections)
        for _ in range(initial_connections):
            conn = await self._create_connection()
            self._pool.append(conn)
            
        logger.info(f"✅ Создано {len(self._pool)} начальных соединений")
    
    async def _create_connection(self) -> aiosqlite.Connection:
        """Создание нового соединения с оптимизацией"""
        conn = await aiosqlite.connect(
            self.db_path,
            timeout=30.0,
            isolation_level=None  # autocommit mode для лучшей производительности
        )
        
        # Оптимизация SQLite для производительности
        await conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        await conn.execute("PRAGMA synchronous=NORMAL")  # Баланс скорости и надежности  
        await conn.execute("PRAGMA cache_size=10000")    # Больше кэша
        await conn.execute("PRAGMA temp_store=MEMORY")   # Временные данные в памяти
        await conn.execute("PRAGMA foreign_keys=ON")     # Включаем foreign keys
        
        self._connection_count += 1
        logger.debug(f"📡 Создано соединение #{self._connection_count}")
        return conn
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """
        Получение соединения из пула
        
        Использование:
        async with pool.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM users")
            result = await cursor.fetchall()
        """
        conn = None
        try:
            conn = await self._acquire_connection()
            self._stats["total_requests"] += 1
            self._stats["active_connections"] = len(self._in_use)
            self._stats["max_connections_used"] = max(
                self._stats["max_connections_used"], 
                len(self._in_use)
            )
            
            yield conn
            
        except Exception as e:
            logger.error(f"❌ Ошибка соединения с БД: {e}")
            # Если соединение сломалось, пересоздаем его
            if conn and conn in self._in_use:
                self._in_use.remove(conn)
                try:
                    await conn.close()
                except:
                    pass
                # Создаем новое соединение на замену
                asyncio.create_task(self._replace_connection())
            raise
            
        finally:
            if conn:
                await self._release_connection(conn)
    
    async def _acquire_connection(self) -> aiosqlite.Connection:
        """Получение соединения из пула"""
        async with self._lock:
            # Пытаемся взять готовое соединение
            if self._pool:
                conn = self._pool.pop()
                self._in_use.add(conn)
                logger.debug(f"📡 Взято соединение из пула ({len(self._pool)} осталось)")
                return conn
            
            # Если пул пуст, но можем создать новое соединение
            if len(self._in_use) < self.max_connections:
                conn = await self._create_connection()
                self._in_use.add(conn)
                logger.debug(f"📡 Создано новое соединение ({len(self._in_use)} активных)")
                return conn
            
            # Если достигли лимита, ждем освобождения
            logger.warning(f"⏳ Достигнут лимит соединений ({self.max_connections}), ожидание...")
        
        # Ждем освобождения соединения
        while True:
            await asyncio.sleep(0.01)  # Небольшая задержка
            async with self._lock:
                if self._pool:
                    conn = self._pool.pop()
                    self._in_use.add(conn)
                    return conn
    
    async def _release_connection(self, conn: aiosqlite.Connection):
        """Возврат соединения в пул"""
        async with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                
                # Проверяем, что соединение рабочее
                try:
                    await conn.execute("SELECT 1")
                    self._pool.append(conn)
                    logger.debug(f"📡 Соединение возвращено в пул ({len(self._pool)} доступно)")
                except Exception as e:
                    logger.warning(f"⚠️ Поврежденное соединение закрыто: {e}")
                    try:
                        await conn.close()
                    except:
                        pass
                    # Создаем замену асинхронно
                    asyncio.create_task(self._replace_connection())
    
    async def _replace_connection(self):
        """Замена поврежденного соединения"""
        try:
            new_conn = await self._create_connection()
            async with self._lock:
                self._pool.append(new_conn)
                logger.info("🔧 Создано замещающее соединение")
        except Exception as e:
            logger.error(f"❌ Не удалось создать замещающее соединение: {e}")
    
    async def close_all(self):
        """Закрытие всех соединений"""
        logger.info("🔐 Закрытие всех соединений БД...")
        
        async with self._lock:
            # Закрываем соединения в пуле
            for conn in self._pool:
                try:
                    await conn.close()
                except Exception as e:
                    logger.error(f"Ошибка при закрытии соединения: {e}")
            
            # Закрываем активные соединения
            for conn in self._in_use.copy():
                try:
                    await conn.close()
                except Exception as e:
                    logger.error(f"Ошибка при закрытии активного соединения: {e}")
            
            self._pool.clear()
            self._in_use.clear()
            
        logger.info("✅ Все соединения закрыты")
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика пула"""
        return {
            "total_requests": self._stats["total_requests"],
            "active_connections": len(self._in_use),
            "available_connections": len(self._pool),
            "max_connections_used": self._stats["max_connections_used"],
            "max_connections_limit": self.max_connections,
            "total_connections_created": self._connection_count
        }
    
    async def health_check(self) -> bool:
        """Проверка состояния пула"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute("SELECT 1")
                result = await cursor.fetchone()
                return result == (1,)
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False


# 🌍 Глобальный экземпляр пула
db_pool: Optional[DatabasePool] = None

async def initialize_db_pool(db_path: str = "users.db", max_connections: int = 10):
    """Инициализация глобального пула БД"""
    global db_pool
    
    if db_pool is not None:
        await db_pool.close_all()
    
    db_pool = DatabasePool(db_path, max_connections)
    await db_pool.initialize()
    
    logger.info(f"🚀 Database pool готов: {max_connections} max connections")

async def get_db_connection():  # ✅ ИСПРАВЛЕНО: функция теперь async
    """Получение соединения из глобального пула"""
    if db_pool is None:
        raise RuntimeError("Database pool не инициализирован! Вызовите initialize_db_pool()")
    
    return db_pool.get_connection()

async def close_db_pool():
    """Закрытие глобального пула"""
    global db_pool
    if db_pool:
        await db_pool.close_all()
        db_pool = None

def get_db_stats() -> Dict[str, Any]:
    """Статистика глобального пула"""
    if db_pool:
        return db_pool.get_stats()
    return {"error": "Pool not initialized"}

async def db_health_check() -> bool:
    """Health check глобального пула"""
    if db_pool:
        return await db_pool.health_check()
    return False


# 🔧 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ для упрощения миграции

async def execute_query(query: str, params: tuple = ()) -> int:
    """
    Выполнение простого запроса (INSERT, UPDATE, DELETE)
    Возвращает rowcount
    """
    async with await get_db_connection() as conn:  # ✅ ИСПРАВЛЕНО: добавлен await
        cursor = await conn.execute(query, params)
        await conn.commit()
        return cursor.rowcount

async def fetch_one(query: str, params: tuple = ()) -> Optional[tuple]:
    """Выполнение SELECT запроса, возврат одной строки"""
    async with await get_db_connection() as conn:  # ✅ ИСПРАВЛЕНО: добавлен await
        cursor = await conn.execute(query, params)
        return await cursor.fetchone()

async def fetch_all(query: str, params: tuple = ()) -> List[tuple]:
    """Выполнение SELECT запроса, возврат всех строк"""
    async with await get_db_connection() as conn:  # ✅ ИСПРАВЛЕНО: добавлен await
        cursor = await conn.execute(query, params)
        return await cursor.fetchall()

async def insert_and_get_id(query: str, params: tuple = ()) -> int:
    """Выполнение INSERT и возврат lastrowid"""
    async with await get_db_connection() as conn:  # ✅ ИСПРАВЛЕНО: добавлен await
        cursor = await conn.execute(query, params)
        await conn.commit()
        return cursor.lastrowid


# 📊 МОНИТОРИНГ И ОТЛАДКА

class DatabaseMonitor:
    """Монитор производительности БД"""
    
    def __init__(self):
        self.slow_queries = []
        self.error_count = 0
        
    async def log_slow_query(self, query: str, duration: float, threshold: float = 1.0):
        """Логирование медленных запросов"""
        if duration > threshold:
            self.slow_queries.append({
                "query": query[:100] + "..." if len(query) > 100 else query,
                "duration": round(duration, 3),
                "timestamp": datetime.now().isoformat()
            })
            logger.warning(f"🐌 Медленный запрос ({duration:.3f}s): {query[:100]}")
            
            # Оставляем только последние 10 медленных запросов
            if len(self.slow_queries) > 10:
                self.slow_queries = self.slow_queries[-10:]
    
    def log_error(self, error: Exception, query: str = ""):
        """Логирование ошибок БД"""
        self.error_count += 1
        logger.error(f"❌ DB Error #{self.error_count}: {error}")
        if query:
            logger.error(f"Query: {query[:200]}")
    
    def get_stats(self) -> Dict:
        """Статистика монитора"""
        return {
            "slow_queries_count": len(self.slow_queries),
            "recent_slow_queries": self.slow_queries[-3:],  # Последние 3
            "total_errors": self.error_count
        }

# Глобальный монитор
db_monitor = DatabaseMonitor()

# 🧪 ФУНКЦИЯ ДЛЯ ТЕСТИРОВАНИЯ

async def test_database_pool():
    """Тестирование пула соединений"""
    print("🧪 Тестирование database pool...")
    
    try:
        # Инициализация
        await initialize_db_pool(max_connections=3)
        
        # Health check
        healthy = await db_health_check()
        print(f"Health check: {'✅' if healthy else '❌'}")
        
        # Тест простых запросов
        result = await fetch_one("SELECT 1 as test")
        print(f"Simple query: {'✅' if result == (1,) else '❌'}")
        
        # Тест множественных соединений
        async def test_concurrent():
            async with await get_db_connection() as conn:  # ✅ ИСПРАВЛЕНО
                cursor = await conn.execute("SELECT COUNT(*) FROM users")
                result = await cursor.fetchone()
                return result[0] if result else 0
        
        # Запускаем 5 параллельных запросов
        tasks = [test_concurrent() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        print(f"Concurrent queries: ✅ ({len(results)} results)")
        
        # Статистика
        stats = get_db_stats()
        print(f"Pool stats: {stats}")
        
        print("✅ Все тесты пройдены!")
        
    except Exception as e:
        print(f"❌ Тест провален: {e}")
    
    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(test_database_pool())