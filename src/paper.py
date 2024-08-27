import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import anthropic
import telegram
from src.database import is_paper_exists, insert_paper, get_users
from config import (
    TELEGRAM_TOKEN,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    HUGGINGFACE_URL,
    HUGGINGFACE_PAPERS_URL,
    CATEGORIES,
    UPDATE_INTERVAL,
    LOG_FORMAT,
)


logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def fetch_data(date):
    logger.info(f"Fetching data... ({date.strftime('%Y-%m-%d')})")
    fetch_day = datetime.now()
    for _ in range(3): # Try 3 days
        day_str = fetch_day.strftime("%Y-%m-%d")
        url = f"{HUGGINGFACE_PAPERS_URL}?date={day_str}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"Fetched content length: {len(content)}")
                        return fetch_day, content
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
        fetch_day -= timedelta(days=1)
    return None, None


async def parse_papers(html_content):
    logger.info(f"Parsing HTML content of length: {len(html_content)}")
    soup = BeautifulSoup(html_content, "html.parser")
    papers = []
    articles = soup.find_all("article")
    logger.info(f"Found {len(articles)} articles")

    for article in articles:
        paper_name_tag = article.find("h3")
        if paper_name_tag:
            paper_name = paper_name_tag.get_text(strip=True)
            paper_url_tag = paper_name_tag.find("a")
            if paper_url_tag and paper_url_tag.has_attr("href"):
                paper_url = HUGGINGFACE_URL + paper_url_tag["href"]
                paper_abstract = await fetch_paper_abstract(paper_url)
                papers.append((paper_name, paper_url, paper_abstract))
    return papers


async def fetch_paper_abstract(paper_url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(paper_url) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), "html.parser")
                    abstract_tag = soup.find(
                        "p", class_="text-gray-700 dark:text-gray-400"
                    )
                    if abstract_tag:
                        return abstract_tag.get_text(strip=True).replace("\n", " ")
    except Exception as e:
        logger.error(f"Error fetching paper abstract: {e}")
    return "Abstract not found."


async def update_paper():
    fetch_day, url_content = await fetch_data()
    new_papers = []
    if url_content:
        logger.info("Parsing papers...")
        papers = await parse_papers(url_content)
        logger.info(f"Parsed {len(papers)} papers")
        for paper_name, paper_url, paper_abstract in papers:
            if not is_paper_exists(paper_name):
                summary = await summarize_text(paper_abstract)
                translate_summary = await translate_text(summary)
                categories = await categorize_paper(paper_name, summary)
                categories_str = ",".join(categories)
                insert_paper(
                    paper_name, fetch_day, summary, translate_summary, categories_str
                )
                new_papers.append(
                    {
                        "title": paper_name,
                        "summary_EN": summary,
                        "summary_KO": translate_summary,
                        "categories": categories,
                        "url": paper_url,
                    }
                )
    return new_papers


async def summarize_text(text):
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1000,
            temperature=0.0,
            system="You are a highly knowledgeable assistant who is very specialized in deep learning field. Provide the summarization of the given content into 2~3 sentences. ONLY provide the summarized sentences.",
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this content into maximum 2 sentences: {text}",
                }
            ],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error summarizing text: {e}")
        return "Error in summarization."


async def translate_text(text):
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1000,
            temperature=0.0,
            system="You are a highly knowledgeable assistant who is very specialized in English-Korean translating. Provide translated text of the given content. Don't translate English terminologies and focus on translating common words. ONLY provide translated sentences.",
            messages=[{"role": "user", "content": f"Translate it into Korean: {text}"}],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return "Error in translation."


async def categorize_paper(title, summary):
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1000,
            temperature=0.0,
            system=f"You are a highly knowledgeable assistant who is very specialized in deep learning field. Suggest one or multiple categories of the given paper. Categories must be selected among {CATEGORIES}. ONLY provide categories separated by comma and nothing else.",
            messages=[
                {
                    "role": "user",
                    "content": f"What categories would you suggest me to add to this paper?\npaper title: {title}\npaper summary: {summary}",
                }
            ],
        )
        categories = response.content[0].text.split(",")
        return [category.strip() for category in categories]
    except Exception as e:
        logger.error(f"Error categorizing paper: {e}")
        return []


async def send_daily_message(user_info, new_papers):
    chat_id, lang, categories_str = user_info
    categories = categories_str.split(",")

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    for paper in new_papers:
        if any(category in paper["categories"] for category in categories):
            message = f"**{paper['title']}**\n\n> {paper[f'summary_{lang}']}\n\n{paper['url']}"
            try:
                await bot.send_message(chat_id, message, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Error sending message to {chat_id}: {e}")


async def run_paper():
    while True:
        try:
            logger.info(f"Starting paper update cycle at {datetime.now()}")
            date = datetime.now()
            fetch_day, html_content = await fetch_data(date)
            if html_content:
                papers = await parse_papers(html_content)
                new_papers = []
                for paper_name, paper_url, paper_abstract in papers:
                    if not is_paper_exists(paper_name):
                        summary = await summarize_text(paper_abstract)
                        translation = await translate_text(summary)
                        categories = await categorize_paper(paper_name, paper_abstract)
                        categories_str = ",".join(categories)
                        insert_paper(
                            paper_name, fetch_day, summary, translation, categories_str
                        )
                        new_papers.append(
                            {
                                "title": paper_name,
                                "summary_EN": summary,
                                "summary_KO": translation,
                                "categories": categories,
                                "url": paper_url,
                            }
                        )
                        logger.info(f"New paper added: {paper_name}")

                if new_papers:
                    users = get_users()
                    for user in users:
                        await send_daily_message(user, new_papers)
                else:
                    logger.info("No new papers found.")
            else:
                logger.info("No content fetched.")

            logger.info(
                f"Finished paper update cycle. Next update in {UPDATE_INTERVAL} seconds."
            )
            await asyncio.sleep(UPDATE_INTERVAL)
        except Exception as e:
            logger.error(f"Error in run_paper: {e}")
            await asyncio.sleep(UPDATE_INTERVAL)
