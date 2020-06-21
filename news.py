from loggingconfig import logging
from stockdb import StockDB
import requests
from bs4 import BeautifulSoup
import sqlite3
import re
from datetime import datetime, timedelta
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import difflib
if __name__ != "news":
    from actions import sendMessage

class NewsTriggerDB():

    def __init__(self):
        self.conn = sqlite3.connect('stocks.db', check_same_thread=False)
        self.cur = self.conn.cursor()
        self.conn.execute("""CREATE TABLE IF NOT EXISTS news_triggers (trigger TEXT, points REAL)""")

    def addTrigger(self, trigger : str, points : int):
        epoints = self.getTriggerPts(trigger)
        if epoints:
            self.conn.execute("""UPDATE news_triggers SET points=? WHERE trigger=?""", (points,trigger))
        else:
            self.conn.execute("""INSERT INTO news_triggers values(?,?)""", (trigger,points))
        self.conn.commit()

    def removeTrigger(self, trigger : str):
        self.conn.execute("""DELETE FROM news_triggers WHERE trigger=?""",(trigger,))
        self.conn.commit()

    def getTriggerPts(self, trigger : str) -> int:
        points = self.conn.execute("""SELECT * FROM news_triggers WHERE trigger=?""",(trigger,)).fetchone()
        return points

    def getAllTriggers(self) -> list:
        triggers = self.conn.execute("""SELECT * FROM news_triggers""").fetchall()
        return triggers

class NewsDB():

    def __init__(self):
        self.conn = sqlite3.connect('news.db', check_same_thread=False)
        self.cur = self.conn.cursor()
        r = requests.get('https://api.iextrading.com/1.0/ref-data/symbols')
        self.stock_symbols = r.json()
        self.lemmatizer = WordNetLemmatizer() 
        self.stopwords = set(stopwords.words('english'))
        self.phrase_dict = {'work from home' : 100, 'takes a nosedive' : 100, 'take a nosedive' : 100}
        self.point_dict = dict(NewsTriggerDB().getAllTriggers())
        
    @staticmethod
    def formatNews(stock_id : str, news : tuple) -> str:
        message = f"""News for {stock_id}:\n{news[2]}\n{news[1]}"""
        return message

    @staticmethod
    def getAllNews(stock_id : str) -> list:
        news = []
        link = f'https://news.google.com/rss/search?q={f"{stock_id} stock news"}'
        req = requests.get(link)
        soup = BeautifulSoup(req.text,'lxml')
        items = soup.find_all('item')
        for item in items:
            title = item.find('title').text
            link = item.contents[2].strip()
            date_obj = datetime.strptime(item.find('pubdate').text, "%a, %d %b %Y %H:%M:%S GMT") + timedelta(hours=8)
            date = datetime.strftime(date_obj, "%A, %d %B %Y %H:%M:%S")
            # description = item.find('description').text
            source = item.find('source').text
            sourcelink = item.find('source')['url']
            # news_dict = {'title' : title, 'link' : link, 'date' : date, 'source' : source, 'sourcelink' : sourcelink}
            if date_obj > datetime.now() - timedelta(hours=24) : news.append((title,link,date,source,sourcelink))
        return news

    def getCompany(self, stock_id : str) -> str:
        for stock in self.stock_symbols:
            if stock['symbol'].upper() == stock_id.upper(): return stock['name'].replace('INC','').replace('LTD','').split('-')[0].title().strip()
        return stock_id

    def removeDuplicates(self, stock_id : str, news : list) -> list:
        self.conn.execute(f"""CREATE TABLE IF NOT EXISTS [{stock_id}] (title TEXT, link TEXT, date TEXT, source TEXT, sourcelink TEXT)""")
        news = [news_record for news_record in news if not self.conn.execute(f"""SELECT * FROM [{stock_id}] WHERE title=? AND source=?""", (news_record[0], news_record[3])).fetchone()]
        return news

    def addNews(self, stock_id : str, news : list):
        self.conn.execute(f"""CREATE TABLE IF NOT EXISTS [{stock_id}] (title TEXT, link TEXT, date TEXT, source TEXT, sourcelink TEXT)""")
        self.conn.executemany(f"""INSERT INTO [{stock_id}] VALUES (?,?,?,?,?)""", news)
        self.conn.commit()
        
    def getImportant(self, stock_id : str, stock_name : str, news : list) -> list:
        imp_news = []
        for news_i in news:
            points = 0
            n = news_i[0]
            for phrase, points_gained in self.phrase_dict.items():
                if phrase in n.lower(): points += points_gained 
            tokenized_words = word_tokenize(n.lower())
            words = [self.lemmatizer.lemmatize(x) for x in tokenized_words if x not in self.stopwords and len(x) != 1]
            for word in words:
                points_gained = self.point_dict.get(word,None)
                if points_gained: points += points_gained 
            if points >= 100: imp_news.append(news_i)
        # news_imp = []
        # for news in imp_news:
        #     ratios = []
        #     ns = news[0].split()
        #     for n in ns:
        #         match1 = difflib.SequenceMatcher(None, n.lower(), stock_id.lower()).ratio()
        #         match2 = difflib.SequenceMatcher(None, n.lower(), stock_name.lower()).ratio()
        #         max_match = max((match1, match2))
        #         ratios.append(max_match)
        #     match_ratio = max(ratios)
        #     if match_ratio >= 0.5: news_imp.append(news)   
        # print(f"Stage 3: {stock_id} - {len(news_imp)}")
        return imp_news

    def getNews(self, stock_id):
        stock_name = self.getCompany(stock_id)
        # print(f"{stock_id} ({stock_name})")
        news = self.getAllNews(stock_id)
        # print(f"Stage 1: {len(news)}")
        news = self.removeDuplicates(stock_id, news)
        # print(f"Stage 2: {len(news)}")
        self.addNews(stock_id, news)
        news = self.getImportant(stock_id, stock_name, news)
        # print(f"Stage 3: {len(news)}")
        # print("------------------")
        return news

    def getNewNews(self, stock_ids : list) -> dict:
        news_dict = dict()
        for stock_id in stock_ids:
            news = self.getNews(stock_id)
            news_dict[stock_id] = news
        return news_dict
        
newsDB = NewsDB()
newstriggerDB = NewsTriggerDB()

if __name__ == "__main__":
    stockDB = StockDB()
    stock_list = [stock[0] for stock in stockDB.stockList()]
    news_dict = newsDB.getNewNews(stock_list)
    for stock_id,news in news_dict.items():
        for news_one in news:
            sendMessage(newsDB.formatNews(stock_id,news_one))
    logging.info("Performed news check successfully")