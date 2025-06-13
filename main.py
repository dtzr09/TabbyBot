from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
import os
import logging
from handlers.setup import setup_handlers, set_bot_commands
import asyncio
# 
# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MODE = os.getenv("MODE", "dev")
PORT = int(os.environ.get("PORT", 8443)) 
RAILWAY_DOMAIN = os.getenv("RAILWAY_DOMAIN")  

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(set_bot_commands).build()
    setup_handlers(app)

    logging.info(f"Bot running in {MODE} mode...")

    if MODE == "prod":
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="/webhook",
            webhook_url=f"https://{RAILWAY_DOMAIN}/webhook"
        )
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(app.bot.delete_webhook(drop_pending_updates=True))
        app.run_polling()

if __name__ == "__main__":
    main()
