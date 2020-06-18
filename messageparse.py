def newMessage(message):
    """ Parse a new message received from Telegram """
    if message[0] == '/':
        command = message.split()[0].strip('/')
    else:
        sendMessage(f"'{message}' is not a valid command.\nType /help for more info")
        return
    if command == 'help':
        sendMessage("Welcome to the Stock bot!\nMade by Sachin Ramanathan")
    elif command == 'add_stock':
        stockDB = StockDB()
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
        stockDB = StockDB()
        items = message.split()
        if len(items) != 3:
            sendMessage("Incorrect Usage!\n\nCorrect Usage:\n\t/remove_stock AAPL BUY")
        else:
            stockDB.removeStock(items[1],items[2])
            sendMessage(f"{items[1]} stock succesfully removed from watchlist!")
    elif command == 'change_stock':
        stockDB = StockDB()
        items = message.split()
        if len(items) != 4:
            sendMessage("Incorrect Usage!\n\nCorrect Usage:\n\t/change_stock AAPL 200 SELL")
        else:
            stockDB.changeStock(items[1],items[2],items[3])
            sendMessage(f"{items[1]} stock succesfully changed in watchlist!")
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
        for stock_id,stock_info in sorted(stock_data.items()):
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
        for stock_id,news in news_dict.items():
            for news_one in news:
                sendMessage(newsDB.formatNews(stock_id,news_one))
        sendMessage("News check ran succesfully")
    elif command == 'add_keyword':
        newstriggerDB = NewsTriggerDB()
        items = message.split()
        if len(items) != 3:
            sendMessage("Incorrect Usage!\n\nCorrect Usage:\n\t/add_keyword breakthrough 200")
        else:
            try:
                points = int(items[2])
                newstriggerDB.addTrigger(items[1],points)
                sendMessage(f"{items[1]} succesfully added to keyword for {items[2]} points!")
            except:
                sendMessage(f"Sorry, your keyword was not added, possibly because the keyword already exists, or was not an integer.")
    elif command == 'remove_keyword':
        newstriggerDB = NewsTriggerDB()
        items = message.split()
        if len(items) != 2:
            sendMessage("Incorrect Usage!\n\nCorrect Usage:\n\t/remove_keyword breakthrough")
        else:
            newstriggerDB.removeTrigger(items[1])
            sendMessage(f"{items[1]} succesfully removed from keywords")
    elif command == 'change_keyword':
        newstriggerDB = NewsTriggerDB()
        items = message.split()
        if len(items) != 3:
            sendMessage("Incorrect Usage!\n\nCorrect Usage:\n\t/change_keyword breakthrough 200")
        else:
            try:
                points = int(items[2])
                newstriggerDB.removeTrigger(items[1])
                newstriggerDB.addTrigger(items[1], items[2])
                sendMessage(f"{items[1]} succesfully changed from keyword for {items[2]} points!")
            except:
                sendMessage(f"Points should be an integer but got {items[2]} instead")
    elif command == 'list_keyword':
        newstriggerDB = NewsTriggerDB()
        items = message.split()
        triggers = newstriggerDB.getAllTriggers()
        message = "Trigger\t-\tPoints\n"
        for trigger,points in triggers:
            message += f"{trigger}\t-\t{points}\n"
        sendMessage(message)
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
    from loggingconfig import logging
    from actions import sendMessage, checkStocksThreaded, QuarterlyCheck, PredictionRecordDB, predictionsCheck, StockDB, NewsDB, NewsTriggerDB, checkStock