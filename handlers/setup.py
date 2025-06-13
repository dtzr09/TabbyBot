
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers.personal_expenses import *
from handlers.settings import *
from handlers.stats import handle_stats, handle_group_stats
from handlers.group_expenses import *
from utils.utils import handle_cancel_callback

def setup_handlers(app):
    '''Private message handler'''
    private_chat = filters.ChatType.PRIVATE
    group_chat = filters.ChatType.GROUP | filters.ChatType.SUPERGROUP
    
    # Commands (FIX THIS FOR GROUPS/SUPERGROUPS)
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("stats", handle_stats, filters=private_chat))
    app.add_handler(CommandHandler("stats", handle_group_stats, filters=group_chat))
    app.add_handler(CommandHandler("start", start_group_command, filters=group_chat))
    app.add_handler(CommandHandler("settle", settle_debt_command, filters=group_chat))
    app.add_handler(CommandHandler("addmembers", handle_add_new_members, filters=group_chat))


    # Text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & private_chat, handle_message))

    # Callbacks: specific patterns FIRST
    app.add_handler(CallbackQueryHandler(settings_callback_handler , pattern="^settings:"))
    app.add_handler(CallbackQueryHandler(handle_edit_expense_prompt, pattern="^edit_expense:"))
    app.add_handler(CallbackQueryHandler(handle_edit_field_selection, pattern="^edit_field:"))
    app.add_handler(CallbackQueryHandler(rename_category_handler, pattern="^renamecat:"))
    app.add_handler(CallbackQueryHandler(handle_edit_category_selection, pattern="^editcat:"))
    app.add_handler(CallbackQueryHandler(handle_delete_category, pattern="^deletecat:"))
    app.add_handler(CallbackQueryHandler(handle_category_callback, pattern="^cat:"))
    app.add_handler(CallbackQueryHandler(settings_category_callback , pattern="^category_settings:"))
    app.add_handler(CallbackQueryHandler(handle_cancel_callback , pattern="cancel"))
    app.add_handler(CallbackQueryHandler(handle_search_navigation , pattern="search_expenses:"))
    app.add_handler(CallbackQueryHandler(settle_debt_callback , pattern="settle_debt:"))

    '''Group message handler'''
    # Text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & group_chat, handle_group_message))

    # Callbacks: 
    app.add_handler(CallbackQueryHandler(handle_group_expense_payer_selection, pattern="^payer:"))
    app.add_handler(CallbackQueryHandler(handle_group_category_callback, pattern=r"^group_cat:"))
