from actions import *
from credentials import token,logfile
import telegram
import logging
import sys
import os
import subprocess
import pandas as pd
from flask import Flask, request

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handler for unhandled exceptions that will write to the log"""
    if issubclass(exc_type, KeyboardInterrupt):
        # call the default excepthook if it is a KeyboardInterrupt
        print("Program interrupted by user")
        return
    logging.critical("", exc_info=(exc_type, exc_value, exc_traceback))

logging.basicConfig(filename=logfile, format='%(asctime)s ~ %(levelname)s : %(message)s', datefmt='%d-%m-%Y %H:%M:%S',level=logging.INFO)
sys.excepthook = handle_unhandled_exception
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

@app.route('/check_predictions',methods=['POST'])
def getPredictions():
    """ Recieves predictions and checks if stocks in the watchlist are included in it """
    request_data = request.get_json(force=True)
    df = pd.read_json(request_data).drop('index',axis=1)
    stocks = []
    stocks_temp = stockDB.stockList()
    for stock in stocks_temp:
        stocks.append(stock[0].upper())
    for result in df.values:
        ticker = result[1]
        if ticker.upper() in stocks:
            message = f"Prediction for {result[0]} ({result[1]}):\nFirm: {result[2]}\nRatings Change: {result[3]}\nPrice Target: {result[4]}"
            sendMessage(message)
    logging.info('Predictions check ran succesfully!')
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