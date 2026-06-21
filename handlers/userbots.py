import logging
import re
import asyncio

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from handlers import router
from keyboards import (
    get_main_keyboard, get_userbot_list_keyboard,
    get_userbot_control_keyboard
)
from Database.database import db, UserbotStatus
from installation import (
    create_userbot, start_userbot, stop_userbot,
    restart_userbot, delete_userbot, get_logs,
    get_registration_url
)

logger = logging.getLogger(__name__)


class CreateBot(StatesGroup):
    waiting_name = State()


def _get_visible_userbots(user_id: int) -> list:
    if db.is_owner(user_id):
        return db.get_all_userbots()
    return db.get_user_userbots(user_id)


def _can_manage(user_id: int, ub: dict) -> bool:
    return db.is_owner(user_id) or ub["user_id"] == user_id


async def _send_registration_link_later(bot: Bot, chat_id: int, name: str):
    try:
        url_ok, url_msg, registration_url = await get_registration_url(name)
        logger.info(f"Юзербот {name}: результат ссылки ok={url_ok}, msg={url_msg}")

        if url_ok and registration_url:
            await bot.send_message(
                chat_id,
                f"✅ <b>Ссылка регистрации для «{name}» готова</b>\n\n"
                f"Откройте веб-интерфейс и завершите вход:\n"
                f"<a href=\"{registration_url}\">{registration_url}</a>",
                parse_mode="HTML"
            )
            return

        await bot.send_message(
            chat_id,
            f"⚠️ <b>Не удалось подготовить ссылку регистрации для «{name}»</b>\n\n"
            f"<code>{url_msg}</code>\n\n"
            f"Откройте логи юзербота и проверьте публичную ссылку "
            f"<code>serveousercontent.com</code> или <code>lhr.life</code>.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Юзербот {name}: ошибка фоновой подготовки ссылки: {e}")
        try:
            await bot.send_message(
                chat_id,
                f"⚠️ Не удалось подготовить ссылку регистрации для «{name}». Проверьте логи сервера.",
                parse_mode="HTML"
            )
        except Exception as send_error:
            logger.warning(f"Не удалось отправить ошибку подготовки ссылки: {send_error}")


@router.message(F.text.in_({"📋 Мои юзерботы", "Мои юзерботы"}))
async def handle_my_userbots(message: Message):
    user_id = message.from_user.id
    userbots = _get_visible_userbots(user_id)

    if not userbots:
        await message.answer(
            "📋 <b>У вас пока нет юзерботов</b>\n\nНажмите «🚀 Установить юзербота» чтобы создать.",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        return

    title = "📋 <b>Все юзерботы:</b>" if db.is_owner(user_id) else "📋 <b>Ваши юзерботы:</b>"
    await message.answer(
        f"{title}\n\nВыберите юзербота для управления:",
        parse_mode="HTML",
        reply_markup=get_userbot_list_keyboard(userbots)
    )


@router.callback_query(F.data.startswith("ub_select_"))
async def callback_select_userbot(callback: CallbackQuery):
    user_id = callback.from_user.id
    name = callback.data.replace("ub_select_", "")
    ub = db.get_userbot(name)

    if not ub or not _can_manage(user_id, ub):
        await callback.answer("🚫 Доступ запрещён", show_alert=True)
        return

    await callback.answer()
    status_emoji = "🟢 Включён" if ub["status"] == UserbotStatus.ON else "🔴 Выключен"
    owner_note = f"\nВладелец: {ub['created_by']}" if db.is_owner(user_id) and ub["user_id"] != user_id else ""
    text = f"""
<b>{ub['name']}</b>

Статус: {status_emoji}
Создан: {ub['created_by']}
Дата: {ub['created_at']}{owner_note}
"""
    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=get_userbot_control_keyboard(name, ub["status"])
    )


@router.callback_query(F.data == "ub_back_list")
async def callback_back_to_list(callback: CallbackQuery):
    user_id = callback.from_user.id
    userbots = _get_visible_userbots(user_id)

    await callback.answer()
    if not userbots:
        await callback.message.edit_text(
            "📋 <b>У вас пока нет юзерботов</b>",
            parse_mode="HTML"
        )
        return

    title = "📋 <b>Все юзерботы:</b>" if db.is_owner(user_id) else "📋 <b>Ваши юзерботы:</b>"
    await callback.message.edit_text(
        f"{title}\n\nВыберите юзербота для управления:",
        parse_mode="HTML",
        reply_markup=get_userbot_list_keyboard(userbots)
    )


async def _exec_userbot_action(callback: CallbackQuery, name: str, func, action_text: str, bot: Bot):
    user_id = callback.from_user.id
    ub = db.get_userbot(name)

    if not ub or not _can_manage(user_id, ub):
        await callback.answer("🚫 Доступ запрещён", show_alert=True)
        return

    await callback.answer(f"⏳ {action_text}...")
    logger.info(f"Юзербот {name}: действие '{action_text}' запросил user_id={user_id}")
    ok, msg = await func(name)
    await callback.answer(msg, show_alert=True)

    if ok:
        if action_text in ("Запуск", "Перезапуск"):
            asyncio.create_task(_send_registration_link_later(bot, callback.message.chat.id, name))

        if db.is_owner(user_id) and ub["user_id"] != user_id:
            try:
                await bot.send_message(
                    ub["user_id"],
                    text=f"<b>Владелец {action_text.lower()} юзербота «{name}»</b>",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Не удалось уведомить пользователя: {e}")

        ub = db.get_userbot(name)
        status = ub["status"] if ub else UserbotStatus.OFF
        status_emoji = "🟢 Включён" if status == UserbotStatus.ON else "🔴 Выключен"
        text = f"""
<b>{name}</b>

Статус: {status_emoji}
"""
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_userbot_control_keyboard(name, status)
        )


