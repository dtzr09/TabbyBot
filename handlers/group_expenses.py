import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db import SessionLocal
from utils.category import build_category_buttons
from db.repositories.user import handle_add_user, get_all_group_members, get_user, get_all_users
from db.repositories.group import register_group, is_group_registered
from db.repositories.category import insert_static_categories, get_category, add_category
from db.repositories.expense import handle_add_expense
from db.repositories.keywordMapping import handle_add_keyword_category_mapping, get_keyword_category_mapping
from db.repositories.debtSettlement import add_debt_settlement
from utils.expense import parse_group_expense_input, handle_expense_split
from handlers.shared_handlers import handle_custom_setting_category_input, handle_currency_update
from handlers.settings import * 
from utils.stats import get_group_balances_stats
from utils.checks import validate_currency_selection
from utils.messages import *

async def start_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        context.chat_data["awaiting_additional_info"] = True
        await update.message.reply_text(
            start_group_text,
            parse_mode='MarkdownV2'
        )
    except Exception:
        logging.exception("❌ Error in start_group_command")
        await update.message.reply_text(add_group_admin_failed)
    finally:
        session.close()

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if context.chat_data.get("awaiting_additional_info"):
        await handle_additional_info(update, context)
    elif context.chat_data.get("awaiting_new_category"):
        await handle_group_custom_category_input(update, context)
    elif context.chat_data.get("awaiting_new_category_from_settings"):
        await handle_custom_setting_category_input(update, context)
    elif context.chat_data.get("awaiting_expense_search"):
        await handle_expense_search(update, context, text) 
    elif "rename_category" in context.chat_data:
        await handle_rename_category(update, context)
    elif "edit_field" in context.chat_data and "editing_expense_id" in context.chat_data:
        await handle_expense_update(update, context)
    elif context.chat_data.get("awaiting_settle_amount"):
        await handle_settle_debt_amount(update, context)
    elif context.chat_data.get("awaiting_currency_change"):
        await handle_currency_update(update, context)
    else:
        await handle_group_expense_entry(update, context)

async def handle_add_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    chat_id = str(update.effective_chat.id)

    if not is_group_registered(session, chat_id):
        await update.message.reply_text(group_not_registered)
        return

    group_admins = get_all_users(session, chat_id=chat_id)
    group_admins_id = [admin.telegram_id for admin in group_admins]
    if not group_admins:
        await update.message.reply_text(group_not_registered)
        return
    
    admins = await context.bot.get_chat_administrators(chat_id)
    
    # Need to include the bot itself in the admins list
    if len(group_admins) == len(admins)-1:
        await update.message.reply_text(no_new_admins, parse_mode='Markdown')
        return
    new_admins = []
    for admin in admins:
        user = admin.user
        if user.is_bot:
            continue
        if str(user.id) in group_admins_id:
            continue
        
        user = handle_add_user(session, user, chat_id)
        new_admins.append(user.username)
    session.close()

    await update.message.reply_text(add_new_admins_success(new_admins))


async def handle_additional_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    session = SessionLocal()
    if not text:
        await update.message.reply_text(additional_info_fail)
        return

    # Split the input into currency and purpose
    parts = text.split(" ", 1)
    if len(parts) != 2:
        await update.message.reply_text(invalid_format_currency_purpose)
        return

    currency, purpose = parts

    if(not validate_currency_selection(currency)):
        await update.message.reply_text(
            invalid_currency
        )
        return


    chat_title = update.effective_chat.title
    chat_id = str(update.effective_chat.id)
    admins = await context.bot.get_chat_administrators(chat_id)
        
    added = []
    for admin in admins:
        user = admin.user
        if user.is_bot:
            continue  # Skip bots
        handle_add_user(session, user, chat_id)
        added.append(f"• {user.full_name.capitalize()} (@{user.username or 'no username'})")

    insert_static_categories(session, None, chat_id)
    register_group(session, chat_id, chat_title, currency, int(purpose))

    context.chat_data["awaiting_additional_info"] = False

    await update.message.reply_text(
        f"🚀 Your group is officially onboarded!\n\n"
        f"👥 Successfully added {len(added)} admin(s):\n" + "\n".join(added) + "\n\n"
        "✅ You can now start adding group expenses! \n\nUse the following formats:\n\n"
        "• 10 lunch @user1 @user2 – for equal split\n"
        "• 10 lunch @user1 5 @user2 10 @user3 20 – for custom split\n"
        "• 10 lunch @user1 5 @user2 10 @me 20 – custom split including yourself (`@me` refers to you)\n"
        "• 10 lunch @user1 5 @user2 10 @me 20 dd/mm – custom split with date\n\n"
    )

