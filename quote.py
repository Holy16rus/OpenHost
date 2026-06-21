from aiogram.types import Message, LinkPreviewOptions, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.enums import ParseMode
from typing import Optional, Union
from dataclasses import dataclass

@dataclass
class QuoteConfig:
    """Конфигурация для цитаты"""
    media_url: str
    text: str
    is_small: bool = True  # Компактный вид (цитата) или большой
    show_above_text: bool = True  # Медиа выше или ниже текста
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None

def create_link_preview(config: QuoteConfig) -> LinkPreviewOptions:
    """Создает настройки предпросмотра для цитаты"""
    return LinkPreviewOptions(
        url=config.media_url,
        prefer_small_media=config.is_small,
        prefer_large_media=not config.is_small,
        show_above_text=config.show_above_text,
        is_disabled=False
    )

async def send_quote_message(
    message: Message,
    text: str,
    media_url: str,
    *,
    is_small: bool = True,
    show_above_text: bool = True,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None
) -> Message:
    """
    Отправляет сообщение с цитатой и медиа предпросмотром
    
    Args:
        message: Исходное сообщение для ответа
        text: Текст сообщения (поддерживает HTML)
        media_url: URL на медиа (фото/видео)
        is_small: Компактный вид (цитата) или большой предпросмотр
        show_above_text: Медиа выше или ниже текста
        reply_markup: Опциональная клавиатура
    
    Returns:
        Отправленное сообщение
    """
    config = QuoteConfig(
        media_url=media_url,
        text=text,
        is_small=is_small,
        show_above_text=show_above_text,
        reply_markup=reply_markup
    )
    
    link_options = create_link_preview(config)
    
    return await message.answer(
        text=text,
        parse_mode=ParseMode.HTML,
        link_preview_options=link_options,
        reply_markup=reply_markup
    )

# Удобные обертки для разных сценариев

async def send_small_quote(
    message: Message,
    text: str,
    media_url: str,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None
) -> Message:
    """Отправляет компактную цитату (медиа сбоку, как цитата)"""
    return await send_quote_message(
        message=message,
        text=text,
        media_url=media_url,
        is_small=True,
        show_above_text=True,
        reply_markup=reply_markup
    )

async def send_large_preview(
    message: Message,
    text: str,
    media_url: str,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None
) -> Message:
    """Отправляет большое превью (медиа во всю ширину)"""
    return await send_quote_message(
        message=message,
        text=text,
        media_url=media_url,
        is_small=False,
        show_above_text=False,
        reply_markup=reply_markup
    )

async def send_media_above_text(
    message: Message,
    text: str,
    media_url: str,
    is_small: bool = True,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None
) -> Message:
    """Отправляет медиа выше текста"""
    return await send_quote_message(
        message=message,
        text=text,
        media_url=media_url,
        is_small=is_small,
        show_above_text=True,
        reply_markup=reply_markup
    )