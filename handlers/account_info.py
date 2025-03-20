from db import get_user, add_user
from datetime import datetime

def send_account_info(bot, update):
    if hasattr(update, "message") and update.message:
        # It's a normal message
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id
    elif hasattr(update, "data"):
        # It's a callback
        chat_id = update.message.chat.id
        user_id = update.from_user.id
    else:
        # Fallback
        chat_id = update.chat.id
        user_id = update.from_user.id

    user = get_user(str(user_id))
    # Now show that user's info
    text = (
        "╭━━━✦❘༻👤 ACCOUNT INFO ༺❘✦━━━╮\n"
        f"┃ ✧ Username: {user.get('username')}\n"
        f"┃ ✧ User ID: {user.get('telegram_id')}\n"
        f"┃ ✧ Join Date: {user.get('join_date')}\n"
        f"┃ ✧ Balance: {user.get('points')} pts\n"
        f"┃ ✧ Total Referrals: {user.get('referrals')}\n"
        "╰━━━━━━━✦✧✦━━━━━━━╯"
    )
    bot.send_message(chat_id, text, parse_mode="HTML")
