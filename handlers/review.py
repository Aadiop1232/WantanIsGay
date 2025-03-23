import telebot
import config
from db import add_review, get_report_by_id, claim_report_by_admin, close_report_in_db
from handlers.logs import log_event

def prompt_review(bot, message):
    """
    Prompt the user to send a review or suggestion.
    """
    msg = bot.send_message(message.chat.id, "💬 Please send your review or suggestion:")
    bot.register_next_step_handler(msg, process_review, bot)

def process_review(bot, message):
    """
    Process a review or suggestion from the user.
    """
    review_text = message.text
    add_review(str(message.from_user.id), review_text)
    for owner in config.OWNERS:
        try:
            bot.send_message(owner,
                             f"📢 Review from {message.from_user.username or message.from_user.first_name} ({message.from_user.id}):\n\n{review_text}",
                             parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending review to owner {owner}: {e}")
    bot.send_message(message.chat.id, "✅ Thank you for your feedback!", parse_mode="Markdown")
    log_event(bot, "review", f"Review received from user {message.from_user.id}.", user=message.from_user)

def process_report(bot, message):
    """
    Process a report from the user and forward it to the owners.
    This function supports text reports as well as media (photo or document) with captions.
    """
    # Combine caption and text if available.
    report_text = ""
    if message.content_type in ["photo", "document"]:
        report_text = message.caption or ""
    if hasattr(message, "text") and message.text:
        # If there's a caption, append the text; otherwise, use it.
        if report_text:
            report_text = f"{report_text}\n{message.text}"
        else:
            report_text = message.text

    user = message.from_user
    username = user.username if user.username else user.first_name
    report_header = f"Report from {username} ({user.id}):\n\n"

    # Add buttons for claim and close functionality.
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Claim Report", callback_data=f"claim_report_{message.message_id}"),
        telebot.types.InlineKeyboardButton("❌ Close Report", callback_data=f"close_report_{message.message_id}")
    )

    # Send report to all owners with buttons
    for owner in config.OWNERS:
        try:
            if message.content_type == "photo":
                # Use highest-resolution photo.
                photo_id = message.photo[-1].file_id
                bot.send_photo(owner, photo_id, caption=report_header + report_text, parse_mode="HTML", reply_markup=markup)
            elif message.content_type == "document":
                bot.send_document(owner, message.document.file_id, caption=report_header + report_text, parse_mode="HTML", reply_markup=markup)
            else:
                bot.send_message(owner, report_header + report_text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            print(f"Error sending report to owner {owner}: {e}")

    bot.send_message(message.chat.id, "✅ Your report has been submitted. Thank you!")

def handle_claim_report(bot, call):
    """
    Handle when an admin claims a report.
    """
    report_id = call.data.split("_")[2]  # Extract report ID from callback
    report = get_report_by_id(report_id)  # Fetch report from the DB

    if report and not report.get('claimed'):
        claim_report_by_admin(call.from_user.id, report_id)  # Mark as claimed
        bot.answer_callback_query(call.id, "Report claimed successfully!")
        bot.send_message(call.message.chat.id, f"Your report has been claimed by {call.from_user.username}.")
        bot.send_message(report['user_id'], f"Your report has been claimed by {call.from_user.username}.")

        # Send report details to the owner/admin
        bot.send_message(call.from_user.id, f"Report claimed: {report['text']}")
        
        # Allow the admin to send messages to the user after claiming the report.
        bot.send_message(call.from_user.id, "You can now reply to this message, and the response will be sent to the user.")
    else:
        bot.answer_callback_query(call.id, "This report has already been claimed or closed.")

def handle_close_report(bot, call):
    """
    Handle when an admin closes a report.
    """
    report_id = call.data.split("_")[2]  # Extract report ID from callback
    report = get_report_by_id(report_id)

    if report:
        close_report_in_db(report_id)  # Close the report in the DB
        bot.answer_callback_query(call.id, "Report has been closed.")
        bot.send_message(call.message.chat.id, "The report has been closed.")
        bot.send_message(report['user_id'], "Your report has been closed by the admin.")

        # Prevent further actions on the closed report
        bot.send_message(call.from_user.id, f"Report {report_id} has been closed.")

def handle_admin_reply_to_report(bot, message):
    """
    Handle when an admin replies to a report's message.
    The message is sent to the user who reported the issue.
    """
    # Check if the message is a reply to a report
    if not message.reply_to_message or not message.reply_to_message.text.startswith("Report:"):
        return  # Ignore if it's not a reply to a report

    report_id = extract_report_id_from_reply(message.reply_to_message)  # Extract report ID
    if is_report_claimed(report_id):
        # Get report details and send it to the user
        report = get_report_by_id(report_id)
        bot.send_message(report['user_id'], f"Admin replied to your report: {message.text}")
    else:
        bot.send_message(message.chat.id, "This report is not claimed or has been closed.")

def extract_report_id_from_reply(message):
    """Helper function to extract the report ID from the reply message."""
    # Assumes the report text includes an identifiable format (e.g., report ID in the text)
    if message.text and message.text.startswith("Report:"):
        return message.text.split("ID: ")[1]  # Extract report ID from the message
    return None

def is_report_claimed(report_id):
    """Check if the report has been claimed by an admin."""
    report = get_report_by_id(report_id)
    return report and report.get("claimed")
