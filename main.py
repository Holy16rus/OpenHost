import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()

from handlers import router
from keyboards import setup_keyboards

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    bot_token = os.getenv("BotToken")
    if not bot_token:
        logger.error("BotToken не найден в переменных окружения!")
        return
    
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True
        )
    )
    
    dp = Dispatcher()
    
    dp.include_router(router)
    
    try:
        setup_keyboards(bot)
    except Exception as e:
        logger.warning(f"Ошибка при настройке клавиатур: {e}")
    
    logger.info("Запуск бота...")
    logger.info(f"Bot ID: {bot.id}")
    
    from aiogram.client.telegram import TelegramAPIServer
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot username: @{bot_info.username}")
    except Exception as e:
        logger.warning(f"Не удалось получить username: {e}")
    
    try:
        await dp.start_polling(
            bot,
            handle_signals=False,
            on_startup=on_startup,
            on_shutdown=on_shutdown
        )
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    """Действия при запуске бота"""
    logger.info("Бот успешно запущен!")
    
async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    """Действия при остановке бота"""
    logger.info("Остановка бота...")
    await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")