import logging
from telegram import Update
from telegram.ext import CallbackContext
from telegram.error import NetworkError

from config import ADMIN_USER_ID
from database.operations import (
    log_user_activity, get_user_language, set_user_language, 
    log_payment, get_user_slh_balance, get_user_referral_count
)
from keyboards.menus import (
    get_main_keyboard, get_language_keyboard, get_payment_keyboard,
    get_back_keyboard, get_network_marketing_keyboard, get_slh_balance_keyboard
)
from translations.texts import get_translation
from utils.helpers import safe_edit_message, safe_send_message, send_admin_alert, send_payment_confirmation

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """מטפל בפקודה /start - רב-לשוני"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        # רישום פעילות
        log_user_activity(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name or "",
            "start",
            f"User ID: {user.id}, Language: {user.language_code}"
        )

        # אם זו קבוצה
        if update.message and update.message.chat.type in ['group', 'supergroup']:
            chat = update.message.chat
            from database.operations import save_group
            save_group(chat.id, chat.title, chat.type)
            
            if update.message.text and '/start' in update.message.text:
                update.message.reply_text(
                    "🤖 הבוט פעיל בקבוצה זו!\n\n"
                    f"🆔 **ID הקבוצה:** `{chat.id}`\n"
                    "👑 **לאדמין:** השתמש ב-`/groupid` או `/chaid` כדי לראות את כל הקבוצות.\n"
                    "👤 **למשתמשים:** שלחו /start בפרטי כדי להתחיל."
                )
            return

        # שליחת תמונה עם הודעת ברוך הבא
        welcome_image_url = "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2032&q=80"
        
        try:
            if update.message:
                update.message.reply_photo(
                    photo=welcome_image_url,
                    caption=get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard(user.id)
                )
            else:
                update.callback_query.message.reply_photo(
                    photo=welcome_image_url,
                    caption=get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard(user.id)
                )
            return
        except Exception as e:
            logger.warning(f"Could not send welcome image: {e}")

        # אם לא הצליחה התמונה, שולח טקסט בלבד
        if update.message:
            update.message.reply_text(
                get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                reply_markup=get_main_keyboard(user.id),
                parse_mode='Markdown'
            )
        else:
            update.callback_query.message.reply_text(
                get_translation(get_user_language(user.id), 'welcome', name=user.first_name),
                reply_markup=get_main_keyboard(user.id),
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        if update.message:
            update.message.reply_text("❌ אירעה שגיאה. אנא נסה שוב.")

def language_handler(update: Update, context: CallbackContext) -> None:
    """מטפל בבחירת שפה"""
    query = update.callback_query
    
    try:
        query.answer()
    except NetworkError:
        pass  # Ignore network errors for answer
    
    user_id = query.from_user.id
    lang_code = query.data.replace('lang_', '')
    
    # שמירת השפה במסד נתונים
    set_user_language(user_id, lang_code)
    
    # הודעת אישור לפי שפה
    confirmation_messages = {
        'he': "✅ שפת הממשק שונתה לעברית",
        'en': "✅ Interface language changed to English", 
        'ru': "✅ Язык интерфейса изменен на русский",
        'ar': "✅ تم تغيير لغة الواجهة إلى العربية"
    }
    
    query.edit_message_text(
        text=confirmation_messages.get(lang_code, "Language changed"),
        reply_markup=get_main_keyboard(user_id)
    )

def button_handler(update: Update, context: CallbackContext) -> None:
    """מטפל בלחיצות על כפתורים - רב-לשוני"""
    query = update.callback_query
    
    try:
        query.answer()
    except Exception as e:
        logger.warning(f"Could not answer callback query: {e}")

    try:
        user = query.from_user
        user_id = user.id
        lang = get_user_language(user_id)
        
        # רישום פעילות
        log_user_activity(user.id, user.username, user.first_name, user.last_name or "", f"button_{query.data}")

        if query.data == 'change_language':
            language_text = "🌐 **בחר שפה / Choose language**\n\nSelect your preferred language:"
            safe_edit_message(query, language_text, get_language_keyboard())
            return

        elif query.data.startswith('lang_'):
            language_handler(update, context)
            return

        elif query.data == 'ecosystem_explanation':
            ecosystem_texts = {
                'he': """
