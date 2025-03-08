# Telegram Registration Bot

Bu Telegram bot Django, python-telegram-bot, va Google Sheets integratsiyasi bilan foydalanuvchilarni ro'yxatdan o'tkazish imkonini beradi. Bot foydalanuvchilarning ma'lumotlarini Django modeliga saqlaydi va Telegram xabar linklarini Google Sheets-ga yuboradi.

## Funksiyalari

- Foydalanuvchilardan to'liq ism, telefon raqami, va o'zi haqida ma'lumot olish
- Telefon raqamini Telegram kontakti orqali tekshirish (foydalanuvchining haqiqiy telefon raqami ekanligiga ishonch hosil qilish)
- Resume fayllarini qabul qilish
- Ma'lumotlarni Django modeliga saqlash
- Resume faylini Telegram guruhiga yuborish va xabar linkini saqlash
- Google Sheets-ga ma'lumotlar va linklar yuborish
- "Ortga" tugmalari orqali navigatsiya

## Texnik talablar

- Python 3.8+
- Django 4.2+
- python-telegram-bot 20.0+
- gspread
- Google API kredensiali
- Telegram Bot API tokeni

## O'rnatish

### 1. Loyiha kodini klonlash

```bash
git clone https://github.com/username/telegram-registration-bot.git
cd telegram-registration-bot
```

### 2. Virtual muhitni yaratish va faollashtirish

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows
```

### 3. Kerakli paketlarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. requirements.txt fayli

```
Django>=4.2.0,<5.0.0
python-telegram-bot>=20.0,<21.0
gspread>=5.7.0,<6.0.0
google-auth>=2.16.0,<3.0.0
gunicorn>=20.1.0,<21.0.0
asgiref>=3.7.0
```

## Fayl tuzilishi

```
telegram_registration/
│
├── manage.py
├── requirements.txt
├── credentials.json  # Google API kredensiallar fayli
├── README.md
│
├── telegram_registration/  # Django asosiy loyiha
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
└── bot/  # Bot ilovasi
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py       # Registration modeli saqlanadi
    ├── telegram_bot.py # Bot asosiy kodi
    ├── views.py        # Webhook uchun ko'rinishlar
    ├── urls.py
    ├── migrations/
    └── management/
        └── commands/
            ├── __init__.py
            ├── start_bot.py    # Polling uchun
            └── set_webhook.py  # Webhook o'rnatish uchun
```

## Konfiguratsiya

### 1. Telegram botini yaratish

1. Telegram-da @BotFather-ga murojaat qiling
2. `/newbot` buyrug'ini yuboring va ko'rsatmalarga amal qiling
3. Bot tokenini oling

### 2. Google Sheets kredensiallarini olish

1. Google Cloud Console (https://console.cloud.google.com) ga kiring
2. Yangi loyiha yarating
3. Google Sheets API va Google Drive API-ni yoqing
4. Service Account (Xizmat hisob qaydnomasi) yarating
5. JSON formatidagi kredensial faylini yuklab oling
6. Faylni `credentials.json` nomi bilan loyiha ildiz papkasiga saqlang

### 3. settings.py faylini sozlash

```python
# Telegram Bot sozlamalari
TELEGRAM_BOT_TOKEN = 'your_telegram_bot_token'
GOOGLE_SHEETS_SPREADSHEET_ID = 'your_google_spreadsheet_id'
GROUP_CHAT_ID = 'your_telegram_group_id'

# Media sozlamalari
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### 4. Google Sheets tayyorlash

1. Google Sheets-da yangi jadvalni yarating
2. Jadval ID sini URL manzilidan oling: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`
3. Jadvalga Service Account emailini taklif qiling (edit huquqlari bilan)
4. Birinchi qatorga sarlavhalar qo'shing:
   - Vaqt
   - Telegram ID
   - Username
   - FIO
   - Telefon
   - Ma'lumot
   - Resume Nomi
   - Resume Linki

### 5. Telegram guruhni sozlash

1. Yangi guruh yarating yoki mavjud guruhdan foydalaning
2. Botingizni guruhga qo'shing va admin qiling
3. Guruh ID sini oling (bu @getidsbot orqali olinishi mumkin)

### 6. Migratsiyalarni yaratish va qo'llash

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Muhim qismlar

1. **Model**:

```python
# bot/models.py
from django.db import models

class Registration(models.Model):
    registration_time = models.DateTimeField(auto_now_add=True)
    telegram_id = models.BigIntegerField()
    telegram_username = models.CharField(max_length=255, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    about = models.TextField()
    resume_file_name = models.CharField(max_length=255)
    resume_telegram_link = models.URLField(max_length=500)
    
    def __str__(self):
        return f"{self.full_name} ({self.telegram_id})"
```

2. **Admin panel**:

```python
# bot/admin.py
from django.contrib import admin
from .models import Registration

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'telegram_username', 'phone_number', 'registration_time')
    search_fields = ('full_name', 'telegram_username', 'phone_number', 'about')
    list_filter = ('registration_time',)
    readonly_fields = ('registration_time',)
