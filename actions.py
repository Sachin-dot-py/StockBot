from stockdb import StockDB, MsgRecordDB, PredictionRecordDB
from state import StateDB
from portfolio import PortfolioDB
from predictions import predictionsCheck
from news import NewsDB, NewsTriggerDB
from credentials import token, chat_id, news_bot_token, FINNHUB_API_KEY, FINNHUB_API_KEY_2, FINNHUB_API_KEY_3
from loggingconfig import logging
from yahoo_fin import stock_info as si
from multiprocessing.pool import ThreadPool
import telegram
import logging
import time
import sys
import subprocess
import finnhub
import requests

bot = telegram.Bot(token=token)
news_bot = telegram.Bot(news_bot_token)
client = finnhub.Client(api_key=FINNHUB_API_KEY)
client2 = finnhub.Client(api_key=FINNHUB_API_KEY_2)
client3 = finnhub.Client(api_key=FINNHUB_API_KEY_3)

def checkStock(stock_id):
    """ Checks price of stock from Finnhub """
    try:
        try:
            stock = client.quote(stock_id)
        except:
            try:
                stock = client2.quote(stock_id)
            except:
                stock = client3.quote(stock_id)
        quote_price = round(stock['c'], 2)
        close_price = stock['pc']
        percentage = round(((quote_price - close_price) / close_price) * 100, 2)
        return (quote_price, percentage, 0, "") # 0, 0 for backward compatibility
    except:
        return _checkStock(stock_id)

def _checkStock(stock_id):
    """ Checks price of stock from Yahoo! Finance """
    try:
        stock = si.get_quote_table(stock_id, dict_result=True)
    except:
        try:
            stock = si.get_quote_table(stock_id, dict_result=True)
        except:
            try:
                stock = si.get_quote_table(stock_id, dict_result=True)
            except:
                stock = si.get_quote_table(stock_id, dict_result=True)
    quote_price = round(stock['Quote Price'], 2)
    close_price = stock['Previous Close']
    percentage = round(((quote_price - close_price) / close_price) * 100, 2)
    day_range = stock["Day's Range"]
    volume = int(stock['Volume'])
    return (quote_price, percentage, volume, day_range)

def _checkStocksThreaded(stock_ids: list) -> dict:
    stock_ids = list(dict.fromkeys(stock_ids))
    results = dict()
    for stock_id in stock_ids:
        try:
            result = checkStock(stock_id)
        except:
            result = _checkStock(stock_id)
        results[stock_id] = result
    return results    

def checkStocksThreaded(stock_ids: list) -> dict:
    stock_ids = list(dict.fromkeys(stock_ids))
    with ThreadPool(128) as pool:
        results = pool.map(checkStock, stock_ids)
    return dict(zip(stock_ids, results))

def conversionRate(source : str="USD", target : str="SGD"):
    """ Get the conversion rate from one currency to another currency """
    resp = requests.get(f"https://api.exchangeratesapi.io/latest?symbols={target}&base={source}").json()
    rate = resp.get('rates')[target]
    return rate

def QuarterlyCheck(stock_datas=None):
    """ 15 minute check during trading hours to make sure stock price has not hit target """
    stockDB = StockDB()
    msgrecordDB = MsgRecordDB()
    stocklist = stockDB.stockList()
    stock_ids = [stock_id for stock_id, _, _ in stocklist]
    if not stock_datas:
        stock_datas = checkStocksThreaded(stock_ids)
    for stock_id, stock_trigger, trigger_type in stocklist:
        stock_data = stock_datas[stock_id]
        last_time = msgrecordDB.getMsgRecord(stock_id, trigger_type)
        if last_time: date = last_time[2]
        message = None
        if last_time:
            if trigger_type == 'sell' and stock_data[0] <= float(
                    stock_trigger):
                message = f"{stock_id} has gone below your trigger amount of ${stock_trigger} after going above at {date}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
            if trigger_type == 'buy' and stock_data[0] >= float(stock_trigger):
                message = f"{stock_id} has gone above your trigger amount of ${stock_trigger} after going below at {date}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
        else:
            if trigger_type == 'sell' and stock_data[0] >= float(
                    stock_trigger):
                message = f"{stock_id} has gone above your trigger amount of ${stock_trigger}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
            if trigger_type == 'buy' and stock_data[0] <= float(stock_trigger):
                message = f"{stock_id} has gone below your trigger amount of ${stock_trigger}.\nCurrent Price: ${stock_data[0]}\nPercentage = {'' if stock_data[1] < 0 else '+'}{stock_data[1]}%"
        if message and last_time:
            sendMessage(message)
            msgrecordDB.removeMsgRecord(stock_id, trigger_type)
        if message and not last_time:
            sendMessage(message)
            msgrecordDB.addMsgRecord(stock_id, trigger_type)
    # stock_datas_n = {stock_id: details[0] for stock_id, details in stock_datas.items()}
    # pfdb = PortfolioDB()
    # pf = pfdb.getPortfolio(stock_datas_n)
    logging.info("Performed quarterly stock price check")


