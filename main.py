from email.mime import application
import logging
import random
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackContext
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")

client = MongoClient(MONGO_URI)
db = client['telegram_bot_db']
users_collection = db['users']

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    full_name = user.full_name
    username = user.username or "NoUsername"
    telegram_id = user.id

    existing_user = users_collection.find_one({"telegram_id": telegram_id})
    if existing_user:
        update.message.reply_text(
            f"{full_name}!\nsiz ro‘yxatdan o‘tgansiz. Buyurtma berishingiz mumkin.",
            reply_markup=ReplyKeyboardRemove()
        )
        web_button = InlineKeyboardButton(
            text="🛒 Buyurtma berish",
            web_app={"url": "https://warm-froyo-dbdbcb.netlify.app/"}
        )
        reply_markup = InlineKeyboardMarkup([[web_button]])
        update.message.reply_text("Quyidagi tugma orqali buyurtma bering:", reply_markup=reply_markup)
        return

    user_id = random.randint(100000, 999999)
    contact_button = KeyboardButton("📞 Telefon raqam yuborish", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)

    context.user_data['user_id'] = user_id
    context.user_data['full_name'] = full_name
    context.user_data['username'] = username
    context.user_data['telegram_id'] = telegram_id

    update.message.reply_text(
        f"Salom {full_name}!\nIltimos, telefon raqamingizni yuboring:",
        reply_markup=reply_markup
    )

def contact_handler(update: Update, context: CallbackContext):
    contact = update.message.contact
    phone_number = contact.phone_number

    user_data = context.user_data
    user_data['phone_number'] = phone_number

    existing_user = users_collection.find_one({"telegram_id": user_data['telegram_id']})
    if existing_user:
        update.message.reply_text("Siz allaqachon ro‘yxatdan o‘tgan ekansiz.")
        return

    users_collection.insert_one({
        "user_id": user_data['user_id'],
        "full_name": user_data['full_name'],
        "username": user_data['username'],
        "telegram_id": user_data['telegram_id'],
        "phone_number": phone_number
    })

    web_button = InlineKeyboardButton(
        text="🛒 Buyurtma berish",
        web_app={"url": "https://warm-froyo-dbdbcb.netlify.app/"}
    )
    reply_markup = InlineKeyboardMarkup([[web_button]])

    update.message.reply_text("✅ Ma’lumotlaringiz olindi. Bemalol buyurtma berishingiz mumkin.",
                              reply_markup=ReplyKeyboardRemove())
    update.message.reply_text("Quyidagi tugma orqali buyurtma bering:", reply_markup=reply_markup)

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.contact, contact_handler))

    print("[BOT] Polling boshlandi...")
    updater.start_polling()
    updater.idle()
if __name__ == "__main__":
    run_bot()
