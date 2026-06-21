from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Информация", style="primary"),
                KeyboardButton(text="Установить юзербота", style="primary")
            ],
            [
                KeyboardButton(text="Мои юзерботы", style="primary"),
                KeyboardButton(text="Настройки", style="primary")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )


def get_access_request_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да",
                    callback_data=f"approve_{user_id}",
                    style="success"
                ),
                InlineKeyboardButton(
                    text="❌ Нет",
                    callback_data=f"deny_{user_id}",
                    style="danger"
                )
            ]
        ]
    )


def get_userbot_list_keyboard(userbots: list) -> InlineKeyboardMarkup:
    kb = []
    for ub in userbots:
        status_icon = "🟢" if ub["status"] == "on" else "🔴"
        kb.append([
            InlineKeyboardButton(
                text=f"{status_icon} {ub['name']}",
                callback_data=f"ub_select_{ub['name']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_userbot_control_keyboard(name: str, status: str) -> InlineKeyboardMarkup:
    if status == "on":
        row1 = [
            InlineKeyboardButton(text="Логи", callback_data=f"ub_logs_{name}", style="success"),
            InlineKeyboardButton(text="Рестарт", callback_data=f"ub_restart_{name}", style="success"),
        ]
        row2 = [
            InlineKeyboardButton(text="Остановить", callback_data=f"ub_stop_{name}", style="danger"),
            InlineKeyboardButton(text="Удалить", callback_data=f"ub_delete_{name}", style="danger"),
        ]
        row3 = [
            InlineKeyboardButton(text="Назад", callback_data="ub_back_list", style="primary"),
        ]
        
        return InlineKeyboardMarkup(
            inline_keyboard=[row1, row2, row3],
            row_width=2 
        )
    else:
        row1 = [
            InlineKeyboardButton(text="Запустить", callback_data=f"ub_start_{name}", style="success"),
            InlineKeyboardButton(text="Назад", callback_data="ub_back_list", style="primary"),
        ]
        
        return InlineKeyboardMarkup(
            inline_keyboard=[row1],
            row_width=2
        )