import logging
import traceback
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
import asyncio
import json

class BotLogger:
    """Улучшенная система логирования для футбольного бота"""
    
    def __init__(self, log_level=logging.INFO, log_file="bot.log"):
        self.log_file = log_file
        self.setup_logging(log_level)
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0
        
    def setup_logging(self, log_level):
        """Настройка системы логирования"""
        
        # Создаем форматтер для логов
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Настраиваем корневой логгер
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Очищаем существующие обработчики
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Файловый обработчик
        try:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # В файл записываем все
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"⚠️ Не удалось создать файл логов: {e}")
        
        # Создаем специальный логгер для бота
        self.logger = logging.getLogger('FootballBot')
        
        # Подавляем лишние логи от библиотек
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('telegram').setLevel(logging.WARNING)
        logging.getLogger('aiohttp').setLevel(logging.WARNING)
        
        self.logger.info("🚀 Система логирования инициализирована")
    
    def log_startup(self, bot_token: str, channel_id: str):
        """Логирование запуска бота"""
        self.logger.info("=" * 50)
        self.logger.info("🤖 ЗАПУСК ФУТБОЛЬНОГО БОТА")
        self.logger.info("=" * 50)
        self.logger.info(f"📱 Канал: {channel_id}")
        self.logger.info(f"🔑 Токен: {bot_token[:10]}...")
        self.logger.info(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 50)
    
    def log_api_request(self, endpoint: str, params: Dict = None, success: bool = True, response_time: float = None):
        """Логирование API запросов"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        
        self.logger.info(f"🌐 API {status}: {endpoint}{time_info}")
        if params:
            self.logger.debug(f"📋 Параметры: {params}")
    
    def log_message_sent(self, message_type: str, channel_id: str, success: bool = True):
        """Логирование отправки сообщений"""
        status = "✅" if success else "❌"
        self.logger.info(f"{status} Сообщение отправлено: {message_type} -> {channel_id}")
    
    def log_database_operation(self, operation: str, table: str, success: bool = True, affected_rows: int = None):
        """Логирование операций с базой данных"""
        status = "✅" if success else "❌"
        rows_info = f" ({affected_rows} строк)" if affected_rows is not None else ""
        self.logger.info(f"{status} БД {operation}: {table}{rows_info}")
    
    def log_job_execution(self, job_name: str, success: bool = True, duration: float = None):
        """Логирование выполнения заданий"""
        status = "✅" if success else "❌"
        time_info = f" за {duration:.2f}с" if duration else ""
        self.logger.info(f"{status} Задание выполнено: {job_name}{time_info}")
    
    def log_error(self, error: Exception, context: str = None, extra_data: Dict = None):
        """Детальное логирование ошибок"""
        self.error_count += 1
        
        error_msg = f"❌ ОШИБКА #{self.error_count}"
        if context:
            error_msg += f" в {context}"
        
        self.logger.error(error_msg)
        self.logger.error(f"🔍 Тип ошибки: {type(error).__name__}")
        self.logger.error(f"💬 Сообщение: {str(error)}")
        
        if extra_data:
            self.logger.error(f"📋 Дополнительные данные: {extra_data}")
        
        # Полный traceback в debug режиме
        self.logger.debug(f"📚 Полный traceback:\n{traceback.format_exc()}")
    
    def log_warning(self, message: str, context: str = None):
        """Логирование предупреждений"""
        self.warning_count += 1
        warning_msg = f"⚠️ ПРЕДУПРЕЖДЕНИЕ #{self.warning_count}"
        if context:
            warning_msg += f" в {context}"
        warning_msg += f": {message}"
        
        self.logger.warning(warning_msg)
    
    def log_info(self, message: str, emoji: str = "ℹ️"):
        """Логирование информационных сообщений"""
        self.info_count += 1
        self.logger.info(f"{emoji} {message}")
    
    def get_stats(self) -> Dict:
        """Получение статистики логирования"""
        return {
            'errors': self.error_count,
            'warnings': self.warning_count,
            'info_messages': self.info_count,
            'log_file': self.log_file
        }

class ErrorHandler:
    """Класс для обработки ошибок бота"""
    
    def __init__(self, logger: BotLogger, bot_app=None):
        self.logger = logger
        self.bot_app = bot_app
        self.critical_errors = []
        self.retry_attempts = {}
        
    def handle_telegram_error(self, error: Exception, context: str = "Telegram API"):
        """Обработка ошибок Telegram API"""
        error_type = type(error).__name__
        
        if "rate limit" in str(error).lower():
            self.logger.log_warning("Превышен лимит запросов Telegram API", context)
            return "rate_limit"
        elif "forbidden" in str(error).lower():
            self.logger.log_error(error, context, {"suggestion": "Проверьте права бота в канале"})
            return "forbidden"
        elif "not found" in str(error).lower():
            self.logger.log_error(error, context, {"suggestion": "Проверьте ID канала"})
            return "not_found"
        else:
            self.logger.log_error(error, context)
            return "unknown"
    
    def handle_api_error(self, error: Exception, endpoint: str, params: Dict = None):
        """Обработка ошибок внешних API"""
        error_info = {
            "endpoint": endpoint,
            "params": params,
            "error_type": type(error).__name__
        }
        
        if "timeout" in str(error).lower():
            self.logger.log_warning(f"Таймаут API запроса: {endpoint}")
            return "timeout"
        elif "connection" in str(error).lower():
            self.logger.log_warning(f"Проблема с подключением к API: {endpoint}")
            return "connection"
        else:
            self.logger.log_error(error, f"API запрос: {endpoint}", error_info)
            return "api_error"
    
    def handle_database_error(self, error: Exception, operation: str, table: str = None):
        """Обработка ошибок базы данных"""
        error_info = {
            "operation": operation,
            "table": table,
            "error_type": type(error).__name__
        }
        
        if "locked" in str(error).lower():
            self.logger.log_warning(f"База данных заблокирована: {operation}")
            return "locked"
        elif "no such table" in str(error).lower():
            self.logger.log_error(error, f"БД операция: {operation}", 
                                {"suggestion": "Возможно, нужно инициализировать БД"})
            return "table_missing"
        else:
            self.logger.log_error(error, f"БД операция: {operation}", error_info)
            return "db_error"
    
    def should_retry(self, error_type: str, operation_key: str, max_retries: int = 3) -> bool:
        """Определение, нужно ли повторить операцию"""
        if operation_key not in self.retry_attempts:
            self.retry_attempts[operation_key] = 0
        
        if self.retry_attempts[operation_key] >= max_retries:
            self.logger.log_warning(f"Превышено количество попыток для {operation_key}")
            return False
        
        # Определяем, какие ошибки можно повторить
        retryable_errors = ["timeout", "connection", "rate_limit", "locked"]
        
        if error_type in retryable_errors:
            self.retry_attempts[operation_key] += 1
            self.logger.log_info(f"Повтор #{self.retry_attempts[operation_key]} для {operation_key}")
            return True
        
        return False
    
    def reset_retry_counter(self, operation_key: str):
        """Сброс счетчика повторов после успешной операции"""
        if operation_key in self.retry_attempts:
            del self.retry_attempts[operation_key]
    
    def add_critical_error(self, error: Exception, context: str):
        """Добавление критической ошибки"""
        critical_error = {
            'timestamp': datetime.now().isoformat(),
            'error': str(error),
            'type': type(error).__name__,
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        self.critical_errors.append(critical_error)
        self.logger.log_error(error, f"КРИТИЧЕСКАЯ ОШИБКА: {context}")
        
        # Ограничиваем количество сохраняемых критических ошибок
        if len(self.critical_errors) > 10:
            self.critical_errors = self.critical_errors[-10:]
    
    def get_error_summary(self) -> Dict:
        """Получение сводки по ошибкам"""
        return {
            'critical_errors_count': len(self.critical_errors),
            'recent_critical_errors': self.critical_errors[-3:] if self.critical_errors else [],
            'active_retries': len(self.retry_attempts),
            'retry_operations': list(self.retry_attempts.keys())
        }

def error_handler_decorator(error_handler: ErrorHandler, operation_name: str):
    """Декоратор для автоматической обработки ошибок"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                error_handler.reset_retry_counter(operation_name)
                return result
            except Exception as e:
                error_type = error_handler.handle_telegram_error(e, operation_name)
                
                if error_handler.should_retry(error_type, operation_name):
                    # Ждем перед повтором
                    await asyncio.sleep(2 ** error_handler.retry_attempts.get(operation_name, 1))
                    return await async_wrapper(*args, **kwargs)
                else:
                    error_handler.add_critical_error(e, operation_name)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                error_handler.reset_retry_counter(operation_name)
                return result
            except Exception as e:
                error_type = error_handler.handle_database_error(e, operation_name)
                
                if error_handler.should_retry(error_type, operation_name):
                    return sync_wrapper(*args, **kwargs)
                else:
                    error_handler.add_critical_error(e, operation_name)
                    raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

