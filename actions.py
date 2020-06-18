from stockdb import StockDB,MsgRecordDB,PredictionRecordDB
from messageparse import newMessage
from predictions import predictionsCheck
from news import NewsDB,NewsTriggerDB
from credentials import token, chat_id
from loggingconfig import logging
from yahoo_fin import stock_info as si
from multiprocessing.pool import ThreadPool
import telegram
import logging
import time
import sys

bot = telegram.Bot(token=token)

def checkStock(stock_id):
    """ Checks price of stock from Yahoo! Finance """
    try:
        stock = si.get_quote_table(stock_id, dict_result = True)
    except:
        stock = si.get_quote_table(stock_id, dict_result = True)
    quote_price = round(stock['Quote Price'],2)
    close_price = stock['Previous Close']
    percentage = round(((quote_price-close_price)/close_price)*100,2)
    day_range = stock["Day's Range"]
    volume = int(stock['Volume'])
    return (quote_price,percentage,volume,day_range)

def checkStocksThreaded(stock_ids : list) -> dict:
    stock_ids = list(dict.fromkeys(stock_ids))
    with ThreadPool(64) as pool:
        results = pool.map(checkStock, stock_ids)
    return dict(zip(stock_ids,results))

def QuarterlyCheck(stock_datas=None):
    """ 15 minute check during trading hours to make sure stock price has not hit target """
    stockDB = StockDB()
    msgrecordDB = MsgRecordDB()
    stocklist = stockDB.stockList()
    stock_ids = [stock_id for stock_id,_,_ in stocklist]
    if not stock_datas:
        stock_datas = checkStocksThreaded(stock_ids)
    for stock_id,stock_trigger,trigger_type in stocklist:
        stock_data = stock_datas[stock_id]
        last_time = msgrecordDB.getMsgRecord(stock_id,trigger_type)
        if last_time: date = last_time[2]
        message = None
        if last_time:
            if trigger_type == 'sell' and stock_data[0] <= float(stock_trigger):
                message = f"{stock_id} has gone below your trigger amount of ${stock_trigger} after going above at {date}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
            if trigger_type == 'buy' and stock_data[0] >= float(stock_trigger):
                message = f"{stock_id} has gone above your trigger amount of ${stock_trigger} after going below at {date}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
        else:
            if trigger_type == 'sell' and stock_data[0] >= float(stock_trigger):
                message = f"{stock_id} has gone above your trigger amount of ${stock_trigger}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
            if trigger_type == 'buy' and stock_data[0] <= float(stock_trigger):
                message = f"{stock_id} has gone below your trigger amount of ${stock_trigger}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
        if message and last_time:
            sendMessage(message)
            msgrecordDB.removeMsgRecord(stock_id,trigger_type)
        if message and not last_time:
            sendMessage(message)
            msgrecordDB.addMsgRecord(stock_id,trigger_type)
    logging.info("Performed quarterly stock price check")

def tradingMode():
    stockDB = StockDB()
    stock_ids = [stock_item[0] for stock_item in stockDB.stockList()]
    stock_data = checkStocksThreaded(stock_ids)
    QuarterlyCheck(stock_data)
    message = "Stocks Report:\n\nStock ID - Stock Price - Increase/Decrease %"
    for stock_id,stock_info in sorted(stock_data.items()):
        line = f"\n{stock_id} : ${stock_info[0]} , {'' if stock_info[1] < 0 else '+'}{stock_info[1]}%"
        message += line
    sendMessage(message)
    logging.info("Trading mode check performed succesfully")

def sendMessage(message,chatid=None): # 1207015683, 855910557
    if not chatid:
        chatid = chat_id
    """ Send message via telegram to user """
    bot.sendMessage(chat_id=chatid,text=message)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        if not (time.strftime("%H") == '21' and int(time.strftime("%M")) < 30):
            tradingMode()
    else:
        QuarterlyCheck()