from actions import *
from credentials import token
from loggingconfig import *
import telegram
import time
import sys
import os
import subprocess
import pandas as pd
from flask import Flask, request

bot = telegram.Bot(token=token)
app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

@app.route('/{}'.format(token), methods=['POST'])
def respond():
    """ Parses telegram update """
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    msg_id = update.message.message_id
    text = update.message.text.encode('utf-8').decode()
    logging.info(f"Recieved message {text}")
    if str(chat_id) not in ['855910557','1207015683'] : return
    newMessage(text)
    return 'ok'

def setWebhook(url):
    """ Sets telegram webhook """
    s = bot.setWebhook('{URL}/{HOOK}'.format(URL=url, HOOK=token))
    if s:
        logging.info("Webhook succesfully set up!")
    else:
        logging.error("Webhook setup failed.")

def ngrok():
    """ Starts ngrok and returns url """
    url = "https://" + subprocess.check_output(r"""curl --silent --show-error http://127.0.0.1:4040/api/tunnels | sed -nE 's/.*public_url":"https:..([^"]*).*/\1/p'""", shell=True).decode('utf-8').strip('\n')
    if url == 'https://':
        os.system('ngrok http 5000 > /dev/null &')
        time.sleep(10)
        url = "https://" + subprocess.check_output(r"""curl --silent --show-error http://127.0.0.1:4040/api/tunnels | sed -nE 's/.*public_url":"https:..([^"]*).*/\1/p'""", shell=True).decode('utf-8').strip('\n')
    if url == 'https://':
        logging.critical("Failure in obtaining ngrok url")
        exit()
    return url

if __name__ == '__main__':
    url = ngrok()
    logging.info(f"Ngrok url obtained - {url}")
    setWebhook(url)
    logging.info("Web app starting")
    app.run(threaded=True)