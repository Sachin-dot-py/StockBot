import sqlite3
import time

class StockDB():
    """ All operations to do with adding, removing and getting stocks from the watchlist"""
    def __init__(self):
        self.conn = sqlite3.connect("stocks.db") 
        self.cur = self.conn.cursor()
        self.conn.execute("""CREATE TABLE IF NOT EXISTS stocklist (stock_id TEXT, stock_trigger REAL , trigger_type TEXT)""")
    
    def addStock(self, stock_id : str, stock_trigger : float, trigger_type : str):
        """ Adds a stock to the database. trigger_type can be 'buy' or 'sell' """
        trigger_type = 'sell' if trigger_type.lower() == 'sell' else 'buy'
        self.conn.execute("""INSERT INTO stocklist (stock_id, stock_trigger, trigger_type) values (?,?,?) """, (stock_id,stock_trigger,trigger_type))
        self.conn.commit()

    def removeStock(self, stock_id : str):
        """ Removes a stock from the database."""
        self.conn.execute("""DELETE FROM stocklist WHERE stock_id=?""",(stock_id,))
        self.conn.commit()

    def changeStock(self, stock_id : str, new_trigger : int, trigger_type : str):
        """ Changes the trigger value and type of a stock from the database"""
        self.conn.execute("""UPDATE stocklist SET stock_trigger=? WHERE stock_id=?, trigger_type=? """,(new_trigger,stock_id,trigger_type))
        conn.commit()

    def stockList(self) -> list:
        """ Lists all stocks in the database """
        stocks = self.conn.execute("""SELECT * FROM stocklist""").fetchall()
        return stocks

class MsgRecordDB():
    """ Managing records of previous alert sent by run_check """
    def __init__(self):
        self.conn = sqlite3.connect("stocks.db") 
        self.cur = self.conn.cursor()
        self.conn.execute("""CREATE TABLE IF NOT EXISTS lastmessages (stock_id TEXT, trigger_type TEXT, trigger_time TEXT)""")

    def addMsgRecord(self, stock_id : str, trigger_type : str):
        """ Adding the record of a sent alert """
        current_time = time.strftime("%b %d %Y, %H:%M")
        self.conn.execute("""INSERT INTO lastmessages (stock_id, trigger_type, trigger_time) values (?,?,?)""", (stock_id,trigger_type,current_time))
        self.conn.commit()

    def removeMsgRecord(self, stock_id : str, trigger_type : str):
        """ Removing a record of a sent alert """
        self.conn.execute("""DELETE FROM lastmessages WHERE stock_id=? AND trigger_type=?""",(stock_id,trigger_type))
        self.conn.commit()

    def getMsgRecord(self, stock_id : str, trigger_type : str) -> tuple:
        """ Getting a single alert record for a stock id """
        record = self.conn.execute("""SELECT * FROM lastmessages WHERE stock_id=? AND trigger_type=?""",(stock_id,trigger_type)).fetchone()
        return record

    def getMsgRecords(self) -> list:
        """ Getting previous alert records """
        records = self.conn.execute("""SELECT * FROM lastmessages""").fetchall()
        return records

stockDB = StockDB()
msgrecordDB = MsgRecordDB()