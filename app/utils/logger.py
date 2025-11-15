import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(
    name: str,
    log_file: str,
    level: str = "INFO",
    max_bytes: int = 10485760,
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum size of log file before rotation (default 10MB)
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def setup_application_loggers(log_dir: str = "./logs", level: str = "INFO") -> None:
    """
    Set up all application loggers.
    
    Args:
        log_dir: Directory for log files
        level: Logging level
    """
    os.makedirs(log_dir, exist_ok=True)
    
    loggers_config = [
        ("app.main", "app.log"),
        ("app.api", "api.log"),
        ("app.services", "services.log"),
        ("app.database", "database.log"),
        ("app.errors", "errors.log"),
    ]
    
    for logger_name, log_file in loggers_config:
        log_path = os.path.join(log_dir, log_file)
        setup_logger(logger_name, log_path, level)
    
    main_logger = get_logger("app.main")
    main_logger.info(f"Application loggers initialized at {datetime.now()}")