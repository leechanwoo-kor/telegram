import logging
import os
from config import LOG_FORMAT # Assuming config.py is accessible

DEFAULT_LOG_LEVEL = "INFO"

def setup_logging():
    """Sets up global logging configuration."""
    log_level_str = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Remove any existing handlers to avoid duplicate logs if setup_logging is called multiple times
    # or if other libraries (like uvicorn in some FastAPI setups) also configure the root logger.
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    logging.basicConfig(format=LOG_FORMAT, level=log_level, force=True) # force=True to override existing basicConfig if any
    
    # Disable httpx and httpcore logging to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level_str}")

if __name__ == '__main__':
    # Example of how to use it (for testing this module directly)
    setup_logging()
    logging.getLogger("my_app.test").info("This is an info message from test.")
    logging.getLogger("my_app.test").debug("This is a debug message from test (should not appear with INFO level).")
    os.environ['LOG_LEVEL'] = 'DEBUG' # Test changing log level via env var
    setup_logging() # Re-setup to apply new level
    logging.getLogger("my_app.test").debug("This is a debug message from test (should appear now).")
