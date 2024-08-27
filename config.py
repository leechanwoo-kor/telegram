import os
from dotenv import load_dotenv

load_dotenv()

# Database settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.getenv("DB_NAME", "telegram.db")
DB_PATH = os.path.join(BASE_DIR, "db", DB_NAME)

# Telegram settings
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Anthropic settings
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-3-haiku-20240307"

CLAUDE3_HAIKU = "claude-3-haiku-20240307"
CLAUDE3_SONNET = "claude-3-sonnet-20240229"
CLAUDE3_OPUS = "claude-3-opus-20240229"
CLAUDE3_5_SONNET = "claude-3-5-sonnet-20240620"

# Paper categories and languages
CATEGORIES = [
    "LLM",
    "Multimodal",
    "Computer vision",
    "Reinforcement learning",
    "Robotics",
    "Recommendation",
]
LANGS = ["KO", "EN"]

# Hugging Face settings
HUGGINGFACE_URL = "https://huggingface.co/"
HUGGINGFACE_PAPERS_URL = "https://huggingface.co/papers"

# Update interval (in seconds)
BOT_POLL_INTERVAL = 1  # 60 second
UPDATE_INTERVAL = 60 * 60  # 1 hour

# Logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"