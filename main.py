from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
import os
import logging
from handlers.setup import setup_handlers, set_bot_commands
import asyncio

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

MODE = os.getenv("MODE", "dev")  # "prod" or "dev"


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    setup_handlers(app)

    logging.info("Bot started...")

    if MODE == "prod":
        # Let Railway run the webhook or polling
        app.run_polling()
    else:
        # Local dev mode: clear webhook first
        asyncio.run(app.bot.delete_webhook(drop_pending_updates=True))
        app.run_polling()

    set_bot_commands(app)

if __name__ == "__main__":
    main()
