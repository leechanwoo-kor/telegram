import asyncio
import logging
from config import LOG_FORMAT
from src.database import initialize_database
from src.paper import run_paper
from src.bot import run_bot

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    try:
        # Initialize the database
        initialize_database()

        # Create tasks for bot and paper update
        bot_task = asyncio.create_task(run_bot())
        paper_task = asyncio.create_task(run_paper())

        # Run both tasks concurrently
        await asyncio.gather(bot_task, paper_task)

    except asyncio.CancelledError:
        logger.info("Main task was cancelled")
    except Exception as e:
        logger.error(f"An error occurred in main: {e}")
    finally:
        # Cancel any pending tasks
        for task in [bot_task, paper_task]:
            if not task.done():
                task.cancel()

        # Wait for tasks to be cancelled
        await asyncio.gather(bot_task, paper_task, return_exceptions=True)
        logger.info("All tasks have been cancelled")


if __name__ == "__main__":
    asyncio.run(main())