def tradingMode():
    stockDB = StockDB()
    stock_ids = [stock_item[0] for stock_item in stockDB.stockList()]
    stock_data = checkStocksThreaded(stock_ids)
    QuarterlyCheck(stock_data)
    message = "Stocks Report:\n\nStock ID - Stock Price - Increase/Decrease %"
    for stock_id, stock_info in sorted(stock_data.items()):
        line = f"\n{stock_id} : ${stock_info[0]} , {'' if stock_info[1] < 0 else '+'}{stock_info[1]}%"
        message += line
    sendMessage(message)
    logging.info("Trading mode check performed succesfully")


def sendMessage(message, chatid=None):  # 1207015683, 855910557
    if not chatid:
        chatid = chat_id
    """ Send message via telegram to user """
    bot.sendMessage(chat_id=chatid, text=message)

def add_portfolio(message):
    stateDB = StateDB()
    pfDB = PortfolioDB()
    if message.lower() == "c":
        stateDB.deleteState()
        sendMessage("Process cancelled succesfully")
        return
    stage = len(stateDB.getVars())
    if stage == 1:
        stateDB.addVar(message.upper())
        sendMessage("How many stocks have you bought/sold? eg. 31 (type C to cancel)")
    if stage == 2:
        try:
            number = int(message)
        except:
            sendMessage("That's not a valid number! Try again.")
        else:
            stateDB.addVar(number)
            sendMessage("How much did you buy/sell it for? eg. 20.67 (type C to cancel)")
    if stage == 3:
        try:
            price = float(message.strip("$"))
        except:
            sendMessage("That's not a valid price! Try again.")
        else:
            stateDB.addVar(price)
            sendMessage("How much was the commission price? eg. 7.50 (type C to cancel)")
    if stage == 4:
        try:
            price = float(message.strip("$"))
        except:
            sendMessage("That's not a valid price! Try again.")
        else:
            stateDB.addVar(price)
            sendMessage("When did you buy/sell it? eg. 02/04/2020 (type C to cancel)")
    if stage == 5:
        try:
            day, month, year = [int(x) for x in message.split("/")]
            
        except:
            sendMessage("That's not a valid year! Try again.")
        else:
            stateDB.addVar(f"{day}/{month}/{year}")
            sendMessage("Are you buying or selling stock? Reply with 'buy' or 'sell'.")
    if stage == 6:
        if message.lower() not in ['buy', 'sell']:
            sendMessage("That's not a valid option! Try again.")
        else:
            stateDB.addVar(message.lower())
            data = stateDB.getVars()
            pfDB.addStock(*data[1:])
            sendMessage(f"Ticker: {data[1]}\nQuantity: {data[2]}\nUnit Price: ${data[3]}\nCommission Price: ${data[4]}\nDate: {data[5]}\nType: {data[6]}\nAdded succesfully to portfolio")
            stateDB.deleteState()


