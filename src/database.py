import sqlite3
from contextlib import closing
from config import DB_PATH, CATEGORIES


def initialize_database():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat (
                    chatId TEXT NOT NULL PRIMARY KEY,
                    lang TEXT DEFAULT EN,
                    category TEXT DEFAULT '%s')
                    """
                % (",".join(CATEGORIES))
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS paper (
                    title TEXT NOT NULL,
                    date DATE,
                    summaryEN TEXT,
                    summaryKO TEXT,
                    categories TEXT
                )
                """
            )
            conn.commit()
    print("Database initialized")


def initialize_chat(chat_id):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "INSERT OR IGNORE INTO chat (chatId) VALUES (?)", (str(chat_id),)
            )
            conn.commit()


def update_chat(chat_id, lang=None, category=None):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with closing(conn.cursor()) as cursor:
            if lang and category:
                cursor.execute(
                    "UPDATE chat SET lang = ?, category = ? WHERE chatId = ?",
                    (lang, category, str(chat_id)),
                )
            elif lang:
                cursor.execute(
                    "UPDATE chat SET lang = ? WHERE chatId = ?", (lang, str(chat_id))
                )
            elif category:
                cursor.execute(
                    "UPDATE chat SET category = ? WHERE chatId = ?",
                    (category, str(chat_id)),
                )
            conn.commit()


def get_users():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with closing(conn.cursor()) as cursor:
            return cursor.execute("SELECT * FROM chat").fetchall()


def insert_paper(title, date, summary_en, summary_ko, categories):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO paper (title, date, summaryEN, summaryKO, categories)
                VALUES (?, ?, ?, ?, ?)
            """,
                (title, date, summary_en, summary_ko, categories),
            )
            conn.commit()


def is_paper_exists(title):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with closing(conn.cursor()) as cursor:
            return (
                cursor.execute(
                    "SELECT 1 FROM paper WHERE title = ?", (title,)
                ).fetchone()
                is not None
            )
