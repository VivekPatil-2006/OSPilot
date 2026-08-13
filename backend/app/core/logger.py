import os
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "ospilot") -> logging.Logger:
    """Configures structured logger with console stdout and RotatingFileHandler writing to data/logs/ospilot.log."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Stream Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Rotating File Handler
        try:
            log_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "logs"))
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "ospilot.log")

            file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass
        
    return logger

logger = setup_logger()