class HealthChecker:
    """Класс для мониторинга здоровья бота"""
    
    def __init__(self, logger: BotLogger):
        self.logger = logger
        self.last_successful_message = None
        self.last_api_call = None
        self.last_db_operation = None
        self.start_time = datetime.now()
    
    def update_message_status(self, success: bool):
        """Обновление статуса отправки сообщений"""
        if success:
            self.last_successful_message = datetime.now()
    
    def update_api_status(self, success: bool):
        """Обновление статуса API вызовов"""
        if success:
            self.last_api_call = datetime.now()
    
    def update_db_status(self, success: bool):
        """Обновление статуса БД операций"""
        if success:
            self.last_db_operation = datetime.now()
    
    def get_health_status(self) -> Dict:
        """Получение статуса здоровья бота"""
        now = datetime.now()
        uptime = now - self.start_time
        
        status = {
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_formatted': str(uptime).split('.')[0],
            'start_time': self.start_time.isoformat(),
            'current_time': now.isoformat()
        }
        
        # Проверяем, когда последний раз были успешные операции
        if self.last_successful_message:
            message_age = (now - self.last_successful_message).total_seconds()
            status['last_message_seconds_ago'] = int(message_age)
            status['message_status'] = 'healthy' if message_age < 3600 else 'warning'
        else:
            status['message_status'] = 'unknown'
        
        if self.last_api_call:
            api_age = (now - self.last_api_call).total_seconds()
            status['last_api_seconds_ago'] = int(api_age)
            status['api_status'] = 'healthy' if api_age < 7200 else 'warning'
        else:
            status['api_status'] = 'unknown'
        
        if self.last_db_operation:
            db_age = (now - self.last_db_operation).total_seconds()
            status['last_db_seconds_ago'] = int(db_age)
            status['db_status'] = 'healthy' if db_age < 3600 else 'warning'
        else:
            status['db_status'] = 'unknown'
        
        # Общий статус
        statuses = [status.get('message_status'), status.get('api_status'), status.get('db_status')]
        if 'unknown' in statuses:
            status['overall_status'] = 'starting'
        elif 'warning' in statuses:
            status['overall_status'] = 'warning'
        else:
            status['overall_status'] = 'healthy'
        
        return status
    
    def log_health_report(self):
        """Логирование отчета о здоровье"""
        health = self.get_health_status()
        
        self.logger.log_info(f"💚 Отчет о здоровье бота:")
        self.logger.log_info(f"⏱️ Время работы: {health['uptime_formatted']}")
        self.logger.log_info(f"📱 Статус сообщений: {health['message_status']}")
        self.logger.log_info(f"🌐 Статус API: {health['api_status']}")
        self.logger.log_info(f"💾 Статус БД: {health['db_status']}")
        self.logger.log_info(f"🎯 Общий статус: {health['overall_status']}")

