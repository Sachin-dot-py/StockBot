from actions import newMessage, sendMessage, checkStocksThreaded
from stockdb import StockDB
from credentials import token
from loggingconfig import logging
import telegram
import time
import os
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template

bot = telegram.Bot(token=token)
app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

@app.route('/{}'.format(token), methods=['POST'])
def respond():
    """ Parses telegram update """
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    text = update.message.text.encode('utf-8').decode()
    logging.info(f"Recieved message {text}")
    if str(chat_id) not in ['855910557','1207015683'] : return
    newMessage(text)
    return 'ok'

@app.route('/')
def index():
    logging.info("Stock Dashboard session started")
    return render_template('index.html')

@app.route('/stock_news')
def stocknews():
    news = ''
    link = 'https://news.google.com/rss' # Change
    req = requests.get(link)
    soup = BeautifulSoup(req.text,'lxml')
    items = soup.find_all('item')
    for item in items:
        title = item.find('title').text
        news += f"{title} | "
    return news

@app.route('/stock_data')
def stockdata():
    indexes = ['^DJI', '^IXIC', '^GSPC']
    index_names = ['Dow Jones', 'Nasdaq', 'S&P 500']
    index_data = checkStocksThreaded(indexes).values()
    index_datas = dict(zip(index_names, index_data))
    stockDB = StockDB()
    stock_list = [stock[0] for stock in stockDB.stockList()]
    stock_data = checkStocksThreaded(stock_list)
    updated_time = time.strftime("%H:%M:%S")
    logging.info("Updated dashboard stock data")
    return render_template('stock_table.html', stock_data=stock_data, updated_time=updated_time, index_datas=index_datas)

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

def ngrok():
    """ Starts ngrok and returns url """
    try:
        req = requests.get('http://127.0.0.1:4040/api/tunnels')
        soup = BeautifulSoup(req.text, 'lxml')
        tunnelsjson = json.loads(soup.find('p').text)
        url = tunnelsjson['tunnels'][0]['public_url'].replace('http://','https://')
    except:
        os.system('ngrok http 4000 > /dev/null &')
        time.sleep(10)
        try:
            req = requests.get('http://127.0.0.1:4040/api/tunnels')
            soup = BeautifulSoup(req.text, 'lxml')
            tunnelsjson = json.loads(soup.find('p').text)
            url = tunnelsjson['tunnels'][0]['public_url'].replace('http://','https://')
        except:
            logging.critical("Failure in obtaining ngrok url")
            exit()
    return url

def create_app():
    app = Flask(__name__)
    url = ngrok()
    logging.info(f"Ngrok url obtained - {url}")
    setWebhook(url)
    logging.info("Web app starting")
    return app

app = create_app()

if __name__ == '__main__':
    app.run(threaded=True)