**🌟 סלה ללא גבולות - האקוסיסטם הטכנולוגי השלם**

**🏗️ המבנה הייחודי שלנו:**

**💎 ליבת המערכת - מטבע SLH**
אנחנו יצרנו מטבע קריפטו ייחודי **SLH** עם ערך אמיתי וצמיחה מתוכננת:
• **ערך נוכחי:** 444₪ ל-SLH 1
• **חלוקה למצטרפים:** כל member מקבל SLH 1 (39₪ מידית + השאר בהדרגה)
• **utility אמיתי:** משמש לתשלומים בכל הפלטפורמות שלנו
• **צמיחה אורגנית:** הערך עולה עם גידול הקהילה

**🚀 4 רכיבי הליבה:**

**1. 🤖 Botshop - פלטפורמת הבוטים**
• בוטים אוטומטיים לניהול קהילות
• מערכות תשלום ואימות
• אינטגרציה עם כל המערכות

**2. 💰 SLH Coin - המערכת הפיננסית**
• מטבע utility עם שימושים אמיתיים
• חוזים חכמים אוטומטיים
• מסחר וארנקים דיגיטליים

**3. 🎨 NFT & Digital Assets**
• שוק NFT לנכסים דיגיטליים
• פלטפורמת מסחר מתקדמת
• קהילת יוצרים ומשקיעים

**4. 📈 Network Marketing**
• שיווק רשתי ל-5 דורות
• הכנסות פסיביות אוטומטיות
• מערכת דוחות מתקדמת
                """,
                'en': """
**🌟 Sela Without Borders - The Complete Technological Ecosystem**

**🏗️ Our Unique Structure:**

**💎 System Core - SLH Coin**
We created a unique cryptocurrency **SLH** with real value and planned growth:
• **Current value:** 444₪ per SLH 1
• **Distribution to members:** Every member receives SLH 1 (39₪ immediately + the rest gradually)
• **Real utility:** Used for payments across all our platforms
• **Organic growth:** Value increases with community growth

**🚀 4 Core Components:**

**1. 🤖 Botshop - Bot Platform**
• Automated bots for community management
• Payment and verification systems
• Integration with all systems

**2. 💰 SLH Coin - Financial System**
• Utility coin with real uses
• Automatic smart contracts
• Trading and digital wallets

**3. 🎨 NFT & Digital Assets**
• NFT market for digital assets
• Advanced trading platform
• Community of creators and investors

**4. 📈 Network Marketing**
• 5-generation network marketing
• Automatic passive income
• Advanced reporting system
                """
            }
            safe_edit_message(query, ecosystem_texts.get(lang, ecosystem_texts['he']), get_back_keyboard(user_id))

        elif query.data == 'join_community':
            join_texts = {
                'he': """
**💎 הצטרפות לקהילת סלה ללא גבולות**

**🎯 מה באמת קונה ה-39₪ שלך?**

זו לא "עלות" - זו **השקעה בנכס דיגיטלי** שמניב הכנסות!

**💼 חבילת הערך המלאה:**

**1. 💰 נכס דיגיטלי - SLH Coin**
• **SLH 1** בשווי 444₪ - 39₪ מידית, השאר בהדרגה
• מטבע utility עם שימושים אמיתיים
• פוטנציאל צמיחה עם גידול הקהילה

**2. 🎯 לינק שיתוף אישי**
• מניב 10% מכל מצטרף חדש דרך הלינק שלך
• הכנסה פסיבית מ-5 דורות
• מערכת דוחות ואימות אוטומטית

**3. 🌐 גישה לכל המערכות**
• פלטפורמת הבוטים המתקדמת
• קהילת VIP עם אנשי עסקים
• הדרכות והכשרות מקצועיות
• תמיכה טכנית 24/7

**4. 🚀 הזדמנויות עסקיות**
• שירותי פיתוח בוטים (בתשלום נוסף)
• השקעה בפרויקטים נוספים
• שותפויות אסטרטגיות
• נטרוקינג איכותי
                """,
                'en': """
