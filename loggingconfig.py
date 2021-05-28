import logging
import traceback
import telegram
import sys
from credentials import logfile, developer_chat_id, token, debug

bot = telegram.Bot(token=token)

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handler for unhandled exceptions that will write to the log"""
    if issubclass(exc_type, KeyboardInterrupt):
        print("Program interrupted by user")
        return

    firstline = f"<i>{str(exc_type).strip('<class>')}</i>: {exc_value}".lstrip(" ").rstrip(' ').replace("'", "")
    traceback_info = ''.join(traceback.format_tb(exc_traceback)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    logging.critical("", exc_info=(exc_type, exc_value, exc_traceback))
    bot.send_message(developer_chat_id, f'<b>{firstline}</b>\n\n<pre><code class="language-python">{traceback_info}</code></pre>' , parse_mode='HTML')

if debug:
    logging.basicConfig(filename=logfile,
                    format='%(asctime)s ~ %(levelname)s : %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S',
                    level=logging.DEBUG)
else:
    logging.basicConfig(filename=logfile,
                        format='%(asctime)s ~ %(levelname)s : %(message)s',
                        datefmt='%d-%m-%Y %H:%M:%S',
                        level=logging.INFO)
sys.excepthook = handle_unhandled_exception
