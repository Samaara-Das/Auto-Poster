'''
This is for setting up a logger for the application. Any file can use this to create its own logger.
This was done to avoid repetition of code.
'''

from logging import getLogger, FileHandler, StreamHandler, Formatter, DEBUG, INFO, WARNING, ERROR, CRITICAL
import sys
from app.configuration.configuration import Config

def logger(logger_name, logger_level=INFO):
    '''This sets up a logger and returns it'''
    logger = getLogger(logger_name)
    logger.setLevel(logger_level)
    
    date_format = "%m.%d.%y %H:%M:%S"
    formatter = Formatter('%(name)s.py %(funcName)s() %(levelname)s: %(message)s %(asctime)s', datefmt=date_format)

    file_handler = FileHandler(Config.LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create a StreamHandler with utf-8 encoding for sys.stdout
    stream_handler = StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def clear_log_file():
    '''This function clears the contents of the specified log file'''
    file = Config.LOG_FILE
    try:
        with open(file, 'w') as log_file:
            log_file.write('')
        print(f"Contents of {file} have been cleared.")
    except IOError as e:
        print(f"Error clearing {file}: {e}")

