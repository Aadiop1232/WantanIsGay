from datetime import datetime
from db import get_user, add_user

def send_account_info(bot, update):
    # If this is a CallbackQuery:
    if isinstance(update, telebot.types.CallbackQuery):
        chat_id = update.message.chat.id
        user_id = update.from_user.id
    # If this is a normal Message:
    elif isinstance(update, telebot.types.Message):
        chat_id = update.chat.id
        user_id = update.from_user.id
    else:
        # Fallback if something else
        return  # or handle differently

    user = get_user(str(user_id))
    if not user:
        # Create the user if not found
        add_user(str(user_id), update.from_user.username or update.from_user.first_name,
                 datetime.now().strftime("%Y-%m-%d"))
        user = get_user(str(user_id))

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
