import sqlite3

class PortfolioDB():
    """ All operations to do with buying, selling stocks from the portfolio"""
    def __init__(self):
        self.conn = sqlite3.connect("portfolio.db", check_same_thread=False)
        self.cur = self.conn.cursor()
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS portfolio (stock_id TEXT, quantity REAL , unit_price REAL, commission_price REAL, date TEXT, trans_type TEXT)"""
        )

    def addStock(self, stock_id, quantity , unit_price, commission_price, date, trans_type):
        """ Add record of buy or selling stock """
        self.conn.execute(
            """INSERT INTO portfolio (stock_id, quantity , unit_price, commission_price, date, trans_type) values (?,?,?,?,?,?) """,
            (stock_id, quantity , unit_price, commission_price, date, trans_type))
        self.conn.commit()

    def listPortfolio(self) -> list:
        """ Lists all stocks in the database """
        stocks = self.conn.execute("""SELECT * FROM portfolio""").fetchall()
        return sorted(stocks)