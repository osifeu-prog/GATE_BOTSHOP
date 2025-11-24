from flask import render_template_string, request, jsonify
from config import ADMIN_PASSWORD
from database.operations import get_user_stats, get_recent_activity, get_pending_payments, get_all_groups, approve_user_payment
from utils.helpers import bot

def setup_admin_routes(app):
    """מגדיר את ה-routes של פאנל הניהול"""
    
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
        
        # כאן יש להכניס את ה-HTML של פאנל הניהול
        # [קוד HTML מהקובץ המקורי]
        
        return render_template_string(admin_html, stats=stats, recent_activity=recent_activity, 
                                   pending_payments=pending_payments, groups=groups)

    @app.route('/admin/approve_payment', methods=['POST'])
    def approve_payment():
        """מאשר תשלום ומשלח הודעה למשתמש"""
        try:
            data = request.get_json()
            password = data.get('password')
            payment_id = data.get('payment_id')
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
                    
                    bot.send_message(
                        chat_id=user_id,
                        text=user_info,
                        parse_mode='Markdown'
                    )
                    
                    logger.info(f"Payment approved for user {user_id}, SLH rewarded: {slh_reward}")
                    
                except Exception as e:
                    logger.error(f"Error sending approval message to user {user_id}: {e}")
                
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'שגיאה באישור התשלום'})
                
        except Exception as e:
            logger.error(f"Error in approve_payment: {e}")
            return jsonify({'success': False, 'error': str(e)})
