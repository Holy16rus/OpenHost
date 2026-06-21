# OpenHost - AI Agent Guidelines

## Project Overview
OpenHost is a Python Telegram bot built with aiogram 3.26.0 for managing userbot installations. The bot handles user authentication, access control, and provides an interface for userbot deployment.

## Build & Run Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot locally (first run asks for BotToken)
python main.py
```

## Testing
**Note**: No formal test suite exists. For testing:
```bash
# Manual testing: run bot and interact via Telegram
python main.py

# Check for syntax errors
python -m py_compile main.py handlers/__init__.py handlers/misc.py handlers/access.py handlers/userbots.py keyboards.py quote.py Database/database.py installation.py
```

## Code Style Guidelines

### General Conventions
- **Language**: Code comments and UI text are in **Russian**, variable names in **English**
- **Async/Await**: All Telegram API calls use async/await pattern
- **Type Hints**: Use Python type hints where practical (especially in Database module)
- **Docstrings**: Russian docstrings for functions, especially handlers
- **Error Handling**: Use try/except with logging, never let bot crash silently

### Import Style
```python
# Standard library first
import asyncio
import json
import logging
import os

# Third-party
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

# Local modules
from handlers import router
from handlers.misc import send_welcome
from keyboards import get_main_keyboard
from Database.database import db, UserbotStatus
from installation import create_userbot, start_userbot
```

### Naming Conventions
- **Functions**: `snake_case` (e.g., `handle_start`, `send_small_quote`)
- **Constants**: `UPPER_SNAKE_CASE` (none currently, but use if needed)
- **Classes**: `PascalCase` (e.g., `QuoteConfig`, `Database`)
- **Files**: `snake_case.py` (e.g., `handlers.py`, `keyboards.py`)

### Handler Pattern
```python
@router.message(CommandStart())
async def handle_start(message: Message):
    user_id = message.from_user.id
    if not db.is_approved(user_id):
        await message.answer("🚫 Доступ ограничен")
        return
    # Main logic
```

### Submodule Pattern
```python
# handlers/userbots.py
from handlers import router
from Database.database import db, UserbotStatus

@router.callback_query(F.data.startswith("ub_start_"))
async def callback_start(callback: CallbackQuery):
    # Logic
```

### Keyboard Pattern
```python
# Inline keyboards for callbacks
def get_welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Информация", callback_data="info"),
            ]
        ]
    )

# Reply keyboards for main menu
def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Информация")]],
        resize_keyboard=True
    )
```

## Architecture

### Directory Structure
```
OpenHost/
├── main.py              # Bot entry point, config.json loading
├── handlers/
│   ├── __init__.py      # Router creation + submodule imports
│   ├── misc.py          # start, info, settings handlers
│   ├── access.py        # approve/deny access callbacks
│   └── userbots.py      # userbot CRUD + management handlers
├── keyboards.py         # Keyboard definitions
├── quote.py             # Media preview utilities
├── installation.py      # Userbot installation via systemd
├── Profile/             # Userbot profiles (gitignored)
│   └── <name>/
│       └── Heroku/      # Cloned repo
├── Database/
│   └── config.json      # BotToken, users, userbots (gitignored)
└── Планы/
    └── plan.md          # Architecture documentation (Russian)
```

### Key Components

1. **Config** (`Database/config.json`):
   - Created on first run via console input
   - Stores BotToken, owner_id, trusted_users, pending_requests, userbots
   - Gitignored

2. **Database Layer** (`Database/database.py`):
   - JSON file-based storage
   - `UserbotStatus` class with `ON` / `OFF` constants
   - Owner/trusted/pending user management
   - Global `db` instance for easy access

3. **Quote System** (`quote.py`):
   - `QuoteConfig` dataclass for message preview configuration
   - Multiple send functions: `send_small_quote`, `send_large_preview`, `send_media_above_text`
   - Uses aiogram's `LinkPreviewOptions` for media placement

4. **Access Control**:
   - First user becomes owner automatically
   - Owner approves/denies pending users
   - Three statuses: owner, trusted, restricted
   - `handlers/access.py` handles approve/deny callbacks

## Userbot Storage Format

Userbots stored in `Database/bot_data.json` under `userbots` field:
```json
{
  "userbot_name": {
    "name": "userbot_name",
    "user_id": 123456789,
    "created_by": "@username",
    "created_at": "31.01.2025 12:00",
    "status": "off"
  }
}
```

## Userbot Storage Format

Userbots stored in `Database/config.json` under `userbots` field:
```json
{
  "userbot_name": {
    "name": "userbot_name",
    "user_id": 123456789,
    "created_by": "@username",
    "created_at": "31.01.2025 12:00",
    "status": "off"
  }
}
```

## Common Patterns

### Error Handling
```python
try:
    await bot.send_message(...)
except Exception as e:
    logger.warning(f"Ошибка при отправке: {e}")
```

### Callback Query Handling
```python
@router.callback_query(F.data == "confirm_yes")
async def callback_confirm_yes(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not db.is_owner(user_id):
        await callback.answer("🚫 Только владелец", show_alert=True)
        return
    await callback.answer()
```

## Adding New Features

### Adding a Handler
1. Define handler in `handlers.py`
2. Add keyboard to `keyboards.py` if needed
3. Import and include in `main.py` router
4. Update access control checks

### Adding New Commands
```python
@router.message(Command("newcommand"))
async def handle_new_command(message: Message):
    if not db.is_approved(message.from_user.id):
        return await message.answer("🚫 Доступ ограничен")
    # Implementation
```

## Important Notes

1. **No CI/CD**: No automated tests or deployment pipelines
2. **No Linting Config**: Code style follows patterns, not enforced tools
3. **Russian Language**: All user-facing text is in Russian
4. **Simple Architecture**: No complex patterns, keep it straightforward
5. **Database**: Simple JSON file, no SQL databases
6. **Setup**: One command installation via README

## When Modifying Code

- Follow existing handler patterns
- Maintain Russian comments for documentation
- Use type hints for new functions
- Add try/except for external API calls
- Keep keyboard definitions in `keyboards.py`
- Don't modify `Database/config.json` directly - use Database methods