```

3. **Vaqt xatoligini tuzatish**:

```python
def save_to_sheets(registration_time, telegram_id, telegram_username, full_name, phone_number, about, resume_file_name, registration_id, resume_telegram_link):
    sheet = get_sheet()
    
    # datetime obyektini string formatga o'tkazamiz
    if isinstance(registration_time, datetime.datetime):
        registration_time = registration_time.strftime("%Y-%m-%d %H:%M:%S")
    
    registration_data = [
        registration_time,  # Endi bu string formatda
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
```

## Foydalanish

Bot ikki xil rejimda ishga tushirilishi mumkin:

### 1. Polling rejimi (rivojlantirish uchun)

```bash
python manage.py start_bot
```

### 2. Webhook rejimi (ishlab chiqarish muhiti uchun)

1. Webhook-ni o'rnatish:

```bash
python manage.py set_webhook https://your-domain.com
```

2. Django serverini ishga tushirish:

```bash
gunicorn telegram_registration.wsgi:application
```

## Deploy qilish (Ishlab chiqarish muhiti uchun)

### VPS serverda deploy qilish

#### 1. Server tayyorlash

```bash
# Kerakli paketlarni o'rnatish
sudo apt update
sudo apt install python3-pip python3-venv nginx

# Loyihani klonlash
git clone https://github.com/username/telegram-registration-bot.git
cd telegram-registration-bot

# Virtual muhitni yaratish
python3 -m venv venv
source venv/bin/activate

# Paketlarni o'rnatish
pip install -r requirements.txt
pip install gunicorn
```

#### 2. Django sozlamalari

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', 'your-server-ip']

# Xavfsizlik kalit so'zini yangilang
SECRET_KEY = 'your-secure-secret-key'
```

#### 3. Static fayllarni to'plash

```bash
python manage.py collectstatic
```

#### 4. Gunicorn systemd servisi yaratish

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Quyidagi kontentni kiriting:

```
[Unit]
Description=Telegram Registration Bot Service
After=network.target

[Service]
User=your-username
Group=www-data
WorkingDirectory=/path/to/telegram-registration-bot
ExecStart=/path/to/telegram-registration-bot/venv/bin/gunicorn --workers 3 --bind unix:/path/to/telegram-registration-bot/telegram-bot.sock telegram_registration.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### 5. Serverni faollashtirish va boshlash

```bash
sudo systemctl daemon-reload
sudo systemctl start telegram-bot
sudo systemctl enable telegram-bot
```

#### 6. Nginx konfiguratsiyasi

```bash
sudo nano /etc/nginx/sites-available/telegram-bot
```

Quyidagi kontentni kiriting:

```
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /path/to/telegram-registration-bot;
    }

    location /media/ {
        root /path/to/telegram-registration-bot;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/telegram-registration-bot/telegram-bot.sock;
    }
}
```

Nginx konfiguratsiyasini faollashtirish:

```bash
sudo ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled
sudo systemctl restart nginx
```

#### 7. Webhook o'rnatish

```bash
python manage.py set_webhook https://your-domain.com/bot/webhook/
```

### SSL sertifikatini o'rnatish (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Ngrok bilan lokal serverda sinab ko'rish

Agar rivojlantirish jarayonida webhook-ni sinab ko'rmoqchi bo'lsangiz, Ngrok orqali:

```bash
# Ngrok o'rnatish (agar o'rnatilmagan bo'lsa)
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-amd64.tgz
tar -xvf ngrok-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Django serverini ishga tushirish
python manage.py runserver

# Boshqa terminal oynasida Ngrok ishga tushirish
ngrok http 8000

# Webhook o'rnatish (Ngrok URL bilan)
python manage.py set_webhook https://your-ngrok-url
```

## Xatoliklarni tuzatish

### 1. Webhook xatoliklari

Webhook to'g'ri ishlashi uchun:
- Serveringiz HTTPS protokolini qo'llab-quvvatlashi kerak
- Telegram API serverlariga kirish imkoniyati bo'lishi kerak
- Webhook URLi to'g'ri ko'rsatilgan bo'lishi kerak
- Django server ishlayotgan bo'lishi kerak

### 2. Google Sheets xatoliklari

Google Sheets bilan ishlash muammolarida:
- `credentials.json` fayli to'g'ri joylashtirilganligini tekshiring
- Service Account-ga spreadsheet bo'yicha huquqlar berilganini tasdiqlang
- Spreadsheet ID to'g'ri ekanligini tekshiring

### 3. Ma'lumotlarni saqlash xatoliklari

Agar ma'lumotlar saqlanmasa:
- Django migratsiyalar to'g'ri qo'llanganligini tekshiring
- Databasega yozish huquqlari borligini tekshiring
- Logglarni tekshirib, xato xabarlarini aniqlang

### 4. Async xatoligi

Agar `You cannot call this from an async context - use a thread or sync_to_async` xatosini ko'rsangiz:
- Django modellariga yozish uchun `sync_to_async` dagi funksiyalardan foydalanayotganingizga ishonch hosil qiling
- Datetime obyektlarini JSON ga saqlashdan oldin string formatga o'tkazayotganingizni tekshiring

### 5. Asosiy xatoliklarni bartaraf etish

1. **Server qayta ishga tushirilganda botning ishlamaslik muammosi**:
   ```bash
   sudo systemctl restart telegram-bot
   sudo systemctl status telegram-bot
   ```

2. **Google Sheets bog'lanishda muammo**:
   ```python
   # Google kredensiallarini tekshirish
   from google.oauth2.service_account import Credentials
   creds = Credentials.from_service_account_file('credentials.json')
   print(creds.valid)  # True bo'lishi kerak
   ```

3. **Bot javob bermasligi**:
   ```bash
   # Webhook statusini tekshirish
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
   ```