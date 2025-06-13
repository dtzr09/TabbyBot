import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import math
from db import SessionLocal
from utils.category import build_category_buttons, get_category_settings
from utils.utils import get_settings_menu, display_prompt
from db.repositories.user import get_user
from db.repositories.category import get_category, delete_category, edit_category
from db.repositories.expense import get_expense_by_id, handle_delete_expense, edit_expense, search_expenses, edit_expenses, get_expenses
from utils.expenseShare import get_splits
from utils.messages import *
from utils.messages import *

# Settings command and handlers
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = get_settings_menu()
    await display_prompt(
            update=update,
            query=None,
            title=get_settings_menu_text("menu"),
            options=buttons,
            callback_prefix=None,
            parse_mode=None,
            cancel_only=True
        )


async def settings_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]
    if data == "settings:edit_expenses":
        await display_prompt(
            query=query,
            title=get_settings_menu_text("edit_expenses"),  
            options=None,
            callback_prefix="settings"
        )
        if group_chat:
            context.chat_data["awaiting_expense_search"] = True
        else:
            context.user_data["awaiting_expense_search"] = True
    elif data == "settings:category":
        await get_category_settings(query)
    elif data == "settings:currency":
        await display_prompt(
            query=query,
            title=get_settings_menu_text("currency"),
            options=None,
            callback_prefix="settings"
        )
        if group_chat:
            context.chat_data["awaiting_currency_change"] = True
        else:
            context.user_data["awaiting_currency_change"] = True

    elif data == "settings:back":
        buttons = get_settings_menu()
        await display_prompt(
            query=query,
            title= get_settings_menu_text("menu"),
            options=buttons,
            callback_prefix=None,
            parse_mode=None,
            cancel_only=True
        )

async def settings_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    if not chat_id:
        await query.edit_message_text(not_found("chat"))
        return
    
    callback_prefix = "category_settings"
    session = SessionLocal()

    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]
    telegram_id = str(update.effective_user.id)
    
    db_user = get_user(
        session,
        telegram_id=telegram_id,
        chat_id=chat_id
    )

    if not db_user:
        await query.edit_message_text(user_not_found(personal=not group_chat))
        return
  
    if data == "category_settings:view_categories":
        await display_prompt(
            query = query,
            title = get_settings_menu_text("view_categories"),
            options=build_category_buttons(user_id=None if group_chat else db_user.id, chat_id=chat_id, view_only=True),
            callback_prefix=callback_prefix
        )

    elif data == "category_settings:rename_category":
        await display_prompt(
            query = query,
            title = get_settings_menu_text("rename_category"),
            options=build_category_buttons(
                user_id=db_user.id,
                chat_id=chat_id,
                callback_prefix="renamecat",
                view_only=True
            ),
            callback_prefix=callback_prefix
        )
    
    elif data == "category_settings:add_category":
        await display_prompt(
            query=query,
            title=get_settings_menu_text("add_category"),
            options=None,
            callback_prefix=callback_prefix
        )
        if group_chat:
            context.chat_data["awaiting_new_category_from_settings"] = True
        else:
            context.user_data["awaiting_new_category_from_settings"] = True
    elif data == "category_settings:delete_category":
        buttons = build_category_buttons(
            user_id=db_user.id if not group_chat else None,
            chat_id=chat_id,
            callback_prefix="deletecat",
            view_only=True
        )
        await display_prompt(
            query=query,
            title= get_settings_menu_text("delete_category"),
            options=buttons,
            callback_prefix=callback_prefix
        )

    elif data == "category_settings:back":
        if group_chat:
            context.chat_data.pop("awaiting_new_category_from_settings", None)
        else:
            context.user_data.pop("awaiting_new_category_from_settings", None)
        await get_category_settings(query)
    
