# Stock Bot (v2)

 [Stock Bot](https://t.me/Stock13Bot) is a Telegram bot that allows you to track your favourite stocks, and get alerts when they cross your target price. It also sends you a message when a prediction is set for a stock in your watchlist.

## Getting started
- Clone this repo to your computer
- Install the requirements using ```pip3 install -r requirements.txt```
- Create a credentials.py file in the below format:
```python3
logfile = 'LOG_FILE_NAME'
token = 'TELEGRAM_TOKEN'
chat_id = 'CHAT_ID'
```
- Type ```flask run --host=0.0.0.0``` and to start the app
- You're all set!
- Visit ```0.0.0.0:4000``` on your device for the dashboard
- For other devices, visit ```<YOUR_PRIVATE_IP>:4000```. For example, if your private IP is 192.168.1.12, visit ```192.168.1.12:4000```
- [Image of Stock Dashboard](https://i.imgur.com/iF568mt.png)
