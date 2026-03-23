from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from keyboards import get_main_keyboard, get_install_keyboard
from docker_manager import (
    build_image,
    create_container,
    is_image_built,
    start_tunnel,
    stop_container,
    is_user_container_running,
)

router = Router()

main_keyboard = get_main_keyboard()


@router.message(CommandStart())
async def handle_start(message: Message):
    """Обработчик команды /start"""
    user_name = message.from_user.first_name or message.from_user.username or "Пользователь"
    
    welcome_text = f"""
{user_name} <b><i>Добро пожаловать в OpenHost</i></b>

<b>⊱︎ Зачем нужен?</b>
<blockquote>Многие пользователи не могут разобраться как установить юзербот на свой сервер поэтому мы решили создать бота который поможет вам с этим</blockquote>
<b>⊱︎ Кто мы?</b>
<blockquote>Мы разработчики энтузиасты @coderholy | @HolyZxc </blockquote>

Выберите действие ниже 👇
"""
    
    await message.answer(
        text=welcome_text,
        parse_mode="HTML",
        reply_markup=main_keyboard
    )

@router.message(F.text == "📋 Информация")
async def handle_info(message: Message):
    """Обработчик кнопки Информация"""
    info_text = """
<b>📋 Информация о боте</b>

<b>OpenHost</b> - ваш помощник в установке юзерботов

<b>Что я умею:</b>
• Создавать контейнеры юзерботов прямо в телеграм
• Управлять их настройками
• Мониторить статус


Нажмите кнопку ниже для создания юзербота
"""
    
    await message.answer(text=info_text, parse_mode="HTML", reply_markup=main_keyboard)



@router.message(F.text == "🚀 Установить юзербота")
async def handle_install(message: Message):
    user_id = message.from_user.id

    try:
        running = is_user_container_running(user_id)
    except Exception:
        await message.answer(
            "<b>❌ Docker недоступен на сервере.</b>\n"
            "Убедитесь что Docker установлен и запущен.",
            parse_mode="HTML",
            reply_markup=main_keyboard,
        )
        return

    if running:
        await message.answer(
            "<b>⚠️ У вас уже запущен юзербот.</b>\n"
            "Используйте настройки для управления.",
            parse_mode="HTML",
            reply_markup=main_keyboard,
        )
        return

    text = (
        "<b>🚀 Установка юзербота Heroku</b>\n\n"
        "<b>Что произойдёт:</b>\n"
        "1. Создадим Docker-контейнер с юзерботом\n"
        "2. Пробросим туннель для веб-авторизации\n"
        "3. Отправим вам ссылку для входа\n\n"
        "<b>После авторизации юзербот начнёт работать автоматически.</b>\n"
        "Контейнер переживёт перезагрузку сервера."
    )

    await message.answer(text=text, parse_mode="HTML", reply_markup=get_install_keyboard())


@router.callback_query(F.data == "install_yes")
async def handle_install_confirm(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer()

    # Автосборка образа если его нет
    if not is_image_built():
        await callback.message.edit_text(
            "<b>⏳ Первый запуск — собираем Docker-образ...</b>\n"
            "Это может занять 5-10 минут, подождите.",
            parse_mode="HTML",
        )
        ok = await build_image()
        if not ok:
            await callback.message.edit_text(
                "<b>❌ Не удалось собрать Docker-образ.</b>\n"
                "Проверьте логи сервера.",
                parse_mode="HTML",
            )
            return

    await callback.message.edit_text(
        "<b>⏳ Создаём контейнер...</b>\nЭто может занять пару минут.",
        parse_mode="HTML",
    )

    try:
        container, port = await create_container(user_id)
    except Exception as e:
        await callback.message.edit_text(
            f"<b>❌ Ошибка при создании контейнера:</b>\n<code>{e}</code>",
            parse_mode="HTML",
        )
        return

    await callback.message.edit_text(
        "<b>⏳ Пробрасываем туннель...</b>",
        parse_mode="HTML",
    )

    url = await start_tunnel(user_id, port)

    if url:
        await callback.message.edit_text(
            "<b>✅ Юзербот готов!</b>\n\n"
            f"<b>Ссылка для авторизации:</b>\n{url}\n\n"
            "Откройте ссылку в браузере и следуйте инструкциям.",
            parse_mode="HTML",
        )
        await callback.message.answer(
            "Выберите действие ниже 👇",
            reply_markup=main_keyboard,
        )
    else:
        await callback.message.edit_text(
            f"<b>⚠️ Контейнер запущен, но туннель не удалось пробросить.</b>\n\n"
            f"Попробуйте открыть вручную: <code>http://localhost:{port}</code>",
            parse_mode="HTML",
        )
        await callback.message.answer(
            "Выберите действие ниже 👇",
            reply_markup=main_keyboard,
        )


@router.callback_query(F.data == "install_no")
async def handle_install_cancel(callback: CallbackQuery):
    await callback.answer("Установка отменена")
    await callback.message.edit_text(
        "Установка отменена. Вы можете начать заново в любой момент.",
        parse_mode="HTML",
    )


@router.message(F.text == "⚙️ Настройки")
async def handle_settings(message: Message):
    """Обработчик кнопки Настройки"""
    settings_text = """
<b>⚙️ Настройки</b>

<b>Ваши настройки:</b>
(Настройки скоро появятся)

"""
    
    await message.answer(text=settings_text, parse_mode="HTML", reply_markup=main_keyboard)
