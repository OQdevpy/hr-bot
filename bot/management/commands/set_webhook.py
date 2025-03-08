# bot/management/commands/set_webhook.py

import logging
import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram.ext import Application

class Command(BaseCommand):
    help = 'Sets the webhook URL for the Telegram bot'

    def add_arguments(self, parser):
        parser.add_argument('webhook_url', type=str, help='The webhook URL to set')

    def handle(self, *args, **options):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        logger = logging.getLogger(__name__)
        
        webhook_url = options['webhook_url']
        
        if not webhook_url.startswith('https://'):
            self.stdout.write(self.style.ERROR('Webhook URL must start with https://'))
            return
        
        try:
            # Create application instance
            application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            
            # Set webhook
            webhook_url = f"{webhook_url.rstrip('/')}/bot/webhook/"
            
            async def set_webhook():
                await application.bot.set_webhook(webhook_url)
            
            # Run the async function
            asyncio.run(set_webhook())
            
            self.stdout.write(self.style.SUCCESS(f'Webhook set to: {webhook_url}'))
            
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            self.stdout.write(self.style.ERROR(f'Error setting webhook: {e}'))