import logging
import sys
from credentials import logfile

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handler for unhandled exceptions that will write to the log"""
    if issubclass(exc_type, KeyboardInterrupt):
        print("Program interrupted by user")
        return
    logging.critical("", exc_info=(exc_type, exc_value, exc_traceback))

logging.basicConfig(filename=logfile, format='%(asctime)s ~ %(levelname)s : %(message)s', datefmt='%d-%m-%Y %H:%M:%S',level=logging.INFO)
sys.excepthook = handle_unhandled_exception