async def handle_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = query.data.replace("deletecat:", "")

    session = SessionLocal()
    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    telegram_id = str(update.effective_user.id)

    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]

    try:
        db_user = get_user(
            session=session,
            telegram_id=telegram_id,
            chat_id=chat_id
        )
        if not db_user:
            await query.edit_message_text()
            return
        category = get_category(
            session=session,
            user_id=db_user.id if not group_chat else None,
            chat_id=chat_id,
            category_id=category_id
        )

        expenses_under_category = get_expenses(
            session=session,
            chat_id=chat_id,
            category_id=category.id
        )
        if len(expenses_under_category) > 0:
            await query.edit_message_text(category_tied_to_expense)
            return


        if not category:
            await query.edit_message_text(not_found("category"))
            return

        success = delete_category(session, category.id)
        if not success:
            await query.edit_message_text(edit_fail("delete"))
            return
        await query.edit_message_text(edit_category_success("delete", category.name))
    except Exception:
        logging.exception("Error while deleting category")
        await query.edit_message_text(edit_fail("delete"))
    finally:
        session.close()


async def rename_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id_to_rename = query.data.replace("renamecat:", "")

    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]

    db_user = get_user(
        session=SessionLocal(),
        telegram_id=str(update.effective_user.id),
        chat_id=str(update.effective_chat.id)
    )
    if not db_user:
        await query.edit_message_text(user_not_found(personal=not group_chat))
        return
    
    category = get_category(
        session=SessionLocal(),
        user_id=db_user.id if not group_chat else None, 
        chat_id=str(update.effective_chat.id),
        category_id=category_id_to_rename
    )

    if group_chat:
        context.chat_data["rename_category"] = category.name
    else:
        context.user_data["rename_category"] = category.name

    await display_prompt(
        query = query,
        title=f"✏️ Type a new name for category *{category.name}*:",
        parse_mode="Markdown",
        options=None,
        callback_prefix="category_settings"
    )

async def handle_rename_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text.strip()
    old_name = context.user_data.get("rename_category")
    if not old_name:
        await update.message.reply_text(no_selection("category"))
        return
    
    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    if not chat_id:
        await update.message.reply_text(not_found("chat"))
        return
    
    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]

    session = SessionLocal()
    try:
        db_user = get_user(
            session,
            telegram_id=update.effective_user.id,
            chat_id=chat_id
        )

        exist = get_category(
            session=session,
            chat_id=chat_id,
            name=new_name,
            user_id=db_user.id if not group_chat else None
        )

        if exist:
            await update.message.reply_text(duplicate_category)
            return

        category = edit_category(
            session=session,
            user_id=db_user.id if not group_chat else None,
            old_name=old_name,
            new_name=new_name,
            chat_id=chat_id
        )

        if category:
            await update.message.reply_text(edit_category_success("rename", old_name, new_name))
        else:
            await update.message.reply_text(not_found("category"))
    except Exception:
        logging.exception("Error while renaming category")
        await update.message.reply_text(edit_fail("rename"))
    finally:
        session.close()

    context.user_data.pop("rename_category", None)


async def handle_expense_search(update, context, keyword, page=0):
    PAGE_SIZE = 10
    user = update.effective_user
    session = SessionLocal()
    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    if not chat_id:
        await update.message.reply_text(not_found("chat"))
        return

    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]

    try:    
        db_user = get_user(session=session, telegram_id=user.id, chat_id=chat_id)

        if not db_user:
            await update.message.reply_text(not_found("user"))
            return
        
        results_count, results = search_expenses(
            session=session,
            keyword=keyword,
            user_id=db_user.id,
            chat_id=chat_id,
            page=page,
            PAGE_SIZE=PAGE_SIZE
        )

        if group_chat:
            context.chat_data.pop("awaiting_expense_search", None)
        else:
            context.user_data.pop("awaiting_expense_search", None)


        if not results:
            await update.message.reply_text(not_found("expense"))
            return
        
        # Store search session
        context.user_data["search_keyword"] = keyword
        context.user_data["search_page"] = page

        # Generate expense buttons
        buttons = []
        for exp in results:
            payer = get_user(
                session=session,
                user_id=exp.payer_id,
                chat_id=chat_id,
            )
            date = exp.date.strftime("%m/%d/%Y") if exp.date else "Unknown date"
            time = exp.date.strftime("%I:%M %p") if exp.date else "Unknown time"

            label = (
                f"{date} {time} • {exp.description} • ${exp.amount:.2f} • Payer: {payer.name if payer else 'Unknown'}\n"
            )

            buttons.append([InlineKeyboardButton(label, callback_data=f"edit_expense:{exp.id}")])

        # Navigation
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data="search_expenses:prev"))
        if (page + 1) * PAGE_SIZE < results_count:
            nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data="search_expenses:next"))
        if nav_buttons:
            buttons.append(nav_buttons)

        total_pages = math.ceil(results_count / PAGE_SIZE)
        current_page = page + 1 

        # if update.message:
        await display_prompt(
            update=update,
            title=f"🔍 Showing page {current_page} of {total_pages}:",
            options=buttons,
            cancel_only=True,
            callback_prefix=None
        )

    finally:
        session.close()

