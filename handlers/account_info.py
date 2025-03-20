import telebot
from datetime import datetime
from db import get_user, add_user

def send_account_info(bot, update):
    """
    Sends the user's account info.
    Works for both Message and CallbackQuery updates.
    """
    # Distinguish between a normal Message vs. a CallbackQuery
    if isinstance(update, telebot.types.Message):
        # update is a Message
        chat_id = update.chat.id
        user_id = str(update.from_user.id)
    elif isinstance(update, telebot.types.CallbackQuery):
        # update is a CallbackQuery
        chat_id = update.message.chat.id
        user_id = str(update.from_user.id)
    else:
        # Unknown update type
        return

    user = get_user(user_id)
    if not user:
        # Create user if not found
        add_user(
            user_id,
            update.from_user.username or update.from_user.first_name,
            datetime.now().strftime("%Y-%m-%d")
        )
        user = get_user(user_id)

    # Build the fancy UI box
    text = (
        "╭━━━✦❘༻👤 ACCOUNT INFO ༺❘✦━━━╮\n"
        "┃\n"
        f"┃ ✧ Username: {user.get('username')}\n"
        f"┃ ✧ User ID: {user_id}\n"
        f"┃ ✧ Join Date: {user.get('join_date')}\n"
        f"┃ ✧ Balance: {user.get('points')} pts\n"
        f"┃ ✧ Total Referrals: {user.get('referrals')}\n"
        "┃\n"
        "╰━━━━━━━✦✧✦━━━━━━━╯"
    )

    bot.send_message(chat_id, text, parse_mode="HTML")
