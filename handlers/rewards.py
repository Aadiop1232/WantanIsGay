import telebot
from telebot import types
import random
import config
import json
import sqlite3
from db import get_user, update_user_points, get_account_claim_cost, get_platforms
from handlers.logs import log_event

def send_rewards_menu(bot, message):
    platforms = get_platforms()
    if not platforms:
        bot.send_message(
            message.chat.id,
            "😢 No platforms available at the moment.",
            reply_to_message_id=message.message_id
        )
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for platform in platforms:
        platform_name = platform.get("platform_name")
        stock = json.loads(platform.get("stock") or "[]")
        price = platform.get("price") or get_account_claim_cost()
        btn_text = f"{platform_name} | Stock: {len(stock)} | Price: {price} pts"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"reward_{platform_name}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_main"))
    try:
        bot.edit_message_text(
            "<b>⚡ 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗣𝗹𝗮𝘁𝗳𝗼𝗿𝗺𝘀 ⚡</b>",
            chat_id=message.chat.id,
            message_id=message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
    except Exception:
        bot.send_message(
            message.chat.id,
            "<b>⚡ 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗣𝗹𝗮𝘁𝗳𝗼𝗿𝗺𝘀 ⚡</b>",
            parse_mode="HTML",
            reply_markup=markup,
            reply_to_message_id=message.message_id
        )

def handle_platform_selection(bot, call, platform_name):
    conn = __import__('db').get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM platforms WHERE platform_name = ?", (platform_name,))
    platform = c.fetchone()
    c.close()
    conn.close()
    if not platform:
        bot.send_message(
            call.message.chat.id,
            "Platform not found.",
            reply_to_message_id=call.message.message_id
        )
        return
    platform = dict(platform)
    stock = json.loads(platform["stock"] or "[]")
    price = platform["price"] or get_account_claim_cost()
    if stock:
        text = f"<b>{platform_name}</b>:\n✅ Accounts Available: {len(stock)}\nPrice: {price} pts per account"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🎁 Claim Account", callback_data=f"claim_{platform_name}"))
    else:
        text = f"<b>{platform_name}</b>:\n😞 No accounts available at the moment.\nPrice: {price} pts per account"
        markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu_rewards"))
    try:
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
    except Exception:
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=markup,
            reply_to_message_id=call.message.message_id
        )

def send_premium_account_info(bot, chat_id, platform_name, account_info):
    """
    If the claimed account is a cookie account (i.e. account_info is a dict with key 'type' == 'cookie'),
    create an in-memory text file (with header) and send it as a document.
    Otherwise, send the account details as a text message.
    """
    import io
    if isinstance(account_info, dict) and account_info.get("type") == "cookie":
        cookie_content = account_info.get("content", "No details found")
        header = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎁 Here Is Your Cookie For: " + platform_name + "\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        full_text = header + cookie_content
        file_stream = io.BytesIO(full_text.encode('utf-8'))
        file_stream.name = f"{platform_name}_cookie.txt"
        bot.send_document(chat_id, file_stream, caption="Your cookie file has been sent.")
    else:
        text = f"""🎉✨ 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝘼𝘾𝘾𝙊𝙐𝙉𝙏 𝙐𝙉𝙇𝙊𝘾𝙆𝙀𝘿  

✨🎉📦 𝙎𝙚𝙧𝙫𝙞𝙘𝙚 : {platform_name}

🔑 𝙔𝙤𝙪𝙧 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 :
<code>{account_info}</code> 📌 

How to login:
1️⃣ Copy the details
2️⃣ Open app/website
3️⃣ Paste & login

❌ Account not working? Report below to get a refund of your points!
By @shadowsquad0"""
        bot.send_message(chat_id, text, parse_mode="HTML")

def claim_account(bot, call, platform_name):
    user_id = str(call.from_user.id)
    user = get_user(user_id)
    if user is None:
        bot.send_message(
            call.message.chat.id,
            "User not found. Please /start the bot first.",
            reply_to_message_id=call.message.message_id
        )
        return
    conn = __import__('db').get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM platforms WHERE platform_name = ?", (platform_name,))
    platform = c.fetchone()
    c.close()
    conn.close()
    if not platform:
        bot.send_message(
            call.message.chat.id,
            "Platform not found.",
            reply_to_message_id=call.message.message_id
        )
        return
    platform = dict(platform)
    stock = json.loads(platform["stock"] or "[]")
    price = platform["price"] or get_account_claim_cost()
    try:
        current_points = int(user.get("points", 0))
    except Exception as e:
        bot.send_message(
            call.message.chat.id,
            f"Error reading your points: {e}",
            reply_to_message_id=call.message.message_id
        )
        return
    if current_points < price:
        bot.send_message(
            call.message.chat.id,
            f"Insufficient points (each account costs {price} pts). Earn more via referrals or keys.",
            reply_to_message_id=call.message.message_id
        )
        return
    if not stock:
        bot.send_message(
            call.message.chat.id,
            "No accounts available.",
            reply_to_message_id=call.message.message_id
        )
        return
    index = random.randint(0, len(stock) - 1)
    account = stock.pop(index)
    from db import update_stock_for_platform, update_user_points
    update_stock_for_platform(platform_name, stock)
    new_points = current_points - price
    update_user_points(user_id, new_points)
    log_event(
        bot,
        "account_claim",
        f"User {user_id} claimed an account from {platform_name}. New balance: {new_points} pts."
    )
    # If claim is from a group chat, send the account info to the user's private chat.
    target_chat_id = call.message.chat.id
    if call.message.chat.type in ["group", "supergroup"]:
        target_chat_id = call.from_user.id
    send_premium_account_info(bot, target_chat_id, platform_name, account)
    bot.send_message(
        call.message.chat.id,
        "✅ Your account details have been sent via DM! Check your messages.",
        reply_to_message_id=call.message.message_id
    )

def get_leaderboard(limit=10):
    """
    Fetch the points leaderboard.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT telegram_id, username, points FROM users ORDER BY points DESC LIMIT ?", (limit,))
    leaderboard = c.fetchall()
    c.close()
    conn.close()
    return [dict(row) for row in leaderboard]

def get_referral_leaderboard(limit=10):
    """
    Fetch the referral leaderboard.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT u.telegram_id, u.username, COUNT(r.referred_id) AS referrals
        FROM users u
        LEFT JOIN referrals r ON u.telegram_id = r.user_id
        GROUP BY u.telegram_id
        ORDER BY referrals DESC
        LIMIT ?
    """, (limit,))
    leaderboard = c.fetchall()
    c.close()
    conn.close()
    return [dict(row) for row in leaderboard]
