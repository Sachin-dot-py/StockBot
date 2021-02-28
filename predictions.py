from portfolio import PortfolioDB
from selenium import webdriver
import pandas as pd
from stockdb import StockDB, PredictionRecordDB
from loggingconfig import logging

def getPredictions():
    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.wsj.com/market-data/stocks/upgradesdowngrades')
    dfs = pd.read_html(driver.page_source)
    df = pd.concat(dfs).fillna('-')
    df.reset_index(inplace=True)
    df = df.drop('index', axis=1)
    return df


def predictionsCheck():
    from actions import sendMessage
    stockDB = StockDB()
    pfdb = PortfolioDB()
    predictionrecordDB = PredictionRecordDB()
    predictions = getPredictions()
    stocks = list(set(pfdb.CurrentStocks() + [stock[0].upper() for stock in stockDB.stockList()]))
    for result in predictions.values:
        ticker = result[1]
        if ticker.upper() in stocks:
            prev_alert = predictionrecordDB.getPredictionRecord(*result)
            if not prev_alert:
                message = f"Prediction for {result[0]} ({result[1]}):\nFirm: {result[2]}\nRatings Change: {result[3]}\nPrice Target: {result[4]}"
                sendMessage(message)
                predictionrecordDB.addPredictionRecord(*result)
    logging.info("Predictions check ran succesfully")


if __name__ == "__main__":
    from actions import sendMessage
    predictionsCheck()
