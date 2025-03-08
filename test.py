import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = '/home/odev/Desktop/hr-bot/credentials.json'
SPREADSHEET_ID = '1akH1zEONGmbCYs2pDMsJj9_yxCbl8YpkhCjMjxRl3SI'

credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
client = gspread.authorize(credentials)

sheet = client.open_by_key(SPREADSHEET_ID).sheet1
print(sheet.get_all_records())  # Print all records in the sheet
