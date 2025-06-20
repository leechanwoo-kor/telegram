import logging
import asyncio
from utils.logging_config import setup_logging

setup_logging()

from bot import run_bot
from paper import run_paper
from database import initialize_database

logger = logging.getLogger(__name__)


async def main():
    """
    애플리케이션의 메인 진입점입니다.
    데이터베이스를 초기화하고 봇과 논문 스크래핑을 비동기적으로 실행합니다.
    """
    bot_task = None
    paper_task = None
    try:
        # 데이터베이스 초기화
        initialize_database()

        # 봇과 논문 업데이트를 위한 비동기 태스크 생성
        bot_task = asyncio.create_task(run_bot())
        paper_task = asyncio.create_task(run_paper())

        # 두 태스크를 동시에 실행
        await asyncio.gather(bot_task, paper_task)

    except asyncio.CancelledError:
        logger.info("메인 태스크가 취소되었습니다.")
    except Exception as e:
        logger.error(f"메인 태스크 실행 중 오류 발생: {e}", exc_info=True)
    finally:
        logger.info("애플리케이션 종료를 시작합니다.")
        # 실행 중인 태스크가 있다면 취소합니다.
        tasks = [t for t in (bot_task, paper_task) if t is not None]
        for task in tasks:
            if not task.done():
                task.cancel()
        
        if tasks:
            # 모든 태스크가 취소될 때까지 대기합니다.
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("모든 백그라운드 태스크가 취소되었습니다.")
        
        logger.info("애플리케이션이 성공적으로 종료되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())