async def handle_search_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    direction = query.data.split(":")[1]

    keyword = context.user_data.get("search_keyword", "")
    page = context.user_data.get("search_page", 0)

    if direction == "next":
        page += 1
    elif direction == "prev" and page > 0:
        page -= 1

    context.user_data["search_page"] = page

    # Delete old message to keep chat clean
    await query.message.delete()

    # Re-call the search
    await handle_expense_search(update, context, keyword, page)

async def handle_edit_expense_prompt(update, context):
    query = update.callback_query
    await query.answer()

    expense_id = int(query.data.replace("edit_expense:", ""))
    session = SessionLocal()

    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]
    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    if not chat_id:
        await query.edit_message_text(not_found("chat"))
        return

    try:
        expense = get_expense_by_id(session, expense_id)
        if not expense:
            await query.edit_message_text(not_found("expense"))
            return

        if group_chat:
            context.chat_data["editing_expense_id"] = expense_id
        else:
            context.user_data["editing_expense_id"] = expense_id

        splits = get_splits(session, expense_id, chat_id=chat_id)

        date_time = expense.date.strftime("%m/%d/%Y %I:%M %p") if expense.date else "Unknown date"

        text = get_expense_details(expense=expense, date_time=date_time)


        if group_chat:
            text +=  f"• 👤 Payer: {get_user(session=session, user_id=expense.payer_id, chat_id=chat_id).name if expense.payer_id else 'Unknown'}\n"
            text +=  f"• 📊 Splits: {', '.join([f'{user}: ${split:.2f}' for user, split in splits.items()]) if splits else 'None'}\n"

        text +=  f"\n🔧 What would you like to tweak?"
        buttons = [
            [InlineKeyboardButton("💵 Amount", callback_data="edit_field:amount")],
            [InlineKeyboardButton("📝 Description", callback_data="edit_field:description")],
            [InlineKeyboardButton("📂 Category", callback_data="edit_field:category")],
            [InlineKeyboardButton("🗑 Delete", callback_data="edit_field:delete")],
        ]

        await display_prompt(
            query = query,
            title=text,
            options=buttons,
            callback_prefix=None,
            parse_mode="Markdown",
            cancel_only=True
        )

    finally:
        session.close()

async def handle_edit_field_selection(update, context):
    query = update.callback_query
    await query.answer()

    field = query.data.replace("edit_field:", "")
    
    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    if not chat_id:
        await query.edit_message_text(not_found("chat"))
        return
    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]

    if group_chat:
        expense_id = context.chat_data.get("editing_expense_id")
    else:
        expense_id = context.user_data.get("editing_expense_id")


    if not expense_id:
        await query.edit_message_text(no_selection("expense"))
        return

    if field == "delete":
        session = SessionLocal()
        try:
            op = handle_delete_expense(session, expense_id)
            if op:
                await query.edit_message_text(expense_deleted)
            else:
                await query.edit_message_text(not_found("expense"))
        finally:
            session.close()

        if group_chat:
            context.chat_data.pop("editing_expense_id", None)
        else:
            context.user_data.pop("editing_expense_id", None)
        return

    if field == "category":
        db_user = get_user(
            session=SessionLocal(),
            telegram_id=str(update.effective_user.id),
            chat_id=chat_id
        )
        if not db_user:
            await query.edit_message_text(user_not_found(personal=not group_chat))
            return
        buttons = build_category_buttons(user_id=None if group_chat else db_user.id, chat_id=chat_id, callback_prefix="editcat", view_only=True)
        await display_prompt(
            query=query,
            title=get_settings_menu_text("new_category"),
            options=buttons,
            callback_prefix=None,
            cancel_only=True,
            parse_mode="Markdown",
        )
        return

    if group_chat:
        context.chat_data["edit_field"] = field
    else:
        context.user_data["edit_field"] = field

    await display_prompt(
        query=query,
        title = f"📝 Updating *{field}* — what should it be now?",
        parse_mode="Markdown",
        options=None,
        callback_prefix=None,
        cancel_only=True
    )

