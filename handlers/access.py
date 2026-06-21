import logging

from aiogram import F, Bot
from aiogram.types import CallbackQuery

from handlers import router
from Database.database import db

logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("approve_"))
async def callback_approve_access(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not db.is_owner(user_id):
        await callback.answer("🚫 Только владелец может одобрять доступ", show_alert=True)
        return

    target_id = int(callback.data.replace("approve_", ""))
    db.add_trusted_user(target_id)
    db.clear_pending_request(target_id)

    await callback.answer("✅ Доступ разрешён")
    await callback.message.delete()

    await bot.send_message(
        target_id,
        text="<b>Поздравляем владелец разрешил доступ </b>\n<blockquote><b><i>Приятного использования бота</i></b></blockquote>",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("deny_"))
async def callback_deny_access(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not db.is_owner(user_id):
        await callback.answer("🚫 Только владелец может отклонять доступ", show_alert=True)
        return

    target_id = int(callback.data.replace("deny_", ""))
    db.remove_trusted_user(target_id)
    db.clear_pending_request(target_id)

    await callback.answer("❌ Доступ отклонён")
    await callback.message.delete()

    await bot.send_message(
        target_id,
        text="<b>В доступе отказано.</b>",
        parse_mode="HTML"
    )
