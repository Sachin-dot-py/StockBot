from portfolio import PortfolioDB
from actions import newMessage, sendMessage, checkStocksThreaded, cwd
from stockdb import StockDB
from credentials import token, mbtoken
from loggingconfig import logging, handle_unhandled_exception
import telegram
import time
import os
import sys
import subprocess
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template

try:
    subprocess.call("pip3 install git+https://github.com/Sachin-dot-py/MovieBot.git --upgrade", shell=True)
    import moviebot as apy
except:
    logging.critical("Unable to import MovieBot")

import currency # Get latest currency rate
bot = telegram.Bot(token=token)
mbot = telegram.Bot(token=mbtoken)
app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
os.chdir(cwd)


@app.route('/{}'.format(mbtoken), methods=['POST'])
def moviebot_respond():
    """ Parses telegram update """
    os.chdir(os.path.expanduser("~"))
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.effective_chat.id
    if str(chat_id) not in ['855910557', '1207015683']:
        logging.warning(f"Unknown chat id: {chat_id}")
        return
    try:
        text = update.message.text.encode('utf-8').decode()
        logging.info(f"MOVIEBOT: Recieved message {text}")
    except:
        logging.info("MOVIEBOT: Recieved message")
    try:
        apy.dispatcher.process_update(update)
    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        handle_unhandled_exception(exc_type, exc_value, exc_tb)
    return 'ok'

@app.route('/{}'.format(token), methods=['POST'])
def respond():
    """ Parses telegram update """
    os.chdir(cwd)
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.effective_chat.id
    if str(chat_id) not in ['855910557', '1207015683']:
        logging.warning(f"Unknown chat id: {chat_id}")
        return
    try:
        text = update.message.text.encode('utf-8').decode()
    except:
        text = update.channel_post.text.encode('utf-8').decode()
    logging.info(f"Recieved message {text}")
    try:
        newMessage(text)
    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        handle_unhandled_exception(exc_type, exc_value, exc_tb)
    return 'ok'


@app.route('/')
def index():
    # Cronjob turns off the dashboard everyday at 1 AM
    logging.info("Stock Dashboard session started")
    return render_template('index.html')


@app.route('/stock_news')
def stocknews():
    start = time.time()
    news = ''
    link = 'https://www.cnbc.com/id/100003114/device/rss/rss.html'  # Change
    req = requests.get(link)
    soup = BeautifulSoup(req.text, 'lxml')
    items = soup.find_all('item')
    for item in items:
        title = item.find('title').text
        news += f"{title} | "
    end = time.time()
    logging.info(f"Updated news in {round(end-start, 2)} seconds")
    return news


@app.route('/stock_data')
def stockdata():
    start = time.time()
    indexes = ['^DJI', '^IXIC', '^GSPC']
    index_names = ['Dow Jones', 'Nasdaq', 'S&P 500']
    index_data = checkStocksThreaded(indexes).values()
    index_datas = {index_name : [int(index_data[0]),index_data[1]] for index_name, index_data in zip(index_names, index_data)}
    stockDB = StockDB()
    pfdb = PortfolioDB()
    stock_list = list(set(pfdb.CurrentStocks() + [stock[0] for stock in stockDB.stockList()]))
    stock_data = checkStocksThreaded(stock_list)
    updated_time = time.strftime("%H:%M:%S")
    end = time.time()
    logging.info(f"Updated dashboard data in {round(end-start, 2)} seconds")
    return render_template('stock_table.html',
                           stock_data=stock_data,
                           updated_time=updated_time,
                           index_datas=index_datas)


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


def setWebhook(url):
    """ Sets telegram webhook """
    s = bot.setWebhook('{URL}/{HOOK}'.format(URL=url, HOOK=token))
    if s:
        logging.info("Webhook succesfully set up!")
    else:
        logging.error("Webhook setup failed.")

def mbsetWebhook(url):
    """ Sets telegram webhook """
    s = mbot.setWebhook('{URL}/{HOOK}'.format(URL=url, HOOK=mbtoken))
    if s:
        logging.info("Movie Bot Webhook succesfully set up!")
    else:
        logging.error("Movie Bot Webhook setup failed.")


def ngrok():
    """ Starts ngrok and returns url """
    try:
        req = requests.get('http://127.0.0.1:4040/api/tunnels')
        soup = BeautifulSoup(req.text, 'lxml')
        tunnelsjson = json.loads(soup.find('p').text)
        url = tunnelsjson['tunnels'][0]['public_url'].replace(
            'http://', 'https://')
    except:
        os.system('ngrok http 4000 > /dev/null &')
        time.sleep(10)
        try:
            req = requests.get('http://127.0.0.1:4040/api/tunnels')
            soup = BeautifulSoup(req.text, 'lxml')
            tunnelsjson = json.loads(soup.find('p').text)
            url = tunnelsjson['tunnels'][0]['public_url'].replace(
                'http://', 'https://')
        except:
            logging.critical("Failure in obtaining ngrok url")
            exit()
    return url


url = ngrok()
logging.info(f"Ngrok url obtained - {url}")
setWebhook(url)
mbsetWebhook(url)
logging.info("Web app starting")
sendMessage("Stock Bot has restarted")

if __name__ == '__main__':
    app.run(port=4000, threaded=True)
    