async def handle_expense_update(update, context):
    new_value = update.message.text.strip()
    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]
    field = context.chat_data.get("edit_field") if group_chat else context.user_data.get("edit_field")
    expense_id = context.chat_data.get("editing_expense_id") if group_chat else context.user_data.get("editing_expense_id")

    session = SessionLocal()
    try:
        kwargs = {}

        if field == "amount":
            try:
                kwargs["amount"] = float(new_value)
            except ValueError:
                await update.message.reply_text(invalid_amount)
                return
        elif field == "description":
            kwargs["description"] = new_value
        else:
            await update.message.reply_text("⚠️ Unknown field.")
            return

        updated = edit_expense(session, expense_id, **kwargs)

        if not updated:
            await update.message.reply_text(edit_fail("edit"))
        else:
            await update.message.reply_text(expense_updated_success)

    except Exception:
        logging.exception("Failed during expense update flow.")
        await update.message.reply_text(edit_fail("something"))
    finally:
        session.close()

    # Clean up context
    if group_chat:
        context.chat_data.pop("edit_field", None)
        context.chat_data.pop("editing_expense_id", None)
    else:
        context.user_data.pop("edit_field", None)
        context.user_data.pop("editing_expense_id", None)

async def handle_edit_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Find all the same category name and change the category respectively
    new_category_id = int(query.data.replace("editcat:", ""))

    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    if not chat_id:
        await query.edit_message_text(not_found("chat"))
        return

    group_chat = update.effective_chat and update.effective_chat.type in ["group", "supergroup"]

    expense_id = context.chat_data.get("editing_expense_id") if group_chat else context.user_data.get("editing_expense_id")

    if not expense_id:
        await query.edit_message_text(no_selection("expense"))
        return
    
    session = SessionLocal()
    try:
        db_user = get_user(
            session,
            telegram_id=update.effective_user.id,
            chat_id=chat_id
        )
        expense = get_expense_by_id(session, expense_id)
        if not expense:
            await query.edit_message_text(not_found("expense"))
            return

        if new_category_id == expense.category_id:
            await query.edit_message_text(same_category_chosen)
            return

        new_category = get_category(
            session=session,
            user_id=None if group_chat else db_user.id,
            chat_id=chat_id,
            category_id=new_category_id
        )
        
        if not new_category:
            await query.edit_message_text(not_found("category"))
            return
        
        updated_expenses = edit_expenses(
            session=session,
            chat_id=chat_id,
            user_id=db_user.id,
            old_category_id=expense.category.id,
            new_category_id=new_category.id,
            name=expense.description
        )

        if not updated_expenses:
            await query.edit_message_text(edit_fail("updating"))
            return

        await query.edit_message_text(f"✅ Updated {len(updated_expenses)} {"expenses' categories" if len(updated_expenses) > 1 else "expense's category"} to *{new_category.name}*. *{expense.description}* will now be categorized under *{new_category.name}*.", parse_mode="Markdown")

    except Exception:
        logging.exception("Failed to update category")
        await query.edit_message_text(edit_fail("updating"))
    finally:
        session.close()

    context.user_data.pop("editing_expense_id", None)
    context.user_data.pop("edit_field", None)
