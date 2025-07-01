import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

class InteractiveHandler:
    """Обработчик интерактивных функций бота в стиле Матч ТВ"""
    
    def __init__(self, db_path: str = 'match_tv_bot.db'):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_user_database()
        
    def _init_user_database(self):
        """Инициализация базы данных пользователей"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица подписок пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    user_id INTEGER,
                    team_name TEXT,
                    player_name TEXT,
                    subscription_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Таблица пользовательских запросов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_requests (
                    user_id INTEGER,
                    request_type TEXT,
                    request_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица пользовательских настроек
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'ru',
                    notification_time TEXT DEFAULT '09:00',
                    timezone TEXT DEFAULT 'UTC+3',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации базы данных пользователей: {e}")

    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user_id = update.effective_user.id
        
        # Регистрируем пользователя
        self._register_user(user_id)
        
        welcome_text = """🏆 Добро пожаловать в Saudi Football TV Bot!

Ваш персональный источник новостей арабского футбола!

🔥 Что умеет бот:
• 📰 Новости каждые 15-30 минут
• ⚽ Детальные превью и обзоры матчей  
• 📊 Статистика и турнирные таблицы
• 🌟 Материалы о звездах лиги
• 🧠 Тактический анализ
• 💰 Трансферные новости

🎯 Интерактивные функции:
• Подписка на любимые команды
• Запросы статистики по командам/игрокам
• Персональные уведомления
• Настройка времени получения новостей

