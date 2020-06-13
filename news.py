from actions import *
from loggingconfig import *
import requests
from bs4 import BeautifulSoup
import sqlite3
import re
from datetime import datetime, timedelta

class NewsDB():

    def __init__(self):
        self.conn = sqlite3.connect('news.db')
        self.cur = self.conn.cursor()

    @staticmethod
    def getCompany(stock_id : str) -> str:
        r = requests.get('https://api.iextrading.com/1.0/ref-data/symbols')
        stock_list = r.json()
        for stock in stock_list:
            if stock['symbol'].upper() == stock_id.upper(): return stock['name'].replace('INC','').replace('LTD','').split('-')[0].title()
        return stock_id

    @staticmethod
    def formatNews(stock_id : str, news : tuple) -> str:
        message = f"""News for {stock_id}:\n{news[2]}\n{news[1]}"""
        return message

    @staticmethod
    def getNews(stock_id : str) -> list:
        link = f'https://news.google.com/rss/search?q={stock_id}'
        req = requests.get(link)
        soup = BeautifulSoup(req.text,'lxml')
        items = soup.find_all('item')
        news = []
        for item in items:
            title = item.find('title').text
            link = item.contents[2].strip()
            date = datetime.strftime(datetime.strptime(item.find('pubdate').text, "%a, %d %b %Y %H:%M:%S GMT") + timedelta(hours=9),"%A, %d %B %Y %H:%M:%S")
            description = item.find('description').text
            source = item.find('source').text
            sourcelink = item.find('source')['url']
            # news_dict = {'title' : title, 'link' : link, 'date' : date, 'description' : description, 'source' : source, 'sourcelink' : sourcelink}
            news.append((title,link,date,description,source,sourcelink))
        return news

    def removeDuplicates(self, stock_id : str, news : list) -> list:
        self.conn.execute(f"""CREATE TABLE IF NOT EXISTS [{stock_id}] (title TEXT, link TEXT, date TEXT, description TEXT, source TEXT, sourcelink TEXT)""")
        news = [news_record for news_record in news if not self.conn.execute(f"""SELECT * FROM [{stock_id}] WHERE title=? AND link=? AND date=? AND description=? AND source=? AND sourcelink=?""", news_record).fetchone()]
        return news

    def addNews(self, stock_id : str, news : list):
        self.conn.execute(f"""CREATE TABLE IF NOT EXISTS [{stock_id}] (title TEXT, link TEXT, date TEXT, description TEXT, source TEXT, sourcelink TEXT)""")
        self.conn.executemany(f"""INSERT INTO [{stock_id}] VALUES (?,?,?,?,?,?)""", news)
        self.conn.commit()
        
    def getImportant(self, stock_id : str, news : list) -> list:
        return news[:1] # TODO

    def checkNews(self, stock_id):
        stock_name = self.getCompany(stock_id)
        news = self.getNews(stock_name)
        news = self.removeDuplicates(stock_id, news)
        self.addNews(stock_id, news)
        news = self.getImportant(stock_id, news)
        return news

    def getAllNews(self, stock_ids : list) -> dict:
        news_dict = dict()
        for stock_id in stock_ids:
            news = self.checkNews(stock_id)
            news_dict[stock_id] = news
        return news_dict
        
newsDB = NewsDB()

if __name__ == "__main__":
    stock_list = [stock[0] for stock in stockDB.stockList()]
    news_dict = newsDB.getAllNews(stock_list)
    for stock_id,news in news_dict.items():
        for news_one in news:
            sendMessage(newsDB.formatNews(stock_id,news_one))
    logging.info("Performed news check successfully")