**💎 Joining Sela Without Borders Community**

**🎯 What does your 39₪ actually buy?**

This is not a "cost" - it's an **investment in a digital asset** that generates income!

**💼 Complete Value Package:**

**1. 💰 Digital Asset - SLH Coin**
• **SLH 1** worth 444₪ - 39₪ immediately, the rest gradually
• Utility coin with real uses
• Growth potential with community growth

**2. 🎯 Personal Sharing Link**
• Generates 10% from every new member
• Passive income from 5 generations
• Automated reporting and verification system

**3. 🌐 Access to All Systems**
• Advanced bot platform
• VIP community with business people
• Professional training and guidance
• 24/7 technical support

**4. 🚀 Business Opportunities**
• Bot development services (additional payment)
• Investment in additional projects
• Strategic partnerships
• Quality networking
                """
            }
            safe_edit_message(query, join_texts.get(lang, join_texts['he']), get_payment_keyboard(user_id))

        elif query.data in ['payment_bank', 'payment_ton', 'payment_crypto']:
            payment_details = {
                'payment_bank': get_translation(lang, 'bank_details'),
                'payment_ton': get_translation(lang, 'ton_details'),
                'payment_crypto': get_translation(lang, 'crypto_details')
            }
            safe_edit_message(query, payment_details[query.data], get_payment_keyboard(user_id))

        elif query.data == 'payment_sent':
            payment_instructions = {
                'he': """
**✅ שלחתי תשלום - מה עכשיו?**

🚀 **מעולה! עכשיו נשאר רק לשלוח לנו את אישור התשלום:**

1. **אם שילמת בהעברה בנקאית:**
   • שלח צילום מסך של ההעברה
   • או הקלד את פרטי ההעברה

2. **אם שילמת בקריפטו:**
   • שלח צילום מסך של העסקה
   • או הקלד את hash העסקה

📸 **שלח עכשיו את אישור התשלום כאן בצ'אט**
ונחזור אליך עם קישור ההצטרפות תוך 24 שעות!

💎 **בונוס מיוחד:** כל תשלום מזכה אותך ב-**SLH 1** בשווי 444₪!
                """,
                'en': """
**✅ I Sent Payment - What Now?**

🚀 **Great! Now just send us the payment confirmation:**

1. **If you paid by bank transfer:**
   • Send a screenshot of the transfer
   • Or type the transfer details

2. **If you paid with crypto:**
   • Send a screenshot of the transaction
   • Or type the transaction hash

📸 **Send the payment confirmation now in this chat**
We'll get back to you with the joining link within 24 hours!

💎 **Special bonus:** Every payment earns you **SLH 1** worth 444₪!
                """
            }
            safe_edit_message(query, payment_instructions.get(lang, payment_instructions['he']), get_payment_keyboard(user_id))

        elif query.data == 'slh_balance':
            slh_balance = get_user_slh_balance(user_id)
            balance_text = {
                'he': f"""
**💎 יתרת SLH שלך**

**🪙 כמות SLH:** {slh_balance}
**💰 שווי נוכחי:** {slh_balance * 444}₪
**🚀 סטטוס:** {'פעיל' if slh_balance > 0 else 'ממתין להצטרפות'}

**📈 מה אפשר לעשות עם SLH?**
• השתתפות בסטייקינג (בקרוב)
• תשלומים בתוך המערכת
• מסחר וניתוח (בפיתוח)
• הצבעות קהילתיות (עתידי)

**💡 טיפ:** כל מצטרף חדש דרך הלינק שלך מזכה אותך בעוד SLH!
                """,
                'en': f"""
**💎 Your SLH Balance**

**🪙 SLH Amount:** {slh_balance}
**💰 Current Value:** {slh_balance * 444}₪
**🚀 Status:** {'Active' if slh_balance > 0 else 'Pending joining'}

**📈 What can you do with SLH?**
• Participate in staking (coming soon)
• Payments within the system
• Trading and analysis (in development)
• Community voting (future)

**💡 Tip:** Every new member through your link earns you more SLH!
                """
            }
            safe_edit_message(query, balance_text.get(lang, balance_text['he']), get_slh_balance_keyboard(user_id))

        elif query.data == 'network_marketing':
            network_texts = {
                'he': """