@router.callback_query(F.data.startswith("ub_start_"))
async def callback_start_userbot(callback: CallbackQuery, bot: Bot):
    name = callback.data.replace("ub_start_", "")
    await _exec_userbot_action(callback, name, start_userbot, "Запуск", bot)


@router.callback_query(F.data.startswith("ub_stop_"))
async def callback_stop_userbot(callback: CallbackQuery, bot: Bot):
    name = callback.data.replace("ub_stop_", "")
    await _exec_userbot_action(callback, name, stop_userbot, "Остановка", bot)


@router.callback_query(F.data.startswith("ub_restart_"))
async def callback_restart_userbot(callback: CallbackQuery, bot: Bot):
    name = callback.data.replace("ub_restart_", "")
    await _exec_userbot_action(callback, name, restart_userbot, "Перезапуск", bot)


@router.callback_query(F.data.startswith("ub_delete_"))
async def callback_delete_userbot(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    name = callback.data.replace("ub_delete_", "")
    ub = db.get_userbot(name)

    if not ub or not _can_manage(user_id, ub):
        await callback.answer("🚫 Доступ запрещён", show_alert=True)
        return

    await callback.answer("⏳ Удаление...")
    ok, msg = await delete_userbot(name)
    await callback.answer(msg, show_alert=True)

    if ok:
        if db.is_owner(user_id) and ub["user_id"] != user_id:
            try:
                await bot.send_message(
                    ub["user_id"],
                    text=f"<b>Владелец удалил юзербота «{name}»</b>",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Не удалось уведомить пользователя: {e}")

        userbots = _get_visible_userbots(user_id)
        if userbots:
            title = "📋 <b>Все юзерботы:</b>" if db.is_owner(user_id) else "📋 <b>Ваши юзерботы:</b>"
            await callback.message.edit_text(
                f"{title}\n\nВыберите юзербота для управления:",
                parse_mode="HTML",
                reply_markup=get_userbot_list_keyboard(userbots)
            )
        else:
            await callback.message.edit_text(
                "📋 <b>У вас пока нет юзерботов</b>",
                parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("ub_logs_"))
async def callback_userbot_logs(callback: CallbackQuery):
    user_id = callback.from_user.id
    name = callback.data.replace("ub_logs_", "")
    ub = db.get_userbot(name)

    if not ub or not _can_manage(user_id, ub):
        await callback.answer("🚫 Доступ запрещён", show_alert=True)
        return

    ok, logs = await get_logs(name)
    if ok:
        text = f"📜 <b>Логи {name}:</b>\n<pre>{logs[:3500]}</pre>"
        if len(logs) > 3500:
            text += "\n\n<i>... (обрезано)</i>"
    else:
        text = f"📜 <b>Логи {name}:</b>\n<pre>Логи пусты</pre>"

    await callback.answer()
    await callback.message.answer(text, parse_mode="HTML")


@router.message(F.text.in_({"🚀 Установить юзербота", "Установить юзербота"}))
async def handle_install_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not db.is_trusted(user_id) and not db.is_owner(user_id):
        await message.answer("🚫 Доступ ограничен")
        return

    await message.answer(
        "🚀 <b>Установка юзербота</b>\n\n"
        "Введите название для вашего юзербота:\n"
        "(только латиница, без цифр, макс. 10 символов)",
        parse_mode="HTML"
    )
    await state.set_state(CreateBot.waiting_name)


@router.message(CreateBot.waiting_name)
async def handle_install_name(message: Message, state: FSMContext, bot: Bot):
    name = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username or f"id{user_id}"

    if not re.match(r"^[a-zA-Z]+$", name):
        await message.answer(
            "❌ Только латиница, без цифр и знаков. Попробуйте ещё раз:",
            parse_mode="HTML"
        )
        return

    if len(name) > 10:
        await message.answer("❌ Максимум 10 символов. Попробуйте ещё раз:")
        return

    await message.answer(
        f"⏳ Создаю юзербота «{name}»...\n"
        f"Клонирование репозитория, установка зависимостей и запуск сервиса...",
        parse_mode="HTML"
    )

    logger.info(f"Юзербот {name}: установка начата user_id={user_id} username=@{username}")
    ok, msg = await create_userbot(name, user_id, f"@{username}")
    logger.info(f"Юзербот {name}: результат установки ok={ok}, msg={msg}")

    if ok:
        await message.answer(
            f"⏳ Юзербот создан. Ищу готовую публичную ссылку в логах...\n"
            f"Как только ссылка будет готова, я пришлю её отдельным сообщением.",
            parse_mode="HTML"
        )
        asyncio.create_task(_send_registration_link_later(bot, message.chat.id, name))

        await message.answer(
            f"✅ <b>Юзербот «{name}» установлен и запущен</b>\n\nСтатус: 🟢 Включён",
            parse_mode="HTML",
            reply_markup=get_userbot_control_keyboard(name, UserbotStatus.ON)
        )
    else:
        await message.answer(msg, parse_mode="HTML", reply_markup=get_main_keyboard())

    await state.clear()
