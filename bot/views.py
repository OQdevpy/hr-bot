# bot/views.py

import json
import logging
import asyncio
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from django.conf import settings
from bot.telegram_bot import (
    start, full_name, phone_number, about, resume, confirmation, cancel,
    FULL_NAME, PHONE_NUMBER, ABOUT, RESUME, CONFIRMATION
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

logger = logging.getLogger(__name__)

# Global application instance
_app = None

def get_application():
    """Get or create the application instance."""
    global _app
    if _app is None:
        _app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        
        # Add conversation handler
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
        
        _app.add_handler(conv_handler)
        
        # Initialize and start the application
        async def setup_app():
            await _app.initialize()
            await _app.start()
        
        # Run the setup
        asyncio.run(setup_app())
        
    return _app

@csrf_exempt
def webhook(request):
    """Django view to receive webhook updates from Telegram."""
    if request.method == "POST":
        try:
            # Get the update from Telegram
            update_data = json.loads(request.body.decode('utf-8'))
            logger.info(f"Received update: {update_data}")
            
            # Get application instance
            application = get_application()
            
            # Convert the update to an Update object
            update = Update.de_json(update_data, application.bot)
            
            # Process the update
            async def process_update():
                # Process the update with the application
                await application.process_update(update)
            
            # Run the async function
            asyncio.run(process_update())
            
            return HttpResponse("OK")
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return HttpResponse(f"Error: {e}", status=500)
    else:
        return HttpResponse("Only POST requests are allowed")

def health_check(request):
    """Simple health check endpoint."""
    return HttpResponse("Bot is running")