**📊 שיווק רשתי - 5 דורות**

**💡 איך עובד המודל?**

**🎯 הלינק האישי שלך - מכונת ההכנסות האוטומטית**

לאחר ההצטרפות, תקבל **לינק שיתוף אישי ייחודי** שמזוהה רק איתך. כל פעילות שמתבצעת דרך הלינק הזה - מייצרת לך הכנסה אוטומטית!

**💰 מודל ההכנסות:**

**1. 💰 עמלות ישירות**
• **10%** מכל רכישה של מצטרף חדש דרך הלינק שלך
• תשלום אוטומטי ומיידי ב-SLH
• אין הגבלה על מספר המצטרפים

**2. 📈 עמלות דורות (5 דורות)**
• **דור 1:** 10% מהמצטרפים הישירים שלך
• **דור 2:** 5% מהמצטרפים שלהם
• **דור 3:** 3% מהמצטרפים הבאים
• **דור 4:** 2% מהדור הרביעי
• **דור 5:** 1% מהדור החמישי

**3. 🎯 יעד: 39 רפראלים לגישה חינם**
• לאחר 39 מצטרפים - גישה מלאה בחינם!
• הכנסה פסיבית לכל החיים
• צמיחה אקספוננציאלית
                """,
                'en': """
**📊 Network Marketing - 5 Generations**

**💡 How does the model work?**

**🎯 Your Personal Link - Automatic Income Machine**

After joining, you'll receive a **unique personal sharing link** that's identified only with you. Any activity through this link generates automatic income for you!

**💰 Income Model:**

**1. 💰 Direct Commissions**
• **10%** from every new member purchase through your link
• Automatic and immediate payment in SLH
• No limit on number of members

**2. 📈 Generation Commissions (5 Generations)**
• **Generation 1:** 10% from your direct members
• **Generation 2:** 5% from their members
• **Generation 3:** 3% from next members
• **Generation 4:** 2% from fourth generation
• **Generation 5:** 1% from fifth generation

**3. 🎯 Goal: 39 Referrals for Free Access**
• After 39 members - full access for free!
• Lifetime passive income
• Exponential growth
                """
            }
            safe_edit_message(query, network_texts.get(lang, network_texts['he']), get_network_marketing_keyboard(user_id))

        elif query.data == 'personal_link':
            user_ref_count = get_user_referral_count(user_id)
            personal_link_texts = {
                'he': f"""
**🎯 הלינק האישי שלך**

**📊 הסטטוס שלך:**
• **רפראלים:** {user_ref_count}/39
• **נותרו:** {39 - user_ref_count} להשלמה
• **הכנסות מצטברות:** {user_ref_count * 3.9:.2f}₪
• **SLH שנצבר:** {user_ref_count * 0.1:.1f}

**🔗 הלינק האישי שלך:**
`https://t.me/Buy_My_Shop_bot?start={user_id}`

**💡 טיפים לשיתוף:**
• שתף בפייסבוק, אינסטגרם, טיקטוק
• הסבר על ההזדמנות הכלכלית
• שתף בקבוצות טלגרם ווואטסאפ

**🎁 לאחר 39 רפראלים תקבל:**
• גישה מלאה בחינם!
• מעמד VIP בקהילה
• הטבות נוספות
                """,
                'en': f"""
**🎯 Your Personal Link**

**📊 Your Status:**
• **Referrals:** {user_ref_count}/39
• **Remaining:** {39 - user_ref_count} to complete
• **Cumulative earnings:** {user_ref_count * 3.9:.2f}₪
• **Accumulated SLH:** {user_ref_count * 0.1:.1f}

**🔗 Your Personal Link:**
`https://t.me/Buy_My_Shop_bot?start={user_id}`

**💡 Sharing Tips:**
• Share on Facebook, Instagram, TikTok
• Explain the economic opportunity
• Share in Telegram and WhatsApp groups

