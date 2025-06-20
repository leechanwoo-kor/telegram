import logging
import asyncio
from datetime import datetime
import telegram
from database import is_paper_exists, insert_paper, get_users
from config import TELEGRAM_TOKEN, UPDATE_INTERVAL
from services.paper_fetcher import fetch_data, parse_papers
from services.anthropic_service import summarize_text, translate_text, categorize_paper

logger = logging.getLogger(__name__)

async def send_daily_message(user_info, new_papers):
    chat_id, lang, categories_str = user_info
    categories = categories_str.split(",")

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    for paper in new_papers:
        if any(category in paper["categories"] for category in categories):
            # 사용자의 설정 언어에 따라 사용할 요약본 결정
            summary_key = f'summary_{lang.upper()}'
            if summary_key not in paper:
                logger.warning(f"Summary for language '{lang}' not found for paper '{paper['title']}'. Defaulting to EN.")
                summary_key = 'summary_EN' # 특정 언어 요약본이 없으면 영어 요약본을 기본으로 사용
            
            message_summary = paper.get(summary_key, paper.get('summary_EN', 'Summary not available.'))

            message = f"**{paper['title']}**\n\n> {message_summary}\n\n{paper['url']}"
            try:
                await bot.send_message(chat_id, message, parse_mode="Markdown")
            except telegram.error.Forbidden as e:
                logger.warning(f"Failed to send message to {chat_id} (user blocked or deactivated): {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while sending message to {chat_id}: {e}")

async def run_paper():
    while True:
        try:
            logger.info(f"Starting paper update cycle at {datetime.now()}")
            current_date = datetime.now()
            # fetch_data는 이제 날짜 인자를 받음
            fetch_day, html_content = await fetch_data(current_date) 
            
            if html_content and fetch_day:
                # parse_papers는 이제 HTML 내용만 인자로 받음
                papers_parsed = await parse_papers(html_content) 
                new_papers_to_send = []
                for paper_name, paper_url, paper_abstract in papers_parsed:
                    if not is_paper_exists(paper_name):
                        # Anthropic 서비스를 사용하여 요약, 번역, 분류 처리
                        summary_en = await summarize_text(paper_abstract)
                        summary_ko = await translate_text(summary_en) # 영어 요약본을 번역
                        paper_categories = await categorize_paper(paper_name, summary_en)
                        
                        categories_str = ",".join(paper_categories)
                        # DB 저장 시 fetch_data에서 가져온 fetch_day 사용
                        insert_paper(
                            paper_name, fetch_day, summary_en, summary_ko, categories_str
                        )
                        new_papers_to_send.append(
                            {
                                "title": paper_name,
                                "summary_EN": summary_en,
                                "summary_KO": summary_ko,
                                "categories": paper_categories,
                                "url": paper_url,
                            }
                        )
                        logger.info(f"New paper added: {paper_name}")

                if new_papers_to_send:
                    users = get_users()
                    for user in users:
                        await send_daily_message(user, new_papers_to_send)
                else:
                    logger.info("No new papers found or all were skipped.")
            else:
                logger.info("No content fetched or fetch_day is None.")

            logger.info(
                f"Finished paper update cycle. Next update in {UPDATE_INTERVAL} seconds."
            )
            await asyncio.sleep(UPDATE_INTERVAL)
        except Exception as e:
            logger.error(f"Error in run_paper: {e}", exc_info=True) # 상세 오류 정보 로깅을 위해 exc_info=True 추가
            await asyncio.sleep(UPDATE_INTERVAL) # 오류 발생 시에도 루프가 계속되도록 sleep 처리
