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

# Инлайн клавиатура для подтверждения установки
def get_install_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Установить", callback_data="install_yes"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="install_no")
            ]
        ]
    )
