import os
import sqlite3
import logging # Added
from contextlib import closing
from config import DB_PATH, DEFAULT_LANGUAGE, DEFAULT_CATEGORIES_STR # Updated imports

logger = logging.getLogger(__name__) # Added


def initialize_database():
    try:
        # 데이터베이스 디렉토리 확인 및 생성
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Ensured database directory exists: {db_dir}")

        with closing(sqlite3.connect(DB_PATH)) as conn:
            with closing(conn.cursor()) as cursor:
                # chat 테이블 생성 (기본값 포함)
                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS chat (
                        chatId TEXT NOT NULL PRIMARY KEY,
                        lang TEXT DEFAULT '{DEFAULT_LANGUAGE}',
                        category TEXT DEFAULT '{DEFAULT_CATEGORIES_STR}'
                    )
                    """
                )
                logger.info("Table 'chat' initialized/verified.")

                # paper 테이블 생성
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS paper (
                        title TEXT NOT NULL PRIMARY KEY,
                        date DATE,
                        summaryEN TEXT,
                        summaryKO TEXT,
                        categories TEXT
                    )
                    """
                )
                logger.info("Table 'paper' initialized/verified.")
                conn.commit()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"SQLite error during database initialization: {e}")
    except OSError as e:
        logger.error(f"OS error during database directory creation: {e}")


def initialize_chat(chat_id):
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    "INSERT OR IGNORE INTO chat (chatId) VALUES (?)", (str(chat_id),)
                )
                conn.commit()
            logger.info(f"Chat initialized or ignored for chatId: {chat_id}")
    except sqlite3.Error as e:
        logger.error(f"SQLite error initializing chat for {chat_id}: {e}")


def update_chat(chat_id, lang=None, category=None):
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with closing(conn.cursor()) as cursor:
                if lang and category:
                    cursor.execute(
                        "UPDATE chat SET lang = ?, category = ? WHERE chatId = ?",
                        (lang, category, str(chat_id)),
                    )
                    logger.info(f"Updated lang to '{lang}' and category to '{category}' for chatId: {chat_id}")
                elif lang:
                    cursor.execute(
                        "UPDATE chat SET lang = ? WHERE chatId = ?", (lang, str(chat_id))
                    )
                    logger.info(f"Updated lang to '{lang}' for chatId: {chat_id}")
                elif category:
                    cursor.execute(
                        "UPDATE chat SET category = ? WHERE chatId = ?",
                        (category, str(chat_id)),
                    )
                    logger.info(f"Updated category to '{category}' for chatId: {chat_id}")
                else:
                    logger.info(f"No update performed for chatId: {chat_id} as lang and category were not provided.")
                    return # No changes to commit if nothing was updated
                conn.commit()
    except sqlite3.Error as e:
        logger.error(f"SQLite error updating chat for {chat_id}: {e}")


def get_users():
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with closing(conn.cursor()) as cursor:
                users = cursor.execute("SELECT chatId, lang, category FROM chat").fetchall() # 명시적으로 컬럼 선택
                logger.info(f"Retrieved {len(users)} users from database.")
                return users
    except sqlite3.Error as e:
        logger.error(f"SQLite error retrieving users: {e}")
        return [] # 오류 발생 시 빈 리스트 반환


def insert_paper(title, date, summary_en, summary_ko, categories):
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with closing(conn.cursor()) as cursor:
                # title이 PRIMARY KEY이므로 중복 방지를 위해 INSERT OR IGNORE 사용
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO paper (title, date, summaryEN, summaryKO, categories)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (title, date, summary_en, summary_ko, categories),
                )
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Inserted new paper: {title}")
                else:
                    logger.info(f"Paper already exists or failed to insert (no rows affected): {title}")
    except sqlite3.Error as e:
        logger.error(f"SQLite error inserting paper '{title}': {e}")


def is_paper_exists(title):
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with closing(conn.cursor()) as cursor:
                result = cursor.execute(
                    "SELECT 1 FROM paper WHERE title = ?", (title,)
                ).fetchone()
                exists = result is not None
                # logger.debug(f"논문 '{title}' 존재 여부 확인: {exists}") # 선택 사항: 디버그 레벨 로그
                return exists
    except sqlite3.Error as e:
        logger.error(f"SQLite error checking if paper '{title}' exists: {e}")
        return False # 오류 발생 또는 존재하지 않는 것으로 간주
