# -*- coding: utf-8 -*-
import telebot
from datetime import datetime
from db import get_user, add_user

def send_account_info(bot, update):
    """
    Sends the user's account info in your fancy ASCII style.
    Works whether 'update' is a Message or a CallbackQuery.

    Make sure you call this function with the actual user update, e.g.:
      @bot.message_handler(commands=["info"])
      def info_handler(message):
          send_account_info(bot, message)

    Or for a callback:
      @bot.callback_query_handler(func=lambda call: call.data == "info")
      def callback_info(call):
          send_account_info(bot, call)
    """

    # Distinguish between a normal Message vs. a CallbackQuery
    if isinstance(update, telebot.types.Message):
        chat_id = update.chat.id
        user_id = str(update.from_user.id)
        print(f"[DEBUG] send_account_info -> from Message: user_id={user_id}, username={update.from_user.username}")
    elif isinstance(update, telebot.types.CallbackQuery):
        chat_id = update.message.chat.id
        user_id = str(update.from_user.id)
        print(f"[DEBUG] send_account_info -> from CallbackQuery: user_id={user_id}, username={update.from_user.username}")
    else:
        print("[DEBUG] send_account_info -> Unknown update type, cannot proceed.")
        return

    # Fetch the user from the DB
    user = get_user(user_id)
    if not user:
        # If user doesn't exist, create them
        # (In normal usage, the user should already be created at /start)
        new_username = update.from_user.username or update.from_user.first_name
        add_user(
            user_id,
            new_username,
            datetime.now().strftime("%Y-%m-%d")
        )
        user = get_user(user_id)

    # Extract info from the DB user doc
    username = user.get("username", "N/A")
    join_date = user.get("join_date", "N/A")
    balance = user.get("points", 0)
    referrals = user.get("referrals", 0)

    # Build the fancy UI box
    text = (
        "╭━━━✦❘༻👤 ACCOUNT INFO ༺❘✦━━━╮\n"
        "┃\n"
        f"┃ ✧ Username: {username}\n"
        f"┃ ✧ User ID: {user_id}\n"
        f"┃ ✧ Join Date: {join_date}\n"
        f"┃ ✧ Balance: {balance} pts\n"
        f"┃ ✧ Total Referrals: {referrals}\n"
        "┃\n"
        "╰━━━━━━━✦✧✦━━━━━━━╯"
    )

    bot.send_message(chat_id, text, parse_mode="HTML")
