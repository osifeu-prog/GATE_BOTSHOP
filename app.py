import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext

# הגדרת משתני הסביבה
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://web-production-b425.up.railway.app') + '/webhook'
MAIN_GROUP_LINK = "https://t.me/+HIzvM8sEgh1kNWY0"
ADMIN_GROUP_LINK = "https://t.me/+aww1rlTDUSplODc0"

# הגדרת הלוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# אתחול הבוט וה-dispatcher
try:
    bot = Bot(token=BOT_TOKEN)
    # יצירת dispatcher עם worker threads
    dispatcher = Dispatcher(bot, None, workers=4)
    logger.info("Bot and dispatcher initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    raise

# --- לוגיקה לרישום משתמשים ושליחת התראות ---
def log_user_interaction(chat_id, first_name, last_name, username, action):
    """רושם פעילות משתמש ושולח התראה לקבוצת הניהול"""
    user_info = f"🆔 ID: {chat_id}\n👤 שם: {first_name} {last_name}\n📛 משתמש: @{username}"
    log_message = f"🔔 **פעילות חדשה בבוט**\n{user_info}\n📝 **פעולה:** {action}"

    try:
        bot.send_message(chat_id=ADMIN_GROUP_LINK.replace('https://t.me/', ''), text=log_message, parse_mode='Markdown')
        logger.info(f"לוג נשלח: {action} עבור {chat_id}")
    except Exception as e:
        logger.error(f"שליחת לוג נכשלה: {e}")

def send_payment_confirmation(chat_id, proof_text):
    """שולח אישור תשלום לקבוצת הניהול"""
    confirmation_message = f"✅ **אישור תשלום חדש!**\n🆔 ID משתמש: {chat_id}\n📸 אישור: {proof_text}"
    try:
        bot.send_message(chat_id=ADMIN_GROUP_LINK.replace('https://t.me/', ''), text=confirmation_message, parse_mode='Markdown')
        logger.info(f"אישור תשלום נשלח עבור {chat_id}")
    except Exception as e:
        logger.error(f"שליחת אישור תשלום נכשלה: {e}")

# --- מטבעות הטלגרם ---
def start(update: Update, context: CallbackContext) -> None:
    """מטפל בפקודה /start"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        # רישום המשתמש ושליחת לוג
        log_user_interaction(
            chat_id=chat_id,
            first_name=user.first_name or "לא צוין",
            last_name=user.last_name or "",
            username=user.username or "לא צוין",
            action="התחיל שיחה עם הבוט (/start)"
        )

        # הודעת ברוך הבא
        welcome_text = f"""
👋 **ברוך הבא {user.first_name}!**

אנחנו שמחים להזמין אותך לקהילת הקריפטו החדשה והמתקדמת בישראל! 🚀

**🌟 מה מחכה לך בקהילה?**
• 💰 **המון הטבות ומבצעים** בלעדיים לחברי הקהילה
• 📊 **ניתוחים טכניים** מקצועיים ומעמיקים
• 🤖 **רובוטים אוטומטיים** למסחר וניהול תיקים
• 🔗 **לינק אישי למכירה חוזרת** - הזדמנות להרוויח כמו בחנות אינטרנטית, ישירות בטלגרם!
• 🌍 **הצטרפות למערכת מלאה** שתשנה את חייך הכלכליים

**🛠 המערכת המלאה שלנו - SLH FULL SUITE:**
זוהי מערכת מונורפו מאוחדת שכוללת:
• **TON-engine** – מנוע ניתוח טכני וניהול סיכונים מתקדם
• **Botshop** – שער קהילתי/בוט טלגרם לקמפיינים וקבוצות
• **SLH Wallet** – שירות ארנק ואיי.פי.איי פיננסי

**📚 הסברים קצרים:**
• **קריפטו** – כסף דיגיטלי מאובטח וחסר ריכוזיות.
• **Web3** – האינטרנט החדש, בו אתה שולט בנתונים ובנכסים הדיגיטליים שלך.
• **NFT** – נכס דיגיטלי ייחודי וב�עדי שאתה הבעלים שלו.
• **ביננס** – אחת מבורסות הקריפטו הגדולות והאמינות בעולם.

**הבוט הזה הוא רק **השער** לעולם חדש של הזדמנויות כלכליות, קהילתיות ובטוחות.**

**🪙 כדי להיכנס ולקבל גישה להכל, נדרש תשלום קבלה סמלי של 39 ₪.**
        """

        # שליחת הודעת ברוך הבא
        update.message.reply_text(welcome_text, parse_mode='Markdown')
        
        # שליחת הוראות התשלום
        send_payment_instructions(update, context)
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        update.message.reply_text("❌ אירעה שגיאה. אנא נסה שוב.")

def send_payment_instructions(update: Update, context: CallbackContext) -> None:
    """שולח למשתמש את הוראות התשלום"""
    payment_text = """
**💳 איך משלמים?**

**אפשרות 1: העברה בנקאית 🏦**
