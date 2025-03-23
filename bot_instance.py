import telebot
import config

# Initialize the bot
bot = telebot.TeleBot(config.TOKEN, parse_mode="HTML")
