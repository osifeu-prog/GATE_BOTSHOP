import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from telegram.ext import Dispatcher

from config import BOT_TOKEN, WEBHOOK_URL, ADMIN_PASSWORD, ADMIN_USER_ID
from database.models import init_db
from database.operations import get_user_stats, get_recent_activity, get_pending_payments, get_all_groups, approve_user_payment
from handlers import setup_handlers
from utils.helpers import bot, send_admin_alert

# הגדרת הלוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/error.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# אתחול מסד נתונים
init_db()

# אתחול dispatcher
dispatcher = Dispatcher(bot, None, workers=4)

# הגדרת handlers
setup_handlers(dispatcher)

# --- Flask routes ---
@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "service": "SLH Community Gateway Bot - Premium Edition", 
        "version": "5.6",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "SLH Coin cryptocurrency ecosystem",
            "Advanced community gateway with smart payments",
            "Elite bot development services", 
            "5-generation network marketing",
            "NFT marketplace integration",
            "Multi-language support (HE/EN/RU/AR)",
            "Real-time analytics dashboard",
            "Advanced admin panel",
            "Payment tracking system",
            "User activity monitoring",
            "Referral tracking system", 
            "Free access after 39 referrals",
            "Enhanced group management system",
            "Admin groupid/chaid commands",
            "Payment confirmation to groups",
            "SLH Token rewards system",
            "Automatic group registration",
            "Group activity tracking"
        ]
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """נקודת הכניסה עבור עדכונים מטלגרם"""
    if request.method == 'POST':
        try:
            from telegram import Update
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
            return jsonify({"status": "Webhook set successfully", "url": WEBHOOK_URL})
        else:
            return jsonify({"status": "Failed to set webhook"}), 500
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"status": f"Error: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# --- פאנל ניהול Flask ---
@app.route('/admin')
def admin_panel():
    """פאנל ניהול מתקדם"""
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return "❌ גישה נדחתה - סיסמה לא תקינה", 401
    
    stats = get_user_stats()
    recent_activity = get_recent_activity(20)
    pending_payments = get_pending_payments()
    groups = get_all_groups()
    
    admin_html = """
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SLH - פאנל ניהול מתקדם</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden; }
        .header { background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: white; padding: 30px; text-align: center; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; padding: 20px; }
        .stat-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; border-left: 5px solid #3498db; transition: transform 0.3s ease; }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-number { font-size: 2.5em; font-weight: bold; color: #2c3e50; margin: 10px 0; }
        .stat-label { color: #7f8c8d; font-size: 1.1em; }
        .section { padding: 20px; margin: 20px; background: #f8f9fa; border-radius: 12px; }
        .section-title { color: #2c3e50; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #3498db; }
        .activity-item, .payment-item, .group-item { padding: 15px; border-bottom: 1px solid #e9ecef; display: flex; justify-content: space-between; align-items: center; }
        .activity-item:last-child, .payment-item:last-child, .group-item:last-child { border-bottom: none; }
        .user-info { font-weight: bold; color: #2c3e50; }
        .action-info { color: #7f8c8d; }
        .time-info { color: #95a5a6; font-size: 0.9em; }
        .payment-actions { display: flex; gap: 10px; }
        .btn { padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; font-size: 0.9em; }
        .btn-approve { background: #27ae60; color: white; }
        .btn-reject { background: #e74c3c; color: white; }
        .btn-refresh { background: #3498db; color: white; }
        .controls { text-align: center; padding: 20px; }
        .pending-badge { background: #e74c3c; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SLH - פאנל ניהול מתקדם</h1>
            <p>ניטור וניהול מלא של פעילות הבוט - נתונים בזמן אמת</p>
        </div>
        
        <div class="controls">
            <button class="btn btn-refresh" onclick="location.reload()">🔄 רענן נתונים</button>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">משתמשים רשומים</div>
                <div class="stat-number">{{ stats.total_users }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">משתמשים פעילים היום</div>
                <div class="stat-number">{{ stats.active_today }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">תשלומים מאומתים</div>
                <div class="stat-number">{{ stats.verified_payments }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">תשלומים ממתינים</div>
                <div class="stat-number">{{ stats.pending_payments }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">פעולות היום</div>
                <div class="stat-number">{{ stats.actions_today }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">קבוצות רשומות</div>
                <div class="stat-number">{{ groups|length }}</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">
                💰 תשלומים ממתינים לאישור
                {% if pending_payments %}<span class="pending-badge">{{ pending_payments|length }}</span>{% endif %}
            </h2>
            <div id="paymentList">
                {% if pending_payments %}
                    {% for payment in pending_payments %}
                    <div class="payment-item">
                        <div>
                            <div class="user-info">{{ payment[2] }} (@{{ payment[3] or 'ללא' }})</div>
                            <div class="action-info">סוג: {{ payment[4] }} | סכום: {{ payment[5] }}₪</div>
                            {% if payment[6] %}
                            <div class="action-info">פרטים: {{ payment[6] }}</div>
                            {% endif %}
                        </div>
                        <div>
                            <div class="time-info">{{ payment[7] }}</div>
                            <div class="payment-actions">
                                <button class="btn btn-approve" onclick="approvePayment({{ payment[0] }}, {{ payment[1] }})">✅ אישור</button>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="text-align: center; color: #7f8c8d; padding: 20px;">אין תשלומים ממתינים לאישור</p>
                {% endif %}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">📁 קבוצות רשומות ({{ groups|length }})</h2>
            <div id="groupsList">
                {% if groups %}
                    {% for group in groups %}
                    <div class="group-item">
                        <div>
                            <div class="user-info">{{ group[1] }}</div>
                            <div class="action-info">ID: {{ group[0] }} | Type: {{ group[2] }}</div>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="text-align: center; color: #7f8c8d; padding: 20px;">אין קבוצות רשומות במערכת</p>
                {% endif %}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">📈 פעילות אחרונה</h2>
            <div id="activityList">
                {% for activity in recent_activity %}
                <div class="activity-item">
                    <div>
                        <span class="user-info">{{ activity[0] }} ({{ activity[1] or 'ללא' }})</span>
                        <span class="action-info"> - {{ activity[2] }}</span>
                        {% if activity[3] %}
                        <div class="action-info" style="color: #95a5a6; font-size: 0.9em;">{{ activity[3] }}</div>
                        {% endif %}
                    </div>
                    <div class="time-info">{{ activity[4] }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        function approvePayment(paymentId, userId) {
            if (confirm('האם לאשר תשלום זה?')) {
                fetch('/admin/approve_payment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        payment_id: paymentId,
                        user_id: userId,
                        password: '{{ request.args.get("password") }}'
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('✅ התשלום אושר! המשתמש קיבל הודעה ו-SLH 1.');
                        location.reload();
                    } else {
                        alert('❌ שגיאה באישור התשלום: ' + data.error);
                    }
                })
                .catch(error => alert('❌ שגיאה: ' + error));
            }
        }
        
        // עדכון אוטומטי כל 30 שניות
        setInterval(() => location.reload(), 30000);
    </script>
</body>
</html>
    """
    
    return render_template_string(admin_html, stats=stats, recent_activity=recent_activity, 
                               pending_payments=pending_payments, groups=groups)

