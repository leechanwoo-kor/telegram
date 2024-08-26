from dotenv import load_dotenv
import os
import logging

import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

import sqlite3
from contextlib import closing

# 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, an error occurred while processing your request."
        )


async def start(update, context):
    await command_daily_paper(update, context)


async def handle_message(update, context):
    await command_daily_paper(update, context)


# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.getenv("DB_NAME")
DB_PATH = os.path.join(BASE_DIR, "db", DB_NAME)

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

CATEGORIES = [
    "LLM",
    "Multimodal",
    "Computer vision",
    "Reinforcement learning",
    "Robotics",
    "Recommendation",
]
LANGS = ["KO", "EN"]

def initialize_database():
    logger.info(f"Initializing database at {DB_PATH}")

    with closing(sqlite3.connect(DB_PATH)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat(
                        chatId TEXT NOT NULL PRIMARY KEY,
                        lang TEXT DEFAULT EN,
                        category TEXT DEFAULT '%s')
                        """
                % (",".join(CATEGORIES))
            )
            conn.commit()

    logger.info("Database initialization complete")


async def command_daily_paper(update, context):
    chat_id = update.effective_chat.id
    msg = update.message.text
    logger.info(f"Received message: {msg} from chat_id: {chat_id}")

    # check if the chat exists in the database
    if msg == "/start":
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with closing(conn.cursor()) as cursor:
                is_exist = cursor.execute(
                    "SELECT * FROM chat WHERE chatId = ?", (chat_id,)
                )
                is_exist = cursor.fetchone()

                if not is_exist:
                    cursor.execute(
                        "INSERT INTO chat (chatId) VALUES (?)", (str(chat_id),)
                    )
                    conn.commit()

        bot = telegram.Bot(token=TELEGRAM_TOKEN)

        message = (
            "Welcome to the daily paper bot!\n\n"
            + "Send the category of the papers you are interested in.\n"
            + "Possible categories: LLM, Multimodal, Computer vision, Reinforcement learning, Robotics, Recommendation.\n"
            + "Send them seperate by comma\n"
            + "ex) /setcategory:LLM,Computer vision\n\n"
            + "Send the language of the summary you want to get.\n"
            + "Possible languages: KO, EN\n"
            + "ex) /setlang:KO"
        )
        await bot.send_message(chat_id, message)

    # set the category
    elif msg.startswith("/setcategory:"):
        categories = msg.split(":")[1].split(",")
        categories = [category.strip() for category in categories]

        if all(category in CATEGORIES for category in categories):
            with closing(sqlite3.connect(DB_PATH)) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute(
                        "UPDATE chat SET category = ? WHERE chatId = ?",
                        (",".join(categories), str(chat_id)),
                    )
                    conn.commit()
            message = "Category is set to " + ",".join(categories)
        else:
            message = (
                "Invalid category. Please choose from the following categories: "
                + ", ".join(CATEGORIES)
            )

        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id, message)

    # set the language
    elif msg.startswith("/setlang:"):
        lang = msg.split(":")[1].strip()
        logger.info(f"Attempting to set language to: {lang}")

        if lang not in LANGS:
            message = (
                "Invalid language. Please choose from the following languages: "
                + ", ".join(LANGS)
            )
        else:
            with closing(sqlite3.connect(DB_PATH)) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute(
                        "UPDATE chat SET lang = ? WHERE chatId = ?",
                        (lang, str(chat_id)),
                    )
                    conn.commit()
            message = "Language is set to " + lang

        logger.info(f"Sending message: {message}")
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id, message)
    else:
        logger.warning(f"Unrecognized command: {msg}")
        await update.message.reply_text("Sorry, I didn't understand that command.")


if __name__ == "__main__":
    initialize_database()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setlang", command_daily_paper))
    application.add_handler(CommandHandler("setcategory", command_daily_paper))

    # Message handler for text messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Error handler
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()
