from telegram.ext import ContextTypes
from telegram import Update
from db import SessionLocal
import logging
from db.repositories.category import get_category, handle_add_category
from db.repositories.user import get_user,update_user
from utils.messages import *
from utils.checks import validate_currency_selection
from db.repositories.group import update_group_currency

async def handle_custom_setting_category_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❗ Category name cannot be empty.")
        return
    chat_id = str(update.effective_chat.id)
    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]
    telegram_id = str(update.effective_user.id) if not group_chat else None

    try:
        with SessionLocal() as session:
            db_user = get_user(
                session,
                chat_id=chat_id,
                telegram_id=telegram_id
            )
            # Check if already exists
            existing = get_category(
                            session,
                            name=text,
                            chat_id=chat_id,
                            user_id=db_user.id if not group_chat else None,
                        )
            
            if existing:
                await update.message.reply_text(
                    f"⚠️ Category '{existing.name}' already exists."
                )
                return

            new_cat = handle_add_category(
                session,
                name=text,
                chat_id=chat_id,
                user_id=db_user.id if not group_chat else None
            )
            
            await update.message.reply_text(
                f"✅ Custom category '{new_cat.name}' created successfully!"
            )

    except Exception:
        logging.exception("❌ Error creating new category")
        await update.message.reply_text("❌ Failed to create new category.")

    if group_chat:
        context.user_data.pop("awaiting_new_category_from_settings", None)
    else:
        context.user_data.pop("awaiting_new_category_from_settings", None)

async def handle_currency_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    currency = update.message.text.strip()
    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]
    chat_id = str(update.effective_chat.id)

    if not currency:
        await update.message.reply_text(empty_input)
        return

    if not validate_currency_selection(currency):
        await update.message.reply_text(invalid_currency)
        return

    session = SessionLocal()

    if group_chat:
        update_group_res = update_group_currency(
            session=session,
            chat_id=chat_id,
            new_currency=currency
        )
        context.chat_data.pop("awaiting_currency_change", None)
        if update_group_res:
            logging.info(f"✅ Group {update.effective_chat.title} ({chat_id}) updated currency to {currency}.")
            await update.message.reply_text(currency_change(currency=currency))
        else:
            await update.message.reply_text(edit_fail("updating group currency"))
    else:
        update_user_res = update_user(
            session=session,
            telegram_id=update.effective_user.id,
            chat_id=chat_id,
            currency=currency
        )
        context.user_data.pop("awaiting_currency_change", None)
        if update_user_res:
            logging.info(f"✅ User {update.effective_user.full_name} ({update.effective_user.id}) updated currency to {currency}.")
            await update.message.reply_text(currency_change(currency=currency))
        else:
            await update.message.reply_text(edit_fail("updating"))

        
  
    