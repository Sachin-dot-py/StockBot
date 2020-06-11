from stockdb import stockDB,msgrecordDB,predictionrecordDB
from credentials import token
from loggingconfig import *
from yahoo_fin import stock_info as si
from multiprocessing.pool import ThreadPool
import telegram
import logging
import time

bot = telegram.Bot(token=token)

def checkStock(stock_id):
    """ Checks price of stock from Yahoo! Finance """
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
    if not stock_datas:
        stocklist = stockDB.stockList()
        stock_ids = [stock_id for stock_id,_,_ in stocklist]
        stock_datas = checkStocksThreaded(stock_ids)
    for stock_id,stock_trigger,trigger_type in stocklist:
        stock_data = stock_datas[stock_id]
        quote_price,percentage,volume,day_range = stock_data
        last_time = msgrecordDB.getMsgRecord(stock_id,trigger_type)
        if last_time: date = last_time[2]
        message = None
        if last_time:
            if trigger_type == 'sell' and stock_data[0] <= float(stock_trigger):
                message = f"{stock_id} has gone below your trigger amount of ${stock_trigger} after going above at {date}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
            if trigger_type == 'buy' and stock_data[0] >= float(stock_trigger):
                message = message = f"{stock_id} has gone above your trigger amount of ${stock_trigger} after going below at {date}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
        else:
            if trigger_type == 'sell' and stock_data[0] >= float(stock_trigger):
                message = f"{stock_id} has gone above your trigger amount of ${stock_trigger}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
            if trigger_type == 'buy' and stock_data[0] <= float(stock_trigger):
                message = message = f"{stock_id} has gone below your trigger amount of ${stock_trigger}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
        if message and last_time:
            sendMessage(message)
            msgrecordDB.removeMsgRecord(stock_id,trigger_type)
        if message and not last_time:
            sendMessage(message)
            msgrecordDB.addMsgRecord(stock_id,trigger_type)
    logging.info("Performed quarterly stock price check")

def tradingMode():
    stock_ids = [stock_item[0] for stock_item in stockDB.stockList()]
    stock_data = checkStocksThreaded(stock_ids)
    QuarterlyCheck(stock_data)
    message = "Stocks Report:\n\nStock ID - Stock Price - Increase/Decrease %"
    for stock_id,stock_info in sorted(stock_data.items()):
        line = f"\n{stock_id} : ${stock_info[0]} , {'' if stock_info[1] < 0 else '+'}{stock_info[1]}%"
        message += line
    sendMessage(message)
    logging.info("Trading mode check performed succesfully")

def sendMessage(message,chat_id='1207015683'): # 1207015683, 855910557
    """ Send message via telegram to user """
    bot.sendMessage(chat_id=chat_id,text=message)

def newMessage(message):
    """ Parse a new message received from Telegram """
    if message[0] == '/':
        command = message.split()[0].strip('/')
    else:
        sendMessage(f"'{message}' is not a valid command.\nType /help for more info")
        return
    if command == 'help':
        sendMessage("Welcome to the Stock bot!\n\nList of commands:\n1. /help - Show this message and exit.\n2. /add_stock - Add a stock to the watch list.\n3. /remove_stock - Remove a stock from the watch list.\n4. /list_stock - Lists all stock and trigger prices in the watchlist\n5. /report - Get a report of the prices of the stocks in your Watchlist\n6. /get_stock - Check the details of any stock\n7. /run_check - Checks if stocks have gone past trigger price")
    elif command == 'add_stock':
        items = message.split()
        if len(items) != 4 or (items[3].lower() != 'buy' and items[3].lower() != 'sell'):
            sendMessage("Incorrect Usage!\n\nCorrect Usage:\n\t/add_stock AAPL 200 BUY\n\t/add_stock AAPL 200 SELL")
        else:
            trigger_type = 'sell' if items[3].lower() == 'sell' else 'buy'
            stockDB.addStock(items[1],items[2],trigger_type)
            try:
                stock_info = checkStock(items[1])
                sendMessage(f"{items[1]} stock added succesfully to watchlist!")
                line = f"Stock ID : {items[1]}\nStock Price : ${stock_info[0]}\nIncrease/Decrease % : {'' if stock_info[1] < 0 else '+'}{stock_info[1]}%\nVolume :  {stock_info[2]}\nDay's Range : {stock_info[3]}"
                sendMessage(line)
            except:
                stockDB.removeStock(items[1],trigger_type)
                sendMessage(f"Error: {items[1]} doesn't exist and therefore not added to watchlist. Check your spelling.")
    elif command == 'remove_stock':
        items = message.split()
        if len(items) != 3:
            sendMessage("Incorrect Usage!\n\nCorrect Usage:\n\t/remove_stock AAPL BUY")
        else:
            stockDB.removeStock(items[1],items[2])
            sendMessage(f"{items[1]} stock succesfully removed from watchlist!")
    elif command == 'change_stock':
        items = message.split()
        if len(items) != 4:
            sendMessage("Incorrect Usage!\n\nCorrect Usage:\n\t/change_stock AAPL 200 SELL")
        else:
            stockDB.changeStock(items[1],items[2],items[3])
            sendMessage(f"{items[1]} stock succesfully changed in watchlist!")
    elif command == 'list_stock':
        message = "Stock Watchlist:\n\nStock ID - Target Price - Buy/Sell"
        stock_list = stockDB.stockList()
        for stock in stock_list:
            line = f"\n{stock[0]} : ${stock[1]} - {stock[2]}"
            message += line
        sendMessage(message)
    elif command == 'report':
        message = "Stocks Report:\n\nStock ID - Stock Price - Increase/Decrease %"
        stock_ids = [stock_item[0] for stock_item in stockDB.stockList()]
        stock_data = checkStocksThreaded(stock_ids)
        for stock_id,stock_info in sorted(stock_data.items()):
            line = f"\n{stock_id} : ${stock_info[0]} , {'' if stock_info[1] < 0 else '+'}{stock_info[1]}%"
            message += line
        sendMessage(message)
    elif command == 'run_check':
        QuarterlyCheck()
        sendMessage("Stock check ran succesfully!")
    elif command == 'predictions_check':
        from predictions import predictionsCheck
        predictionsCheck()
        sendMessage("Predictions check ran succesfully")
    elif command == 'get_stock':
        items = message.split()
        if len(items) != 2:
            sendMessage("Incorrect Usage!\n\nCorrect Usage:\n\t/get_stock AAPL")
        else:
            stock_info = checkStock(items[1])
            line = f"Stock ID : {items[1]}\nStock Price : ${stock_info[0]}\nIncrease/Decrease % : {'' if stock_info[1] < 0 else '+'}{stock_info[1]}%\nVolume :  {stock_info[2]}\nDay's Range : {stock_info[3]}"
            sendMessage(line)
    else:
        sendMessage(f"Invalid command /{command}!")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        if not (time.strftime("%H") == '21' and int(time.strftime("%M")) < 30):
            tradingMode()
    else:
        QuarterlyCheck()