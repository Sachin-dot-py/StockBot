from actions import *
from loggingconfig import *
import requests
from bs4 import BeautifulSoup
import sqlite3
import re
from datetime import datetime, timedelta
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import difflib

class NewsDB():

    def __init__(self):
        self.conn = sqlite3.connect('news.db')
        self.cur = self.conn.cursor()
        r = requests.get('https://api.iextrading.com/1.0/ref-data/symbols')
        self.stock_symbols = r.json()
        self.lemmatizer = WordNetLemmatizer() 
        self.stopwords = set(stopwords.words('english'))
        self.phrase_dict = {'work from home' : 100, 'takes a nosedive' : 100, 'take a nosedive' : 100}
        self.point_dict = {'analyst' : 200, 'plummet' : 200, 'recover' : 50, 'recovery' : 50,
        'capacity' : 200, 'impact' : 50, 'market' : 25, 'rebound' : 200, 'rebounding' : 200, 'contract' : 200, 'invest' : 200, 'investing' : 200, 
        'stake' : 200, 'new' : 50, 'profit' : 200, 'profiting' : 200, 'loss' : 200, 'lost' : 200, 'losses' : 200, 'sale' : 200, 'purchase' : 200, 'bankrupt' : 200, 'peak' : 200, 
        'high' : 200, 'low' : 200, 'crash' : 200, 'soar' : 200, 'stream' : 50, 'streaming' : 50, 'cloud' : 100, 'upgrade' : 200, 'downgrade' : 200, 'rate' : 200,
        'positive' : 200, 'negative' : 200, 'cancel' : 200, 'blocked' : 100, 'deal' : 200, 'sign' : 200, 'benefit' : 200, 'under-value' : 50, 'undervalue' : 50,
        'lower-value' : 50, 'lowervalue' : 50, 'depth' : 200, 'develop' : 200, 'developing' : 200, 'hit' : 200, 'opinion' : 200, 'work-from-home' : 200, 'fail' : 200, 'win' : 200,
        'dip' : 200, 'trend' : 200, 'listing' : 200, 'decline' : 200, 'drop' : 200, 'collapse' : 200, 'boom' : 200, 'surge' : 200, 'steady' : 200, 'plunge' : 200, 'earning' : 200,
        'license' : 50, 'join' : 100, 'complain' : 100, 'freeze' : 200, 'capability' : 200, 'production' : 100, 'potential' : 100, 'upside' : 100, 'outperform' : 200, 'significant' : 200,
        'loan' : 100, 'provision' : 100, 'milestone' : 200, 'billion' : 200, 'million' : 200, 'releases' : 200, } 

    @staticmethod
    def formatNews(stock_id : str, news : tuple) -> str:
        message = f"""News for {stock_id}:\n{news[2]}\n{news[1]}"""
        return message

    @staticmethod
    def getAllNews(stock_id : str, stock_name : str) -> list:
        news = []
        for i in [stock_id, stock_name]:
            link = f'https://news.google.com/rss/search?q={i}+when:1d'
            req = requests.get(link)
            soup = BeautifulSoup(req.text,'lxml')
            items = soup.find_all('item')
            for item in items:
                title = item.find('title').text
                link = item.contents[2].strip()
                date_obj = datetime.strptime(item.find('pubdate').text, "%a, %d %b %Y %H:%M:%S GMT") + timedelta(hours=8)
                date = datetime.strftime(date_obj, "%A, %d %B %Y %H:%M:%S")
                description = item.find('description').text
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
        news_imp = []
        for news in imp_news:
            ratios = []
            ns = news[0].split()
            for n in ns:
                match1 = difflib.SequenceMatcher(None, n.lower(), stock_id.lower()).ratio()
                match2 = difflib.SequenceMatcher(None, n.lower(), stock_name.lower()).ratio()
                max_match = max((match1, match2))
                ratios.append(max_match)
            match_ratio = max(ratios)
            if match_ratio >= 0.5: news_imp.append(news)       
        return news_imp

    def getNews(self, stock_id):
        stock_name = self.getCompany(stock_id)
        news = self.getAllNews(stock_id, stock_name)
        news = self.removeDuplicates(stock_id, news)
        self.addNews(stock_id, news)
        news = self.getImportant(stock_id, stock_name, news)
        return news

    def getNewNews(self, stock_ids : list) -> dict:
        news_dict = dict()
        for stock_id in stock_ids:
            news = self.getNews(stock_id)
            news_dict[stock_id] = news
        return news_dict
        
newsDB = NewsDB()

if __name__ == "__main__":
    stock_list = [stock[0] for stock in stockDB.stockList()]
    news_dict = newsDB.getNewNews(stock_list)
    for stock_id,news in news_dict.items():
        for news_one in news:
            sendMessage(newsDB.formatNews(stock_id,news_one))
    logging.info("Performed news check successfully")