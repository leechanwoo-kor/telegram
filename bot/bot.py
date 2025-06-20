import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN, CATEGORIES, LANGS, BOT_POLL_INTERVAL
from database import initialize_chat, update_chat
logger = logging.getLogger(__name__)


async def start(update, context):
    chat_id = update.effective_chat.id
    # 새로운 사용자인 경우 채팅 정보 초기화
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

    # 입력된 카테고리 문자열을 파싱하여 리스트로 변환
    input_categories = [cat.strip() for cat in " ".join(context.args).split(",")]

    # 유효한 카테고리 필터링
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
    # 입력된 언어를 가져와 대문자로 변환
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


# 정의되지 않은 명령어 또는 일반 텍스트 메시지 처리
async def handle_message(update, context):
    await update.message.reply_text(
        "Sorry, I didn't understand that command. Use /start for available commands."
    )


async def run_bot():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # 명령어 핸들러 등록
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setcategory", set_category))
    application.add_handler(CommandHandler("setlang", set_lang))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    await application.initialize()
    await application.start()

    try:
        logger.info("Bot started successfully")
        # 봇 폴링 시작
        await application.updater.start_polling(poll_interval=BOT_POLL_INTERVAL)
        # 인터럽트(Ctrl+C 등) 시까지 봇 실행 유지
        # 비동기 중지 신호 생성
        stop_signal = asyncio.Future()
        await stop_signal
    except asyncio.CancelledError:
        pass
    finally:
        await application.stop()
