import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# הגדרת משתני הסביבה
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://web-production-b425.up.railway.app') + '/webhook'
MAIN_GROUP_LINK = "https://t.me/+HIzvM8sEgh1kNWY0"
ADMIN_GROUP_LINK = "https://t.me/+aww1rlTDUSplODc0"

# states לשיחת צור קשר
CHOOSING, TYPING_CONTACT = range(2)

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

def send_contact_request(chat_id, user_name, contact_type, message):
    """שולח בקשת קשר לקבוצת הניהול"""
    contact_message = f"📞 **בקשת קשר חדשה!**\n👤 ממשתמש: {user_name}\n🆔 ID: {chat_id}\n📋 נושא: {contact_type}\n💬 הודעה: {message}"
    try:
        bot.send_message(chat_id=ADMIN_GROUP_LINK.replace('https://t.me/', ''), text=contact_message, parse_mode='Markdown')
        logger.info(f"בקשת קשר נשלחה עבור {chat_id}")
    except Exception as e:
        logger.error(f"שליחת בקשת קשר נכשלה: {e}")

# --- מקלדות ---
def get_main_keyboard():
    """מחזיר את המקלדת הראשית"""
    keyboard = [
        [InlineKeyboardButton("👥 מי אנחנו?", callback_data='who_we_are')],
        [InlineKeyboardButton("💳 הצטרפות לקהילה - 39₪", callback_data='join_community')],
        [InlineKeyboardButton("🚀 השקעה בפרויקט", callback_data='investment')],
        [InlineKeyboardButton("📞 צור קשר", callback_data='contact')],
        [InlineKeyboardButton("🆘 עזרה ראשונה", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contact_keyboard():
    """מחזיר את מקלדת נושאי הקשר"""
    keyboard = [
        [InlineKeyboardButton("💼 עסקים ושותפויות", callback_data='contact_business')],
        [InlineKeyboardButton("🚀 השקעה בפרויקט", callback_data='contact_investment')],
        [InlineKeyboardButton("🤔 תמיכה טכנית", callback_data='contact_support')],
        [InlineKeyboardButton("💬 כל נושא אחר", callback_data='contact_other')],
        [InlineKeyboardButton("↩️ חזרה לתפריט", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    """מחזיר את מקלדת אפשרויות התשלום"""
    keyboard = [
        [InlineKeyboardButton("🏦 העברה בנקאית", callback_data='payment_bank')],
        [InlineKeyboardButton("💎 תשלום ב-TON", callback_data='payment_ton')],
        [InlineKeyboardButton("✅ שלחתי תשלום", callback_data='payment_sent')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

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

        # הודעת ברוך הבא עם תמונה (אם יש)
        welcome_text = f"""
🎉 **ברוך הבא {user.first_name} לעולם החדש של הכלכלה הקהילתית!** 🌍

🤝 **אנחנו כאן כדי לשנות את הכללים** - ליצור קהילה של חברים, בעלי עסקים ויזמים שרוצים יחד לבנות כלכלה קהילתית חזקה ומשגשגת.

💫 **החלום שלנו:** לשפר את המצב החברתי והקהילתי בישראל דרך טכנולוגיה מתקדמת וכלכלה מבוזרת.

✨ **הצטרפות לקהילה שלנו תפתח בפניך עולם של אפשרויות:**
• 🤖 **גישה למערכת SLH המלאה** - כבר בפרודקשן!
• 📊 **ניתוחים טכניים מתקדמים** ורובוטים אוטומטיים
• 🔗 **לינק אישי למכירה חוזרת** - תוכל להרוויח כמו בחנות אינטרנטית
• 👥 **קהילה תומכת** של אנשי עסקים ויזמים
• 💼 **הזדמנויות עסקיות** ושותפויות אסטרטגיות

**🎯 אנחנו לא רק קהילה - אנחנו תנועה כלכלית חברתית!**
        """

        # שליחת הודעת ברוך הבא עם מקלדת
        update.message.reply_text(
            welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        update.message.reply_text("❌ אירעה שגיאה. אנא נסה שוב.")

def button_handler(update: Update, context: CallbackContext) -> None:
    """מטפל בלחיצות על כפתורים"""
    query = update.callback_query
    query.answer()

    try:
        if query.data == 'who_we_are':
            who_we_are_text = """
**👥 מי אנחנו? - המייסדים**

**אוסיף אונגר & צביקה קאופמן** - שותפים לעסקים, מייסדי SLH ישראל.

🎯 **החזון שלנו:** ליצור את המערכת הפיננסית הדיגיטלית המתקדמת בישראל, שתשחרר את הכלכלה המקומית ותביא לשגשוג קהילתי.

🚀 **המערכת שלנו כבר רצה!** אנחנו בשלב ה-production המלא של:
• **SLH FULL SUITE** - מערכת מונורפו מאוחדת
• **TON-engine** - מנוע ניתוח טכני וניהול סיכונים
• **Botshop** - שער קהילתי/בוטים
• **SLH Wallet** - שירות ארנק פיננסי

💡 **בדיוק כמו שדובאי בנתה על ביננס** - אנחנו בונים את העתיד הכלכלי של ישראל על קריפטו ו-Web3.

🤝 **אנחנו כאן עבורך** - תמיד זמינים לתמיכה, הדרכה ושותפויות.
            """
            query.edit_message_text(
                who_we_are_text,
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'join_community':
            join_text = """
**💫 הצטרפות לקהילת SLH ישראל**

🎯 **למה להצטרף?**
• 🤝 **קהילת חברים** - אנחנו בונים רשת של אנשי עסקים תומכים
• 💼 **הזדמנויות עסקיות** - שיתופי פעולה ופרויקטים משותפים
• 🚀 **גישה למערכת המלאה** - כלים מתקדמים להצלחה כלכלית
• 📚 **הדרכות וליווי** - נעזור לך להצליח

💰 **עלות הצטרפות סמלית:** 39 ₪ בלבד

**🪙 התשלום הוא השער לעולם חדש של אפשרויות:**
• קהילה תומכת של יזמים
• כלים טכנולוגיים מתקדמים
• הזדמנויות להכנסה פסיבית
• שינוי כלכלי אמיתי
            """
            query.edit_message_text(
                join_text,
                reply_markup=get_payment_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'investment':
            investment_text = """
**🚀 הזדמנות השקעה ייחודית!**

💎 **אנחנו מחפשים משקיעים שיצטרפו להצלחה!**

**הפרויקט שלנו כבר ב-production** עם:
✅ **מערכת SLH FULL SUITE** פעילה
✅ **קהילה גדלה** של משתמשים
✅ **טכנולוגיה מתקדמת** שכבר עובדת
✅ **מודל עסקי** מוכח

**🎯 מה אנחנו מציעים למשקיעים:**
• **החזר השקעה** משמעותי
• **שותפות** בפרויקט פורץ דרך
• **גישה** לכל הטכנולוגיות שלנו
• **ליווי אישי** מצוות המייסדים

**📊 החזון:** להפוך למערכת הפיננסית הדיגיטלית המובילה בישראל

**💼 מעוניינים?** לחצו על '📞 צור קשר' ובחרו 'השקעה בפרויקט'
            """
            query.edit_message_text(
                investment_text,
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'contact':
            contact_text = """
**📞 צור קשר עם המייסדים**

אנחנו כאן כדי לעזור! בחר נושא לפניה:
            """
            query.edit_message_text(
                contact_text,
                reply_markup=get_contact_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'help':
            help_text = """
**🆘 עזרה ראשונה**

**❓ בעיות טכניות?**
• נסה לסגור ולפתוח את הבוט מחדש
• ודא שיש לך חיבור אינטרנט

**💳 בעיות בתשלום?**
• שלח לנו צילום מסך של ההעברה
• נבדוק ונחזור אליך תוך 24 שעות

**👥 רוצה להצטרף לקהילה?**
• לחץ על 'הצטרפות לקהילה'
• עקוב אחר הוראות התשלום

**📞 צריך עזרה נוספת?**
• לחץ על 'צור קשר'
• נשמח לעזור!
            """
            query.edit_message_text(
                help_text,
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'payment_bank':
            bank_text = """
**🏦 העברה בנקאית**
בנק: הפועלים
סניף: כפר גנים (153)
מספר חשבון: 73462
שם המוטב: קאופמן צביקה

**📝 חשוב:** אחרי ההעברה, שלח אלינו את אישור התשלום באמצעות הכפתור '✅ שלחתי תשלום'
            """
            query.edit_message_text(
                bank_text,
                reply_markup=get_payment_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'payment_ton':
            ton_text = """
**💎 תשלום ב-TON**
UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp

**📝 חשוב:** אחרי ההעברה, שלח אלינו את אישור התשלום באמצעות הכפתור '✅ שלחתי תשלום'
"""
            query.edit_message_text(
                ton_text,
                reply_markup=get_payment_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'payment_sent':
            payment_sent_text = """
**✅ אישור תשלום**

מצוין! שלח אלינו עכשיו את **אישור התשלום** כ:

📸 **צילום מסך** של ההעברה
📝 **או** פרטי ההעברה בטקסט

**🚀 אחרי האימות** (עד 24 שעות) נשלח לך את הקישור להצטרפות לקהילה!
            """
            query.edit_message_text(
                payment_sent_text,
                reply_markup=get_payment_keyboard(),
                parse_mode='Markdown'
            )
            context.user_data['waiting_for_payment'] = True

        elif query.data in ['contact_business', 'contact_investment', 'contact_support', 'contact_other']:
            contact_types = {
                'contact_business': '💼 עסקים ושותפויות',
                'contact_investment': '🚀 השקעה בפרויקט', 
                'contact_support': '🤔 תמיכה טכנית',
                'contact_other': '💬 כל נושא אחר'
            }
            
            context.user_data['contact_type'] = contact_types[query.data]
            contact_info_text = f"""
**📞 צור קשר - {contact_types[query.data]}**

**👤 פרטי התקשרות:**
**אוסיף אונגר**: 058-4203384
**צביקה קאופמן**: 054-6671882

**💬 אנא כתוב את הודעתך:**
(נא לתאר בקצרה את פנייתך)
            """
            query.edit_message_text(
                contact_info_text,
                parse_mode='Markdown'
            )
            return TYPING_CONTACT

        elif query.data == 'back_to_main':
            start(update, context)

    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        query.edit_message_text("❌ אירעה שגיאה. אנא נסה שוב.")

def handle_contact_message(update: Update, context: CallbackContext) -> int:
    """מטפל בהודעת קשר מהמשתמש"""
    try:
        user = update.effective_user
        user_message = update.message.text
        
        # שליחת בקשת הקשר לקבוצת הניהול
        send_contact_request(
            chat_id=update.effective_chat.id,
            user_name=f"{user.first_name} {user.last_name or ''}",
            contact_type=context.user_data.get('contact_type', 'לא צוין'),
            message=user_message
        )
        
        # הודעת תודה למשתמש
        update.message.reply_text(
            "✅ **תודה רבה!** ההודעה שלך נשלחה למייסדים.\n\n"
            "📞 ניצור איתך קשר בהקדם האפשרי.",
            reply_markup=get_main_keyboard()
        )
        
        # ניקוי ה-state
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_contact_message: {e}")
        update.message.reply_text("❌ אירעה שגיאה בשליחת ההודעה. אנא נסה שוב.")
        return ConversationHandler.END

def handle_payment_proof(update: Update, context: CallbackContext) -> None:
    """מטפל בשליחת אישור תשלום מהמשתמש"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        # בדיקה אם המשתמש שלח תמונה (צילום מסך)
        if update.message.photo:
            photo_file = update.message.photo[-1].get_file()
            try:
                bot.send_photo(
                    chat_id=ADMIN_GROUP_LINK.replace('https://t.me/', ''), 
                    photo=photo_file.file_id, 
                    caption=f"📸 אישור תשלום מהמשתמש: {user.first_name} (ID: {chat_id})"
                )
                update.message.reply_text(
                    "✅ **תודה רבה!** אישור התשלום התקבל ונשלח לאימות.\n\n"
                    "🚀 **נחזור אליך עם קישור ההצטרפות תוך 24 שעות!**",
                    reply_markup=get_main_keyboard()
                )
            except Exception as e:
                logger.error(f"שגיאה בשליחת התמונה לקבוצת הניהול: {e}")
                update.message.reply_text("❌ אירעה שגיאה בשליחת האישור. אנא נסה שוב מאוחר יותר.")

        # בדיקה אם המשתמש שלח טקסט (תמלול ההעברה)
        elif update.message.text and not update.message.text.startswith('/'):
            proof_text = update.message.text
            # שליחת אישור תשלום לקבוצת הניהול
            payment_message = f"✅ **אישור תשלום חדש!**\n👤 ממשתמש: {user.first_name}\n🆔 ID: {chat_id}\n📝 פרטים: {proof_text}"
            bot.send_message(
                chat_id=ADMIN_GROUP_LINK.replace('https://t.me/', ''), 
                text=payment_message, 
                parse_mode='Markdown'
            )
            update.message.reply_text(
                "✅ **תודה רבה!** פרטי האישור התקבלו ונשלחו לאימות.\n\n"
                "🚀 **נחזור אליך עם קישור ההצטרפות תוך 24 שעות!**",
                reply_markup=get_main_keyboard()
            )

        else:
            # אם זו פקודה או סוג תוכן אחר
            pass
            
    except Exception as e:
        logger.error(f"Error in handle_payment_proof: {e}")
        update.message.reply_text("❌ אירעה שגיאה בעיבוד האישור. אנא נסה שוב.")

def cancel(update: Update, context: CallbackContext) -> int:
    """מבטל את שיחת צור קשר"""
    update.message.reply_text(
        "❌ הפניה בוטלה.",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

# --- הגדרת handlers ---
def setup_handlers():
    """מגדיר את ה-handlers עבור הפקודות"""
    # ConversationHandler עבור צור קשר
    contact_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^(contact_business|contact_investment|contact_support|contact_other)$')],
        states={
            TYPING_CONTACT: [MessageHandler(Filters.text & ~Filters.command, handle_contact_message)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(contact_conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_payment_proof))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_payment_proof))
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
    """בדיקת בריאות של האפליקציה"""
    return jsonify({"status": "healthy", "service": "SLH Community Gateway Bot"}), 200

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

# הפעלת שרת Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
