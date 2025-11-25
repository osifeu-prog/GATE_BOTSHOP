
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters

def setup_handlers(dispatcher):
    """מגדיר את כל ה-handlers"""
    from .user_handlers import start, language_handler, handle_payment_proof
    from .admin_handlers import admin, chatid, groupid, chaid, broadcast, group_broadcast, refresh_all_groups
    from .group_handlers import handle_group_add, handle_group_activity
    
    # handlers בסיסיים
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("admin", admin))
    dispatcher.add_handler(CommandHandler("chatid", chatid))
    dispatcher.add_handler(CommandHandler("groupid", groupid))
    dispatcher.add_handler(CommandHandler("chaid", chaid))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("group_broadcast", group_broadcast))
    dispatcher.add_handler(CommandHandler("refresh_groups", refresh_all_groups))
    
    # handlers לכפתורים
    from .user_handlers import button_handler
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    
    # handlers להודעות
    dispatcher.add_handler(MessageHandler(Filters.photo & Filters.chat_type.private, handle_payment_proof))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command & Filters.chat_type.private, handle_payment_proof))
    
    # handlers לקבוצות
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, handle_group_add))
    dispatcher.add_handler(MessageHandler(Filters.chat_type.groups & Filters.all, handle_group_activity))
