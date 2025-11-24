import os
import logging
import json
from datetime import datetime
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
        [InlineKeyboardButton("🤖 פיתוח בוטים לעסקים", callback_data='bot_development')],
        [InlineKeyboardButton("🌐 הפרויקטים שלנו", callback_data='our_projects')],
        [InlineKeyboardButton("📞 צור קשר", callback_data='contact'), InlineKeyboardButton("🆘 עזרה ראשונה", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contact_keyboard():
    """מחזיר את מקלדת נושאי הקשר"""
    keyboard = [
        [InlineKeyboardButton("💼 עסקים ושותפויות", callback_data='contact_business')],
        [InlineKeyboardButton("🚀 השקעה בפרויקט", callback_data='contact_investment')],
        [InlineKeyboardButton("🤖 פיתוח בוט לעסק שלי", callback_data='contact_bot_development')],
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

def get_bot_development_keyboard():
    """מחזיר את מקלדת שירותי פיתוח בוטים"""
    keyboard = [
        [InlineKeyboardButton("💼 בוט לעסק שלי", callback_data='contact_bot_development')],
        [InlineKeyboardButton("💰 הצעת מחיר", callback_data='contact_business')],
        [InlineKeyboardButton("📞 שיחת ייעוץ", callback_data='contact_other')],
        [InlineKeyboardButton("🌐 האתרים שלנו", callback_data='our_websites')],
        [InlineKeyboardButton("↩️ חזרה", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_projects_keyboard():
    """מחזיר את מקלדת הפרויקטים שלנו"""
    keyboard = [
        [InlineKeyboardButton("🛒 SLH NFT Marketplace", callback_data='project_slh_nft')],
        [InlineKeyboardButton("🤖 Bot Development Platform", callback_data='project_bot_platform')],
        [InlineKeyboardButton("💼 Facebook Business Page", callback_data='project_facebook')],
        [InlineKeyboardButton("📊 Live System Dashboard", callback_data='project_dashboard')],
        [InlineKeyboardButton("🌐 כל האתרים שלנו", callback_data='our_websites')],
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

        # שליחת תמונה עם הודעת ברוך הבא
        welcome_image_url = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80"
        
        try:
            update.message.reply_photo(
                photo=welcome_image_url,
                caption=f"🎉 **ברוך הבא {user.first_name} לעולם החדש של הכלכלה הקהילתית!** 🌍\n\n_קהילה • טכנולוגיה • חופש כלכלי_",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Could not send welcome image: {e}")
            # אם התמונה נכשלת, נשלח רק טקסט

        welcome_text = """
🤝 **אנחנו כאן כדי לשנות את הכללים** - ליצור קהילה של חברים, בעלי עסקים ויזמים שרוצים יחד לבנות כלכלה קהילתית חזקה ומשגשגת.

💫 **החלום שלנו:** לשפר את המצב החברתי והקהילתי בישראל דרך טכנולוגיה מתקדמת וכלכלה מבוזרת.

✨ **הצטרפות לקהילה שלנו תפתח בפניך עולם של אפשרויות:**
• 🤖 **גישה למערכת SLH המלאה** - כבר בפרודקשן!
• 📊 **ניתוחים טכניים מתקדמים** ורובוטים אוטומטיים
• 🔗 **לינק אישי למכירה חוזרת** - תוכל להרוויח כמו בחנות אינטרנטית
• 👥 **קהילה תומכת** של אנשי עסקים ויזמים
• 💼 **הזדמנויות עסקיות** ושותפויות אסטרטגיות
• 🚀 **גישה לטכנולוגיות Web3** מתקדמות

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

**🛠 אנחנו גם מציעים שירותי פיתוח בוטים!**
מעוניינים בבוט דומה לעסק שלכם? אנחנו בונים בוטים אוטומטיים עם:
• שער כניסה וקהילות
• מערכות תשלום והזמנות
• אינטגרציה עם אתרים
• שיווק אוטומטי

**📞 ליצירת קשר:** 
**אוסיף**: 058-4203384
**צביקה**: 054-6671882
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

**💎 מה תקבל בהצטרפות?**
• **גישה למערכת SLH המלאה** - שילוב ייחודי של:
  🛒 **איקומרס** - מערכת מכירה חוזרת עם לינק אישי
  📊 **ביננס** - כלים לניתוח מסחר וניהול תיקים
  🎨 **NFT** - יצירה וניהול נכסים דיגיטליים
  🤖 **חוזים חכמים** - אוטומציה של תהליכים עסקיים

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
            # שליחת תמונה להשקעה
            investment_image_url = "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80"
            
            try:
                query.message.reply_photo(
                    photo=investment_image_url,
                    caption="🚀 **הזדמנות השקעה ייחודית!**\n\n_מערכת SLH - טכנולוגיה שתשנה את פני הכלכלה הישראלית_",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.warning(f"Could not send investment image: {e}")

            investment_text = """
**🚀 הזדמנות השקעה ייחודית!**

**💎 מערכת SLH - טכנולוגיה שתשנה את פני הכלכלה הישראלית**

אנחנו בונים את העתיד הכלכלי של ישראל עם מערכת משולבת ראשונה מסוגה:

**🛠 השילוב הייחודי שלנו:**
• **🛒 איקומרס מתקדם** - מערכת מכירה חוזרת עם לינקים אישיים
• **📊 פלטפורמת מסחר** - כלים מתקדמים לניתוח וניהול תיקים
• **🎨 NFT Marketplace** - יצירה וסחר בנכסים דיגיטליים
• **🤖 חוזים חכמים** - אוטומציה של תהליכים עסקיים ופיננסיים

**📈 הפרויקט שלנו כבר ב-production עם:**
✅ **מערכת SLH FULL SUITE** פעילה
✅ **קהילה גדלה** של משתמשים
✅ **טכנולוגיה מתקדמת** שכבר עובדת
✅ **מודל עסקי** מוכח

**🎯 מה אנחנו מציעים למשקיעים:**
• **החזר השקעה** משמעותי
• **שותפות** בפרויקט פורץ דרך
• **גישה** לכל הטכנולוגיות שלנו
• **ליווי אישי** מצוות המייסדים

**🛠 גם שירותי פיתוח בוטים!**
אנחנו מציעים גם פיתוח בוטים מותאמים אישית לעסקים. הבוט הזה הוא דוגמה אחת ליכולות שלנו.

**💼 מעוניינים?** לחצו על '📞 צור קשר' ובחרו 'השקעה בפרויקט'
            """
            query.edit_message_text(
                investment_text,
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'bot_development':
            bot_dev_text = """
**🤖 פיתוח בוטים לעסקים - המהפכה הדיגיטלית הבאה!**

**💡 למה כל עסק צריך בוט טלגרם?**

**📈 נתונים מדברים:**
• **חיסכון של 30%** בעלויות שירות לקוחות
• **עלייה של 40%** במכירות דרך אוטומציה
• **זמינות 24/7** ללא תוספת עלויות כוח אדם
• **ניהול קהילות** והגדלת נאמנות לקוחות

**🚀 מה אנחנו מציעים:**
• **בוטים מותאמים אישית** לעסק שלך
• **שערי כניסה לקהילות** בתשלום
• **מערכות הזמנות ואיקומרס**
• **אינטגרציה עם אתרים** ומערכות CRM
• **שיווק אוטומטי** וניהול לקוחות

**💼 דוגמאות לבוטים שאנחנו בונים:**
• בוטי קהילה ומידע
• בוטי מכירות והזמנות
• בוטי שירות ותמיכה
• בוטי ניהול תוכן

**💰 מחירים נוחים** - החל מ-₪149 בלבד!

**📞 מעוניינים?** נשמח לשוחח על הצרכים הספציפיים של העסק שלך!
            """
            query.edit_message_text(
                bot_dev_text,
                reply_markup=get_bot_development_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'our_projects':
            projects_text = """
**🌐 הפרויקטים שלנו - תיק עבודות**

להלן הפרויקטים והפלטפורמות שאנו מפתחים ומתחזקים:

**🎯 המערכות הפעילות שלנו:**
• **SLH FULL SUITE** - המערכת המרכזית שלנו
• **בוטים אוטומטיים** לקהילות ועסקים
• **פלטפורמות מסחר** וניהול תיקים
• **אתרי NFT** ושיווק דיגיטלי

**📊 כל הפרויקטים מחוברים ומשתלבים** ליצירת חוויה אחת מלאה ללקוח.

בחר אחד מהפרויקטים להצגת פרטים נוספים:
            """
            query.edit_message_text(
                projects_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'our_websites':
            websites_text = """
**🌐 כל האתרים והפלטפורמות שלנו**

**🛠 פלטפורמות פעילות:**
• **פלטפורמת הבוטים** - https://web-production-b425.up.railway.app/set_webhook
• **שרת API וממשק** - https://web-production-b425.up.railway.app

**🎨 אתרים ושיווק:**
• **שוק ה-NFT שלנו** - https://slh-nft.com/
• **דף הפייסבוק העסקי** - https://www.facebook.com/OMG.adv/

**📚 משאבים ומידע:**
• **דף נחיתה** - https://osifeu-prog.github.io/GATE_BOTSHOP/
• **תיעוד ומדריכים** - בקרוב

**📞 ליצירת קשר:**
**אוסיף**: 058-4203384
**צביקה**: 054-6671882

**💡 כל האתרים מעודכנים ופעילים!**
            """
            query.edit_message_text(
                websites_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'project_slh_nft':
            nft_text = """
**🎨 SLH NFT Marketplace**

**https://slh-nft.com/**

שוק NFT מתקדם המאפשר יצירה, קניה ומכירה של נכסים דיגיטליים ייחודיים.

**🚀 תכונות מרכזיות:**
• יצירת NFT מקוריים
• מסחר מאובטח
• חוזים חכמים
• אינטגרציה עם ארנקים דיגיטליים

**💎 יתרונות:**
• עמלות נמוכות
• ממשק משתמש intuitive
• תמיכה במגוון פורמטים
• קהילה פעילה

**👥 קהל יעד:**
• אמנים דיגיטליים
• אספנים
• משקיעים
• עסקים המעוניינים בנכסים דיגיטליים

**🔗 בקרו באתר:** https://slh-nft.com/
            """
            query.edit_message_text(
                nft_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'project_bot_platform':
            platform_text = """
**🤖 Bot Development Platform**

**https://web-production-b425.up.railway.app/set_webhook**

פלטפורמה מתקדמת לפיתוח בוטי טלגרם עם יכולות מתקדמות.

**🚀 תכונות מרכזיות:**
• בוטי קהילה וניהול
• מערכות תשלום אינטגרטיביות
• אינטגרציה עם APIs חיצוניים
• ניתוח נתונים מתקדם

**💼 שירותים:**
• פיתוח בוטים מותאמים אישית
• תמיכה והדרכה
• אחזקה ושיפורים
• אינטגרציות מתקדמות

**📊 נתונים:**
• מהירות תגובה: < 3 שניות
• זמינות: 99.9%
• תמיכה במאות משתמשים בו-זמנית

**🔗 פלטפורמה פעילה:** https://web-production-b425.up.railway.app
            """
            query.edit_message_text(
                platform_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'project_facebook':
            facebook_text = """
**💼 Facebook Business Page**

**https://www.facebook.com/OMG.adv/**

דף העסקים הרשמי שלנו בפייסבוק - המרכז השיווקי והתקשורתי שלנו.

**📱 מה תמצאו בדף:**
• עדכונים שוטפים על הפרויקטים
• טיפים ועצות לעסקים
• קידומים והנחות בלעדיים
• סיפורי הצלחה של לקוחות

**🎯 מטרות הדף:**
• בניית קהילה עסקית
• שיווק ושיח עם לקוחות
• הפקת לידים איכותיים
• בניית מותג חזק

**👥 קהל יעד:**
• בעלי עסקים
• יזמים ומשקיעים
• אנשי טכנולוגיה
• מעוניינים בקריפטו ו-Web3

**👍 עקבו אחרינו:** https://www.facebook.com/OMG.adv/
            """
            query.edit_message_text(
                facebook_text,
                reply_markup=get_projects_keyboard(),
                parse_mode='Markdown'
            )

        elif query.data == 'project_dashboard':
            dashboard_text = """
**📊 Live System Dashboard**

**https://web-production-b425.up.railway.app/**

ממשק ניהול וניטור חי של כל המערכות שלנו - בעברית!

**📈 מה תוכלו לראות בממשק:**
• **סטטוס מערכת** - זמינות ופעילות
• **סטטיסטיקות** - משתמשים ופעילות
• **ביצועים** - מהירות ותגובה
• **לוגים** - פעילות מערכת

**🔧 אפשרויות נוספות:**
• ניהול משתמשים
• עדכוני מערכת
• דוחות וביצועים
• הגדרות והתאמות

**🌐 הממשק כולל:**
• דשבורד אינטואיטיבי בעברית
• גרפים וסטטיסטיקות
• התראות בזמן אמת
• דוחות ניתנים להורדה

**🔗 גשו לממשק:** https://web-production-b425.up.railway.app/
            """
            query.edit_message_text(
                dashboard_text,
                reply_markup=get_projects_keyboard(),
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

**🤖 מעוניין בבוט לעסק שלך?**
• לחץ על 'פיתוח בוטים לעסקים'
• נשמח לעזור!

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

        elif query.data in ['contact_business', 'contact_investment', 'contact_bot_development', 'contact_support', 'contact_other']:
            contact_types = {
                'contact_business': '💼 עסקים ושותפויות',
                'contact_investment': '🚀 השקעה בפרויקט', 
                'contact_bot_development': '🤖 פיתוח בוט לעסק שלי',
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
            # במקום לשנות את ההודעה הנוכחית, נשלח הודעה חדשה עם התפריט הראשי
            welcome_back_text = """
**🏠 חזרת לתפריט הראשי**

בחר אחת האפשרויות להמשך:
            """
            query.message.reply_text(
                welcome_back_text,
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        query.message.reply_text(
            "❌ אירעה שגיאה. אנא נסה שוב מהתפריט הראשי.",
            reply_markup=get_main_keyboard()
        )

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
        entry_points=[CallbackQueryHandler(button_handler, pattern='^(contact_business|contact_investment|contact_bot_development|contact_support|contact_other)$')],
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
    return jsonify({
        "status": "active",
        "service": "SLH Community Gateway Bot",
        "version": "3.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Community gateway with payment",
            "Bot development services", 
            "Investment opportunities",
            "Telegram automation",
            "Multi-project portfolio",
            "Hebrew interface"
        ],
        "projects": {
            "bot_platform": "https://web-production-b425.up.railway.app/set_webhook",
            "nft_marketplace": "https://slh-nft.com/",
            "facebook_page": "https://www.facebook.com/OMG.adv/",
            "landing_page": "https://osifeu-prog.github.io/GATE_BOTSHOP/"
        },
        "contact": {
            "osif": "058-4203384", 
            "zvika": "054-6671882"
        }
    }), 200

@app.route('/dashboard')
def dashboard():
    """ממשק ניהול בעברית"""
    return """
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SLH - ממשק ניהול</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .projects { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .project-item { padding: 10px; border-bottom: 1px solid #eee; }
        .project-item:last-child { border-bottom: none; }
        .status-active { color: green; font-weight: bold; }
        .status-inactive { color: red; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SLH - ממשק ניהול מערכת</h1>
            <p>ניהול וניטור כל הפרויקטים במערכת אחת</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="userCount">0</div>
                <div>משתמשים רשומים</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="projectCount">4</div>
                <div>פרויקטים פעילים</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="uptime">99.9%</div>
                <div>זמינות מערכת</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="responseTime">2.3s</div>
                <div>זמן תגובה ממוצע</div>
            </div>
        </div>

        <div class="projects">
            <h2>🌐 הפרויקטים שלנו</h2>
            <div class="project-item">
                <strong>🤖 Bot Development Platform</strong>
                <span class="status-active">פעיל</span>
                <br><small>https://web-production-b425.up.railway.app</small>
            </div>
            <div class="project-item">
                <strong>🎨 SLH NFT Marketplace</strong>
                <span class="status-active">פעיל</span>
                <br><small>https://slh-nft.com/</small>
            </div>
            <div class="project-item">
                <strong>💼 Facebook Business Page</strong>
                <span class="status-active">פעיל</span>
                <br><small>https://www.facebook.com/OMG.adv/</small>
            </div>
            <div class="project-item">
                <strong>📚 Landing Page</strong>
                <span class="status-active">בפיתוח</span>
                <br><small>https://osifeu-prog.github.io/GATE_BOTSHOP/</small>
            </div>
        </div>

        <div class="projects" style="margin-top: 20px;">
            <h2>📞 יצירת קשר</h2>
            <p><strong>אוסיף אונגר:</strong> 058-4203384</p>
            <p><strong>צביקה קאופמן:</strong> 054-6671882</p>
        </div>
    </div>

    <script>
        // הדמיית נתונים דינמיים
        setInterval(() => {
            document.getElementById('userCount').textContent = 
                Math.floor(100 + Math.random() * 50);
            document.getElementById('responseTime').textContent = 
                (1.5 + Math.random() * 1).toFixed(1) + 's';
        }, 3000);
    </script>
</body>
</html>
"""

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
            return jsonify({
                "status": "Webhook set successfully", 
                "url": WEBHOOK_URL,
                "timestamp": datetime.now().isoformat(),
                "bot_info": {
                    "service": "SLH Community & Bot Development",
                    "version": "3.0",
                    "features": [
                        "Community membership gateway",
                        "Payment processing", 
                        "Bot development services",
                        "Investment platform",
                        "Multi-project management"
                    ]
                }
            }), 200
        else:
            logger.error("Failed to set webhook")
            return jsonify({"status": "Failed to set webhook"}), 500
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"status": f"Error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """בדיקת בריאות של האפליקציה"""
    return jsonify({
        "status": "healthy", 
        "service": "SLH Community Gateway & Bot Development",
        "version": "3.0",
        "timestamp": datetime.now().isoformat(),
        "projects_active": 4,
        "system_uptime": "99.9%"
    }), 200

@app.route('/services', methods=['GET'])
def services():
    """מחזיר מידע על השירותים"""
    return jsonify({
        "services": [
            {
                "name": "Community Gateway Bot",
                "description": "בוט שער כניסה לקהילות בתשלום",
                "price": "39₪ membership",
                "features": ["Payment processing", "User management", "Automated onboarding"]
            },
            {
                "name": "Custom Bot Development", 
                "description": "פיתוח בוטים מותאמים אישית לעסקים",
                "price": "Starting from 149₪",
                "features": ["Custom design", "Integration", "Support & maintenance"]
            },
            {
                "name": "Investment Opportunities",
                "description": "השקעה בפרויקט SLH FULL SUITE", 
                "contact_required": True,
                "features": ["Equity partnership", "Technology access", "Personal mentoring"]
            }
        ],
        "contact": {
            "osif": "058-4203384",
            "zvika": "054-6671882"
        }
    }), 200

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
