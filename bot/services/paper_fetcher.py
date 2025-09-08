import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import HUGGINGFACE_URL, HUGGINGFACE_PAPERS_URL

logger = logging.getLogger(__name__)

async def fetch_data(date):
    logger.info(f"Fetching data... ({date.strftime('%Y-%m-%d')})")
    fetch_day = date # 전달된 날짜를 기준으로 시작
    for i in range(3): # 최대 3일치 시도 (전달된 날짜 포함)
        current_try_date = fetch_day - timedelta(days=i)
        day_str = current_try_date.strftime("%Y-%m-%d")
        url = f"{HUGGINGFACE_PAPERS_URL}?date={day_str}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"Fetched content for {day_str} with length: {len(content)}")
                        return current_try_date, content # 데이터를 찾은 날짜와 내용을 반환
                    else:
                        logger.warning(f"Failed to fetch data for {day_str}. Status: {response.status}")
        except Exception as e:
            logger.error(f"Error fetching data for {day_str}: {e}")
    logger.warning("Failed to fetch data after 3 attempts.")
    return None, None

async def fetch_paper_abstract(paper_url, session, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with session.get(paper_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), "html.parser")
                    abstract_header = soup.find(lambda tag: tag.name in ['h2', 'h3'] and 'Abstract' in tag.text) # 'Abstract' 텍스트를 포함하는 h2 또는 h3 태그 검색 (새로운 초록 구조)
                    if abstract_header:
                        abstract_text = ""
                        next_element = abstract_header.find_next()
                        while next_element and next_element.name not in ['h2', 'h3']:
                            if next_element.name == 'p' or next_element.string:
                                text = next_element.get_text(strip=True)
                                if text and 'View arXiv page' not in text and 'View PDF' not in text and 'Add to collection' not in text:
                                    abstract_text += text + " "
                            next_element = next_element.find_next()
                        if abstract_text:
                            return abstract_text.strip()
                    
                    abstract_tag = soup.find("p", class_="text-gray-700 dark:text-gray-400")
                    if abstract_tag: # 기존 방식의 초록 태그 검색 (class 사용)
                        return abstract_tag.get_text(strip=True).replace("\n", " ")
                    logger.warning(f"Could not find abstract for {paper_url} using known methods.")
                    return "초록을 찾을 수 없음"
                else:
                    logger.warning(f"Failed to fetch abstract page {paper_url}. Status: {response.status}, Attempt: {attempt + 1}")
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching abstract for {paper_url}. Attempt: {attempt + 1}")
        except Exception as e:
            logger.error(f"Error fetching paper abstract for {paper_url}: {e}, Attempt: {attempt + 1}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(1)  # Wait before retry
    
    logger.error(f"Failed to fetch abstract for {paper_url} after {max_retries} attempts")
    return "초록을 찾을 수 없음"

async def parse_papers(html_content):
    logger.info(f"Parsing HTML content of length: {len(html_content)}")
    soup = BeautifulSoup(html_content, "html.parser")
    papers = []
    articles = soup.find_all("article")
    logger.info(f"Found {len(articles)} articles")

    # Create session for concurrent requests
    async with aiohttp.ClientSession() as session:
        # Prepare all paper URLs first
        paper_tasks = []
        paper_info = []
        
        for article in articles:
            paper_name_tag = article.find("h3")
            if paper_name_tag:
                paper_name = paper_name_tag.get_text(strip=True)
                paper_url_tag = paper_name_tag.find("a")
                if paper_url_tag and paper_url_tag.has_attr("href"):
                    paper_url = HUGGINGFACE_URL + paper_url_tag["href"]
                    paper_info.append((paper_name, paper_url))
                    paper_tasks.append(fetch_paper_abstract(paper_url, session))
        
        # Fetch all abstracts concurrently
        logger.info(f"Fetching {len(paper_tasks)} abstracts concurrently...")
        abstracts = await asyncio.gather(*paper_tasks)
        
        # Process results
        for (paper_name, paper_url), abstract in zip(paper_info, abstracts):
            if abstract != "초록을 찾을 수 없음":
                papers.append((paper_name, paper_url, abstract))
                logger.debug(f"Successfully added paper: {paper_name}")
            else:
                logger.warning(f"Skipping paper '{paper_name}' due to missing abstract.")
    
    logger.info(f"Successfully parsed {len(papers)} papers with abstracts out of {len(articles)} articles.")
    return papers
