import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN, CATEGORIES, LANGS, LOG_FORMAT, BOT_POLL_INTERVAL
from src.database import initialize_chat, update_chat

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update, context):
    chat_id = update.effective_chat.id
    initialize_chat(chat_id)

    welcome_message = (
        "Welcome to the daily paper bot!\n\n"
        "Here are the available commands:\n"
        "/setcategory - Set your preferred paper categories\n"
        "  Usage: /setcategory category1,category2,category3\n"
        f"  Available categories: {', '.join(CATEGORIES)}\n"
        "  Example: /setcategory LLM,Computer vision\n\n"
        "/setlang - Set your preferred language for summaries\n"
        "  Usage: /setlang language\n"
        f"  Available languages: {', '.join(LANGS)}\n"
        "  Example: /setlang KO\n"
    )
    await context.bot.send_message(chat_id, welcome_message)


async def set_category(update, context):
    chat_id = update.effective_chat.id
    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Please provide categories. Ex: /setcategory LLM,Computer vision",
        )
        return

    input_categories = [cat.strip() for cat in " ".join(context.args).split(",")]

    valid_categories = [cat for cat in input_categories if cat in CATEGORIES]
    invalid_categories = [cat for cat in input_categories if cat not in CATEGORIES]

    if valid_categories:
        update_chat(chat_id, category=",".join(valid_categories))
        success_message = f"Category is set to: {', '.join(valid_categories)}"
        if invalid_categories:
            success_message += (
                f"\nInvalid categories ignored: {', '.join(invalid_categories)}"
            )
        await context.bot.send_message(chat_id=chat_id, text=success_message)
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"No valid categories provided. Please choose from: {', '.join(CATEGORIES)}",
        )


async def set_lang(update, context):
    chat_id = update.effective_chat.id
    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id, text="Please provide a language. Ex: /setlang KO"
        )
        return
    lang = context.args[0].strip().upper()
    if lang in LANGS:
        update_chat(chat_id, lang=lang)
        await context.bot.send_message(
            chat_id=chat_id, text=f"Language is set to {lang}"
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Invalid language. Please choose from: {', '.join(LANGS)}",
        )


async def handle_message(update, context):
    await update.message.reply_text(
        "Sorry, I didn't understand that command. Use /start for available commands."
    )


async def run_bot():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setcategory", set_category))
    application.add_handler(CommandHandler("setlang", set_lang))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    await application.initialize()
    await application.start()

    try:
        logging.info("Bot started successfully")
        await application.updater.start_polling(poll_interval=BOT_POLL_INTERVAL)
        # Keep the bot running until interrupted
        stop_signal = asyncio.Future()
        await stop_signal
    except asyncio.CancelledError:
        pass
    finally:
        await application.stop()
