import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Улучшенный генератор контента для футбольного бота"""
    
    def __init__(self, database_manager=None):
        self.db = database_manager
        self.load_content_templates()
        self.load_football_data()
    
    def load_content_templates(self):
        """Загрузка шаблонов для генерации контента"""
        
        # Шаблоны для срочных новостей (15 минут)
        self.quick_news_templates = [
            "🔥 {team} готовится к решающему матчу - эксклюзивные кадры с тренировки",
            "⚡ {player} показал феноменальную форму на сегодняшней тренировке",
            "📈 {team} демонстрирует впечатляющую статистику в текущем сезоне",
            "🏆 Тренер {team} раскрыл секретную тактику перед важным матчем",
            "💪 {player} полностью восстановился и готов к возвращению на поле",
            "📊 Аналитики прогнозируют рост позиций {team} в турнирной таблице",
            "🎯 {team} активно работает над усилением состава в зимнее окно",
            "⭐ {player} получил особое признание от болельщиков и экспертов",
            "🔄 {team} меняет игровую схему для достижения лучших результатов",
            "📢 Официальное заявление руководства {team} о планах на сезон"
        ]
        
        # Шаблоны для полных новостей (30 минут)
        self.full_news_templates = [
            {
                "title": "{team} одержал убедительную победу со счетом {score} над {opponent}",
                "content": "В напряженном матче {tournament} команда {team} продемонстрировала отличную игру, обыграв {opponent} со счетом {score}. Ключевую роль в победе сыграл {player}, который {achievement}. Тренер команды отметил высокий уровень подготовки игроков и их стремление к победе.",
                "tags": ["матч", "победа", "результат"]
            },
            {
                "title": "{player} установил новый рекорд, забив {goals} голов в матче против {opponent}",
                "content": "Звездный нападающий {team} {player} вошел в историю саудовского футбола, установив новый рекорд результативности. В матче против {opponent} он забил {goals} голов, продемонстрировав исключительное мастерство. Болельщики устроили овацию, а тренерский штаб выразил гордость за достижения игрока.",
                "tags": ["рекорд", "голы", "игрок"]
            },
            {
                "title": "{team} объявил о трансфере {player} за {amount} миллионов долларов",
                "content": "Руководство {team} официально подтвердило подписание контракта с {player}. Сумма трансфера составила {amount} миллионов долларов, что делает его одним из самых дорогих в истории саудовского футбола. Новый игрок уже приступил к тренировкам и готов дебютировать в ближайшем матче.",
                "tags": ["трансфер", "подписание", "новичок"]
            },
            {
                "title": "Тренер {team} представил новую тактическую схему перед стартом сезона",
                "content": "Главный тренер {team} провел пресс-конференцию, на которой представил обновленную тактическую схему команды. Новая система игры направлена на усиление атакующих действий и улучшение контроля мяча. Игроки положительно отреагировали на изменения и готовы применить новую тактику в официальных матчах.",
                "tags": ["тактика", "тренер", "стратегия"]
            },
            {
                "title": "{team} поднялся на {position} место в турнирной таблице после серии побед",
                "content": "Благодаря впечатляющей серии из {wins} побед подряд, {team} значительно улучшил свои позиции в турнирной таблице. Команда теперь занимает {position} место и имеет реальные шансы на попадание в еврокубки. Ключевую роль в успехе сыграли {player} и слаженная работа всей команды.",
                "tags": ["таблица", "позиция", "успех"]
            }
        ]
        
        # Шаблоны для матчей
        self.match_templates = [
            "🔥 Центральный матч тура: {home} принимает {away}",
            "⚽ Принципиальное дерби: {home} vs {away}",
            "🏆 Битва за очки: {home} встречается с {away}",
            "💥 Горячий матч: {home} против {away}",
            "🎯 Ключевая встреча: {home} - {away}"
        ]
        
        # Шаблоны для турнирной таблицы
        self.table_templates = [
            "📊 **ТУРНИРНАЯ ТАБЛИЦА - САУДОВСКАЯ ПРО ЛИГА**\n\n*Актуальные позиции команд после {round} тура*",
            "🏆 **ПОЛОЖЕНИЕ КОМАНД В ЧЕМПИОНАТЕ**\n\n*Борьба за титул продолжается!*",
            "📈 **РЕЙТИНГ КОМАНД САУДОВСКОЙ ЛИГИ**\n\n*Кто лидирует в гонке за чемпионство?*"
        ]
    
    def load_football_data(self):
        """Загрузка футбольных данных"""
        
        # Саудовские команды с реальными данными
        self.saudi_teams = [
            {"name": "Аль-Хиляль", "city": "Эр-Рияд", "founded": 1957, "stadium": "Стадион Короля Фахда"},
            {"name": "Аль-Насср", "city": "Эр-Рияд", "founded": 1955, "stadium": "Стадион Мршуд"},
            {"name": "Аль-Иттихад", "city": "Джидда", "founded": 1927, "stadium": "Стадион Короля Абдулазиза"},
            {"name": "Аль-Ахли", "city": "Джидда", "founded": 1937, "stadium": "Стадион Короля Абдуллы"},
            {"name": "Аль-Шабаб", "city": "Эр-Рияд", "founded": 1947, "stadium": "Стадион Принца Фейсала"},
            {"name": "Аль-Таавун", "city": "Бурайда", "founded": 1956, "stadium": "Стадион Короля Абдуллы"},
            {"name": "Аль-Фатех", "city": "Эль-Хуфуф", "founded": 1958, "stadium": "Стадион Принца Абдуллы"},
            {"name": "Аль-Райян", "city": "Табук", "founded": 1967, "stadium": "Стадион Принца Фахда"},
            {"name": "Аль-Веда", "city": "Мекка", "founded": 1945, "stadium": "Стадион Короля Абдулазиза"},
            {"name": "Дамак", "city": "Хамис-Мушайт", "founded": 1972, "stadium": "Стадион Принца Султана"},
            {"name": "Аль-Хазм", "city": "Эр-Расс", "founded": 1957, "stadium": "Стадион Принца Абдулрахмана"},
            {"name": "Аль-Фейсали", "city": "Эль-Маджмаа", "founded": 1954, "stadium": "Стадион Принца Салмана"}
        ]
        
        # Известные игроки саудовской лиги
        self.famous_players = [
            {"name": "Криштиану Роналду", "team": "Аль-Насср", "position": "Нападающий", "nationality": "Португалия"},
            {"name": "Садио Мане", "team": "Аль-Насср", "position": "Крайний нападающий", "nationality": "Сенегал"},
            {"name": "Рияд Марез", "team": "Аль-Ахли", "position": "Крайний нападающий", "nationality": "Алжир"},
            {"name": "Н'Голо Канте", "team": "Аль-Иттихад", "position": "Полузащитник", "nationality": "Франция"},
            {"name": "Карим Бензема", "team": "Аль-Иттихад", "position": "Нападающий", "nationality": "Франция"},
            {"name": "Роберто Фирмино", "team": "Аль-Ахли", "position": "Нападающий", "nationality": "Бразилия"},
            {"name": "Неймар", "team": "Аль-Хиляль", "position": "Крайний нападающий", "nationality": "Бразилия"},
            {"name": "Малком", "team": "Аль-Хиляль", "position": "Крайний нападающий", "nationality": "Бразилия"},
            {"name": "Фабиньо", "team": "Аль-Иттихад", "position": "Полузащитник", "nationality": "Бразилия"},
            {"name": "Милинкович-Савич", "team": "Аль-Хиляль", "position": "Полузащитник", "nationality": "Сербия"}
        ]
        
        # Турниры
        self.tournaments = [
            "Саудовская Про Лига",
            "Кубок Саудовской Аравии",
            "Суперкубок Саудовской Аравии",
            "Азиатская Лига чемпионов",
            "Кубок Короля Салмана"
        ]
        
        # ТВ каналы
        self.tv_channels = [
            "SSC Sport 1", "SSC Sport 2", "SSC Sport 3",
            "beIN Sports 1", "beIN Sports 2",
            "Dubai Sports", "Abu Dhabi Sports",
            "KSA Sports", "Saudi Sports"
        ]
        
        # Достижения игроков
        self.player_achievements = [
            "забил решающий гол на последних минутах",
            "сделал голевую передачу",
            "отразил пенальти",
            "забил дубль",
            "оформил хет-трик",
            "получил желтую карточку за грубую игру",
            "был удален с поля",
            "стал лучшим игроком матча",
            "установил новый рекорд скорости",
            "провел 90 минут без замен"
        ]
    
    def generate_smart_quick_news(self, use_real_data: bool = True) -> Dict:
        """Умная генерация срочных новостей с использованием реальных данных"""
        
        # Если есть доступ к БД, пытаемся использовать реальные данные
        if use_real_data and self.db:
            # Получаем последние матчи или события из БД
            recent_matches = self.db.get_today_matches()
            if recent_matches:
                match = random.choice(recent_matches)
                template = random.choice([
                    f"🔥 Подготовка к матчу: {match['home']} vs {match['away']} в {match['time']}",
                    f"⚽ Последние новости перед игрой {match['home']} - {match['away']}",
                    f"📺 Матч {match['home']} против {match['away']} покажет {match['tv']}"
                ])
                
                content = f"Команды активно готовятся к предстоящему матчу в рамках {match['tournament']}. Болельщики с нетерпением ждут начала игры."
                
                return {
                    'title': template,
                    'content': content,
                    'news_type': 'quick_real',
                    'source': 'database',
                    'importance': 2
                }
        
        # Генерируем новость на основе шаблонов
        team_data = random.choice(self.saudi_teams)
        player_data = random.choice(self.famous_players)
        
        template = random.choice(self.quick_news_templates)
        title = template.format(
            team=team_data['name'],
            player=player_data['name']
        )
        
        # Генерируем содержание на основе типа новости
        content_options = [
            f"Источники в клубе сообщают о позитивных изменениях в команде {team_data['name']}.",
            f"Эксперты отмечают высокий уровень подготовки игроков {team_data['name']}.",
            f"Болельщики {team_data['name']} выражают поддержку команде перед важными матчами.",
            f"Тренерский штаб {team_data['name']} работает над улучшением игровых показателей.",
            f"Статистика показывает рост популярности {team_data['name']} среди фанатов."
        ]
        
        return {
            'title': title,
            'content': random.choice(content_options),
            'news_type': 'quick_generated',
            'source': 'generator',
            'tags': ['срочно', team_data['name']],
            'importance': 1
        }
    
    def generate_smart_full_news(self, use_real_data: bool = True) -> List[Dict]:
        """Умная генерация полных новостей"""
        
        news_list = []
        
        # Генерируем 3-5 новостей
        for _ in range(random.randint(3, 5)):
            template = random.choice(self.full_news_templates)
            
            # Выбираем случайные данные
            team_data = random.choice(self.saudi_teams)
            opponent_data = random.choice([t for t in self.saudi_teams if t != team_data])
            player_data = random.choice([p for p in self.famous_players if p['team'] == team_data['name']])
            
            if not player_data:
                player_data = random.choice(self.famous_players)
            
            # Генерируем динамические данные
            score = f"{random.randint(1, 4)}-{random.randint(0, 3)}"
            goals = random.randint(1, 3)
            amount = random.randint(10, 80)
            position = random.randint(1, 8)
            wins = random.randint(3, 7)
            achievement = random.choice(self.player_achievements)
            tournament = random.choice(self.tournaments)
            
            # Заполняем шаблон
            title = template['title'].format(
                team=team_data['name'],
                opponent=opponent_data['name'],
                player=player_data['name'],
                score=score,
                goals=goals,
                amount=amount,
                position=position
            )
            
            content = template['content'].format(
                team=team_data['name'],
                opponent=opponent_data['name'],
                player=player_data['name'],
                score=score,
                goals=goals,
                amount=amount,
                position=position,
                wins=wins,
                achievement=achievement,
                tournament=tournament
            )
            
            # Добавляем дополнительную информацию
            extended_content = content + f" Матч проходил на стадионе {team_data['stadium']} в городе {team_data['city']}."
            
            news_item = {
                'title': title,
                'content': extended_content,
                'summary': content[:100] + "...",
                'news_type': 'full_generated',
                'source': 'generator',
                'tags': template['tags'] + [team_data['name'], player_data['name']],
                'importance': random.randint(1, 3),
                'time': (datetime.now() - timedelta(hours=random.randint(1, 6))).strftime('%H:%M')
            }
            
            news_list.append(news_item)
        
        return news_list
    
    def generate_smart_matches(self, date: str = None) -> List[Dict]:
        """Умная генерация расписания матчей"""
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Если есть БД, сначала проверяем реальные данные
        if self.db:
            real_matches = self.db.get_today_matches()
            if real_matches:
                return real_matches
        
        # Генерируем матчи
        matches = []
        
        # Случайно решаем, будут ли матчи (80% вероятность)
        if random.random() < 0.2:
            return []
        
        num_matches = random.randint(1, 4)
        used_teams = set()
        
        for _ in range(num_matches):
            # Выбираем команды, которые еще не играют
            available_teams = [t for t in self.saudi_teams if t['name'] not in used_teams]
            
            if len(available_teams) < 2:
                break
            
            home_team = random.choice(available_teams)
            away_team = random.choice([t for t in available_teams if t != home_team])
            
            used_teams.add(home_team['name'])
            used_teams.add(away_team['name'])
            
            match = {
                'home': home_team['name'],
                'away': away_team['name'],
                'time': f"{random.randint(15, 22)}:{random.choice(['00', '30'])}",
                'tournament': random.choice(self.tournaments),
                'tv': random.choice(self.tv_channels),
                'venue': home_team['stadium'],
                'status': 'scheduled'
            }
            
            matches.append(match)
        
        return matches
    
    def generate_smart_league_table(self) -> List[Dict]:
        """Умная генерация турнирной таблицы"""
        
        # Если есть БД, пытаемся получить реальные данные
        if self.db:
            real_table = self.db.get_league_standings()
            if real_table:
                return real_table
        
        # Генерируем реалистичную таблицу
        table = []
        
        for i, team_data in enumerate(self.saudi_teams):
            # Создаем реалистичную статистику
            games = random.randint(25, 30)
            wins = max(0, random.randint(8, 20) - i)  # Лидеры выигрывают больше
            losses = max(0, random.randint(2, 12) + i//2)  # Аутсайдеры проигрывают больше
            draws = games - wins - losses
            
            goals_for = wins * random.randint(1, 3) + draws * random.randint(0, 2)
            goals_against = losses * random.randint(1, 3) + draws * random.randint(0, 2)
            goal_difference = goals_for - goals_against
            points = wins * 3 + draws
            
            table.append({
                'name': team_data['name'],
                'position': i + 1,
                'games': games,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'goals_for': goals_for,
                'goals_against': goals_against,
                'goal_difference': goal_difference,
                'points': points,
                'city': team_data['city'],
                'stadium': team_data['stadium']
            })
        
        # Сортируем по очкам и разности голов
        table.sort(key=lambda x: (x['points'], x['goal_difference']), reverse=True)
        
        # Обновляем позиции после сортировки
        for i, team in enumerate(table):
            team['position'] = i + 1
        
        return table
    
    def format_league_table_message(self, table: List[Dict], detailed: bool = False) -> str:
        """Форматирование турнирной таблицы для сообщения"""
        
        header = random.choice(self.table_templates)
        
        if detailed:
            text = header + "\n\n```\n"
            text += "Поз Команда           И  П  Н  Пр ГЗ ГП  О\n"
            text += "─────────────────────────────────────────\n"
            
            for team in table[:12]:  # Показываем топ-12
                name = team['name'][:12].ljust(12)
                text += f"{team['position']:2d}. {name} {team['games']:2d} {team['wins']:2d} {team['draws']:2d} {team['losses']:2d} {team['goals_for']:2d} {team['goals_against']:2d} {team['points']:2d}\n"
        else:
            text = header + "\n\n```\n"
            text += "Поз Команда           И  О\n"
            text += "───────────────────────────\n"
            
            for team in table[:8]:  # Показываем топ-8
                name = team['name'][:12].ljust(12)
                text += f"{team['position']:2d}. {name} {team['games']:2d} {team['points']:2d}\n"
        
        text += "```\n\n"
        text += f"📅 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        text += "🏆 Следите за чемпионатом вместе с нами!"
        
        return text
    
    def format_matches_message(self, matches: List[Dict], date: str = None) -> str:
        """Форматирование расписания матчей для сообщения"""
        
        if not date:
            date = datetime.now().strftime('%d.%m.%Y')
        
        text = f"⚽ **МАТЧИ НА СЕГОДНЯ ({date})**\n\n"
        
        if matches:
            for i, match in enumerate(matches, 1):
                match_template = random.choice(self.match_templates)
                match_title = match_template.format(
                    home=match['home'],
                    away=match['away']
                )
                
                text += f"**{i}. {match_title}**\n"
                text += f"🕐 {match['time']}\n"
                text += f"🏆 {match['tournament']}\n"
                text += f"📺 {match['tv']}\n"
                if 'venue' in match:
                    text += f"🏟️ {match['venue']}\n"
                text += "\n"
        else:
            text += "😔 На сегодня матчей не запланировано\n\n"
            text += "📅 Следите за расписанием - скоро будут новые игры!\n\n"
        
        text += "📱 Используйте бота для быстрого доступа к информации!"
        
        return text
    
    def get_content_stats(self) -> Dict:
        """Получение статистики генерации контента"""
        
        stats = {
            'teams_count': len(self.saudi_teams),
            'players_count': len(self.famous_players),
            'tournaments_count': len(self.tournaments),
            'quick_templates': len(self.quick_news_templates),
            'full_templates': len(self.full_news_templates),
            'match_templates': len(self.match_templates),
            'table_templates': len(self.table_templates)
        }
        
        if self.db:
            db_stats = self.db.get_database_stats()
            stats.update(db_stats)
        
        return stats

# Пример использования
if __name__ == "__main__":
    print("🧪 Тестирование генератора контента...")
    
    generator = ContentGenerator()
    
    # Тест генерации срочных новостей
    quick_news = generator.generate_smart_quick_news(use_real_data=False)
    print(f"⚡ Срочная новость: {quick_news['title']}")
    
    # Тест генерации полных новостей
    full_news = generator.generate_smart_full_news(use_real_data=False)
    print(f"📰 Сгенерировано {len(full_news)} полных новостей")
    
    # Тест генерации матчей
    matches = generator.generate_smart_matches()
    print(f"⚽ Сгенерировано {len(matches)} матчей")
    
    # Тест генерации таблицы
    table = generator.generate_smart_league_table()
    print(f"📊 Сгенерирована таблица с {len(table)} командами")
    
    # Статистика
    stats = generator.get_content_stats()
    print(f"📈 Статистика: {stats}")
    
    print("🎉 Тестирование завершено!")

