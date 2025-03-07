import os
import logging
import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
    filters,
)
import gspread
from google.oauth2.service_account import Credentials
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
FULL_NAME, PHONE_NUMBER, PHONE_VERIFICATION, ABOUT, RESUME, CONFIRMATION = range(6)

# Google Sheets setup
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
CREDENTIALS_FILE = "credentials.json"  # Your Google API credentials file
SPREADSHEET_ID = "your_spreadsheet_id_here"  # Replace with your actual spreadsheet ID
GROUP_CHAT_ID = "your_group_chat_id_here"  # Replace with your actual group chat ID

def get_sheet():
    credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client.open_by_key(SPREADSHEET_ID).sheet1

async def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask for user's full name."""
    user = update.message.from_user
    logger.info(f"User {user.first_name} started the registration process.")
    
    # Initialize user data in context
    context.user_data["registration_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context.user_data["telegram_id"] = user.id
    context.user_data["telegram_username"] = user.username
    
    await update.message.reply_text(
        "Assalomu alaykum! Ro'yxatdan o'tish uchun, iltimos, to'liq ismingizni kiriting (FIO):"
    )
    
    return FULL_NAME

async def full_name(update: Update, context: CallbackContext) -> int:
    """Store the full name and ask for phone number."""
    user = update.message.from_user
    full_name = update.message.text
    context.user_data["full_name"] = full_name
    logger.info(f"Full name of {user.first_name}: {full_name}")
    
    # Create keyboard with contact sharing button
    keyboard = [
        [KeyboardButton("Telefon raqamimni yuborish", request_contact=True)],
        [KeyboardButton("Ortga")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Rahmat! Endi telefon raqamingizni tasdiqlash uchun \"Telefon raqamimni yuborish\" tugmasini bosing:",
        reply_markup=reply_markup,
    )
    
    return PHONE_NUMBER

async def phone_number(update: Update, context: CallbackContext) -> int:
    """Check phone number and ask user to confirm with contact."""
    user = update.message.from_user
    
    # Check if user clicked "Back" button
    if update.message.text == "Ortga":
        await update.message.reply_text(
            "Iltimos, to'liq ismingizni kiriting (FIO):"
        )
        return FULL_NAME
    
    # If user shared their contact, process it
    if update.message.contact:
        # Verify that the shared contact belongs to the user
        if update.message.contact.user_id == user.id:
            phone_number = update.message.contact.phone_number
            context.user_data["phone_number"] = phone_number
            logger.info(f"Phone number of {user.first_name}: {phone_number}")
            
            keyboard = [[KeyboardButton("Ortga")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "Rahmat! Endi o'zingiz haqingizda qisqacha ma'lumot kiriting:",
                reply_markup=reply_markup,
            )
            return ABOUT
        else:
            await update.message.reply_text(
                "Kechirasiz, bu boshqa odamning kontakti. Iltimos, o'zingizning telefon raqamingizni yuboring."
            )
            return PHONE_NUMBER
    else:
        await update.message.reply_text(
            "Iltimos, \"Telefon raqamimni yuborish\" tugmasini bosing."
        )
        return PHONE_NUMBER

async def about(update: Update, context: CallbackContext) -> int:
    """Store the about info and ask for resume."""
    user = update.message.from_user
    
    # Check if user clicked "Back" button
    if update.message.text == "Ortga":
        keyboard = [
            [KeyboardButton("Telefon raqamimni yuborish", request_contact=True)],
            [KeyboardButton("Ortga")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "Telefon raqamingizni tasdiqlash uchun \"Telefon raqamimni yuborish\" tugmasini bosing:",
            reply_markup=reply_markup,
        )
        return PHONE_NUMBER
    
    about_text = update.message.text
    context.user_data["about"] = about_text
    logger.info(f"About info of {user.first_name}: {about_text}")
    
    keyboard = [[KeyboardButton("Ortga")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Rahmat! Endi rezumeyingizni (CV) fayl ko'rinishida yuboring:",
        reply_markup=reply_markup,
    )
    
    return RESUME

async def resume(update: Update, context: CallbackContext) -> int:
    """Store the resume and ask for confirmation."""
    user = update.message.from_user
    
    # Check if user clicked "Back" button
    if update.message.text == "Ortga":
        keyboard = [[KeyboardButton("Ortga")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "O'zingiz haqingizda qisqacha ma'lumot kiriting:",
            reply_markup=reply_markup,
        )
        return ABOUT
    
    # Check if a document was sent
    if update.message.document:
        file = await update.message.document.get_file()
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name
        
        # Download the file
        file_path = f"downloads/{file_id}_{file_name}"
        await file.download_to_drive(file_path)
        
        context.user_data["resume"] = {
            "file_id": file_id,
            "file_name": file_name,
            "local_path": file_path
        }
        
        logger.info(f"Resume of {user.first_name} received: {file_name}")
        
        # Present a summary of entered information for confirmation
        keyboard = [
            [KeyboardButton("Tasdiqlash")],
            [KeyboardButton("Ortga")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        summary = (
            f"Kiritilgan ma'lumotlarni ko'rib chiqing:\n\n"
            f"FIO: {context.user_data['full_name']}\n"
            f"Telefon: {context.user_data['phone_number']}\n"
            f"O'zingiz haqingizda: {context.user_data['about']}\n"
            f"Rezume: {file_name}\n\n"
            f"Ma'lumotlar to'g'rimi? Tasdiqlash uchun \"Tasdiqlash\" tugmasini bosing"
        )
        
        await update.message.reply_text(
            summary,
            reply_markup=reply_markup,
        )
        
        return CONFIRMATION
    else:
        await update.message.reply_text(
            "Iltimos, rezumeyingizni fayl ko'rinishida yuboring."
        )
        return RESUME

async def confirmation(update: Update, context: CallbackContext) -> int:
    """Confirm registration and save data to Google Sheets."""
    user = update.message.from_user
    
    # Check if user clicked "Back" button
    if update.message.text == "Ortga":
        keyboard = [[KeyboardButton("Ortga")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "Rezumeyingizni (CV) fayl ko'rinishida yuboring:",
            reply_markup=reply_markup,
        )
        return RESUME
    
    if update.message.text == "Tasdiqlash":
        # Save data to Google Sheets
        try:
            sheet = get_sheet()
            
            # Prepare data for Google Sheets
            registration_data = [
                context.user_data["registration_time"],
                context.user_data["telegram_id"],
                context.user_data["telegram_username"],
                context.user_data["full_name"],
                context.user_data["phone_number"],
                context.user_data["about"],
                context.user_data["resume"]["file_name"],
            ]
            
            # Append data to Google Sheets
            sheet.append_row(registration_data)
            
            logger.info(f"Data for {user.first_name} saved to Google Sheets")
            
            # Forward all information to the group
            resume_path = context.user_data["resume"]["local_path"]
            caption = (
                f"Yangi ro'yxatdan o'tish:\n\n"
                f"Vaqt: {context.user_data['registration_time']}\n"
                f"Telegram ID: {context.user_data['telegram_id']}\n"
                f"Username: @{context.user_data['telegram_username']}\n"
                f"FIO: {context.user_data['full_name']}\n"
                f"Telefon: {context.user_data['phone_number']}\n"
                f"O'zi haqida: {context.user_data['about']}"
            )
            
            # Send message to the group
            await context.bot.send_document(
                chat_id=GROUP_CHAT_ID,
                document=open(resume_path, 'rb'),
                caption=caption
            )
            
            # Notify user of successful registration
            await update.message.reply_text(
                "Rahmat! Siz muvaffaqiyatli ro'yxatdan o'tdingiz.",
                reply_markup=ReplyKeyboardRemove(),
            )
            
            # Remove downloaded resume file
            if os.path.exists(resume_path):
                os.remove(resume_path)
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            await update.message.reply_text(
                "Kechirasiz, ma'lumotlarni saqlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Iltimos, \"Tasdiqlash\" tugmasini bosing yoki \"Ortga\" tugmasi orqali qaytib ma'lumotlarni o'zgartiring."
        )
        return CONFIRMATION

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the conversation."""
    user = update.message.from_user
    logger.info(f"User {user.first_name} canceled the registration.")
    
    await update.message.reply_text(
        "Ro'yxatdan o'tish bekor qilindi. Qayta boshlash uchun /start ni bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    return ConversationHandler.END

def setup_application():
    """Set up the Application and add handlers."""
    # Create the Application object
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Ensure download directory exists
    os.makedirs("downloads", exist_ok=True)
    
    # Add conversation handler with states
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
    
    return application

# Django webhook handler
@csrf_exempt
def telegram_webhook(request):
    if request.method == "POST":
        application = setup_application()
        update = Update.de_json(json.loads(request.body.decode()), application.bot)
        application.process_update(update)
        return HttpResponse("OK")
    return HttpResponse("Only POST requests are allowed")