from telebot import types
from db import get_user
from handlers.admin import is_admin
from bot_instance import bot  # Import bot from bot_instance

def send_main_menu(bot, update):
    # Fetch user details
    if hasattr(update, "message") and update.message:
        chat_id = update.message.chat.id
        user = get_user(str(update.message.from_user.id))
    elif hasattr(update, "from_user") and update.from_user:
        chat_id = update.chat.id if hasattr(update, "message") and update.message else update.chat.id
        user = get_user(str(update.from_user.id))
    else:
        chat_id = update.chat.id
        user = get_user(str(update.from_user.id))
    
    # Create the main menu
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("🎉 Rewards", callback_data="menu_rewards"),
        types.InlineKeyboardButton("👥 Info", callback_data="menu_info"),
        types.InlineKeyboardButton("🤝 Referral", callback_data="menu_referral"),
        types.InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard")  # Leaderboard button added
    )
    markup.add(
        types.InlineKeyboardButton("📠 Review", callback_data="menu_review"),
        types.InlineKeyboardButton("📣 Report", callback_data="menu_report"),
        types.InlineKeyboardButton("💬 Support", callback_data="menu_support")
    )

    # Show admin options if the user is an admin
    if is_admin(user):
        markup.add(types.InlineKeyboardButton("🔨 Admin Panel", callback_data="menu_admin"))

    # Send the main menu
    bot.send_message(chat_id, "Main Menu\nPlease choose an option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "menu_leaderboard")
def leaderboard_menu(call):
    # Create markup for leaderboard section
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏅 Points Leaderboard", callback_data="leaderboard_points"),
        types.InlineKeyboardButton("📊 Referral Leaderboard", callback_data="leaderboard_referral")
    )
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_main"))
    
    # Send the leaderboard section
    bot.edit_message_text("Welcome to the Leaderboard Section. Choose below:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard_points")
def points_leaderboard(call):
    # Fetch the points leaderboard
    leaderboard = get_leaderboard()  # Fetch top leaderboard from DB
    text = "Points Leaderboard:\n\n"
    for rank, user in enumerate(leaderboard, 1):
        text += f"{rank}. {user['username']} - {user['points']} points\n"
    
    # Add back button
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu_leaderboard"))
    
    # Show points leaderboard
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard_referral")
def referral_leaderboard(call):
    # Fetch the referral leaderboard
    leaderboard = get_referral_leaderboard()  # Fetch referral leaderboard
    text = "Referral Leaderboard:\n\n"
    for rank, user in enumerate(leaderboard, 1):
        text += f"{rank}. {user['username']} - {user['referrals']} referrals\n"
    
    # Add back button
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu_leaderboard"))
    
    # Show referral leaderboard
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "menu_rewards")
def rewards_menu(call):
    send_rewards_menu(bot, call.message)

@bot.callback_query_handler(func=lambda call: call.data == "menu_info")
def account_info(call):
    send_account_info(bot, call)

@bot.callback_query_handler(func=lambda call: call.data == "menu_referral")
def referral_menu(call):
    send_referral_menu(bot, call.message)

@bot.callback_query_handler(func=lambda call: call.data == "menu_review")
def review_menu(call):
    prompt_review(bot, call.message)

@bot.callback_query_handler(func=lambda call: call.data == "menu_report")
def report_menu(call):
    msg = bot.send_message(call.message.chat.id, "📝 Please type your report message (you may attach a photo or document):", reply_to_message_id=call.message.message_id)
    bot.register_next_step_handler(msg, lambda m: process_report(bot, m))

@bot.callback_query_handler(func=lambda call: call.data == "menu_support")
def support_menu(call):
    from handlers.support import send_support_message
    send_support_message(bot, call.message)

@bot.callback_query_handler(func=lambda call: call.data == "menu_admin")
def admin_menu(call):
    send_admin_menu(bot, call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def callback_back_main(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        print("Error deleting message:", e)
    send_main_menu(bot, call.message)