async def handle_group_expense_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = str(update.effective_chat.id)
    session = SessionLocal()
    sender = update.effective_user

    try:
        if not is_group_registered(session, chat_id):
            await update.message.reply_text(group_not_registered)
            return
    finally:
        session.close()


    result = parse_group_expense_input(session, chat_id, text, sender)

    if result["warning"]:
        await update.message.reply_text(result["warning"])
        return

    context.chat_data["group_expense_data"] = {
        "amount": result["amount"],
        "description": result["description"],
        "date": result["date"],
        "chat_id": str(update.effective_chat.id),
        'participants': result["mentions_ids"],
        'is_equal_split': result['is_equal_split'],
        'custom_split': result['custom_split']
    }

    members = get_all_group_members(session, chat_id)
    buttons = []
    for m in members:
        buttons.append([InlineKeyboardButton(m.name.capitalize(), callback_data=f"payer:{m.id}")])

    await update.message.reply_text("💰 Who paid for this expense?", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_group_expense_payer_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    payer_id = int(query.data.replace("payer:", ""))

    context.chat_data["group_expense_data"]["payer_id"] = payer_id
    chat_id = context.chat_data["group_expense_data"]["chat_id"]

    with SessionLocal() as session:
        match = get_keyword_category_mapping(
            session=session,
            keyword=context.chat_data["group_expense_data"]["description"],
            category_id=None,
            keyword_only=True,
            chat_id=chat_id
        )
        if match:
            context.chat_data["group_expense_data"]["category_id"] = match.category_id
            await save_group_expense(session, query, context)
            return
        else:
            context.chat_data["group_expense_data"]["category_id"] = None
            buttons = build_category_buttons(chat_id=chat_id, callback_prefix="group_cat")
            await query.edit_message_text("📂 Choose a category for this expense:", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_group_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.replace("group_cat:", "")

    expense_data = context.chat_data.get("group_expense_data", {})
    if not expense_data:
        await query.edit_message_text(no_pending_group_expense)
        return

    if data == "__new__":
        context.chat_data["awaiting_new_category"] = True
        await query.edit_message_text(new_cateogory_name, parse_mode='MarkdownV2')
        return

    try:
        category_id = int(data)
        context.chat_data["group_expense_data"]["category_id"] = category_id

        with SessionLocal() as session:
            await save_group_expense(session, query, context)
    except Exception:
        logging.exception("❌ Error handling group category selection")
        await query.edit_message_text(edit_fail("edit"))


async def handle_group_custom_category_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text(additional_info_fail)
        return
    
    chat_id = str(update.effective_chat.id)

    try:
        with SessionLocal() as session:
            # Check if already exists
            existing = get_category(
                session,
                name=text,
                chat_id=chat_id,
            )
            if existing:
                context.chat_data["group_expense_data"]["category_id"] = existing.id
                await save_group_expense(session, update, context)
                return
            
            new_cat = add_category(
                session,
                name=text,
                chat_id=chat_id,
            )

            context.chat_data["group_expense_data"]["category_id"] = new_cat.id
            await save_group_expense(session, update, context, from_message=True)

    except Exception:
        logging.exception("❌ Error creating custom group category")
        await update.message.reply_text(edit_fail("create"))

    context.chat_data.pop("awaiting_new_category", None)
    context.chat_data.pop("category_context", None)

async def save_group_expense(session, trigger, context, from_message=False):
    data = context.chat_data["group_expense_data"]
    try:
        payer = get_user(
            session=session,
            user_id=data["payer_id"],
            chat_id=data["chat_id"]
        )
        category_id = data["category_id"]

        expense = handle_add_expense(
            session,
            db_user=payer,
            amount=data["amount"],
            description=data["description"],
            date=data["date"],
            category_id=category_id,
            chat_id=data["chat_id"]
        )

        handle_add_keyword_category_mapping(
            session,
            data["description"],
            category_id,
            data["chat_id"],
            expense_id=expense.id
        )

        users, message = handle_expense_split(
            session=session,
            expense=expense,
            payer_id=data['payer_id'],
            participant_ids=data['participants'],
            chat_id=data['chat_id'],
            amount=data['amount'],
            custom_split=data['custom_split'],
            is_equal_split=data['is_equal_split']
        )

        if from_message:
            await trigger.message.reply_text(message)
        else:
            await trigger.edit_message_text(message)

    except Exception:
        logging.exception("❌ Failed to save group expense")
        if from_message:
            await trigger.message.reply_text(edit_fail("saving"))
        else:
            await trigger.edit_message_text(edit_fail("saving"))
    finally:
        session.close()
        context.chat_data.pop("group_expense_data", None)


async def settle_debt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    chat_id = str(update.effective_chat.id)
    telegram_id = update.effective_user.id

    try:
        if not is_group_registered(session, chat_id):
            await update.message.reply_text(group_not_registered)
            return

        user_id = get_user(session, telegram_id=telegram_id, chat_id=chat_id).id
        group_net_balances = get_group_balances_stats(session, chat_id)['net_balances']
        creditors = group_net_balances.get(user_id, {})

        if creditors == {}:
            await update.message.reply_text(no_debts_to_settle)
            return
        else:
            creditors = creditors.keys()

        buttons = []
        for creditor in creditors:
            creditor_name = get_user(session, user_id=creditor).name
            owe_amount = group_net_balances[user_id][creditor]
            text = f"{creditor_name.capitalize()} – ${owe_amount:.2f}"
            buttons.append([InlineKeyboardButton(text, callback_data=f"settle_debt:{creditor} - {owe_amount:.2f}")])

        await display_prompt(
            update=update,
            title="💸 Who do you want to settle debts with:",
            options=buttons,
            callback_prefix="settle",
            cancel_only=True,
        )

    except Exception:
        logging.exception("❌ Error settling debts")
        await update.message.reply_text(edit_fail("settle"))

async def settle_debt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = query.data.replace("settle_debt:", "").split(" - ")
    creditor_id = int(text[0])
    owe_amount = float(text[1])
    
    chat_id = str(update.effective_chat.id)
    telegram_id = update.effective_user.id

    session = SessionLocal()

    payer = get_user(
        session=session,
        telegram_id=telegram_id,
        chat_id=chat_id
    )

    context.chat_data["settle_debt_data"] = {
        "creditor_id": creditor_id,
        "chat_id": chat_id,
        "payer_id": payer.id,
        "owe_amount": owe_amount
    }

    context.chat_data["awaiting_settle_amount"] = True
    await query.edit_message_text(
        f"💸 You are settling debt with {get_user(session=SessionLocal(), user_id=creditor_id, chat_id=chat_id).name.capitalize()}.\n"
        "Please enter the amount you want to settle with this user:"
    )

async def handle_settle_debt_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    session = SessionLocal()
    if not text:
        await update.message.reply_text(additional_info_fail)
        return
    try:    
        settle_data = context.chat_data.get("settle_debt_data", {})
        if not settle_data:
            await update.message.reply_text("⚠️ No pending debt settlement.")
            return

        creditor_id = settle_data["creditor_id"]
        chat_id = settle_data["chat_id"]
        payer_id = settle_data["payer_id"]
        owe_amount = settle_data["owe_amount"]

        amount = float(text)

        if amount <= 0:
            await update.message.reply_text(settle_amount_less_than_debt)
            return
        elif amount > owe_amount:
            await update.message.reply_text(settle_amount_exceeds_debt(owe_amount))
            return
        
        success = add_debt_settlement(
            session=session,
            chat_id=chat_id,
            payer_id=payer_id,
            payee_id=creditor_id,
            amount=amount
        )

        if success:
            creditor = get_user(session=session, user_id=creditor_id, chat_id=chat_id)
            context.chat_data.pop("awaiting_settle_amount", None)
            context.chat_data.pop("settle_debt_data", None)

            await update.message.reply_text(f"✅ Debt of ${amount:.2f} settled with {creditor.name}.")
        else:
            await update.message.reply_text(edit_fail("settle"))

    except ValueError:
        await update.message.reply_text(invalid_amount)
    except Exception:
        logging.exception("❌ Error settling debt")
        await update.message.reply_text(edit_fail("settle"))
    finally:
        session.close()