**🎁 After 39 referrals you'll get:**
• Full access for free!
• VIP status in community
• Additional benefits
                """
            }
            safe_edit_message(query, personal_link_texts.get(lang, personal_link_texts['he']), get_network_marketing_keyboard(user_id))

        elif query.data == 'back_to_main':
            welcome_back_text = get_translation(lang, 'welcome_back')
            safe_edit_message(query, welcome_back_text, get_main_keyboard(user_id))

        else:
            # ברירת מחדל
            safe_edit_message(query, get_translation(lang, 'welcome_back'), get_main_keyboard(user_id))
            
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        try:
            safe_send_message(user.id, "❌ אירעה שגיאה. נסה שוב.", get_main_keyboard(user.id))
        except:
            pass

def handle_payment_proof(update: Update, context: CallbackContext) -> None:
    """מטפל בשליחת אישור תשלום מהמשתמש"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        lang = get_user_language(user.id)

        # רישום פעילות
        log_user_activity(user.id, user.username, user.first_name, user.last_name or "", "payment_proof_sent")

        success_messages = {
            'he': """
✅ **תודה רבה! אישור התשלום התקבל ונשלח לאימות.**

🚀 **נחזור אליך עם קישור ההצטרפות תוך 24 שעות!**

💎 **בונוס SLH:** קיבלת **SLH 1** בשווי 444₪!

📧 **מה תקבל:**
• קישור להצטרפות לקהילת VIP
• הלינק האישי שלך לשיתוף והכנסות  
• 39₪ ב-SLH (מתוך ה-444₪)
• שיחת ייעוץ אישית
• כל הבונוסים

💎 **בינתיים, מוזמן לבדוק את שאר האפשרויות!**
            """,
            'en': """
✅ **Thank you! Payment confirmation received and sent for verification.**

🚀 **We'll get back to you with the joining link within 24 hours!**

💎 **SLH Bonus:** You received **SLH 1** worth 444₪!

📧 **What you'll receive:**
• Link to join VIP community
• Your personal sharing link for earnings
• 39₪ in SLH (out of 444₪)
• Personal consultation call
• All bonuses

💎 **Meanwhile, feel free to check out other options!**
            """
        }

        # בדיקה אם המשתמש שלח תמונה
        if update.message.photo:
            photo_file = update.message.photo[-1].get_file()
            
            # רישום תשלום
            log_payment(user.id, "העברה בנקאית", 39, "אישור תמונה")
            
            # שליחת התראה
            send_payment_confirmation(
                user_id=user.id,
                user_name=f"{user.first_name} {user.last_name or ''}",
                payment_type="העברה בנקאית",
                amount=39,
                proof_text="אישור תמונה",
                image_file_id=photo_file.file_id
            )
            
            update.message.reply_text(
                success_messages.get(lang, success_messages['he']),
                reply_markup=get_main_keyboard(user.id),
                parse_mode='Markdown'
            )

        # בדיקה אם המשתמש שלח טקסט
        elif update.message.text and not update.message.text.startswith('/'):
            proof_text = update.message.text
            
            # רישום תשלום
            log_payment(user.id, "העברה בנקאית", 39, proof_text)
            
            # שליחת התראה
            send_payment_confirmation(
                user_id=user.id,
                user_name=f"{user.first_name} {user.last_name or ''}",
                payment_type="העברה בנקאית", 
                amount=39,
                proof_text=proof_text
            )
            
            update.message.reply_text(
                success_messages.get(lang, success_messages['he']),
                reply_markup=get_main_keyboard(user.id),
                parse_mode='Markdown'
            )

        else:
            instruction_messages = {
                'he': "📸 **נא שלח צילום מסך של ההעברה או פרטי התשלום בטקסט.**",
                'en': "📸 **Please send a screenshot of the transfer or payment details in text.**"
            }
            update.message.reply_text(
                instruction_messages.get(lang, instruction_messages['he']),
                reply_markup=get_payment_keyboard(user.id),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in handle_payment_proof: {e}")
        lang = get_user_language(update.effective_user.id)
        error_messages = {
            'he': "❌ אירעה שגיאה בעיבוד האישור. אנא נסה שוב או צור קשר.",
            'en': "❌ An error occurred processing the confirmation. Please try again or contact us."
        }
        update.message.reply_text(
            error_messages.get(lang, error_messages['he']),
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
