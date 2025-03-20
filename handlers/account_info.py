from datetime import datetime
from db import get_user, add_user

def send_account_info(bot, update):
    """
    Sends the account info for the user who triggered this command or callback.
    Retains the original logic: if it's a callback, we use update.from_user
    and update.message.chat; otherwise, we use update.from_user and update.chat.
    """
    # Distinguish CallbackQuery vs. normal Message
    if hasattr(update, "data"):
        # It's a callback query
        user_obj = update.from_user
        chat_id = update.message.chat.id
    else:
        # It's a normal message
        user_obj = update.from_user
        chat_id = update.chat.id

    telegram_id = str(user_obj.id)
    user = get_user(telegram_id)
    if not user:
        # Create user if not found
        add_user(
            telegram_id,
            user_obj.username or user_obj.first_name,
            datetime.now().strftime("%Y-%m-%d")
        )
        user = get_user(telegram_id)

    # Build the fancy UI box
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
