import os
import logging
import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
    filters,
)
import gspread
from google.oauth2.service_account import Credentials
from django.conf import settings

from bot.models import Registration

from asgiref.sync import sync_to_async


def save_to_sheets(registration_time, telegram_id, telegram_username, full_name, phone_number, about, resume_file_name, registration_id, resume_telegram_link):
    sheet = get_sheet()
    
    formatted_registration_time = registration_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(registration_time, datetime.datetime) else registration_time
    
    registration_data = [
        formatted_registration_time,
        telegram_id,
        telegram_username,
        f"ID: {registration_id} - {full_name}",
        phone_number,
        about,
        resume_file_name,
        resume_telegram_link
    ]
    
    sheet.append_row(registration_data)
    return True


def save_registration(telegram_id, telegram_username, full_name, phone_number, about, resume_file_name, resume_telegram_link):
    from bot.models import Registration
    
    registration = Registration(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        full_name=full_name,
        phone_number=phone_number,
        about=about,
        resume_file_name=resume_file_name,
        resume_telegram_link=resume_telegram_link
    )
    registration.save()
    save_to_sheets(registration.registration_time, telegram_id, telegram_username, full_name, phone_number, about, resume_file_name, registration.id, resume_telegram_link)
    return registration.id




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
CREDENTIALS_FILE = os.path.join(settings.BASE_DIR, "credentials.json")
SPREADSHEET_ID = getattr(
    settings, "GOOGLE_SHEETS_SPREADSHEET_ID", "your_spreadsheet_id_here"
)
GROUP_CHAT_ID = getattr(settings, "GROUP_CHAT_ID", "your_group_chat_id_here")


def get_sheet():
    credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client.open_by_key(SPREADSHEET_ID).sheet1


os.makedirs(os.path.join(settings.BASE_DIR, "downloads"), exist_ok=True)


async def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info(f"User {user.first_name} started the registration process.")

    context.user_data["registration_time"] = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    context.user_data["telegram_id"] = user.id
    context.user_data["telegram_username"] = user.username or "No username"

    await update.message.reply_text(
        "Assalomu alaykum! Ro'yxatdan o'tish uchun, iltimos, to'liq ismingizni kiriting (FIO):"
    )

    return FULL_NAME


async def full_name(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    full_name = update.message.text
    context.user_data["full_name"] = full_name
    logger.info(f"Full name of {user.first_name}: {full_name}")

    keyboard = [
        [KeyboardButton("Telefon raqamimni yuborish", request_contact=True)],
        [KeyboardButton("Ortga")],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(
        'Rahmat! Endi telefon raqamingizni tasdiqlash uchun "Telefon raqamimni yuborish" tugmasini bosing:',
        reply_markup=reply_markup,
    )

    return PHONE_NUMBER


async def phone_number(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user

    if update.message.text == "Ortga":
        await update.message.reply_text("Iltimos, to'liq ismingizni kiriting (FIO):")
        return FULL_NAME

    if update.message.contact:
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
            'Iltimos, "Telefon raqamimni yuborish" tugmasini bosing.'
        )
        return PHONE_NUMBER


async def about(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user

    if update.message.text == "Ortga":
        keyboard = [
            [KeyboardButton("Telefon raqamimni yuborish", request_contact=True)],
            [KeyboardButton("Ortga")],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )

        await update.message.reply_text(
            'Telefon raqamingizni tasdiqlash uchun "Telefon raqamimni yuborish" tugmasini bosing:',
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
    user = update.message.from_user

    if update.message.text == "Ortga":
        keyboard = [[KeyboardButton("Ortga")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "O'zingiz haqingizda qisqacha ma'lumot kiriting:",
            reply_markup=reply_markup,
        )
        return ABOUT

    if update.message.document:
        file = await update.message.document.get_file()
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name

        downloads_dir = os.path.join(settings.BASE_DIR, "downloads")
        os.makedirs(downloads_dir, exist_ok=True)

        file_path = os.path.join(downloads_dir, f"{file_id}_{file_name}")
        await file.download_to_drive(file_path)

        context.user_data["resume"] = {
            "file_id": file_id,
            "file_name": file_name,
            "local_path": file_path,
        }

        logger.info(f"Resume of {user.first_name} received: {file_name}")

        keyboard = [[KeyboardButton("Tasdiqlash")], [KeyboardButton("Ortga")]]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )

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
    user = update.message.from_user
    
    if update.message.text == "Ortga":
        keyboard = [[KeyboardButton("Ortga")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "Rezumeyingizni (CV) fayl ko'rinishida yuboring:",
            reply_markup=reply_markup,
        )
        return RESUME
    
    if update.message.text == "Tasdiqlash":
        try:
            caption = (
                f"Yangi ro'yxatdan o'tish:\n\n"
                f"Vaqt: {context.user_data['registration_time']}\n"
                f"Telegram ID: {context.user_data['telegram_id']}\n"
                f"Username: @{context.user_data['telegram_username']}\n"
                f"FIO: {context.user_data['full_name']}\n"
                f"Telefon: {context.user_data['phone_number']}\n"
                f"O'zi haqida: {context.user_data['about']}"
            )
            
            resume_path = context.user_data["resume"]["local_path"]
            sent_message = await context.bot.send_document(
                chat_id=GROUP_CHAT_ID,
                document=open(resume_path, 'rb'),
                caption=caption
            )
            
            chat_id_str = str(GROUP_CHAT_ID)
            if chat_id_str.startswith('-100'):
                chat_id_for_link = chat_id_str[4:]
            else:
                chat_id_for_link = chat_id_str.lstrip('-') 
                
            resume_telegram_link = f"https://t.me/c/{chat_id_for_link}/{sent_message.message_id}"
            logger.info(f"Resume Telegram link: {resume_telegram_link}")
            
            registration_id = await sync_to_async(save_registration)(
                context.user_data["telegram_id"],
                context.user_data["telegram_username"],
                context.user_data["full_name"],
                context.user_data["phone_number"],
                context.user_data["about"],
                context.user_data["resume"]["file_name"],
                resume_telegram_link
            )
            
            logger.info(f"Data for {user.first_name} saved to database with ID: {registration_id}")
            
            await update.message.reply_text(
                "Rahmat! Siz muvaffaqiyatli ro'yxatdan o'tdingiz.",
                reply_markup=ReplyKeyboardRemove(),
            )
            
            if os.path.exists(resume_path):
                os.remove(resume_path)
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
    user = update.message.from_user
    logger.info(f"User {user.first_name} canceled the registration.")

    await update.message.reply_text(
        "Ro'yxatdan o'tish bekor qilindi. Qayta boshlash uchun /start ni bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END
