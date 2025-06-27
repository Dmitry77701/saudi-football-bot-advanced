import os
import asyncio
import logging
import json
import sqlite3
import time
from datetime import datetime, timedelta
import random
from typing import List, Dict, Optional
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

# Импортируем наши модули
from database_manager import DatabaseManager
from content_generator import ContentGenerator
from error_handler import BotLogger, ErrorHandler, HealthChecker, error_handler_decorator

# ВАШИ ДАННЫЕ (уже вставлены!)
BOT_TOKEN = os.getenv('BOT_TOKEN', '7541467929:AAGLOxsVGckECmb-RJX9xIxiaFXuzDcOHbNQ')
CHANNEL_ID = os.getenv('CHANNEL_ID', '-1002643651612')
PORT = int(os.getenv('PORT', '8080'))

# API настройки
THESPORTSDB_API_KEY = "123"  # Бесплатный ключ
THESPORTSDB_BASE_URL = "https://www.thesportsdb.com/api/v1/json"

class AdvancedFootballBot:
    """Продвинутый футбольный бот с улучшениями"""
    
    def __init__(self):
        # Инициализация компонентов
        self.bot_logger = BotLogger(log_level=logging.INFO)
        self.error_handler = ErrorHandler(self.bot_logger)
        self.health_checker = HealthChecker(self.bot_logger)
        self.db_manager = DatabaseManager()
        self.content_generator = ContentGenerator(self.db_manager)
        
        self.app = None
        self.bot_logger.log_startup(BOT_TOKEN, CHANNEL_ID)
    
    @error_handler_decorator(None, "start_command")
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start с улучшенным интерфейсом"""
        try:
            keyboard = [
                [InlineKeyboardButton("📰 Свежие новости", callback_data='news')],
                [InlineKeyboardButton("⚽ Матчи сегодня", callback_data='matches')],
                [InlineKeyboardButton("📊 Турнирная таблица", callback_data='table')],
                [InlineKeyboardButton("📈 Статистика бота", callback_data='stats')],
                [InlineKeyboardButton("ℹ️ О боте", callback_data='about')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_text = """
🤖 **Добро пожаловать в УЛУЧШЕННЫЙ Saudi Football Bot!**

🆕 **НОВЫЕ ВОЗМОЖНОСТИ:**
• Реальные данные через спортивные API
• Умная база данных SQLite с кэшированием
• Избежание дублирования новостей
• Улучшенная генерация контента
• Продвинутая обработка ошибок
• Мониторинг здоровья бота

⚽ **Что умеет бот:**
• Срочные новости каждые 15 минут
• Полные новости каждые 30 минут
• Ежедневное расписание матчей (9:00)
• Турнирные таблицы (понедельник, 10:00)
• Интерактивное меню с кнопками

