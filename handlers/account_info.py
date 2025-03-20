from datetime import datetime
from db import get_user, add_user

def send_account_info(bot, update):
    """
    Sends account info for the user who triggered this command or callback.
    Handles both normal messages and callback queries.
    """
    # Distinguish between a normal Message and a CallbackQuery
    if hasattr(update, "message") and update.message:
        # It's a normal message
        chat_id = update.message.chat.id
        user_id = str(update.message.from_user.id)
        username = update.message.from_user.username or update.message.from_user.first_name
    elif hasattr(update, "data"):
        # It's a callback query
        chat_id = update.message.chat.id
        user_id = str(update.from_user.id)
        username = update.from_user.username or update.from_user.first_name
    else:
        # Fallback if neither
        chat_id = update.chat.id
        user_id = str(update.from_user.id)
        username = update.from_user.username or update.from_user.first_name

    # Fetch the user's record from the DB
    user = get_user(user_id)
    # If user not found, create one
    if not user:
        add_user(
            user_id,
            username,
            datetime.now().strftime("%Y-%m-%d")
        )
        user = get_user(user_id)

    # Build fancy text
    text = (
        "╭━━━✦❘༻👤 ACCOUNT INFO ༺❘✦━━━╮\n"
        f"┃ ✧ Username: {user.get('username')}\n"
        f"┃ ✧ User ID: {user.get('telegram_id')}\n"
        f"┃ ✧ Join Date: {user.get('join_date')}\n"
        f"┃ ✧ Balance: {user.get('points')} pts\n"
        f"┃ ✧ Total Referrals: {user.get('referrals')}\n"
        "╰━━━━━━━✦✧✦━━━━━━━╯"
    )

    # Send the message
    bot.send_message(chat_id, text, parse_mode="HTML")