Используйте /menu для доступа ко всем функциям!"""

        # Создаем клавиатуру с основными функциями
        keyboard = [
            [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")],
            [InlineKeyboardButton("⚽ Подписаться на команду", callback_data="subscribe_team")],
            [InlineKeyboardButton("📊 Статистика", callback_data="statistics")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def handle_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /menu"""
        menu_text = """📋 ГЛАВНОЕ МЕНЮ Saudi Football TV Bot

Выберите интересующий раздел:"""

        keyboard = [
            [
                InlineKeyboardButton("⚽ Команды", callback_data="teams_menu"),
                InlineKeyboardButton("🌟 Игроки", callback_data="players_menu")
            ],
            [
                InlineKeyboardButton("📊 Статистика", callback_data="statistics_menu"),
                InlineKeyboardButton("🏆 Турнирная таблица", callback_data="table_menu")
            ],
            [
                InlineKeyboardButton("📰 Последние новости", callback_data="latest_news"),
                InlineKeyboardButton("⚽ Расписание матчей", callback_data="fixtures")
            ],
            [
                InlineKeyboardButton("🔔 Мои подписки", callback_data="my_subscriptions"),
                InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
            ],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(menu_text, reply_markup=reply_markup)

    async def handle_teams_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка меню команд"""
        teams_text = """⚽ КОМАНДЫ Saudi Pro League

Выберите команду для получения информации:"""

        teams = [
            ("Аль-Хиляль", "team_alhilal"),
            ("Аль-Насср", "team_alnassr"), 
            ("Аль-Ахли", "team_alahli"),
            ("Аль-Иттихад", "team_alittihad"),
            ("Аль-Шабаб", "team_alshabab"),
            ("Аль-Фатех", "team_alfateh")
        ]
        
        keyboard = []
        for i in range(0, len(teams), 2):
            row = []
            row.append(InlineKeyboardButton(teams[i][0], callback_data=teams[i][1]))
            if i + 1 < len(teams):
                row.append(InlineKeyboardButton(teams[i+1][0], callback_data=teams[i+1][1]))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(teams_text, reply_markup=reply_markup)

    async def handle_team_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка информации о команде"""
        callback_data = update.callback_query.data
        team_name = self._get_team_name_from_callback(callback_data)
        user_id = update.effective_user.id
        
        # Получаем информацию о команде
        team_info = self._get_team_detailed_info(team_name)
        
        # Проверяем, подписан ли пользователь на эту команду
        is_subscribed = self._check_user_subscription(user_id, team_name, 'team')
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Статистика", callback_data=f"team_stats_{callback_data.split('_')[1]}"),
                InlineKeyboardButton("⚽ Матчи", callback_data=f"team_matches_{callback_data.split('_')[1]}")
            ],
            [
                InlineKeyboardButton("🌟 Состав", callback_data=f"team_squad_{callback_data.split('_')[1]}"),
                InlineKeyboardButton("📰 Новости", callback_data=f"team_news_{callback_data.split('_')[1]}")
            ]
        ]
        
        # Кнопка подписки/отписки
        if is_subscribed:
            keyboard.append([InlineKeyboardButton("🔕 Отписаться от команды", callback_data=f"unsubscribe_team_{callback_data.split('_')[1]}")])
        else:
            keyboard.append([InlineKeyboardButton("🔔 Подписаться на команду", callback_data=f"subscribe_team_{callback_data.split('_')[1]}")])
        
        keyboard.append([InlineKeyboardButton("🔙 К командам", callback_data="teams_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(team_info, reply_markup=reply_markup)

    async def handle_players_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка меню игроков"""
        players_text = """🌟 ЗВЕЗДЫ Saudi Pro League

Выберите игрока для получения информации:"""

        players = [
            ("Криштиану Роналду", "player_ronaldo"),
            ("Карим Бензема", "player_benzema"),
            ("Н'Голо Канте", "player_kante"),
            ("Рияд Махрез", "player_mahrez"),
            ("Садио Мане", "player_mane"),
            ("Роберто Фирмино", "player_firmino")
        ]
        
        keyboard = []
        for i in range(0, len(players), 2):
            row = []
            row.append(InlineKeyboardButton(players[i][0], callback_data=players[i][1]))
            if i + 1 < len(players):
                row.append(InlineKeyboardButton(players[i+1][0], callback_data=players[i+1][1]))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(players_text, reply_markup=reply_markup)

    async def handle_player_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка информации об игроке"""
        callback_data = update.callback_query.data
        player_name = self._get_player_name_from_callback(callback_data)
        user_id = update.effective_user.id
        
        # Получаем информацию об игроке
        player_info = self._get_player_detailed_info(player_name)
        
        # Проверяем, подписан ли пользователь на этого игрока
        is_subscribed = self._check_user_subscription(user_id, player_name, 'player')
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Статистика сезона", callback_data=f"player_stats_{callback_data.split('_')[1]}"),
                InlineKeyboardButton("⚽ Последние матчи", callback_data=f"player_matches_{callback_data.split('_')[1]}")
            ],
            [
                InlineKeyboardButton("🏆 Достижения", callback_data=f"player_achievements_{callback_data.split('_')[1]}"),
                InlineKeyboardButton("📰 Новости", callback_data=f"player_news_{callback_data.split('_')[1]}")
            ]
        ]
        
        # Кнопка подписки/отписки
        if is_subscribed:
            keyboard.append([InlineKeyboardButton("🔕 Отписаться от игрока", callback_data=f"unsubscribe_player_{callback_data.split('_')[1]}")])
        else:
            keyboard.append([InlineKeyboardButton("🔔 Подписаться на игрока", callback_data=f"subscribe_player_{callback_data.split('_')[1]}")])
        
        keyboard.append([InlineKeyboardButton("🔙 К игрокам", callback_data="players_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(player_info, reply_markup=reply_markup)

    async def handle_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка подписок/отписок"""
        callback_data = update.callback_query.data
        user_id = update.effective_user.id
        
        parts = callback_data.split('_')
        action = parts[0]  # subscribe/unsubscribe
        entity_type = parts[1]  # team/player
        entity_id = parts[2]
        
        entity_name = self._get_entity_name_from_id(entity_type, entity_id)
        
        if action == "subscribe":
            success = self._add_user_subscription(user_id, entity_name, entity_type)
            if success:
                message = f"✅ Вы подписались на {entity_name}!\n\nТеперь вы будете получать уведомления о всех новостях, связанных с {entity_name}."
            else:
                message = f"❌ Ошибка при подписке на {entity_name}. Попробуйте позже."
        else:  # unsubscribe
            success = self._remove_user_subscription(user_id, entity_name, entity_type)
            if success:
                message = f"✅ Вы отписались от {entity_name}."
            else:
                message = f"❌ Ошибка при отписке от {entity_name}. Попробуйте позже."
        
        # Возвращаемся к информации о сущности
        if entity_type == "team":
            back_callback = f"team_{entity_id}"
        else:
            back_callback = f"player_{entity_id}"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=back_callback)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)

    async def handle_my_subscriptions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка просмотра подписок пользователя"""
        user_id = update.effective_user.id
        subscriptions = self._get_user_subscriptions(user_id)
        
        if not subscriptions:
            text = """🔔 МОИ ПОДПИСКИ

У вас пока нет активных подписок.

Подпишитесь на интересующие команды и игроков, чтобы получать персональные уведомления о новостях!"""
            
            keyboard = [
                [InlineKeyboardButton("⚽ Подписаться на команду", callback_data="teams_menu")],
                [InlineKeyboardButton("🌟 Подписаться на игрока", callback_data="players_menu")],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
            ]
        else:
            text = "🔔 МОИ ПОДПИСКИ\n\n"
            
            teams = [sub for sub in subscriptions if sub['type'] == 'team']
            players = [sub for sub in subscriptions if sub['type'] == 'player']
            
            if teams:
                text += "⚽ КОМАНДЫ:\n"
                for team in teams:
                    text += f"• {team['name']}\n"
                text += "\n"
            
            if players:
                text += "🌟 ИГРОКИ:\n"
                for player in players:
                    text += f"• {player['name']}\n"
                text += "\n"
            
            text += f"Всего активных подписок: {len(subscriptions)}"
            
            keyboard = [
                [InlineKeyboardButton("⚽ Управление командами", callback_data="manage_team_subs")],
                [InlineKeyboardButton("🌟 Управление игроками", callback_data="manage_player_subs")],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

    async def handle_statistics_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка меню статистики"""
        stats_text = """📊 СТАТИСТИКА Saudi Pro League

Выберите тип статистики:"""

        keyboard = [
            [
                InlineKeyboardButton("🏆 Турнирная таблица", callback_data="current_table"),
                InlineKeyboardButton("⚽ Бомбардиры", callback_data="top_scorers")
            ],
            [
                InlineKeyboardButton("🎯 Ассистенты", callback_data="top_assists"),
                InlineKeyboardButton("🥅 Лучшие вратари", callback_data="top_keepers")
            ],
            [
                InlineKeyboardButton("📈 Статистика команд", callback_data="team_statistics"),
                InlineKeyboardButton("🔥 Форма команд", callback_data="team_form")
            ],
            [
                InlineKeyboardButton("📊 Статистика матчей", callback_data="match_statistics"),
                InlineKeyboardButton("📅 Календарь", callback_data="fixtures_calendar")
            ],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(stats_text, reply_markup=reply_markup)

    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка настроек пользователя"""
        user_id = update.effective_user.id
        settings = self._get_user_settings(user_id)
        
        settings_text = f"""⚙️ НАСТРОЙКИ

Текущие настройки:
• 🌍 Язык: {settings.get('language', 'Русский')}
• 🕐 Время уведомлений: {settings.get('notification_time', '09:00')}
• 🌐 Часовой пояс: {settings.get('timezone', 'UTC+3')}

Выберите, что хотите изменить:"""

        keyboard = [
            [
                InlineKeyboardButton("🌍 Изменить язык", callback_data="change_language"),
                InlineKeyboardButton("🕐 Время уведомлений", callback_data="change_time")
            ],
            [
                InlineKeyboardButton("🌐 Часовой пояс", callback_data="change_timezone"),
                InlineKeyboardButton("🔔 Настройки уведомлений", callback_data="notification_settings")
            ],
            [
                InlineKeyboardButton("📊 Экспорт данных", callback_data="export_data"),
                InlineKeyboardButton("🗑️ Удалить аккаунт", callback_data="delete_account")
            ],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(settings_text, reply_markup=reply_markup)

    # Вспомогательные методы для работы с базой данных
    
    def _register_user(self, user_id: int):
        """Регистрация нового пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO user_settings (user_id)
                VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Ошибка регистрации пользователя {user_id}: {e}")

    def _add_user_subscription(self, user_id: int, entity_name: str, entity_type: str) -> bool:
        """Добавление подписки пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем, нет ли уже такой подписки
            cursor.execute('''
                SELECT COUNT(*) FROM user_subscriptions 
                WHERE user_id = ? AND team_name = ? AND subscription_type = ? AND is_active = 1
            ''', (user_id, entity_name, entity_type))
            
            if cursor.fetchone()[0] > 0:
                conn.close()
                return False  # Подписка уже существует
            
            # Добавляем новую подписку
            if entity_type == 'team':
                cursor.execute('''
                    INSERT INTO user_subscriptions (user_id, team_name, subscription_type)
                    VALUES (?, ?, ?)
                ''', (user_id, entity_name, entity_type))
            else:  # player
                cursor.execute('''
                    INSERT INTO user_subscriptions (user_id, player_name, subscription_type)
                    VALUES (?, ?, ?)
                ''', (user_id, entity_name, entity_type))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления подписки для пользователя {user_id}: {e}")
            return False

    def _remove_user_subscription(self, user_id: int, entity_name: str, entity_type: str) -> bool:
        """Удаление подписки пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if entity_type == 'team':
                cursor.execute('''
                    UPDATE user_subscriptions 
                    SET is_active = 0 
                    WHERE user_id = ? AND team_name = ? AND subscription_type = ?
                ''', (user_id, entity_name, entity_type))
            else:  # player
                cursor.execute('''
                    UPDATE user_subscriptions 
                    SET is_active = 0 
                    WHERE user_id = ? AND player_name = ? AND subscription_type = ?
                ''', (user_id, entity_name, entity_type))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления подписки для пользователя {user_id}: {e}")
            return False

    def _check_user_subscription(self, user_id: int, entity_name: str, entity_type: str) -> bool:
        """Проверка наличия подписки у пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if entity_type == 'team':
                cursor.execute('''
                    SELECT COUNT(*) FROM user_subscriptions 
                    WHERE user_id = ? AND team_name = ? AND subscription_type = ? AND is_active = 1
                ''', (user_id, entity_name, entity_type))
            else:  # player
                cursor.execute('''
                    SELECT COUNT(*) FROM user_subscriptions 
                    WHERE user_id = ? AND player_name = ? AND subscription_type = ? AND is_active = 1
                ''', (user_id, entity_name, entity_type))
            
            result = cursor.fetchone()[0] > 0
            conn.close()
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки подписки для пользователя {user_id}: {e}")
            return False

    def _get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """Получение всех подписок пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT team_name, player_name, subscription_type 
                FROM user_subscriptions 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            subscriptions = []
            for row in rows:
                team_name, player_name, sub_type = row
                name = team_name if sub_type == 'team' else player_name
                subscriptions.append({
                    'name': name,
                    'type': sub_type
                })
            
            return subscriptions
            
        except Exception as e:
            self.logger.error(f"Ошибка получения подписок для пользователя {user_id}: {e}")
            return []

    def _get_user_settings(self, user_id: int) -> Dict:
        """Получение настроек пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT language, notification_time, timezone 
                FROM user_settings 
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'language': row[0] or 'ru',
                    'notification_time': row[1] or '09:00',
                    'timezone': row[2] or 'UTC+3'
                }
            else:
                return {
                    'language': 'ru',
                    'notification_time': '09:00',
                    'timezone': 'UTC+3'
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка получения настроек для пользователя {user_id}: {e}")
            return {}

    def get_subscribed_users(self, entity_name: str, entity_type: str) -> List[int]:
        """Получение списка пользователей, подписанных на сущность"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if entity_type == 'team':
                cursor.execute('''
                    SELECT DISTINCT user_id FROM user_subscriptions 
                    WHERE team_name = ? AND subscription_type = ? AND is_active = 1
                ''', (entity_name, entity_type))
            else:  # player
                cursor.execute('''
                    SELECT DISTINCT user_id FROM user_subscriptions 
                    WHERE player_name = ? AND subscription_type = ? AND is_active = 1
                ''', (entity_name, entity_type))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in rows]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения подписчиков для {entity_name}: {e}")
            return []

    # Методы для получения информации о сущностях
    
    def _get_team_name_from_callback(self, callback_data: str) -> str:
        """Получение названия команды из callback_data"""
        team_mapping = {
            'team_alhilal': 'Аль-Хиляль',
            'team_alnassr': 'Аль-Насср',
            'team_alahli': 'Аль-Ахли',
            'team_alittihad': 'Аль-Иттихад',
            'team_alshabab': 'Аль-Шабаб',
            'team_alfateh': 'Аль-Фатех'
        }
        return team_mapping.get(callback_data, 'Неизвестная команда')

    def _get_player_name_from_callback(self, callback_data: str) -> str:
        """Получение имени игрока из callback_data"""
        player_mapping = {
            'player_ronaldo': 'Криштиану Роналду',
            'player_benzema': 'Карим Бензема',
            'player_kante': 'Н\'Голо Канте',
            'player_mahrez': 'Рияд Махрез',
            'player_mane': 'Садио Мане',
            'player_firmino': 'Роберто Фирмино'
        }
        return player_mapping.get(callback_data, 'Неизвестный игрок')

    def _get_entity_name_from_id(self, entity_type: str, entity_id: str) -> str:
        """Получение названия сущности по ID"""
        if entity_type == 'team':
            return self._get_team_name_from_callback(f"team_{entity_id}")
        else:
            return self._get_player_name_from_callback(f"player_{entity_id}")

    def _get_team_detailed_info(self, team_name: str) -> str:
        """Получение детальной информации о команде"""
        team_data = {
            'Аль-Хиляль': {
                'stadium': 'Стадион Короля Фахда',
                'founded': 1957,
                'position': 1,
                'points': 65,
                'matches': 25,
                'wins': 20,
                'draws': 5,
                'losses': 0,
                'goals_for': 68,
                'goals_against': 15
            },
            'Аль-Насср': {
                'stadium': 'Стадион Мрсул Парк',
                'founded': 1955,
                'position': 2,
                'points': 60,
                'matches': 25,
                'wins': 18,
                'draws': 6,
                'losses': 1,
                'goals_for': 62,
                'goals_against': 20
            }
        }
        
        data = team_data.get(team_name, {
            'stadium': 'Стадион',
            'founded': 1950,
            'position': 5,
            'points': 45,
            'matches': 25,
            'wins': 12,
            'draws': 9,
            'losses': 4,
            'goals_for': 40,
            'goals_against': 30
        })
        
        return f"""⚽ {team_name}

🏟️ Домашний стадион: {data['stadium']}
📅 Год основания: {data['founded']}

📊 ТЕКУЩИЙ СЕЗОН:
• Позиция в таблице: {data['position']} место
• Очки: {data['points']}
• Матчи: {data['matches']}
• Победы: {data['wins']}
• Ничьи: {data['draws']}
• Поражения: {data['losses']}
• Голы забито: {data['goals_for']}
• Голы пропущено: {data['goals_against']}

🔥 Форма: П-П-Н-П-П (последние 5 матчей)

#SaudiProLeague #{team_name.replace('-', '').replace(' ', '')}"""

    def _get_player_detailed_info(self, player_name: str) -> str:
        """Получение детальной информации об игроке"""
        player_data = {
            'Криштиану Роналду': {
                'team': 'Аль-Насср',
                'position': 'Нападающий',
                'age': 39,
                'nationality': 'Португалия',
                'goals': 22,
                'assists': 6,
                'matches': 24,
                'rating': 8.7
            },
            'Карим Бензема': {
                'team': 'Аль-Иттихад',
                'position': 'Нападающий',
                'age': 36,
                'nationality': 'Франция',
                'goals': 18,
                'assists': 8,
                'matches': 22,
                'rating': 8.4
            }
        }
        
        data = player_data.get(player_name, {
            'team': 'Команда',
            'position': 'Игрок',
            'age': 28,
            'nationality': 'Страна',
            'goals': 10,
            'assists': 5,
            'matches': 20,
            'rating': 7.5
        })
        
        return f"""🌟 {player_name}

⚽ Команда: {data['team']}
🎯 Позиция: {data['position']}
👤 Возраст: {data['age']} лет
🌍 Национальность: {data['nationality']}

📊 СТАТИСТИКА СЕЗОНА:
• Матчи: {data['matches']}
• Голы: {data['goals']}
• Передачи: {data['assists']}
• Средний рейтинг: {data['rating']}/10

🔥 Последние 5 матчей: ⭐⭐⭐⭐⭐

#SaudiProLeague #Player #{player_name.replace(' ', '')}"""

