import logging
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from utils.category import build_category_buttons
from utils.expense import parse_expense_text
from handlers.settings import handle_rename_category, handle_expense_search, handle_expense_update
from db.repositories.user import handle_add_user, get_user
from db.repositories.category import insert_static_categories, get_category, handle_add_category
from db.repositories.expense import handle_add_expense
from db.repositories.keywordMapping import handle_add_keyword_category_mapping, get_keyword_category_mapping
from handlers.shared_handlers import handle_custom_setting_category_input, handle_currency_update
from utils.messages import *

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        tg_user = update.effective_user
        chat_id = str(update.effective_chat.id) if update.effective_chat else None
        if not chat_id:
            await update.message.reply_text(not_found("chat"))
            return
        db_user = handle_add_user(session, tg_user, chat_id=chat_id)
        if not db_user:
            await update.message.reply_text(user_not_found(personal=True))
            return

        insert_static_categories(session, user_id=db_user.id, chat_id=chat_id)
    finally:
        session.close()  
        
    text = update.message.text.strip()

    if context.user_data.get('awaiting_new_category'):
        await handle_custom_category_input(update, context)
        return
    elif context.user_data.get("awaiting_new_category_from_settings"):
        await handle_custom_setting_category_input(update, context)
    elif "rename_category" in context.user_data:
        await handle_rename_category(update, context)
        return
    elif context.user_data.get("awaiting_expense_search"):
        await handle_expense_search(update, context, text)
        return
    elif "edit_field" in context.user_data and "editing_expense_id" in context.user_data:
        await handle_expense_update(update, context)
        return
    elif context.user_data.get("awaiting_currency_change"):
        await handle_currency_update(update, context)
        return
    else:
        await handle_expense_entry(update, context)


async def handle_custom_category_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text(not_found("category"))
        return
    try:
        with SessionLocal() as session:
            chat_id = str(update.effective_chat.id) if update.effective_chat else None
            if not chat_id:
                await update.message.reply_text(not_found("chat"))
                return
            
            db_user = get_user(
                session,
                telegram_id=update.effective_user.id,
                chat_id=chat_id
            )
            category = handle_add_category(session, name=text, user_id=db_user.id, chat_id=chat_id)

            expense_data = context.user_data.get("pending_expense")
            if not expense_data:
                await update.message.reply_text(not_found("expense"))
                return

            expense = handle_add_expense(
                session=session,
                db_user=db_user,
                amount=expense_data["amount"],
                description=expense_data["description"],
                date=expense_data["date"],
                category_id=category.id,
                chat_id=chat_id
            )

            if not expense:
                await update.message.reply_text(edit_fail("saving"))
                return

            try:
                handle_add_keyword_category_mapping(
                    session=session,
                    keyword=expense_data["keyword"],
                    category_id=category.id,
                    chat_id=chat_id,
                    expense_id=expense.id
                )
            except Exception:
                logging.warning("⚠️ Keyword already mapped. Skipping.")

            await update.message.reply_text(
                log_personal_expense_success(
                    description=expense_data["description"],
                    category_name=category.name),
                parse_mode="Markdown"
            )

    except Exception:
        logging.exception("❌ Error while handling custom category input.")
        await update.message.reply_text(edit_fail("saving"))

    context.user_data.pop("awaiting_new_category", None)
    context.user_data.pop("pending_expense", None)

async def handle_expense_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    result = parse_expense_text(text)
    user = update.effective_user
    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    if not chat_id:
        await update.message.reply_text(not_found("chat"))
        return

    if "warning" in result:
        await update.message.reply_text(result["warning"], parse_mode="Markdown")
        return

    amount = result.get("amount")
    description = result.get("description")
    keyword = result.get("keyword", "")
    date = result.get("date")

    if not amount or not description:
        await update.message.reply_text(personal_expense_format_fail)
        return

    try:
        with SessionLocal() as session:
            match = get_keyword_category_mapping(
                session=session, keyword=keyword, category_id=None, keyword_only=True, chat_id=chat_id
            )
            db_user = get_user(
                session,
                telegram_id=user.id,
                chat_id=chat_id

            )
            if not db_user:
                    await update.message.reply_text(user_not_found(personal=True))
                    return

            if match:
                category = get_category(session=session, category_id=match.category_id, user_id=db_user.id, chat_id=chat_id)
                if not category:
                    await update.message.reply_text(not_found("category"))
                    return

                success = handle_add_expense(session, db_user=db_user, amount=amount, description=description, date=date, category_id=category.id, chat_id=chat_id)
                if not success:
                    await update.message.reply_text(edit_fail("saving"))
                else:
                    await update.message.reply_text(
                        log_personal_expense_success(
                            description=description,
                            category_name=category.name
                        ),
                        parse_mode="Markdown"
                    )
            else:
                context.user_data["pending_expense"] = {
                    "amount": amount,
                    "description": description,
                    "keyword": keyword,
                    "date": date
                }
                context.user_data['awaiting_new_category'] = True
                buttons = build_category_buttons(user_id=db_user.id, chat_id=chat_id)
                await update.message.reply_text(
                    "Choose a category for this expense:",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )

    except Exception:
        logging.exception("❌ Error while handling expense entry.")
        await update.message.reply_text(edit_fail("saving"))


async def handle_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.replace("cat:", "") 

    session = SessionLocal()
    try:
        expense_data = context.user_data.get("pending_expense", {})
        if not expense_data:
            await query.edit_message_text(not_found("expense"))
            return

        chat_id = str(update.effective_chat.id) if update.effective_chat else None
        if not chat_id:
            await query.edit_message_text(not_found("chat"))
            return

        if data == "__new__":
            await query.edit_message_text(new_cateogory_name, parse_mode="Markdown")
            context.user_data["awaiting_new_category"] = True
            return
        
        db_user = get_user(
            session,
            telegram_id=update.effective_user.id,
            chat_id=chat_id
        )

        category = handle_add_category(session=session, category_id=data, user_id=db_user.id, chat_id=chat_id)

        expense = handle_add_expense(session=session, db_user=db_user,
                           amount=expense_data["amount"],
                           description=expense_data["description"],
                           date=expense_data["date"],
                           category_id=category.id, chat_id=chat_id)

        handle_add_keyword_category_mapping(
            session=session,
            keyword=expense_data["keyword"],
            category_id=category.id,
            chat_id=chat_id,
            expense_id=expense.id
        )

        await query.edit_message_text(
            log_personal_expense_success(
                description=expense_data["description"],
                category_name=category.name
            ),
            parse_mode="Markdown"
        )

        context.user_data["awaiting_new_category"] = False
        context.user_data.pop("pending_expense")
    finally:
        session.close()

