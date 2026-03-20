from aiogram import Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def setup_keyboards(bot: Bot):
    """Настройка клавиатур бота"""
    pass

# Главная клавиатура
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает главную клавиатуру"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Информация"),
                KeyboardButton(text="🚀 Установить юзербота")
            ],
            [
                KeyboardButton(text="⚙️ Настройки")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

# Инлайн клавиатура для подтверждения
def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Возвращает инлайн клавиатуру для подтверждения действия"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="confirm_no")
            ]
        ]
    )
