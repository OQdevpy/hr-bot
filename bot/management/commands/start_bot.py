# bot/management/commands/start_bot.py

import logging
import asyncio
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from bot.telegram_bot import (
    start, full_name, phone_number, about, resume, confirmation, cancel,
    FULL_NAME, PHONE_NUMBER, ABOUT, RESUME, CONFIRMATION
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = settings.TELEGRAM_BOT_TOKEN

def main() -> None:
    downloads_dir = os.path.join(settings.BASE_DIR, "downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)],
            PHONE_NUMBER: [
                MessageHandler(filters.CONTACT, phone_number),
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone_number),
            ],
            ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, about)],
            RESUME: [
                MessageHandler(filters.Document.ALL, resume),
                MessageHandler(filters.TEXT & ~filters.COMMAND, resume),
            ],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

class Command(BaseCommand):
    help = 'Starts the Telegram bot in polling mode'

    def handle(self, *args, **options):
        main()