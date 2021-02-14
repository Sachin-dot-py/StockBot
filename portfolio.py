import sqlite3
import os
from credentials import cwd

class PortfolioDB():
    """ All operations to do with buying, selling stocks from the portfolio"""
    def __init__(self):
        os.chdir(cwd)
        self.conn = sqlite3.connect("portfolio.db", check_same_thread=False)
        self.cur = self.conn.cursor()
        self.conn.execute("""CREATE TABLE IF NOT EXISTS portfolio (stock_id TEXT, quantity REAL , unit_price REAL, commission_price REAL, date TEXT, trans_type TEXT)""")
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS uninvested (amount REAL)"""
        )
    
    def getPortfolio(self, stock_datas={}): # stock_datas = {"AAPL" : 105.5, "CCL" : 3.02}
        from actions import checkStock, _checkStock, checkStocksThreaded
        stocks = {}
        portfolios = self.PortfolioList()
        if not stock_datas: 
            results = checkStocksThreaded([portfolio[0] for portfolio in portfolios])
            stock_datas = {stock_id: details[0] for stock_id, details in results.items()}
        for portfolio in portfolios:
            stock_id, quantity, unit_price, commission_price, date, trans_type = portfolio

            if stock_id not in stocks.keys():
                cur_quantity = 0
                cur_value = 0
            else:
                cur = stocks[stock_id]
                cur_quantity = cur['quantity']
                cur_value = cur['value']

            trans_value = unit_price * quantity

            if trans_type == "buy":
                cur_quantity += quantity
                cur_value += trans_value

            if trans_type == "sell":
                wap = (cur_value / cur_quantity) if cur_quantity != 0 else 0
                trans_value = wap * quantity

                cur_quantity -= quantity
                cur_value -= trans_value

            wap = (cur_value / cur_quantity) if cur_quantity != 0 else 0

            try:  
                if stock_id in stock_datas.keys():
                    quote_price = stock_datas[stock_id]
                else:
                    try:
                        quote_price, *_ = checkStock(stock_id)
                    except:
                        quote_price, *_ = _checkStock(stock_id)
                
                latest_value = quote_price * cur_quantity
                percentage = 0 if cur_value == 0 else ((latest_value-cur_value)/cur_value)*100
                
                if cur_quantity != 0: 
                    stocks[stock_id] = {'quantity' : int(cur_quantity), 'value' : round(cur_value, 2), 'wap' : wap, 'current' : round(latest_value, 2), 'percentage' : round(percentage,2)}
                else:
                    del stocks[stock_id]
            
            except:
                if cur_quantity != 0:
                    stocks[stock_id] = {'quantity' : int(cur_quantity), 'value' : cur_value, 'wap' : wap, 'current' : None, 'percentage' : None}
                else:
                    del stocks[stock_id]

            """trans_value = unit_price * quantity

            if stock_id not in stocks.keys():
                cur_quantity = 0
                cur_value = 0
            else:
                cur = stocks[stock_id]
                cur_quantity = cur['quantity']
                cur_value = cur['value']
                
            if trans_type == 'buy':
                new_quantity =  cur_quantity + quantity 
                new_value = cur_value  + trans_value 
            else:
                new_quantity =  cur_quantity - quantity
                new_value = cur_value  - trans_value

            try:
                quote_price, *_ = checkStock(stock_id)
            except:
                quote_price, *_ = _checkStock(stock_id)
            
            latest_value = quote_price * new_quantity
            if new_value != 0:
                percentage = ((latest_value-new_value)/new_value)*100
            else:
                percentage = 0

            stocks[stock_id] = {'quantity' : int(new_quantity), 'value' : new_value, 'current' : latest_value, 'percentage' : round(percentage,2)}"""
        return stocks

    def OverallPortfolio(self, portfolio={}):
        """ Get details of portfolio as a whole"""
        uninvested = float(self.getUninvested())
        investment_val = 0
        current_val = 0

        if portfolio=={}: portfolio = self.getPortfolio()
        
        for _, stock in portfolio.items():
            investment_val += stock['value']
            current_val += stock['current']

        try:
            percentage = ((current_val-investment_val)/investment_val)*100  
        except:
            percentage = 0

        overall = {'investment' : round(investment_val, 2), 'current' : round(current_val+uninvested, 2), 'percentage': round(percentage, 2), 'uninvested' : round(uninvested, 2)}
        return overall

    def addStock(self, stock_id, quantity , unit_price, commission_price, date, trans_type):
        """ Add record of buy or selling stock """
        self.conn.execute(
            """INSERT INTO portfolio (stock_id, quantity , unit_price, commission_price, date, trans_type) values (?,?,?,?,?,?) """,
            (stock_id, int(quantity) , unit_price, commission_price, date, trans_type))

        if trans_type.lower() == "sell":
            self.addUninvested(float((int(quantity) * float(unit_price)) + float(commission_price)))
        elif trans_type.lower() == "buy":
            self.subtractUninvested(float((int(quantity) * float(unit_price)) + float(commission_price)))
        self.conn.commit()

    def PortfolioList(self):
        """ Lists the transactions in the portfolio """
        portfolio = self.conn.execute("""SELECT * from portfolio""").fetchall()
        return portfolio

    def addUninvested(self, amount_add: float):
        """ Add uninvested money to database """
        record = self.conn.execute("""SELECT amount FROM uninvested""").fetchone()
        if record:
            amount = float(record[0]) + float(amount_add)
            self.conn.execute("""UPDATE uninvested SET amount=?""", (amount,))
        else:
            amount = float(amount_add)
            self.conn.execute("""INSERT INTO uninvested VALUES (?)""", (amount,))
        self.conn.commit()
        return amount

    def getUninvested(self) -> float:
        """ Get uninvested money in database """
        record = self.conn.execute("""SELECT amount FROM uninvested""").fetchone()
        if record:
            return float(record[0])
        else:
            return 0

    def subtractUninvested(self, amount_sub : float) -> float:
        """ Subtract uninvested money from database """
        record = self.conn.execute("""SELECT amount FROM uninvested""").fetchone()
        if record:
            amount = float(record[0]) - float(amount_sub)
            self.conn.execute("""UPDATE uninvested SET amount=?""", (amount,))
        else:
            amount = float(-amount_sub)
        self.conn.commit()
        return amount
