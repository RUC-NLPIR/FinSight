"""Thread-safe logging utilities."""
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
import contextvars


_cv_agent_id: contextvars.ContextVar[str] = contextvars.ContextVar('agent_id', default='N/A')
_cv_agent_name: contextvars.ContextVar[str] = contextvars.ContextVar('agent_name', default='N/A')


class AgentContextFilter(logging.Filter):
    """Injects agent context into log records."""
    
    def filter(self, record):
        record.agent_id = _cv_agent_id.get()
        record.agent_name = _cv_agent_name.get()
        return True


class Logger:
    """Thread-safe singleton logger."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not Logger._initialized:
            self._setup_logger()
            Logger._initialized = True
    
    def _setup_logger(self, log_dir: Optional[str] = None, log_level: int = logging.INFO):
        """Configure the logging system."""
        self.logger = logging.getLogger('finsight')
        self.logger.setLevel(log_level)
        
        if self.logger.handlers:
            return
        
        detailed_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(agent_name)s:%(agent_id)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(agent_name)s:%(agent_id)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        context_filter = AgentContextFilter()
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        console_handler.addFilter(context_filter)
        self.logger.addHandler(console_handler)
        
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'finsight.log')
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(detailed_formatter)
            file_handler.addFilter(context_filter)
            self.logger.addHandler(file_handler)
    
    def set_log_dir(self, log_dir: str):
        """Configure the directory used for log files."""
        if not Logger._initialized:
            self._setup_logger(log_dir=log_dir)
        else:
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, 'finsight.log')
                detailed_formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)s] [%(agent_name)s:%(agent_id)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                context_filter = AgentContextFilter()
                
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=10*1024*1024,
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(detailed_formatter)
                file_handler.addFilter(context_filter)
                
                has_file_handler = any(
                    isinstance(h, RotatingFileHandler) and h.baseFilename == log_file
                    for h in self.logger.handlers
                )
                if not has_file_handler:
                    self.logger.addHandler(file_handler)
    
    def set_agent_context(self, agent_id: str, agent_name: str):
        """Set the agent identifiers for the current async context."""
        _cv_agent_id.set(agent_id)
        _cv_agent_name.set(agent_name)
    
    def clear_agent_context(self):
        """Reset the agent identifiers for the current async context (restore to N/A)."""
        _cv_agent_id.set('N/A')
        _cv_agent_name.set('N/A')
    
    def debug(self, message: str):
        """Log a DEBUG-level message."""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log an INFO-level message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log a WARNING-level message."""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Log an ERROR-level message."""
        self.logger.error(message, exc_info=exc_info)
    
    def exception(self, message: str):
        """Log an exception with stack trace."""
        self.logger.exception(message)
    
    def critical(self, message: str):
        """Log a CRITICAL-level message."""
        self.logger.critical(message)
    
    def addHandler(self, handler):
        """Add a handler to the underlying logger."""
        self.logger.addHandler(handler)
    
    def removeHandler(self, handler):
        """Remove a handler from the underlying logger."""
        self.logger.removeHandler(handler)


# Global logger singleton
_logger_instance = None


def get_logger() -> Logger:
    """Return the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance


def setup_logger(log_dir: Optional[str] = None, log_level: int = logging.INFO) -> Logger:
    """Configure and return the logger instance."""
    logger = get_logger()
    logger._setup_logger(log_dir=log_dir, log_level=log_level)
    if log_dir:
        logger.set_log_dir(log_dir)
    return logger


# Convenience wrappers for the global logger
def debug(message: str):
    """Log a DEBUG-level message."""
    get_logger().debug(message)


def info(message: str):
    """Log an INFO-level message."""
    get_logger().info(message)


def warning(message: str):
    """Log a WARNING-level message."""
    get_logger().warning(message)


def error(message: str, exc_info: bool = False):
    """Log an ERROR-level message."""
    get_logger().error(message, exc_info=exc_info)


def exception(message: str):
    """Log an exception."""
    get_logger().exception(message)


def critical(message: str):
    """Log a CRITICAL-level message."""
    get_logger().critical(message)

