import logging

from aiogram import F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message

from handlers import router
from keyboards import get_main_keyboard, get_access_request_keyboard
from Database.database import db
from quote import send_small_quote

logger = logging.getLogger(__name__)

main_keyboard = get_main_keyboard()

WELCOME_IMAGE = "https://pix-up.ru/uploads/img_6a1c0e0b7e4380.01573475_1780223499.png"
ACCESS_IMAGE = "https://pix-up.ru/uploads/img_6a1c0330358555.41904691_1780220720.png"


async def send_welcome(message: Message, user_name: str):
    await send_small_quote(
        message,
        text=f"""
{user_name} <b><i>Добро пожаловать в OpenHost</i></b>

<b>⊱︎ Зачем нужен?</b>
<blockquote>Многие пользователи не могут разобраться как установить юзербот на свой сервер поэтому мы решили создать бота который поможет вам с этим</blockquote>
<b>⊱︎ Кто мы?</b>
<blockquote>Мы разработчики энтузиасты @coderholy | @HolyZxc </blockquote>

Выберите действие ниже 👇
""",
        media_url=WELCOME_IMAGE,
        reply_markup=main_keyboard
    )


@router.message(CommandStart())
async def handle_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username or "Нет username"
    first_name = message.from_user.first_name or "Пользователь"
    user_name = message.from_user.first_name or message.from_user.username or "Пользователь"

    if db.is_owner(user_id) or db.is_trusted(user_id):
        await send_welcome(message, user_name)
        return

    if db.get_owner_id() is None:
        db.set_owner(user_id)
        await send_welcome(message, user_name)
        return

    await send_small_quote(
        message,
        text="<a href=\"tg://emoji?id=5821453562680448557\">🔐</a> <b>Владелец получит уведомление о вашем запросе</b>",
        media_url=ACCESS_IMAGE
    )

    if db.has_pending_request(user_id):
        return

    db.add_pending_request(user_id)

    owner_id = db.get_owner_id()
    if owner_id:
        from datetime import datetime
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        owner_text = f"""
<b>Запрос на доступ</b>

Пользователь: @{username}
Name: {first_name}
Дата: {now}

Просит доступ к боту, разрешить?
"""
        await bot.send_message(
            owner_id,
            text=owner_text,
            parse_mode="HTML",
            reply_markup=get_access_request_keyboard(user_id)
        )


@router.message(F.text.in_({"📋 Информация", "Информация"}))
async def handle_info(message: Message):
    info_text = """
<b>📋 Информация о боте</b>

<b>OpenHost</b> - ваш помощник в установке юзерботов

<b>Что я умею:</b>
• Создавать юзерботов на сервере
• Управлять их настройками через systemd
• Мониторить статус

Нажмите кнопку ниже для создания юзербота
"""
    await message.answer(text=info_text, parse_mode="HTML", reply_markup=main_keyboard)


@router.message(F.text.in_({"⚙️ Настройки", "Настройки"}))
async def handle_settings(message: Message):
    settings_text = """
<b>⚙️ Настройки</b>

<b>Ваши настройки:</b>
(Настройки скоро появятся)
"""
    await message.answer(text=settings_text, parse_mode="HTML", reply_markup=main_keyboard)