@app.route('/admin/approve_payment', methods=['POST'])
def approve_payment():
    """מאשר תשלום ומשלח הודעה למשתמש"""
    try:
        data = request.get_json()
        password = data.get('password')
        user_id = data.get('user_id')
        
        if password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'סיסמה לא תקינה'})
        
        # אישור התשלום במסד הנתונים והוספת SLH
        success, slh_reward = approve_user_payment(user_id, 'admin')
        
        if success:
            # שליחת הודעה למשתמש
            try:
                from config import MAIN_GROUP_LINK
                user_info = f"🎉 **מזל טוב! התשלום שלך אושר!**\n\n"
                user_info += f"**💎 בונוס SLH:** קיבלת **{slh_reward} SLH** בשווי {slh_reward * 444}₪!\n\n"
                user_info += f"**🚀 קישור ההצטרפות לקהילה:**\n{MAIN_GROUP_LINK}\n\n"
                user_info += f"**🔗 הלינק האישי שלך לשיתוף:**\n`https://t.me/Buy_My_Shop_bot?start={user_id}`\n\n"
                user_info += f"**📊 מה תקבל:**\n• גישה מלאה לקהילת VIP\n• {slh_reward} SLH בשווי {slh_reward * 444}₪\n• מערכת הכנסות פסיביות\n• תמיכה טכנית 24/7\n\n**💫 ברוך הבא למהפכה!**"
                
                bot.send_message(chat_id=user_id, text=user_info, parse_mode='Markdown')
                logger.info(f"Payment approved for user {user_id}, SLH rewarded: {slh_reward}")
            except Exception as e:
                logger.error(f"Error sending approval message to user {user_id}: {e}")
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'שגיאה באישור התשלום'})
            
    except Exception as e:
        logger.error(f"Error in approve_payment: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/dashboard')
def dashboard():
    """ממשק ניהול בעברית"""
    return """
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <title>SLH - ממשק ניהול</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .admin-link { background: #ff6b6b; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none; display: inline-block; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SLH - ממשק ניהול מערכת</h1>
            <p>ניהול וניטור כל הפרויקטים במערכת אחת</p>
            <a href="/admin?password=slh2025" class="admin-link">🔐 פאנל ניהול מתקדם</a>
        </div>
        
        <div class="stats">
            <div class="stat-card"><div class="stat-number" id="userCount">0</div><div>משתמשים רשומים</div></div>
            <div class="stat-card"><div class="stat-number">4</div><div>פרויקטים פעילים</div></div>
            <div class="stat-card"><div class="stat-number">444₪</div><div>ערך SLH Coin</div></div>
            <div class="stat-card"><div class="stat-number" id="responseTime">2.3s</div><div>זמן תגובה ממוצע</div></div>
        </div>
    </div>
    <script>
        setInterval(() => {
            document.getElementById('userCount').textContent = Math.floor(500 + Math.random() * 100);
            document.getElementById('responseTime').textContent = (1.5 + Math.random() * 1).toFixed(1) + 's';
        }, 3000);
    </script>
</body>
</html>
"""

def initialize_bot():
    """אתחול הבוט"""
    try:
        # קביעת webhook
        bot.set_webhook(WEBHOOK_URL)
        logger.info(f"✅ Webhook set: {WEBHOOK_URL}")
        
        # הודעת אתחול
        send_admin_alert("🚀 **בוט SLH הותחל בהצלחה!**\nגרסה: 5.6 - עם מערכת ניהול קבוצות\nפקודות: /admin, /groupid\nפאנל: /admin?password=slh2025")
        
    except Exception as e:
        logger.error(f"Bot initialization error: {e}")

# אתחול
initialize_bot()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
