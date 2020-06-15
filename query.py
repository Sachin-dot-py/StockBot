import sqlite3

class DB():
    
    def __init__(self, db : str):
        self.conn = sqlite3.connect(db)
        self.cur = conn.cursor()

    def run(self, query : str):
        self.conn.execute(query)
        self.conn.commit()

    def get(self, query : str):
        results = self.conn.execute(query)
        self.conn.commit()
        return results

stockdb = DB('stocks.db')
newsdb = DB('news.db')