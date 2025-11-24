import os

# הגדרות סביבה
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://web-production-b425.up.railway.app') + '/webhook'
MAIN_GROUP_LINK = os.environ.get('MAIN_GROUP_LINK', 'https://t.me/your_main_group')
ADMIN_GROUP_ID = os.environ.get('ADMIN_GROUP_ID', '-1002147033592')
PAYMENT_CONFIRMATION_GROUP = os.environ.get('PAYMENT_CONFIRMATION_GROUP', '-1002147033592')
MAIN_COMMUNITY_GROUP = os.environ.get('MAIN_COMMUNITY_GROUP', '-1002147033592')
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID', '6996423991')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'slh2025')

# states לשיחת צור קשר
CHOOSING, TYPING_CONTACT = range(2)

# הגדרות מסד נתונים
DB_PATH = 'bot_data.db'

# לוגים
LOG_LEVEL = 'INFO'
