import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# הגדרת משתני הסביבה
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL') + '/webhook'
MAIN_GROUP_LINK = "https://t.me/+HIzvM8sEgh1kNWY0"
ADMIN_GROUP_LINK = "https://t.me/+aww1rlTDUSplODc0"

# הגדרת states לשיחה (אם יידרש להרחבה)
WAITING_FOR_PAYMENT_CONFIRMATION = range(1)

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# --- לוגיקה לרישום משתמשים ושליחת התראות ---
def log_user_interaction(chat_id, first_name, last_name, username, action):
    """רושם פעילות משתמש ושולח התראה לקבוצת הניהול"""
    user_info = f"🆔 ID: {chat_id}\n👤 שם: {first_name} {last_name}\n📛 משתמש: @{username}"
    log_message = f"🔔 **פעילות חדשה בבוט**\n{user_info}\n📝 **פעולה:** {action}"

    try:
        bot.send_message(chat_id=ADMIN_GROUP_LINK, text=log_message, parse_mode='Markdown')
        logging.info(f"לוג נשלח: {action} עבור {chat_id}")
    except Exception as e:
        logging.error(f"שליחת לוג נכשלה: {e}")

def send_payment_confirmation(chat_id, proof_text):
    """שולח אישור תשלום לקבוצת הניהול"""
    confirmation_message = f"✅ **אישור תשלום חדש!**\n🆔 ID משתמש: {chat_id}\n📸 אישור: {proof_text}"
    try:
        bot.send_message(chat_id=ADMIN_GROUP_LINK, text=confirmation_message, parse_mode='Markdown')
        logging.info(f"אישור תשלום נשלח עבור {chat_id}")
    except Exception as e:
        logging.error(f"שליחת אישור תשלום נכשלה: {e}")

# --- מטבעות הטלגרם ---
def start(update: Update, context: CallbackContext) -> None:
    """מטפל בפקודה /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # רישום המשתמש ושליחת לוג
    log_user_interaction(
        chat_id=chat_id,
        first_name=user.first_name,
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
• 📊 **ניתוחים טכניים** מקצועיים ומעמ�ים
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
• **NFT** – נכס דיגיטלי ייחודי ובלעדי שאתה הבעלים שלו.
• **ביננס** – אחת מבורסות הקריפטו הגדולות והאמינות בעולם.

**הבוט הזה הוא רק **השער** לעולם חדש של הזדמנויות כלכליות, קהילתיות ובטוחות.**

**🪙 כדי להיכנס ולקבל גישה להכל, נדרש תשלום קבלה סמלי של 39 ₪.**
    """

    # שליחת הודעת ברוך הבא
    try:
        # אם יש תמונת ברוך הבא (START_IMAGE_PATH), ניתן להוסיף: # update.message.reply_photo(photo=open(START_IMAGE_PATH, 'rb'))
        update.message.reply_text(welcome_text, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"שגיאה בשליחת הודעת ברוך הבא: {e}")
        update.message.reply_text("ברוך הבא! משהו השתבש בשליחת ההודעה המלאה. נא נסה שוב.")

    # שליחת הוראות התשלום
    send_payment_instructions(update, context)

def send_payment_instructions(update: Update, context: CallbackContext) -> None:
    """שולח למשתמש את הוראות התשלום"""
    payment_text = """
**💳 **איך משלמים?**

**אפשרות 1: העברה בנקאית 🏦**
בנק: הפועלים
סניף: כפר גנים (153)
מספר חשבון: 73462
שם המוטב: קאופמן צביקה

**אפשרות 2: תשלום ב-TON 💎**
`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`

**✅ **לאחר התשלום:**

1. **שמור את אישור התשלום** (צילום מסך/תמלול ההעברה).
2. **שלח את האישור אלינו כאן בצ'אט הזה**.
3. **מייד לאחר האימות**, נשלח לך את הקישור להצטרפות לקבוצה הסגורה: {}

**⚡ **הערה:** האימות ידני ולרוב ייקח עד 24 שעות.

אנא שלח כעת את אישור התשלום כצילום מסך או הודעה.
    """.format(MAIN_GROUP_LINK)

    update.message.reply_text(payment_text, parse_mode='Markdown')

def handle_payment_proof(update: Update, context: CallbackContext) -> None:
    """מטפל בשליחת אישור התשלום מהמשתמש"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # בדיקה אם המשתמש שלח תמונה (צילום מסך)
    if update.message.photo:
        # לוקחים את התמונה באיכות הגבוהה ביותר
        photo_file = update.message.photo[-1].get_file()
        # מעבירים את הקובץ לקבוצת הניהול
        try:
            bot.send_photo(chat_id=ADMIN_GROUP_LINK, photo=photo_file.file_id, caption=f"📸 אישור תשלום מהמשתמש: {user.first_name} (ID: {chat_id})")
            update.message.reply_text("✅ **תודה רבה!** אישור התשלום התקבל ונשלח לאימות. נחזור אליך עם קישור ההצטרפות בהקדם האפשרי (עד 24 שעות).")
            send_payment_confirmation(chat_id, "צילום מסך")
        except Exception as e:
            logging.error(f"שגיאה בשליחת התמונה לקבוצת הניהול: {e}")
            update.message.reply_text("❌ אירעה שגיאה בשליחת האישור. אנא נסה שוב מאוחר יותר.")

    # בדיקה אם המשתמש שלח טקסט (תמלול ההעברה)
    elif update.message.text:
        proof_text = update.message.text
        send_payment_confirmation(chat_id, proof_text)
        update.message.reply_text("✅ **תודה רבה!** פרטי האישור התקבלו ונשלחו לאימות. נחזור אליך עם קישור ההצטרפות בהקדם האפשרי (עד 24 שעות).")

    else:
        update.message.reply_text("❌ אנא שלח את אישור התשלום כ**צילום מסך** או **הודעת טקסט** עם פרטי ההעברה.")

# --- הגדרת Flask ו-Webhook ---
@app.route('/')
def home():
    return "🤖 הבוט פעיל וחי!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """נקודת הכניסה עבור עדכונים מטלגרם"""
    if request.method == 'POST':
        update = Update.de_json(request.get_json(), bot)
        dispatcher.process_update(update)
        return 'ok', 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """קובע את ה-Webhook עבור הבוט"""
    try:
        success = bot.set_webhook(WEBHOOK_URL)
        if success:
            return jsonify({"status": "Webhook set successfully"}), 200
        else:
            return jsonify({"status": "Failed to set webhook"}), 500
    except Exception as e:
        return jsonify({"status": f"Error: {str(e)}"}), 500

# --- הרכבה והפעלה ---
def main():
    # הגדרת הלוגים
    logging.basicConfig(level=logging.INFO)

    # הוספת מטפלים לפקודות ולהודעות
    dispatcher.add_handler(CommandHandler("start", start))
    
    # מטפל לכל הודעה שלא בתהליך שיחה - מניח שמדובר באישור תשלום
    dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_payment_proof))

    # קביעת ה-Webhook בעת ההפעלה
    try:
        bot.set_webhook(WEBHOOK_URL)
        logging.info("Webhook set successfully.")
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")

    # הפעלת שרת Flask (ב-Railway, הפורט מוגדר ע"י משתנה הסביבה PORT)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
