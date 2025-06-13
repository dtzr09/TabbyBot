from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
import os
import logging
from handlers.setup import setup_handlers, set_bot_commands

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(set_bot_commands).build()
    setup_handlers(app)

    logging.info("Bot started...")

    app.run_polling()

if __name__ == "__main__":
    main()
