from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

async def display_prompt(
    title: str,
    options: list[list[InlineKeyboardButton]] | None,
    callback_prefix: str,
    update: Update = None,
    query=None,
    parse_mode=None,
    cancel_only=False,
    back_only=False,
):
    # Ensure options exist
    if not options:
        options = []
    options.append(get_back_cancel_button(callback_prefix=callback_prefix, cancel_only=cancel_only, back_only=back_only))

    # Decide where to send the message
    reply_markup = InlineKeyboardMarkup(options)
    
    if update and update.message:
        await update.message.reply_text(title, reply_markup=reply_markup, parse_mode=parse_mode)
    elif update and update.callback_query.message:
        await update.callback_query.message.reply_text(title, reply_markup=reply_markup, parse_mode=parse_mode)
    elif query:
        try:
            await query.edit_message_text(
                text=title,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise


def get_back_cancel_button(callback_prefix="category_settings", cancel_only=False, back_only=False):
    if cancel_only:
        return [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    if back_only:
        return [InlineKeyboardButton("⬅️ Back", callback_data=f"{callback_prefix}:back")]
    return [
        InlineKeyboardButton("⬅️ Back", callback_data=f"{callback_prefix}:back"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
    ]

async def handle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.chat_data.clear()
    await update.callback_query.message.delete()
    await update.effective_chat.send_message("🙅‍♂️ Action cancelled — like it never even happened.")
    
def get_settings_menu():
    buttons = [
        [InlineKeyboardButton("✏️ Edit My Expenses", callback_data="settings:edit_expenses")],
        [InlineKeyboardButton("⚙️ Category Settings", callback_data="settings:category")],
        [InlineKeyboardButton("💱 Change Currency", callback_data="settings:currency")]
    ]
    return buttons
