# Stock Bot (v2)

 [Stock Bot](t.me/Stock13Bot) is a Telegram bot that allows you to track your favourite stocks, and get alerts when they cross your target price. It also sends you a message when a prediction is set for a stock in your watchlist.

## Getting started
- Clone this repo to your computer
- Install the requirements using ```python3 pip3 install -r requirements.txt```
- Create a credentials.py file in the below format:
```python3
url = 'SITE_URL'
logfile = 'LOG_FILE_NAME'
token = 'TELEGRAM_TOKEN'
```
- Type ```flask run``` and to start the app
- Use serveo.net to expose your local ip to the internet
```shell
$ ssh -R sachin@serveo.net:22:localhost:22 serveo.net
``` 
- You're all set!