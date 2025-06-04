import logging
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states for the conversation
PHONE, OTP = range(2)

# Hardcoded OTP for demo (replace with proper OTP generation/verification)
EXPECTED_OTP = "123456"

def start(update: Update, context: CallbackContext) -> int:
    """Handle the /start command and request phone number."""
    user = update.message.from_user
    logger.info(f"User {user.id} started the bot")

    # Create a button to request phone number
    keyboard = [[KeyboardButton("Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    update.message.reply_text(
        "Welcome! Please share your phone number by clicking the button below.",
        reply_markup=reply_markup
    )
    return PHONE

def receive_phone(update: Update, context: CallbackContext) -> int:
    """Handle the phone number shared by the user."""
    user = update.message.from_user
    contact = update.message.contact

    if contact and contact.phone_number:
        phone_number = contact.phone_number
        context.user_data["phone_number"] = phone_number
        logger.info(f"User {user.id} shared phone number: {phone_number}")

        update.message.reply_text(
            f"Thank you! Your phone number is {phone_number}. Now, please enter the OTP sent to your phone."
        )
        return OTP
    else:
        update.message.reply_text("Please share a valid phone number.")
        return PHONE

def receive_otp(update: Update, context: CallbackContext) -> int:
    """Handle the OTP input by the user."""
    user = update.message.from_user
    otp = update.message.text

    if otp == EXPECTED_OTP:  # Replace with proper OTP verification logic
        phone_number = context.user_data.get("phone_number", "Unknown")
        logger.info(f"User {user.id} entered correct OTP for phone: {phone_number}")
        update.message.reply_text("OTP verified successfully! You're all set.")
        return ConversationHandler.END
    else:
        logger.info(f"User {user.id} entered incorrect OTP")
        update.message.reply_text("Incorrect OTP. Please try again.")
        return OTP

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the conversation."""
    update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main():
    """Run the bot with webhook for Heroku."""
    # Get bot token and webhook URL from environment variables
    bot_token = os.getenv("BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")
    port = int(os.environ.get("PORT", 8443))

    if not bot_token or not webhook_url:
        logger.error("BOT_TOKEN or WEBHOOK_URL not set")
        return

    # Create the Updater
    updater = Updater(bot_token, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Create a ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(Filters.contact, receive_phone)],
            OTP: [MessageHandler(Filters.text & ~Filters.command, receive_otp)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add ConversationHandler to the dispatcher
    dp.add_handler(conv_handler)

    # Set webhook
    updater.bot.set_webhook(url=f"{webhook_url}/bot")

    # Start the webhook
    updater.start_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="/bot",
        webhook_url=f"{webhook_url}/bot"
    )

    # Run the bot until interrupted
    updater.idle()

if __name__ == "__main__":
    main()
