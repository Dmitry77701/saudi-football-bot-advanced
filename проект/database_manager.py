import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Расширенный менеджер базы данных для футбольного бота"""
    
    def __init__(self, db_path: str = "football_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация всех таблиц базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для команд
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_id TEXT UNIQUE,
                name TEXT NOT NULL,
                league TEXT,
                country TEXT,
                logo_url TEXT,
                founded INTEGER,
                venue TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица для матчей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_id TEXT UNIQUE,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_team_id TEXT,
                away_team_id TEXT,
                match_date TEXT,
                match_time TEXT,
                tournament TEXT,
                tv_channel TEXT,
                status TEXT DEFAULT 'scheduled',
                home_score INTEGER DEFAULT 0,
                away_score INTEGER DEFAULT 0,
                venue TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица для новостей с улучшенной структурой
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                summary TEXT,
                news_type TEXT,
                source TEXT,
                tags TEXT,
                importance INTEGER DEFAULT 1,
                published_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_published BOOLEAN DEFAULT FALSE,
                publish_count INTEGER DEFAULT 0,
                UNIQUE(title, news_type)
            )
        ''')
        
        # Таблица для турнирной таблицы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS league_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                team_id TEXT,
                position INTEGER,
                games_played INTEGER,
                wins INTEGER,
                draws INTEGER,
                losses INTEGER,
                goals_for INTEGER,
                goals_against INTEGER,
                goal_difference INTEGER,
                points INTEGER,
                league TEXT,
                season TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team_name, league, season)
            )
        ''')
        
        # Таблица для игроков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_id TEXT UNIQUE,
                name TEXT NOT NULL,
                team TEXT,
                position TEXT,
                age INTEGER,
                nationality TEXT,
                goals INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица для кэширования API запросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                params TEXT,
                response_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                UNIQUE(endpoint, params)
            )
        ''')
        
        # Таблица для статистики бота
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type TEXT NOT NULL,
                stat_value TEXT,
                date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ База данных полностью инициализирована")
    
    def save_team(self, team_data: Dict) -> bool:
        """Сохранение информации о команде"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO teams 
                (api_id, name, league, country, logo_url, founded, venue)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                team_data.get('api_id'),
                team_data.get('name'),
                team_data.get('league'),
                team_data.get('country'),
                team_data.get('logo_url'),
                team_data.get('founded'),
                team_data.get('venue')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения команды: {e}")
            return False
    
    def save_match(self, match_data: Dict) -> bool:
        """Сохранение информации о матче"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO matches 
                (api_id, home_team, away_team, home_team_id, away_team_id,
                 match_date, match_time, tournament, tv_channel, status,
                 home_score, away_score, venue)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_data.get('api_id'),
                match_data.get('home_team'),
                match_data.get('away_team'),
                match_data.get('home_team_id'),
                match_data.get('away_team_id'),
                match_data.get('match_date'),
                match_data.get('match_time'),
                match_data.get('tournament'),
                match_data.get('tv_channel'),
                match_data.get('status', 'scheduled'),
                match_data.get('home_score', 0),
                match_data.get('away_score', 0),
                match_data.get('venue')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения матча: {e}")
            return False
    
    def save_news_advanced(self, news_data: Dict) -> bool:
        """Расширенное сохранение новости"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем, существует ли уже такая новость
            cursor.execute(
                "SELECT id, publish_count FROM news WHERE title = ? AND news_type = ?",
                (news_data.get('title'), news_data.get('news_type'))
            )
            existing = cursor.fetchone()
            
            if existing:
                # Если новость уже существует, увеличиваем счетчик попыток публикации
                cursor.execute(
                    "UPDATE news SET publish_count = publish_count + 1 WHERE id = ?",
                    (existing[0],)
                )
                conn.commit()
                conn.close()
                return False  # Не публикуем повторно
            
            # Сохраняем новую новость
            cursor.execute('''
                INSERT INTO news 
                (title, content, summary, news_type, source, tags, importance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                news_data.get('title'),
                news_data.get('content'),
                news_data.get('summary'),
                news_data.get('news_type'),
                news_data.get('source', 'generated'),
                json.dumps(news_data.get('tags', [])),
                news_data.get('importance', 1)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения новости: {e}")
            return False
    
    def get_unpublished_news(self, news_type: str = None, limit: int = 5) -> List[Dict]:
        """Получение неопубликованных новостей"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM news WHERE is_published = FALSE"
            params = []
            
            if news_type:
                query += " AND news_type = ?"
                params.append(news_type)
            
            query += " ORDER BY importance DESC, published_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            news_list = []
            for row in rows:
                news_list.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'summary': row[3],
                    'news_type': row[4],
                    'source': row[5],
                    'tags': json.loads(row[6] or '[]'),
                    'importance': row[7],
                    'published_date': row[8]
                })
            
            conn.close()
            return news_list
        except Exception as e:
            logger.error(f"❌ Ошибка получения новостей: {e}")
            return []
    
    def mark_news_published(self, news_id: int):
        """Отметить новость как опубликованную"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE news SET is_published = TRUE WHERE id = ?",
                (news_id,)
            )
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статуса новости: {e}")
    
    def save_api_cache(self, endpoint: str, params: str, response_data: Any, ttl_minutes: int = 60):
        """Сохранение кэша API запроса"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
            
            cursor.execute('''
                INSERT OR REPLACE INTO api_cache 
                (endpoint, params, response_data, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (endpoint, params, json.dumps(response_data), expires_at))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения кэша: {e}")
    
    def get_api_cache(self, endpoint: str, params: str) -> Optional[Any]:
        """Получение кэшированного ответа API"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT response_data FROM api_cache 
                WHERE endpoint = ? AND params = ? AND expires_at > ?
            ''', (endpoint, params, datetime.now()))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения кэша: {e}")
            return None
    
    def clean_old_cache(self):
        """Очистка устаревшего кэша"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM api_cache WHERE expires_at < ?", (datetime.now(),))
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted > 0:
                logger.info(f"🧹 Очищено {deleted} устаревших записей кэша")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша: {e}")
    
    def save_bot_stat(self, stat_type: str, stat_value: str):
        """Сохранение статистики бота"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bot_stats (stat_type, stat_value, date)
                VALUES (?, ?, ?)
            ''', (stat_type, stat_value, datetime.now().strftime('%Y-%m-%d')))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения статистики: {e}")
    
    def get_today_matches(self) -> List[Dict]:
        """Получение матчей на сегодня из БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT home_team, away_team, match_time, tournament, tv_channel, status
                FROM matches 
                WHERE match_date = ?
                ORDER BY match_time
            ''', (today,))
            
            rows = cursor.fetchall()
            conn.close()
            
            matches = []
            for row in rows:
                matches.append({
                    'home': row[0],
                    'away': row[1],
                    'time': row[2],
                    'tournament': row[3],
                    'tv': row[4],
                    'status': row[5]
                })
            
            return matches
        except Exception as e:
            logger.error(f"❌ Ошибка получения матчей: {e}")
            return []
    
    def get_league_standings(self, league: str = 'Saudi Pro League') -> List[Dict]:
        """Получение турнирной таблицы из БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT team_name, position, games_played, wins, draws, losses,
                       goals_for, goals_against, goal_difference, points
                FROM league_table 
                WHERE league = ?
                ORDER BY position ASC
            ''', (league,))
            
            rows = cursor.fetchall()
            conn.close()
            
            standings = []
            for row in rows:
                standings.append({
                    'name': row[0],
                    'position': row[1],
                    'games': row[2],
                    'wins': row[3],
                    'draws': row[4],
                    'losses': row[5],
                    'goals_for': row[6],
                    'goals_against': row[7],
                    'goal_difference': row[8],
                    'points': row[9]
                })
            
            return standings
        except Exception as e:
            logger.error(f"❌ Ошибка получения таблицы: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """Получение статистики базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Количество записей в каждой таблице
            tables = ['teams', 'matches', 'news', 'league_table', 'players', 'api_cache']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # Количество опубликованных новостей
            cursor.execute("SELECT COUNT(*) FROM news WHERE is_published = TRUE")
            stats['published_news'] = cursor.fetchone()[0]
            
            # Количество неопубликованных новостей
            cursor.execute("SELECT COUNT(*) FROM news WHERE is_published = FALSE")
            stats['unpublished_news'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики БД: {e}")
            return {}

# Пример использования
if __name__ == "__main__":
    # Тестирование менеджера базы данных
    db = DatabaseManager()
    
    # Тестовые данные
    test_team = {
        'api_id': 'test_123',
        'name': 'Аль-Хиляль',
        'league': 'Saudi Pro League',
        'country': 'Saudi Arabia',
        'logo_url': 'https://example.com/logo.png',
        'founded': 1957,
        'venue': 'King Fahd Stadium'
    }
    
    test_news = {
        'title': 'Тестовая новость о футболе',
        'content': 'Содержание тестовой новости',
        'summary': 'Краткое содержание',
        'news_type': 'test',
        'source': 'test_source',
        'tags': ['футбол', 'тест'],
        'importance': 2
    }
    
    # Тестирование функций
    print("🧪 Тестирование базы данных...")
    
    if db.save_team(test_team):
        print("✅ Команда сохранена")
    
    if db.save_news_advanced(test_news):
        print("✅ Новость сохранена")
    
    stats = db.get_database_stats()
    print(f"📊 Статистика БД: {stats}")
    
    print("🎉 Тестирование завершено!")