📱 **Выберите действие ниже:**
            """
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            self.bot_logger.log_info("Пользователь запустил бота", "🚀")
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "start_command")
            raise

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки с улучшенной логикой"""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == 'news':
                await self.send_latest_news(query)
            elif query.data == 'matches':
                await self.send_today_matches(query)
            elif query.data == 'table':
                await self.send_league_table(query)
            elif query.data == 'stats':
                await self.send_bot_stats(query)
            elif query.data == 'about':
                await self.send_about_info(query)
            
            self.bot_logger.log_info(f"Обработана кнопка: {query.data}")
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, f"button_callback_{query.data}")
            await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")

    async def send_latest_news(self, query):
        """Отправка последних новостей с использованием умного генератора"""
        try:
            # Получаем новости из умного генератора
            news_list = self.content_generator.generate_smart_full_news(use_real_data=True)
            
            text = "📰 **ПОСЛЕДНИЕ НОВОСТИ АРАБСКОГО ФУТБОЛА**\n\n"
            
            for i, article in enumerate(news_list[:3], 1):
                text += f"**{i}. {article['title']}**\n"
                text += f"{article['summary']}\n"
                text += f"🕐 {article['time']}\n"
                text += f"🏷️ {', '.join(article['tags'][:2])}\n\n"
            
            text += "📢 *Больше новостей в нашем канале!*\n"
            text += f"🤖 *Сгенерировано умным алгоритмом в {datetime.now().strftime('%H:%M')}*"
            
            await query.edit_message_text(text, parse_mode='Markdown')
            self.health_checker.update_message_status(True)
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "send_latest_news")
            await query.edit_message_text("❌ Ошибка загрузки новостей")

    async def send_today_matches(self, query):
        """Отправка расписания матчей с использованием умного генератора"""
        try:
            # Получаем матчи из умного генератора
            matches = self.content_generator.generate_smart_matches()
            
            # Форматируем сообщение
            formatted_message = self.content_generator.format_matches_message(matches)
            
            await query.edit_message_text(formatted_message, parse_mode='Markdown')
            self.health_checker.update_message_status(True)
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "send_today_matches")
            await query.edit_message_text("❌ Ошибка загрузки расписания")

    async def send_league_table(self, query):
        """Отправка турнирной таблицы с использованием умного генератора"""
        try:
            # Получаем таблицу из умного генератора
            table = self.content_generator.generate_smart_league_table()
            
            # Форматируем сообщение
            formatted_message = self.content_generator.format_league_table_message(table, detailed=False)
            
            await query.edit_message_text(formatted_message, parse_mode='Markdown')
            self.health_checker.update_message_status(True)
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "send_league_table")
            await query.edit_message_text("❌ Ошибка загрузки таблицы")

    async def send_bot_stats(self, query):
        """Отправка статистики бота"""
        try:
            # Получаем статистику от всех компонентов
            logger_stats = self.bot_logger.get_stats()
            error_stats = self.error_handler.get_error_summary()
            health_stats = self.health_checker.get_health_status()
            db_stats = self.db_manager.get_database_stats()
            content_stats = self.content_generator.get_content_stats()
            
            text = "📈 **СТАТИСТИКА БОТА**\n\n"
            
            # Общее здоровье
            status_emoji = {"healthy": "💚", "warning": "⚠️", "starting": "🔄"}.get(health_stats['overall_status'], "❓")
            text += f"{status_emoji} **Статус:** {health_stats['overall_status']}\n"
            text += f"⏱️ **Время работы:** {health_stats['uptime_formatted']}\n\n"
            
            # Статистика сообщений
            text += f"📱 **Сообщения:**\n"
            text += f"• Информационных: {logger_stats['info_messages']}\n"
            text += f"• Предупреждений: {logger_stats['warnings']}\n"
            text += f"• Ошибок: {logger_stats['errors']}\n\n"
            
            # База данных
            text += f"💾 **База данных:**\n"
            text += f"• Команд: {db_stats.get('teams_count', 0)}\n"
            text += f"• Матчей: {db_stats.get('matches_count', 0)}\n"
            text += f"• Новостей: {db_stats.get('news_count', 0)}\n"
            text += f"• Опубликовано: {db_stats.get('published_news', 0)}\n\n"
            
            # Генератор контента
            text += f"🎨 **Контент:**\n"
            text += f"• Команд в базе: {content_stats['teams_count']}\n"
            text += f"• Игроков: {content_stats['players_count']}\n"
            text += f"• Шаблонов новостей: {content_stats['full_templates']}\n\n"
            
            text += f"🕐 *Обновлено: {datetime.now().strftime('%H:%M:%S')}*"
            
            await query.edit_message_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "send_bot_stats")
            await query.edit_message_text("❌ Ошибка загрузки статистики")

    async def send_about_info(self, query):
        """Информация о боте с описанием улучшений"""
        try:
            text = """
ℹ️ **УЛУЧШЕННЫЙ SAUDI FOOTBALL BOT v2.0**

🚀 **НОВЫЕ ВОЗМОЖНОСТИ:**

🧠 **Умный контент:**
• Реальные данные через TheSportsDB API
• Избежание дублирования новостей
• Кэширование для быстрой работы
• Более 50 шаблонов новостей

💾 **База данных:**
• SQLite для надежного хранения
• Автоматическое кэширование API
• Статистика и аналитика
• Резервное копирование данных

🛡️ **Надежность:**
• Продвинутая обработка ошибок
• Автоматические повторы запросов
• Мониторинг здоровья бота
• Детальное логирование

⚡ **Производительность:**
• Асинхронная архитектура
• Оптимизированные запросы
• Умное управление памятью
• Быстрые ответы пользователям

📱 **Команды:**
• /start - главное меню с кнопками
• Интерактивная навигация
• Статистика в реальном времени

🔔 **Автоматические публикации:**
• Срочные новости: каждые 15 минут
• Полные новости: каждые 30 минут
• Матчи: ежедневно в 9:00
• Таблица: понедельник в 10:00

💡 *Бот работает 24/7 с максимальной надежностью!*
            """
            
            await query.edit_message_text(text, parse_mode='Markdown')
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "send_about_info")
            await query.edit_message_text("❌ Ошибка загрузки информации")

    async def send_smart_quick_news(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправка умных срочных новостей"""
        try:
            start_time = time.time()
            
            # Генерируем умную новость
            quick_news = self.content_generator.generate_smart_quick_news(use_real_data=True)
            
            # Проверяем, не публиковали ли мы уже эту новость
            is_new = self.db_manager.save_news_advanced(quick_news)
            
            if is_new:
                text = f"⚡ **СРОЧНЫЕ НОВОСТИ**\n\n"
                text += f"📰 {quick_news['title']}\n\n"
                text += f"{quick_news['content']}\n\n"
                text += f"🕐 {datetime.now().strftime('%H:%M')} | 🔥 Горячая новость!"
                
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text,
                    parse_mode='Markdown'
                )
                
                # Обновляем статистику
                self.health_checker.update_message_status(True)
                self.db_manager.save_bot_stat("quick_news_sent", "1")
                
                duration = time.time() - start_time
                self.bot_logger.log_job_execution("send_smart_quick_news", True, duration)
            else:
                self.bot_logger.log_warning("Срочная новость уже была опубликована", "send_smart_quick_news")
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "send_smart_quick_news")

    async def send_smart_news_to_channel(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправка умных новостей в канал"""
        try:
            start_time = time.time()
            
            # Генерируем умные новости
            news_list = self.content_generator.generate_smart_full_news(use_real_data=True)
            
            # Фильтруем только новые новости
            new_news = []
            for news_item in news_list:
                if self.db_manager.save_news_advanced(news_item):
                    new_news.append(news_item)
            
            if new_news:
                text = "📰 **НОВОСТИ АРАБСКОГО ФУТБОЛА**\n\n"
                
                for i, article in enumerate(new_news[:3], 1):
                    text += f"**{i}. {article['title']}**\n"
                    text += f"{article['summary']}\n"
                    text += f"🕐 {article['time']}\n"
                    text += f"🏷️ {', '.join(article['tags'][:2])}\n\n"
                
                text += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                text += "🔔 Подпишитесь на уведомления!"
                
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text,
                    parse_mode='Markdown'
                )
                
                # Обновляем статистику
                self.health_checker.update_message_status(True)
                self.db_manager.save_bot_stat("full_news_sent", str(len(new_news)))
                
                duration = time.time() - start_time
                self.bot_logger.log_job_execution("send_smart_news_to_channel", True, duration)
            else:
                self.bot_logger.log_info("Нет новых новостей для публикации")
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "send_smart_news_to_channel")

    async def send_smart_matches_to_channel(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправка умного расписания матчей в канал"""
        try:
            start_time = time.time()
            
            # Генерируем умное расписание
            matches = self.content_generator.generate_smart_matches()
            
            # Форматируем сообщение
            formatted_message = self.content_generator.format_matches_message(matches)
            
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=formatted_message,
                parse_mode='Markdown'
            )
            
            # Обновляем статистику
            self.health_checker.update_message_status(True)
            self.db_manager.save_bot_stat("matches_sent", str(len(matches)))
            
            duration = time.time() - start_time
            self.bot_logger.log_job_execution("send_smart_matches_to_channel", True, duration)
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "send_smart_matches_to_channel")

    async def send_smart_table_to_channel(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправка умной турнирной таблицы в канал"""
        try:
            start_time = time.time()
            
            # Пытаемся получить реальные данные
            try:
                await self.fetch_real_league_data()
                self.health_checker.update_api_status(True)
            except Exception as api_error:
                self.error_handler.handle_api_error(api_error, "league_table", {})
            
            # Генерируем умную таблицу
            table = self.content_generator.generate_smart_league_table()
            
            # Форматируем сообщение
            formatted_message = self.content_generator.format_league_table_message(table, detailed=True)
            
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=formatted_message,
                parse_mode='Markdown'
            )
            
            # Обновляем статистику
            self.health_checker.update_message_status(True)
            self.db_manager.save_bot_stat("table_sent", "1")
            
            duration = time.time() - start_time
            self.bot_logger.log_job_execution("send_smart_table_to_channel", True, duration)
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "send_smart_table_to_channel")

    async def fetch_real_league_data(self):
        """Получение реальных данных лиги"""
        try:
            async with aiohttp.ClientSession() as session:
                # Пытаемся получить данные саудовской лиги
                url = f"{THESPORTSDB_BASE_URL}/{THESPORTSDB_API_KEY}/lookuptable.php?l=4480"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('table'):
                            # Сохраняем данные в БД
                            for team in data['table']:
                                team_data = {
                                    'api_id': team.get('idTeam'),
                                    'name': team.get('strTeam'),
                                    'league': 'Saudi Pro League',
                                    'country': 'Saudi Arabia'
                                }
                                self.db_manager.save_team(team_data)
                            
                            self.bot_logger.log_api_request("lookuptable", {"league": "4480"}, True)
                            self.health_checker.update_api_status(True)
                        else:
                            self.bot_logger.log_warning("API вернул пустые данные таблицы")
                    else:
                        self.bot_logger.log_warning(f"API вернул статус {response.status}")
        except Exception as e:
            self.error_handler.handle_api_error(e, "lookuptable", {"league": "4480"})
            raise

    async def send_startup_message(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправка сообщения о запуске улучшенного бота"""
        try:
            text = """
🚀 **УЛУЧШЕННЫЙ БОТ ЗАПУЩЕН!**

✅ Бот успешно запущен с МАКСИМАЛЬНЫМИ улучшениями!

🆕 **НОВЫЕ ВОЗМОЖНОСТИ:**
• Реальные данные через TheSportsDB API
• Умная база данных SQLite с кэшированием
• Избежание дублирования новостей
• Продвинутая обработка ошибок
• Мониторинг здоровья бота в реальном времени
• Улучшенная генерация контента

📅 **МАКСИМАЛЬНО ЧАСТОЕ РАСПИСАНИЕ:**
• Срочные новости: каждые 15 минут
• Полные новости: каждые 30 минут
• Матчи: ежедневно в 9:00
• Таблица: понедельник в 10:00

🤖 Используйте команду /start для интерактивного меню
📊 Доступна статистика работы бота в реальном времени

🔥 **БОТ ГОТОВ К МАКСИМАЛЬНОЙ ПРОИЗВОДИТЕЛЬНОСТИ!**
            """
            
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=text,
                parse_mode='Markdown'
            )
            
            self.bot_logger.log_info("Отправлено сообщение о запуске улучшенного бота", "🚀")
            
        except Exception as e:
            self.error_handler.handle_telegram_error(e, "send_startup_message")

    async def periodic_health_check(self, context: ContextTypes.DEFAULT_TYPE):
        """Периодическая проверка здоровья бота"""
        try:
            # Очищаем старый кэш
            self.db_manager.clean_old_cache()
            
            # Логируем отчет о здоровье
            self.health_checker.log_health_report()
            
            # Сохраняем статистику
            health_stats = self.health_checker.get_health_status()
            self.db_manager.save_bot_stat("health_check", health_stats['overall_status'])
            
        except Exception as e:
            self.error_handler.handle_database_error(e, "periodic_health_check")

    def setup_jobs(self):
        """Настройка расписания заданий с улучшениями"""
        job_queue = self.app.job_queue
        
        # МАКСИМАЛЬНО ЧАСТЫЕ ОБНОВЛЕНИЯ С УЛУЧШЕНИЯМИ!
        
        # 1. Срочные новости каждые 15 минут
        job_queue.run_repeating(
            self.send_smart_quick_news,
            interval=900,  # 15 минут
            first=300  # Первый запуск через 5 минут
        )
        
        # 2. Полные новости каждые 30 минут
        job_queue.run_repeating(
            self.send_smart_news_to_channel,
            interval=1800,  # 30 минут
            first=60  # Первый запуск через 1 минуту
        )
        
        # 3. Матчи каждый день в 9:00
        job_queue.run_daily(
            self.send_smart_matches_to_channel,
            time=datetime.strptime("09:00", "%H:%M").time()
        )
        
        # 4. Турнирная таблица каждый понедельник в 10:00
        job_queue.run_daily(
            self.send_smart_table_to_channel,
            time=datetime.strptime("10:00", "%H:%M").time(),
            days=(0,)  # 0 = понедельник
        )
        
        # 5. Сообщение о запуске
        job_queue.run_once(
            self.send_startup_message,
            when=10  # Через 10 секунд после запуска
        )
        
        # 6. Периодическая проверка здоровья каждые 2 часа
        job_queue.run_repeating(
            self.periodic_health_check,
            interval=7200,  # 2 часа
            first=3600  # Первая проверка через час
        )
        
        self.bot_logger.log_info("🔥 Настроено МАКСИМАЛЬНО ЧАСТОЕ расписание с ПОЛНЫМИ УЛУЧШЕНИЯМИ!")

    async def run_bot(self):
        """Запуск улучшенного бота"""
        try:
            # Создание приложения
            self.app = Application.builder().token(BOT_TOKEN).build()
            
            # Обновляем ссылку на error_handler
            self.error_handler.bot_app = self.app
            
            # Добавление обработчиков
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Настройка заданий
            self.setup_jobs()
            
            self.bot_logger.log_info("🚀 УЛУЧШЕННЫЙ бот запускается с максимальными возможностями...")
            
            # Запуск бота
            await self.app.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            self.error_handler.add_critical_error(e, "run_bot")
            self.bot_logger.log_error(e, "Критическая ошибка запуска бота")
            raise

def main():
    """Главная функция"""
    bot = AdvancedFootballBot()
    
    print("🚀 Запуск УЛУЧШЕННОГО Saudi Football Bot v2.0...")
    print(f"📱 Канал: {CHANNEL_ID}")
    print("🔥 МАКСИМАЛЬНЫЕ УЛУЧШЕНИЯ АКТИВИРОВАНЫ:")
    print("   • Реальные данные через API")
    print("   • Умная база данных SQLite")
    print("   • Продвинутая обработка ошибок")
    print("   • Мониторинг здоровья")
    print("   • Избежание дублирования")
    print("   • Максимально частые обновления")
    
    # Запуск бота
    bot.run_bot()

if __name__ == "__main__":
    main()

