# simple_bot.py

import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token
TOKEN = "7454177892:AAF2crdQWyXeJOwiINNCK4FZmWlA9JPcrPk"  # O'z token-ingizni kiriting

# Define a few command handlers
async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    logger.info(f"User {update.effective_user.first_name} started the bot")
    await update.message.reply_text(f'Salom, {update.effective_user.first_name}! Men test botman.')

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Yordam uchun /start ni bosing.')

async def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    logger.info(f"Received message: {update.message.text}")
    await update.message.reply_text(f"Siz yubordingiz: {update.message.text}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()