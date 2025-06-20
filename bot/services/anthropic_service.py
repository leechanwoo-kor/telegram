import logging
import anthropic
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, CATEGORIES

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

async def summarize_text(text):
    logger.info(f"Summarizing text of length: {len(text)}")
    if not text or text == "초록을 찾을 수 없음":
        logger.warning("Cannot summarize empty or placeholder abstract.")
        return "요약할 수 없는 내용입니다."
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
        summary = response.content[0].text
        logger.info(f"Successfully summarized text. Summary length: {len(summary)}")
        return summary
    except Exception as e:
        logger.error(f"Error summarizing text: {e}")
        return "요약 중 오류 발생."

async def translate_text(text, lang='KO'): # lang 파라미터 추가 (추후 확장성 고려)
    logger.info(f"Translating text to {lang}. Original length: {len(text)}")
    if not text or text == "요약할 수 없는 내용입니다." or text == "요약 중 오류 발생.":
        logger.warning("Cannot translate empty or error placeholder text.")
        return "번역할 수 없는 내용입니다."
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1000,
            temperature=0.0,
            system="You are a highly knowledgeable assistant who is very specialized in English-Korean translating. Provide translated text of the given content. Don't translate English terminologies and focus on translating common words. ONLY provide translated sentences.",
            messages=[{"role": "user", "content": f"Translate it into Korean: {text}"}],
        )
        translation = response.content[0].text
        logger.info(f"Successfully translated text. Translation length: {len(translation)}")
        return translation
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return "번역 중 오류 발생."

async def categorize_paper(title, summary):
    logger.info(f"Categorizing paper: {title}")
    if not summary or summary == "요약할 수 없는 내용입니다." or summary == "요약 중 오류 발생.":
        logger.warning(f"Cannot categorize paper '{title}' due to empty or error placeholder summary.")
        return []
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
        categories_str = response.content[0].text
        categories = [category.strip() for category in categories_str.split(",") if category.strip()]
        logger.info(f"Successfully categorized paper '{title}'. Categories: {categories}")
        return categories
    except Exception as e:
        logger.error(f"Error categorizing paper '{title}': {e}")
        return []
