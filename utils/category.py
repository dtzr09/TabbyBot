from telegram import InlineKeyboardButton
from db import SessionLocal
from db.repositories.category import get_all_categories
from utils.utils import display_prompt

def build_category_buttons(chat_id, user_id=None, callback_prefix="cat", view_only=False):
    session = SessionLocal()
    buttons = []

    try:
        db_categories = get_all_categories(
            session,
            user_id=user_id,
            chat_id=chat_id,
        )

        for cat in db_categories:
            name = cat.name.strip()
            buttons.append([InlineKeyboardButton(name, callback_data=f"{callback_prefix}:{cat.id}")])

    finally:
        session.close()

    if not view_only:
        buttons.append([InlineKeyboardButton("➕ New Category", callback_data=f"{callback_prefix}:__new__")])
    return buttons

async def get_category_settings(query):
    buttons = [
        [InlineKeyboardButton("📊 View Categories", callback_data="category_settings:view_categories")],
        [InlineKeyboardButton("✏️ Rename Category", callback_data="category_settings:rename_category")],
        [InlineKeyboardButton("➕ Add Category", callback_data="category_settings:add_category")],
        [InlineKeyboardButton("🗑️ Delete Category", callback_data="category_settings:delete_category")],
    ]
    await display_prompt(
        query=query,
        title="⚙️ Category Settings:",
        options=buttons,
        callback_prefix="settings"
    )
   


