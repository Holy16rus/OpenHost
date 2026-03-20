from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from keyboards import get_main_keyboard

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



@router.message(F.text == "⚙️ Настройки")
async def handle_settings(message: Message):
    """Обработчик кнопки Настройки"""
    settings_text = """
<b>⚙️ Настройки</b>

<b>Ваши настройки:</b>
(Настройки скоро появятся)

"""
    
    await message.answer(text=settings_text, parse_mode="HTML", reply_markup=main_keyboard)