def newMessage(message):
    """ Parse a new message received from Telegram """
    if message[0] == '/':
        command = message.split()[0].strip('/')
    else:
        stateDB = StateDB()
        state = stateDB.getState()
        if state: 
            if state == "add_portfolio":
                add_portfolio(message)
        else:
            sendMessage(
                f"'{message}' is not a valid command.\nType /help for more info")
        return
    if command == 'help':
        sendMessage("Welcome to the Stock bot!\nMade by Sachin Ramanathan")
    elif command == 'add_stock':
        stockDB = StockDB()
        items = message.split()
        if len(items) != 4 or (items[3].lower() != 'buy'
                               and items[3].lower() != 'sell'):
            sendMessage(
                "Incorrect Usage!\n\nCorrect Usage:\n\t/add_stock AAPL 200 BUY\n\t/add_stock AAPL 200 SELL"
            )
        else:
            trigger_type = 'sell' if items[3].lower() == 'sell' else 'buy'
            stockDB.addStock(items[1], items[2], trigger_type)
            try:
                stock_info = checkStock(items[1])
                sendMessage(
                    f"{items[1]} stock added succesfully to watchlist!")
                line = f"Stock ID : {items[1]}\nStock Price : ${stock_info[0]}\nIncrease/Decrease % : {'' if stock_info[1] < 0 else '+'}{stock_info[1]}%\nVolume :  {stock_info[2]}\nDay's Range : {stock_info[3]}"
                sendMessage(line)
            except:
                stockDB.removeStock(items[1], trigger_type)
                sendMessage(
                    f"Error: {items[1]} doesn't exist and therefore not added to watchlist. Check your spelling."
                )
    elif command == 'remove_stock':
        stockDB = StockDB()
        items = message.split()
        if len(items) != 3:
            sendMessage(
                "Incorrect Usage!\n\nCorrect Usage:\n\t/remove_stock AAPL BUY")
        else:
            stockDB.removeStock(items[1], items[2])
            sendMessage(
                f"{items[1]} stock succesfully removed from watchlist!")
    elif command == 'change_stock':
        stockDB = StockDB()
        items = message.split()
        if len(items) != 4:
            sendMessage(
                "Incorrect Usage!\n\nCorrect Usage:\n\t/change_stock AAPL 200 SELL"
            )
        else:
            try:
                stockDB.changeStock(items[1], items[2], items[3])
                sendMessage(
                    f"{items[1]} stock succesfully changed in watchlist!")
            except:
                sendMessage(
                    f"Error changing details of {items[1]} in watchlist!")
    elif command == 'list_stock':
        stockDB = StockDB()
        message = "Stock Watchlist:\n\nStock ID - Target Price - Buy/Sell"
        stock_list = stockDB.stockList()
        for stock in stock_list:
            line = f"\n{stock[0]} : ${stock[1]} - {stock[2]}"
            message += line
        sendMessage(message)
    elif command == 'report':
        stockDB = StockDB()
        message = "Stocks Report:\n\nStock ID - Stock Price - Increase/Decrease %"
        stock_ids = [stock_item[0] for stock_item in stockDB.stockList()]
        stock_data = checkStocksThreaded(stock_ids)
        for stock_id, stock_info in sorted(stock_data.items()):
            line = f"\n{stock_id} : ${stock_info[0]} , {'' if stock_info[1] < 0 else '+'}{stock_info[1]}%"
            message += line
        sendMessage(message)
    elif command == 'run_check':
        QuarterlyCheck()
        sendMessage("Stock check ran succesfully!")
    elif command == 'predictions_check':
        predictionsCheck()
        sendMessage("Predictions check ran succesfully")
    elif command == 'news_check':
        stockDB = StockDB()
        newsDB = NewsDB()
        stock_list = [stock[0] for stock in stockDB.stockList()]
        news_dict = newsDB.getNewNews(stock_list)
        for stock_id, news in news_dict.items():
            for news_one in news:
                news_bot.sendMessage(chat_id=chat_id, text=newsDB.formatNews(stock_id, news_one))
        sendMessage("News check ran succesfully")
    elif command == 'add_keyword':
        newstriggerDB = NewsTriggerDB()
        items = message.split()
        if len(items) != 3:
            sendMessage(
                "Incorrect Usage!\n\nCorrect Usage:\n\t/add_keyword breakthrough 200"
            )
        else:
            try:
                points = int(items[2])
                newstriggerDB.addTrigger(items[1], points)
                sendMessage(
                    f"{items[1]} succesfully added to keyword for {items[2]} points!"
                )
            except:
                sendMessage(
                    f"Sorry, your keyword was not added, possibly because the keyword already exists, or was not an integer."
                )
    elif command == 'remove_keyword':
        newstriggerDB = NewsTriggerDB()
        items = message.split()
        if len(items) != 2:
            sendMessage(
                "Incorrect Usage!\n\nCorrect Usage:\n\t/remove_keyword breakthrough"
            )
        else:
            newstriggerDB.removeTrigger(items[1])
            sendMessage(f"{items[1]} succesfully removed from keywords")
    elif command == 'change_keyword':
        newstriggerDB = NewsTriggerDB()
        items = message.split()
        if len(items) != 3:
            sendMessage(
                "Incorrect Usage!\n\nCorrect Usage:\n\t/change_keyword breakthrough 200"
            )
        else:
            try:
                points = int(items[2])
                newstriggerDB.removeTrigger(items[1])
                newstriggerDB.addTrigger(items[1], items[2])
                sendMessage(
                    f"{items[1]} succesfully changed from keyword for {items[2]} points!"
                )
            except:
                sendMessage(
                    f"Points should be an integer but got {items[2]} instead")
    elif command == 'list_keyword':
        newstriggerDB = NewsTriggerDB()
        items = message.split()
        triggers = newstriggerDB.getAllTriggers()
        message = "Trigger\t-\tPoints\n"
        for trigger, points in triggers:
            message += f"{trigger}\t-\t{points}\n"
        sendMessage(message)
    elif command == 'get_stock':
        items = message.split()
        if len(items) != 2:
            sendMessage(
                "Incorrect Usage!\n\nCorrect Usage:\n\t/get_stock AAPL")
        else:
            stock_info = checkStock(items[1])
            line = f"Stock ID : {items[1]}\nStock Price : ${stock_info[0]}\nIncrease/Decrease % : {'' if stock_info[1] < 0 else '+'}{stock_info[1]}%\nVolume :  {stock_info[2]}\nDay's Range : {stock_info[3]}"
            sendMessage(line)
    elif command == 'start_dashboard':
        subprocess.call(
            'DISPLAY=:0 /usr/bin/chromium-browser --noerrdialogs --disable-infobars --kiosk --app= http://0.0.0.0:4000 &',
            shell=True)
        sendMessage("Dashboard starting...")
    elif command == 'stop_dashboard':
        subprocess.call('pkill -o chromium', shell=True)
        sendMessage("Dashboard stopping...")
    elif command == "dashboard_link":
        ips = subprocess.check_output("hostname -I", shell=True).decode("utf-8").split()
        ip = ips[1]
        sendMessage(f"Link to your dashboard:\n{ip}:4000")
    elif command == "add_portfolio":
        stateDB = StateDB()
        stateDB.setState("add_portfolio")
        sendMessage("What is the ticker name of the stock? eg. AAPL (type C to cancel)")
    elif command == "view_portfolio":
        portfolioDB = PortfolioDB()
        portfolio = portfolioDB.getPortfolio()
        overall = portfolioDB.OverallPortfolio()
        rate = conversionRate()
        message = f"Investment Amount (USD): ${overall['investment']}\nInvestment Amount (SGD): ${round(overall['investment'] * rate, 2)}\nCurrent Amount (USD): ${overall['current']}\nCurrent Amount (SGD): ${round(overall['current'] * rate, 2)}\nPercentage: {'+' if overall['percentage'] > 0 else ''}{overall['percentage']}%\n\n"   
        message += "Ticker - Quantity - Investment - Current - Per(%)\n"
        for stock_id, details in portfolio.items():
            message += f"{stock_id} : {details['quantity']} - ${details['value']} - ${details['current']} : {'+' if details['percentage'] > 0 else ''}{details['percentage']}%\n"
        sendMessage(message)
    elif command == 'reboot':
        sendMessage("Rebooting Raspberry Pi...")
        subprocess.call('sudo reboot now', shell=True)
    else:
        sendMessage(f"Invalid command /{command}!")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        if not (time.strftime("%H") == '21' and int(time.strftime("%M")) < 30):
            tradingMode()
    else:
        QuarterlyCheck()
