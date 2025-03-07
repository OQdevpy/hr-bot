# bot/views.py

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from telegram import Update
from .telegram_bot import setup_application

logger = logging.getLogger(__name__)

@csrf_exempt
def webhook(request):
    """Django view to receive webhook updates from Telegram."""
    if request.method == "POST":
        try:
            # Get the update from Telegram
            update_data = json.loads(request.body.decode('utf-8'))
            logger.info(f"Received update: {update_data}")
            
            # Process the update
            application = setup_application()
            update = Update.de_json(update_data, application.bot)
            application.process_update(update)
            
            return HttpResponse("OK")
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return HttpResponse(f"Error: {e}", status=500)
    else:
        return HttpResponse("Only POST requests are allowed")

def health_check(request):
    """Simple health check endpoint."""
    return HttpResponse("Bot is running")


