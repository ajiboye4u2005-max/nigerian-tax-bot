import os
import sys
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working on Railway!")

def main():
    logger.info("Starting test bot...")
    logger.info(f"Token present: {bool(BOT_TOKEN)}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    logger.info("Bot running!")
    app.run_polling()

if __name__ == '__main__':
    main()