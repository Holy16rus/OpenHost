import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import router
from Database.database import db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_or_create_config() -> str:
    token = db.get_token()
    if token:
        return token

    print("=" * 40)
    print("Первый запуск! Введите BotToken:")
    print("(Получить: @BotFather -> /newbot -> скопировать токен)")
    print("=" * 40)
    token = input("BotToken: ").strip()

    if not token:
        logger.error("Токен не может быть пустым!")
        exit(1)

    db.set_token(token)
    logger.info("Токен сохранён в Database/config.json")
    return token


async def main():
    bot_token = load_or_create_config()

    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True
        )
    )

    dp = Dispatcher()

    dp.include_router(router)

    logger.info("Запуск бота...")
    logger.info(f"Bot ID: {bot.id}")

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
    logger.info("Бот успешно запущен!")


async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    logger.info("Остановка бота...")
    await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