# Пример использования
if __name__ == "__main__":
    print("🧪 Тестирование системы логирования и обработки ошибок...")
    
    # Создаем логгер
    bot_logger = BotLogger(log_level=logging.DEBUG)
    
    # Создаем обработчик ошибок
    error_handler = ErrorHandler(bot_logger)
    
    # Создаем монитор здоровья
    health_checker = HealthChecker(bot_logger)
    
    # Тестируем различные типы логов
    bot_logger.log_startup("test_token", "@test_channel")
    bot_logger.log_api_request("/test/endpoint", {"param": "value"}, True, 0.5)
    bot_logger.log_message_sent("news", "@test_channel", True)
    bot_logger.log_database_operation("INSERT", "news", True, 1)
    bot_logger.log_job_execution("send_news", True, 2.3)
    
    # Тестируем обработку ошибок
    try:
        raise ValueError("Тестовая ошибка")
    except Exception as e:
        error_handler.handle_telegram_error(e, "test_context")
    
    # Тестируем монитор здоровья
    health_checker.update_message_status(True)
    health_checker.update_api_status(True)
    health_checker.update_db_status(True)
    health_checker.log_health_report()
    
    # Получаем статистику
    logger_stats = bot_logger.get_stats()
    error_stats = error_handler.get_error_summary()
    health_stats = health_checker.get_health_status()
    
    print(f"📊 Статистика логгера: {logger_stats}")
    print(f"❌ Статистика ошибок: {error_stats}")
    print(f"💚 Статистика здоровья: {health_stats}")
    
    print("🎉 Тестирование завершено!")

