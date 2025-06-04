import logging
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /start command and request phone number."""
    user = update.message.from_user
    logger.info(f"User {user.id} started the bot")

    # Create a button to request phone number
    keyboard = [[KeyboardButton("Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "Welcome! Please share your phone number by clicking the button below.",
        reply_markup=reply_markup
    )
    return PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the phone number shared by the user."""
    user = update.message.from_user
    contact = update.message.contact

    if contact and contact.phone_number:
        phone_number = contact.phone_number
        context.user_data["phone_number"] = phone_number
        logger.info(f"User {user.id} shared phone number: {phone_number}")

        await update.message.reply_text(
            f"Thank you! Your phone number is {phone_number}. Now, please enter the OTP sent to your phone."
        )
        return OTP
    else:
        await update.message.reply_text("Please share a valid phone number.")
        return PHONE

async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the OTP input by the user."""
    user = update.message.from_user
    otp = update.message.text

    if otp == EXPECTED_OTP:  # Replace with proper OTP verification logic
        phone_number = context.user_data.get("phone_number", "Unknown")
        logger.info(f"User {user.id} entered correct OTP for phone: {phone_number}")
        await update.message.reply_text("OTP verified successfully! You're all set.")
        return ConversationHandler.END
    else:
        logger.info(f"User {user.id} entered incorrect OTP")
        await update.message.reply_text("Incorrect OTP. Please try again.")
        return OTP

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

async def main() -> None:
    """Run the bot with webhook for Heroku."""
    # Get bot token and webhook URL from environment variables
    bot_token = os.getenv("BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")
    port = int(os.environ.get("PORT", 8443))

    if not bot_token or not webhook_url:
        logger.error("BOT_TOKEN or WEBHOOK_URL not set")
        return

    # Create the Application
    application = Application.builder().token(bot_token).build()

    # Create a ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, receive_phone)],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add ConversationHandler to the application
    application.add_handler(conv_handler)

    # Set webhook
    await application.bot.set_webhook(url=f"{webhook_url}/bot")
    
    # Start webhook
    await application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="/bot",
        webhook_url=f"{webhook_url}/bot"
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
