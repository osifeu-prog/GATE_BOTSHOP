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
בנק: הפועלים
סניף: כפר גנים (153)
מספר חשבון: 73462
שם המוטב: קאופמן צביקה

**אפשרות 2: תשלום ב-TON 💎**
`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`

**✅ לאחר התשלום:**

1. **שמור את אישור התשלום** (צילום מסך/תמלול ההעברה).
2. **שלח את האישור אלינו כאן בצ'אט הזה**.
3. **מייד לאחר האימות**, נשלח לך את הקישור להצטרפות לקבוצה הסגורה: {}

**⚡ הערה:** האימות ידני ולרוב ייקח עד 24 שעות.

אנא שלח כעת את אישור התשלום כצילום מסך או הודעה.
    """.format(MAIN_GROUP_LINK)

    update.message.reply_text(payment_text, parse_mode='Markdown')

def handle_payment_proof(update: Update, context: CallbackContext) -> None:
    """מטפל בשליחת אישור התשלום מהמשתמש"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        # בדיקה אם המשתמש שלח תמונה (צילום מסך)
        if update.message.photo:
            # לוקחים את התמונה באיכות הגבוהה ביותר
            photo_file = update.message.photo[-1].get_file()
            # מעבירים את הקובץ לקבוצת הניהול
            try:
                bot.send_photo(
                    chat_id=ADMIN_GROUP_LINK.replace('https://t.me/', ''), 
                    photo=photo_file.file_id, 
                    caption=f"📸 אישור תשלום מהמשתמש: {user.first_name} (ID: {chat_id})"
                )
                update.message.reply_text("✅ **תודה רבה!** אישור התשלום התקבל ונשלח לאימות. נחזור אליך עם קישור ההצטרפות בהקדם האפשרי (עד 24 שעות).")
                send_payment_confirmation(chat_id, "צילום מסך")
            except Exception as e:
                logger.error(f"שגיאה בשליחת התמונה לקבוצת הניהול: {e}")
                update.message.reply_text("❌ אירעה שגיאה בשליחת האישור. אנא נסה שוב מאוחר יותר.")

        # בדיקה אם המשתמש שלח טקסט (תמלול ההעברה)
        elif update.message.text and not update.message.text.startswith('/'):
            proof_text = update.message.text
            send_payment_confirmation(chat_id, proof_text)
            update.message.reply_text("✅ **תודה רבה!** פרטי האישור התקבלו ונשלחו לאימות. נחזור אליך עם קישור ההצטרפות בהקדם האפשרי (עד 24 שעות).")

        else:
            # אם זו פקודה או סוג תוכן אחר - מתעלמים
            pass
            
    except Exception as e:
        logger.error(f"Error in handle_payment_proof: {e}")
        update.message.reply_text("❌ אירעה שגיאה בעיבוד האישור. אנא נסה שוב.")

def handle_unknown(update: Update, context: CallbackContext) -> None:
    """מטפל בהודעות לא מזוהות"""
    update.message.reply_text("🤔 לא הבנתי. השתמש ב-/start כדי להתחיל.")

# --- הגדרת handlers ---
def setup_handlers():
    """מגדיר את ה-handlers עבור הפקודות"""
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_payment_proof))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_payment_proof))
    dispatcher.add_handler(MessageHandler(Filters.all, handle_unknown))
    logger.info("Handlers setup completed")

# --- הגדרת Flask routes ---
@app.route('/')
def home():
    return "🤖 הבוט פעיל וחי! שלח /start לבוט כדי להתחיל.", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """נקודת הכניסה עבור עדכונים מטלגרם"""
    if request.method == 'POST':
        try:
            update = Update.de_json(request.get_json(force=True), bot)
            dispatcher.process_update(update)
            return 'ok', 200
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")
            return 'error', 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """קובע את ה-Webhook עבור הבוט"""
    try:
        success = bot.set_webhook(WEBHOOK_URL)
        if success:
            logger.info(f"Webhook set successfully to: {WEBHOOK_URL}")
            return jsonify({"status": "Webhook set successfully", "url": WEBHOOK_URL}), 200
        else:
            logger.error("Failed to set webhook")
            return jsonify({"status": "Failed to set webhook"}), 500
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"status": f"Error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """בדיקת בריאות של האפלי�켦יה"""
    return jsonify({"status": "healthy", "service": "Crypto Community Gateway Bot"}), 200

# --- אתחול ---
def initialize_bot():
    """אתחול הבוט והגדרות"""
    try:
        # הגדרת handlers
        setup_handlers()
        
        # קביעת webhook
        webhook_result = bot.set_webhook(WEBHOOK_URL)
        if webhook_result:
            logger.info(f"✅ Webhook set successfully: {WEBHOOK_URL}")
        else:
            logger.error("❌ Failed to set webhook")
            
        # בדיקת פרטי הבוט
        bot_info = bot.get_me()
        logger.info(f"✅ Bot initialized: @{bot_info.username}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")

# אתחול הבוט כאשר המודול נטען
initialize_bot()

# הפעלת שרת Flask (ב-Railway, הפורט מוגדר ע"י משתנה הסביבה PORT)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
